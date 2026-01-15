# app/ui/menu_window.py

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGridLayout, QFrame, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from typing import List, Dict, Any, Optional
import sys

from app.config import ConfigLoader
from app.ui.styles import get_stylesheet
from app.ui import empresa_cadastro_window # Será refatorado para Qt depois

# Type hint para o controller (evita import circular se usar TYPE_CHECKING)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.app_controller import AppController

class MenuWindow(QMainWindow):
    """
    Janela Principal (Dashboard) utilizando PySide6.
    """
    def __init__(self, config: ConfigLoader, username: str, permissions: List[str]):
        super().__init__()
        self.config = config
        self.username = username
        self.user_permissions = permissions
        self.wants_to_logout = False

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("VM Contadores - Hub de Ferramentas")
        self.resize(900, 600)
        self.setStyleSheet(get_stylesheet(self.config.font_family))

        # Widget Central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- HEADER ---
        header_frame = QFrame()
        header_frame.setStyleSheet(f"background-color: {self.config.theme_definition.get('BACKGROUND')}; border-bottom: 1px solid #3f3f46;")
        header_frame.setFixedHeight(80)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 0, 30, 0)

        lbl_logo = QLabel("VM")
        lbl_logo.setStyleSheet("font-size: 20px; font-weight: bold; color: #71717a;") # Logo sutil

        lbl_welcome = QLabel(f"Bem-vindo, {self.username.capitalize()}!")
        lbl_welcome.setObjectName("Title")
        lbl_welcome.setStyleSheet("font-size: 22px;")

        btn_logout = QPushButton("Logout")
        btn_logout.setCursor(Qt.PointingHandCursor)
        btn_logout.setFixedSize(100, 35)
        btn_logout.clicked.connect(self.do_logout)

        header_layout.addWidget(lbl_logo)
        header_layout.addSpacing(20)
        header_layout.addWidget(lbl_welcome)
        header_layout.addStretch()
        header_layout.addWidget(btn_logout)

        main_layout.addWidget(header_frame)

        # --- CONTENT AREA (Grid de Cards) ---
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 40, 40, 40)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)

        # Definição dos Cards
        self.card_definitions = [
            {
                'key': '-ANALISADOR-', 'title': 'Analisador Fiscal', 'desc': 'Análise fiscal para Comercio',
                'permission': 'run_analysis', 'icon': '📊'
            },
            {
                'key': '-INVEST-', 'title': 'Apuração Invest', 'desc': 'Gera planilha SETE (XML + NCM)',
                'permission': 'run_apuracao_invest', 'icon': '💰'
            },
            {
                'key': '-FILTRO_SPED-', 'title': 'Filtro Sped', 'desc': 'Filtragem de arquivos SPED',
                'permission': 'run_filtro_sped', 'icon': '🔍'
            },
            {
                'key': '-EXTRATOR_CHAVES-', 'title': 'Extrator de Chaves', 'desc': 'Extrair Chaves XML (Entradas)',
                'permission': 'run_key_extractor', 'icon': '🔑'
            },
        ]

        # Renderiza os cards
        row, col = 0, 0
        max_cols = 2

        for card_def in self.card_definitions:
            perm = card_def.get('permission')
            if not perm or perm in self.user_permissions:
                btn_card = self._create_card_button(card_def)
                grid_layout.addWidget(btn_card, row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

        content_layout.addLayout(grid_layout)
        content_layout.addStretch() # Empurra grid para cima

        # --- ADMIN SECTION ---
        # Verifica se tem permissões administrativas para mostrar a seção inferior
        has_admin_user = 'manage_users' in self.user_permissions or 'view_logs' in self.user_permissions
        has_admin_empresa = 'admin' in self.user_permissions

        if has_admin_user or has_admin_empresa:
            admin_frame = QFrame()
            admin_frame.setStyleSheet("border-top: 1px solid #3f3f46; margin-top: 20px;")
            admin_layout = QHBoxLayout(admin_frame)
            admin_layout.setContentsMargins(0, 20, 0, 0)
            admin_layout.addStretch()

            if has_admin_user:
                btn_admin_users = self._create_admin_button("Administração", "⚙️", '-ADMIN_MENU-')
                admin_layout.addWidget(btn_admin_users)
                admin_layout.addSpacing(20)

            if has_admin_empresa:
                btn_admin_empresas = self._create_admin_button("Gerenciar Empresas", "🏢", '-ADMIN_EMPRESAS-')
                admin_layout.addWidget(btn_admin_empresas)

            admin_layout.addStretch()
            content_layout.addWidget(admin_frame)

        main_layout.addWidget(content_widget)

    def _create_card_button(self, card_data):
        """Cria um botão estilizado como 'Card'."""
        key = card_data['key']
        title = card_data['title']
        desc = card_data['desc']
        icon = card_data.get('icon', '')

        btn = QPushButton()
        btn.setObjectName("Card")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(300, 120)

        # Usando HTML para formatar o texto dentro do botão (Titulo bold, desc normal)
        btn.setText(f"{icon}  {title}\n\n{desc}")

        # Estilo específico para o card
        btn.setStyleSheet("""
            QPushButton#Card {
                background-color: #27272a;
                border: 1px solid #3f3f46;
                border-radius: 8px;
                text-align: left;
                padding: 15px;
                font-size: 14px;
                color: #f4f4f5;
            }
            QPushButton#Card:hover {
                background-color: #3f3f46;
                border: 1px solid #52525b;
            }
            QPushButton#Card:pressed {
                background-color: #18181b;
            }
        """)

        # Conecta o clique passando a key. Usamos lambda com default arg para capturar o valor atual do loop
        btn.clicked.connect(lambda checked=False, k=key: self.on_tool_clicked(k))
        return btn

    def _create_admin_button(self, title, icon, key):
        btn = QPushButton(f"{icon}  {title}")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(200, 50)
        # Estilo um pouco diferente para admin
        btn.setStyleSheet("""
            QPushButton {
                background-color: #0f766e; /* Teal-700 */
                border: none;
                border-radius: 4px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #115e59; /* Teal-800 */
            }
        """)
        btn.clicked.connect(lambda checked=False, k=key: self.on_tool_clicked(k))
        return btn

    def on_tool_clicked(self, key):
        """Callback quando uma ferramenta é clicada."""
        print(f"Tool clicked: {key}")

        if key == '-ADMIN_EMPRESAS-':
            # Abre modal de cadastro de empresas (agora Qt)
            self.hide()
            try:
                # Import dinâmico ou uso direto se refatorado
                from app.ui.empresa_cadastro_window import EmpresaCadastroWindow
                win = EmpresaCadastroWindow(self.config)
                win.exec() # Modal
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao abrir Gerenciar Empresas:\n{e}")
            finally:
                self.show()

        elif hasattr(self, 'controller') and self.controller:
            self.hide()
            try:
                self.controller._launch_tool(key)
            except Exception as e:
                 QMessageBox.critical(self, "Erro", f"Erro ao lançar ferramenta '{key}':\n{e}")
            finally:
                 self.show()

    def do_logout(self):
        self.wants_to_logout = True
        self.close()

    def run(self, controller: 'AppController') -> bool:
        """
        Inicia a janela.
        Retorna True se o usuário quis fazer logout, False se fechou o app.
        """
        self.controller = controller
        # No PySide6, normalmente instanciamos e mostramos.
        # Como o AppController gerencia o loop, aqui usamos show() mas precisamos bloquear?
        # Não, o menu principal geralmente é a janela "raiz" enquanto o usuário está logado.
        # Mas para manter a lógica sequencial do AppController (Login -> Menu -> Loop),
        # podemos usar um loop local de eventos se quisermos bloquear, OU
        # (Melhor) o AppController deve chamar app.exec() apenas uma vez?
        # O padrão atual do AppController é while True: Login... Menu...
        # Para compatibilidade sem reescrever todo o AppController para ser event-driven puro:
        # Vamos fazer o Menu bloquear o fluxo usando um loop local (QEventLoop) ou
        # simplesmente não retornar até fechar.
        # Como é QMainWindow, não tem exec(). Vamos ter que confiar que o AppController
        # já tem uma QApplication rodando e aqui só vamos esperar o fechamento.

        # TRUQUE: Transformar em "modal" lógico para o fluxo sequencial do controller funcionar
        # Vamos usar um QEventLoop local para esperar o fechamento desta janela.

        from PySide6.QtCore import QEventLoop
        self.show()

        loop = QEventLoop()
        self.destroyed.connect(loop.quit)
        # Sobrescrever closeEvent para garantir quit do loop? O destroyed resolve se o widget for deletado.
        # Mas self.close() apenas esconde se WA_DeleteOnClose não estiver setado.
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Conectar sinal de fechamento ao loop
        loop.exec()

        return self.wants_to_logout
