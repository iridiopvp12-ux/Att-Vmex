# app/ui/login_window.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QWidget, QFrame, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon

from typing import Optional, Tuple, List
from app.config import ConfigLoader
from app.auth import AuthManager
from app.ui.styles import get_stylesheet

class LoginWindow(QDialog):
    """
    Janela de Login utilizando PySide6.
    """
    def __init__(self, config: ConfigLoader, auth_manager: AuthManager):
        super().__init__()
        self.config = config
        self.auth_manager = auth_manager

        self.username: Optional[str] = None
        self.permissions: List[str] = []
        self.success = False

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("VM Contadores - Acesso")
        self.setFixedSize(400, 450)
        self.setStyleSheet(get_stylesheet(self.config.font_family))

        # Layout Principal
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        self.setLayout(layout)

        # Título
        lbl_title = QLabel("VM CONTADORES")
        lbl_title.setObjectName("Title")
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)

        lbl_subtitle = QLabel("Acesso ao Sistema")
        lbl_subtitle.setObjectName("Subtitle")
        lbl_subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_subtitle)

        layout.addSpacing(20)

        # Inputs Container
        input_container = QWidget()
        input_layout = QVBoxLayout()
        input_layout.setContentsMargins(0,0,0,0)
        input_layout.setSpacing(10)
        input_container.setLayout(input_layout)

        # Usuário
        lbl_user = QLabel("Usuário")
        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("Digite seu usuário")
        self.txt_user.setFixedHeight(40)
        input_layout.addWidget(lbl_user)
        input_layout.addWidget(self.txt_user)

        # Senha
        lbl_pass = QLabel("Senha")
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.Password)
        self.txt_pass.setPlaceholderText("Digite sua senha")
        self.txt_pass.setFixedHeight(40)
        self.txt_pass.returnPressed.connect(self.do_login) # Enter aciona login
        input_layout.addWidget(lbl_pass)
        input_layout.addWidget(self.txt_pass)

        layout.addWidget(input_container)

        layout.addStretch()

        # Botões
        self.btn_login = QPushButton("Entrar")
        self.btn_login.setObjectName("Primary")
        self.btn_login.setFixedHeight(45)
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.clicked.connect(self.do_login)
        layout.addWidget(self.btn_login)

        self.btn_exit = QPushButton("Sair")
        self.btn_exit.setFlat(True)
        self.btn_exit.setCursor(Qt.PointingHandCursor)
        self.btn_exit.clicked.connect(self.reject)
        layout.addWidget(self.btn_exit)

    def do_login(self):
        user = self.txt_user.text().strip()
        pwd = self.txt_pass.text().strip()

        if not user:
            QMessageBox.warning(self, "Aviso", "Nome de usuário é obrigatório.")
            return

        # Lógica de primeiro login admin
        is_first_setup = (
            user.lower() == self.config.admin_user and
            self.auth_manager.get_user_data(user)["password"] == "temp_placeholder"
        )

        if is_first_setup and not pwd:
            QMessageBox.warning(self, "Configuração Inicial", "Primeiro login do Admin. Por favor, defina uma senha.")
            return

        success, username, permissions = self.auth_manager.authenticate(user, pwd)

        if success:
            self.username = username
            self.permissions = permissions
            self.success = True

            if is_first_setup:
                QMessageBox.information(self, "Configuração Inicial", f"Bem-vindo, {username}!\nSenha de administrador definida com sucesso.")

            self.accept() # Fecha o dialog retornando Accepted
        else:
            QMessageBox.critical(self, "Erro", "Usuário ou Senha inválidos.")
            self.txt_pass.clear()

    def run(self) -> Tuple[Optional[str], List[str]]:
        """
        Método de compatibilidade para o controller chamar.
        """
        if self.exec() == QDialog.Accepted:
            return self.username, self.permissions
        return None, []
