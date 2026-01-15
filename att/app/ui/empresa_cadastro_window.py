# app/ui/empresa_cadastro_window.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QFrame,
    QGroupBox, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from typing import Optional, Dict, Any
import sys

# Adaptação dos imports de lógica
try:
    from app import empresa_logic
    from app.config import ConfigLoader
except ImportError:
    # Fallback para execução isolada (dev)
    pass

from app.ui.styles import get_stylesheet

class EmpresaCadastroWindow(QDialog):
    def __init__(self, config: ConfigLoader):
        super().__init__()
        self.config = config
        self.selected_cnpj: Optional[str] = None

        # Inicializa banco
        try:
            empresa_logic.inicializar_banco(self.config.db_empresas_path)
        except Exception as e:
            QMessageBox.critical(self, "Erro DB", f"Erro CRÍTICO ao inicializar banco:\n{e}")
            self.reject()

        self.init_ui()
        self.atualizar_tabela()

    def init_ui(self):
        self.setWindowTitle("Gestão de Empresas e Regras")
        self.resize(900, 650)
        self.setStyleSheet(get_stylesheet(self.config.font_family))

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # --- FRAME DE CADASTRO (Superior) ---
        cadastro_group = QGroupBox("Cadastrar / Editar Empresa")
        cadastro_layout = QVBoxLayout(cadastro_group)
        cadastro_layout.setSpacing(15)

        # Linha 1: CNPJ e Razão
        row1 = QHBoxLayout()

        self.txt_cnpj = QLineEdit()
        self.txt_cnpj.setPlaceholderText("CNPJ (somente números)")
        self.txt_cnpj.setFixedWidth(150)

        self.txt_razao = QLineEdit()
        self.txt_razao.setPlaceholderText("Razão Social")

        row1.addWidget(QLabel("CNPJ:"))
        row1.addWidget(self.txt_cnpj)
        row1.addWidget(QLabel("Razão Social:"))
        row1.addWidget(self.txt_razao)

        cadastro_layout.addLayout(row1)

        # Regras de Automação
        regras_auto_group = QGroupBox("Regras de Automação")
        ra_layout = QVBoxLayout(regras_auto_group)
        self.chk_ignorar_canceladas = QCheckBox("Ignorar Notas Fiscais Canceladas?")
        ra_layout.addWidget(self.chk_ignorar_canceladas)
        cadastro_layout.addWidget(regras_auto_group)

        # Regras do Analisador
        regras_ana_group = QGroupBox("Regras do Analisador Fiscal")
        ran_layout = QVBoxLayout(regras_ana_group)

        self.chk_simples = QCheckBox("Não calcular PIS/COFINS (Simples Nacional)?")
        self.chk_simples.setToolTip("Pula a validação de PIS/COFINS para este CNPJ.")

        self.chk_tolerancia_zero = QCheckBox("Usar Tolerância Zero (Valores Exatos)?")
        self.chk_tolerancia_zero.setToolTip("Valida impostos e totais com R$ 0,00 de tolerância.")

        self.chk_sem_c170 = QCheckBox("SPED não escritura C170 (Ignorar Itens)?")
        self.chk_sem_c170.setToolTip("Pula a validação de CFOP item a item (C170 vs <det>).")

        self.chk_ignorar_icms = QCheckBox("Desativar validação de crédito de ICMS?")
        self.chk_ignorar_icms.setToolTip("Desativa completamente a verificação de STATUS_ICMS.")

        self.chk_exigir_acum = QCheckBox("Exigir Acumulador (Forçar 'Revisar')?")
        self.chk_exigir_acum.setToolTip("Se um acumulador não for encontrado, força o STATUS_GERAL da nota para 'REVISAR'.")

        ran_layout.addWidget(self.chk_simples)
        ran_layout.addWidget(self.chk_tolerancia_zero)
        ran_layout.addWidget(self.chk_sem_c170)
        ran_layout.addWidget(self.chk_ignorar_icms)
        ran_layout.addWidget(self.chk_exigir_acum)
        cadastro_layout.addWidget(regras_ana_group)

        # Botões de Ação do Cadastro
        btn_row = QHBoxLayout()
        self.btn_salvar = QPushButton("Salvar Empresa")
        self.btn_salvar.setObjectName("Primary")
        self.btn_salvar.clicked.connect(self.salvar_empresa)

        self.btn_limpar = QPushButton("Limpar Campos")
        self.btn_limpar.clicked.connect(self.limpar_form)

        btn_row.addWidget(self.btn_salvar)
        btn_row.addWidget(self.btn_limpar)
        btn_row.addStretch()

        cadastro_layout.addLayout(btn_row)
        main_layout.addWidget(cadastro_group)

        # --- FRAME DE LISTAGEM (Inferior) ---
        lista_group = QGroupBox("Empresas Salvas")
        lista_layout = QVBoxLayout(lista_group)

        # Busca
        busca_row = QHBoxLayout()
        self.txt_busca = QLineEdit()
        self.txt_busca.setPlaceholderText("Buscar por CNPJ ou Razão...")
        self.txt_busca.textChanged.connect(lambda: self.atualizar_tabela(self.txt_busca.text()))

        btn_atualizar = QPushButton("Atualizar Lista")
        btn_atualizar.clicked.connect(lambda: self.atualizar_tabela(self.txt_busca.text()))

        busca_row.addWidget(QLabel("Buscar:"))
        busca_row.addWidget(self.txt_busca)
        busca_row.addWidget(btn_atualizar)
        lista_layout.addLayout(busca_row)

        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["CNPJ", "Razão Social"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_table_select)

        lista_layout.addWidget(self.table)

        # Botão Excluir
        self.btn_excluir = QPushButton("Excluir Selecionada")
        self.btn_excluir.setObjectName("Danger")
        self.btn_excluir.setEnabled(False)
        self.btn_excluir.clicked.connect(self.excluir_empresa)

        lista_layout.addWidget(self.btn_excluir, alignment=Qt.AlignRight)

        main_layout.addWidget(lista_group)

    def atualizar_tabela(self, search_term=""):
        try:
            empresas_list = empresa_logic.listar_todas_empresas(self.config.db_empresas_path, search_term)
            self.table.setRowCount(0)
            for row_idx, row_data in enumerate(empresas_list):
                self.table.insertRow(row_idx)
                # row_data é [cnpj, razao]
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0])))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(row_data[1])))
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar empresas:\n{e}")

    def on_table_select(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.selected_cnpj = None
            self.btn_excluir.setEnabled(False)
            return

        # Pega a linha selecionada
        row = selected_items[0].row()
        cnpj = self.table.item(row, 0).text()
        razao = self.table.item(row, 1).text()

        self.carregar_empresa(cnpj, razao)

    def carregar_empresa(self, cnpj, razao):
        self.selected_cnpj = cnpj
        self.btn_excluir.setEnabled(True)
        self.btn_salvar.setText("Atualizar Empresa")
        self.txt_cnpj.setText(cnpj)
        self.txt_cnpj.setDisabled(True) # Não pode editar PK
        self.txt_razao.setText(razao)

        try:
            regras = empresa_logic.obter_regras_empresa(self.config.db_empresas_path, cnpj) or {}
            self.chk_ignorar_canceladas.setChecked(regras.get('ignorar_canceladas', False))
            self.chk_simples.setChecked(regras.get('nao_calcular_pis_cofins', False))
            self.chk_tolerancia_zero.setChecked(regras.get('usar_tolerancia_zero', False))
            self.chk_sem_c170.setChecked(regras.get('sped_sem_c170_nfe', False))
            self.chk_ignorar_icms.setChecked(regras.get('ignorar_validacao_icms', False))
            self.chk_exigir_acum.setChecked(regras.get('exigir_acumulador', False))
        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"Erro ao carregar regras:\n{e}")

    def limpar_form(self):
        self.selected_cnpj = None
        self.txt_cnpj.clear()
        self.txt_cnpj.setDisabled(False)
        self.txt_cnpj.setFocus()
        self.txt_razao.clear()

        self.chk_ignorar_canceladas.setChecked(False)
        self.chk_simples.setChecked(False)
        self.chk_tolerancia_zero.setChecked(False)
        self.chk_sem_c170.setChecked(False)
        self.chk_ignorar_icms.setChecked(False)
        self.chk_exigir_acum.setChecked(False)

        self.btn_salvar.setText("Salvar Empresa")
        self.btn_excluir.setEnabled(False)
        self.table.clearSelection()

    def salvar_empresa(self):
        cnpj = self.txt_cnpj.text().strip()
        razao = self.txt_razao.text().strip()

        if not cnpj or not razao:
            QMessageBox.warning(self, "Aviso", "CNPJ e Razão Social são obrigatórios.")
            return

        regras_dict = {
            'ignorar_canceladas': self.chk_ignorar_canceladas.isChecked(),
            'nao_calcular_pis_cofins': self.chk_simples.isChecked(),
            'usar_tolerancia_zero': self.chk_tolerancia_zero.isChecked(),
            'sped_sem_c170_nfe': self.chk_sem_c170.isChecked(),
            'ignorar_validacao_icms': self.chk_ignorar_icms.isChecked(),
            'exigir_acumulador': self.chk_exigir_acum.isChecked(),
        }

        try:
            empresa_logic.salvar_empresa(self.config.db_empresas_path, cnpj, razao, regras_dict)
            QMessageBox.information(self, "Sucesso", "Empresa salva com sucesso.")
            self.limpar_form()
            self.atualizar_tabela(self.txt_busca.text())
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar no banco:\n{e}")

    def excluir_empresa(self):
        if not self.selected_cnpj: return

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja EXCLUIR a empresa CNPJ: {self.selected_cnpj}?\nEsta ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                empresa_logic.delete_empresa(self.config.db_empresas_path, self.selected_cnpj)
                QMessageBox.information(self, "Sucesso", "Empresa excluída.")
                self.limpar_form()
                self.atualizar_tabela(self.txt_busca.text())
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir empresa:\n{e}")

# Método de compatibilidade para chamada estática, se necessário
def main(config: ConfigLoader):
    win = EmpresaCadastroWindow(config)
    win.exec()
