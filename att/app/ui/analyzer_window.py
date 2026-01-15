# app/ui/analyzer_window.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QFileDialog, QProgressBar, QTextEdit, QFrame, QComboBox, QMessageBox, QGroupBox,
    QGridLayout
)
from PySide6.QtCore import Qt, Slot, QThread
from PySide6.QtGui import QIcon

import threading
import sys
import os
import subprocess
from pathlib import Path
from typing import List, Optional

from app.config import ConfigLoader
from app.ui.styles import get_stylesheet
from app.ui.qt_adapter import WorkerSignals, WindowAdapter

# Imports de lógica (compatibilidade)
from app.fiscal_logic import setup_logging, executar_analise_completa
# from app.ui.admin_window import AdminWindow # REMOVIDO: Janela não portada ainda

class AnalyzerWindow(QWidget):
    """
    Janela do Analisador Fiscal em PySide6.
    """
    def __init__(self, config: ConfigLoader, username: str, permissions: List[str]):
        super().__init__()
        self.config = config
        self.username = username
        self.permissions = permissions

        self.report_path: Optional[Path] = None
        self.log_filename: Optional[Path] = None

        # Sinais para thread worker
        self.worker_signals = WorkerSignals()
        self.worker_signals.progress_update.connect(self.on_progress_update)
        self.worker_signals.log_update.connect(self.on_log_update)
        self.worker_signals.thread_done.connect(self.on_thread_done)
        self.worker_signals.thread_error.connect(self.on_thread_error)
        self.worker_signals.xml_parse_error.connect(self.on_xml_parse_error)

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Massucatti - Analisador Fiscal")
        self.resize(1000, 800)
        self.setStyleSheet(get_stylesheet(self.config.font_family))

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Header
        lbl_title = QLabel("Analisador Fiscal Massucatti")
        lbl_title.setObjectName("Title")
        lbl_title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(lbl_title)

        lbl_desc = QLabel("Conciliação de SPED Fiscal vs. XMLs de Notas Fiscais")
        lbl_desc.setObjectName("Subtitle")
        lbl_desc.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(lbl_desc)

        main_layout.addSpacing(10)

        # --- Configurações de Análise (GroupBox) ---
        config_group = QGroupBox("Configurações de Análise")
        config_layout = QGridLayout()
        config_layout.setSpacing(10)

        # SPED File
        config_layout.addWidget(QLabel("Arquivo SPED Fiscal:"), 0, 0)
        self.txt_sped = QLineEdit()
        self.txt_sped.setReadOnly(True)
        config_layout.addWidget(self.txt_sped, 0, 1)
        btn_sped = QPushButton("📁 Procurar SPED")
        btn_sped.clicked.connect(lambda: self.browse_file(self.txt_sped, "Arquivo SPED (*.txt)"))
        config_layout.addWidget(btn_sped, 0, 2)

        # XML Folder
        config_layout.addWidget(QLabel("Pasta com os XMLs:"), 1, 0)
        self.txt_xml = QLineEdit()
        self.txt_xml.setReadOnly(True)
        config_layout.addWidget(self.txt_xml, 1, 1)
        btn_xml = QPushButton("📁 Procurar XML")
        btn_xml.clicked.connect(lambda: self.browse_folder(self.txt_xml))
        config_layout.addWidget(btn_xml, 1, 2)

        # Regras File
        config_layout.addWidget(QLabel("Arquivo de Regras (Acum.):"), 2, 0)
        self.txt_regras = QLineEdit()
        self.txt_regras.setReadOnly(True)
        config_layout.addWidget(self.txt_regras, 2, 1)
        btn_regras = QPushButton("📁 Procurar REGRAS")
        btn_regras.clicked.connect(lambda: self.browse_file(self.txt_regras, "CSV/Excel (*.csv *.xlsx *.xls)"))
        config_layout.addWidget(btn_regras, 2, 2)

        # Setor Combo
        config_layout.addWidget(QLabel("Setor / Atividade:"), 3, 0)
        self.cmb_setor = QComboBox()
        self.cmb_setor.addItems(['Comercio', 'Moveleiro', 'E-commerce'])
        config_layout.addWidget(self.cmb_setor, 3, 1)

        # Regras Detalhadas (Checkbox + Input)
        self.chk_detalhes = QCheckBox("Usar Regras Detalhadas (NCM)?")
        self.chk_detalhes.toggled.connect(self.toggle_detalhes)
        config_layout.addWidget(self.chk_detalhes, 4, 0)

        self.txt_detalhes = QLineEdit()
        self.txt_detalhes.setReadOnly(True)
        self.txt_detalhes.setEnabled(False)
        config_layout.addWidget(self.txt_detalhes, 4, 1)

        self.btn_detalhes = QPushButton("📁 Procurar")
        self.btn_detalhes.setEnabled(False)
        self.btn_detalhes.clicked.connect(lambda: self.browse_file(self.txt_detalhes, "Excel (*.xlsx *.xls)"))
        config_layout.addWidget(self.btn_detalhes, 4, 2)

        # Apuração (Checkbox + Input)
        self.chk_apuracao = QCheckBox("Apuração (Opcional)")
        self.chk_apuracao.toggled.connect(self.toggle_apuracao)
        config_layout.addWidget(self.chk_apuracao, 5, 0)

        self.txt_apuracao = QLineEdit()
        self.txt_apuracao.setReadOnly(True)
        self.txt_apuracao.setEnabled(False)
        config_layout.addWidget(self.txt_apuracao, 5, 1)

        self.btn_apuracao = QPushButton("📁 Procurar Template")
        self.btn_apuracao.setEnabled(False)
        self.btn_apuracao.clicked.connect(lambda: self.browse_file(self.txt_apuracao, "Excel (*.xlsx)"))
        config_layout.addWidget(self.btn_apuracao, 5, 2)

        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # Botão Start
        self.btn_start = QPushButton("▶️ INICIAR ANÁLISE COMPLETA")
        self.btn_start.setObjectName("Primary")
        self.btn_start.setFixedHeight(50)
        self.btn_start.clicked.connect(self.start_analysis)

        # Validação de Permissão
        if 'run_analysis' not in self.permissions:
            self.btn_start.setEnabled(False)
            self.btn_start.setText("PERMISSÃO NEGADA")
        else:
            # Habilita verificação dinâmica (opcional, pode ser feito ao clicar)
            self.txt_sped.textChanged.connect(self.check_start_enabled)
            self.txt_xml.textChanged.connect(self.check_start_enabled)
            self.txt_regras.textChanged.connect(self.check_start_enabled)
            self.btn_start.setEnabled(False) # Inicia desabilitado até preencher

        main_layout.addWidget(self.btn_start)

        # Logs e Progresso
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setPlaceholderText("Logs do processamento aparecerão aqui...")
        main_layout.addWidget(self.txt_log)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Status: Aguardando arquivos...")
        main_layout.addWidget(self.lbl_status)

        main_layout.addSpacing(10)

        # Botões Rodapé
        footer_layout = QHBoxLayout()
        self.btn_open_report = QPushButton("✅ Abrir Relatório")
        self.btn_open_report.setObjectName("Primary")
        self.btn_open_report.setVisible(False)
        self.btn_open_report.clicked.connect(self.open_report)
        footer_layout.addWidget(self.btn_open_report)

        footer_layout.addStretch()

        self.btn_back = QPushButton("⬅️ Voltar")
        self.btn_back.clicked.connect(self.close) # Fecha a janela (volta pro menu se modal, ou fecha app se main)
        footer_layout.addWidget(self.btn_back)

        main_layout.addLayout(footer_layout)

    # --- Helpers de UI ---

    def browse_file(self, line_edit, filter_str):
        fpath, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo", "", filter_str)
        if fpath:
            line_edit.setText(fpath)

    def browse_folder(self, line_edit):
        dpath = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if dpath:
            line_edit.setText(dpath)

    def toggle_detalhes(self, checked):
        self.txt_detalhes.setEnabled(checked)
        self.btn_detalhes.setEnabled(checked)
        if not checked: self.txt_detalhes.clear()
        self.check_start_enabled()

    def toggle_apuracao(self, checked):
        self.txt_apuracao.setEnabled(checked)
        self.btn_apuracao.setEnabled(checked)
        if not checked: self.txt_apuracao.clear()

    def check_start_enabled(self):
        if 'run_analysis' not in self.permissions: return

        has_sped = bool(self.txt_sped.text())
        has_xml = bool(self.txt_xml.text())
        has_regras = bool(self.txt_regras.text())

        detalhes_ok = True
        if self.chk_detalhes.isChecked():
            detalhes_ok = bool(self.txt_detalhes.text())

        self.btn_start.setEnabled(has_sped and has_xml and has_regras and detalhes_ok)

    # --- Lógica de Execução ---
    def start_analysis(self):
        # Setup Logging (precisamos adaptar o logging para escrever no QTextEdit ou capturar sinal)
        # O setup_logging original usa um widget multiline do SG.
        # Vamos passar None lá e usar o sinal log_update daqui.
        # OU criar um Handler customizado que emite para self.worker_signals.log_update

        self.txt_log.clear()
        self.btn_start.setEnabled(False)
        self.btn_open_report.setVisible(False)
        self.progress_bar.setValue(0)
        self.lbl_status.setText("Status: Iniciando análise...")

        # Paths
        sped_path = Path(self.txt_sped.text())
        xml_path = Path(self.txt_xml.text())
        regras_path = Path(self.txt_regras.text())

        # Opcionais
        regras_det_path = Path(self.txt_detalhes.text()) if self.chk_detalhes.isChecked() else None
        apuracao_path = Path(self.txt_apuracao.text()) if self.chk_apuracao.isChecked() else None

        tipo_setor = self.cmb_setor.currentText()

        # Adapter para a lógica
        adapter = WindowAdapter(self.worker_signals)

        # Thread
        t = threading.Thread(target=self.run_logic_thread, args=(
            sped_path, xml_path, regras_path, adapter, self.username,
            self.config.cfop_sem_credito_icms, self.config.cfop_sem_credito_ipi,
            self.config.tolerancia_valor,
            regras_det_path, apuracao_path, tipo_setor
        ))
        t.daemon = True
        t.start()

    def run_logic_thread(self, *args):
        # Wrapper para chamar a função lógica
        # args: sped_path, xml_path, regras_path, window(adapter), username, ...
        try:
            executar_analise_completa(*args)
        except Exception as e:
            self.worker_signals.thread_error.emit(str(e))

    # --- Slots (Recebem sinais da Thread) ---
    @Slot(tuple)
    def on_progress_update(self, data):
        current, total = data
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            percent = int((current / total) * 100)
            self.lbl_status.setText(f"Status: Processando XMLs... ({percent}%)")

    @Slot(str)
    def on_log_update(self, msg):
        self.txt_log.append(msg)

    @Slot(object)
    def on_thread_done(self, result_data):
        path, problemas = result_data
        self.report_path = path

        msg = f"Concluído! ({problemas} inconsistências)" if problemas > 0 else "Concluído! Sucesso total."
        self.lbl_status.setText(f"Status: {msg}")
        self.progress_bar.setValue(self.progress_bar.maximum())

        self.btn_open_report.setVisible(True)
        self.check_start_enabled() # Reabilita botão start

        QMessageBox.information(self, "Sucesso", "Análise de conciliação concluída!")

    @Slot(str)
    def on_thread_error(self, err_msg):
        self.lbl_status.setText("Status: ERRO NA ANÁLISE!")
        self.check_start_enabled()
        QMessageBox.critical(self, "Erro na Análise", f"A análise falhou.\n\nDetalhe: {err_msg}")

    @Slot(str)
    def on_xml_parse_error(self, filename):
        # Apenas loga ou mostra aviso não intrusivo
        self.txt_log.append(f"[AVISO] XML mal formatado ignorado: {filename}")

    def open_report(self):
        if self.report_path and self.report_path.exists():
            try:
                if sys.platform == "win32":
                    os.startfile(str(self.report_path.resolve()))
                elif sys.platform == "darwin":
                    subprocess.run(['open', str(self.report_path.resolve())])
                else:
                    subprocess.run(['xdg-open', str(self.report_path.resolve())])
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Não foi possível abrir o relatório:\n{e}")
        else:
            QMessageBox.warning(self, "Erro", "Arquivo de relatório não encontrado.")

    # Compatibilidade: Método run não é padrão Qt (usamos show no controller), mas se precisar
    def run(self):
        self.show()
