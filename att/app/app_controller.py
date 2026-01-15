# att/app/app_controller.py

import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from pathlib import Path
import json
from typing import List, Optional, Any
import traceback
import logging
from datetime import datetime

# --- Bloco de Segurança de Importação ---
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- IMPORTAR A FUNÇÃO DE LOGGING ---
try:
    from app.logging_config import setup_logging
except ImportError as e:
    def setup_logging(*args, **kwargs):
        print(f"ERRO CRÍTICO: Função setup_logging não importada. Detalhe: {e}")

# --- Importações da Estrutura da Aplicação ---
try:
    from app.config import ConfigLoader
    from app.auth import AuthManager
    from app.ui.ui_utils import popup_error, popup_notify # Helpers Qt

    # Janelas (Agora em Qt)
    from app.ui.login_window import LoginWindow
    from app.ui.menu_window import MenuWindow
    from app.ui.analyzer_window import AnalyzerWindow
    from app.ui.empresa_cadastro_window import EmpresaCadastroWindow

    # Placeholder para janelas não migradas ainda
    # from app.ui import sped_filter_window
    # from app.ui.keys_extractor_window import KeysExtractorWindow
    # from app.ui.invest_window import InvestWindow

except ImportError as e:
    # Como ainda não temos QApplication rodando, usamos print/stderr ou messagebox simples do sistema se possível
    # Mas aqui vamos assumir console
    print(f"Erro crítico de importação no Controlador: {e}")
    traceback.print_exc()
    sys.exit(1)


class AppController:
    """
    Classe principal que gerencia o ciclo de vida e o fluxo da aplicação.
    Agora adaptada para PySide6.
    """
    def __init__(self, config: ConfigLoader) -> None:
        self.config: ConfigLoader = config
        self.authenticator: Optional[AuthManager] = None
        self.logged_in_user: str | None = None
        self.user_permissions: List[str] = []

        # Inicializa QApplication se não existir
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("VM Contadores App")
            # Ícone da app pode ser setado aqui globalmente

        try:
            logging.info(f"[DEBUG] Inicializando AuthManager. Arquivo de usuários: {self.config.db_usuarios_path}")
            self.authenticator = AuthManager(
                self.config.db_usuarios_path,
                self.config.admin_user
            )
        except Exception as e:
            # popup_error precisa de QApplication rodando, ok aqui
            popup_error(f"Erro ao inicializar o AuthManager:\n{e}", title="Erro de Autenticação")
            traceback.print_exc()
            sys.exit(1)

    def run(self) -> None:
        """Inicia o loop principal da aplicação (Login -> Menu -> Logout)."""
        if not self.config or not self.authenticator:
            logging.error("Falha na inicialização do controller. Encerrando.")
            return

        try:
            while True:
                # 1. TELA DE LOGIN (Modal)
                login_win = LoginWindow(self.config, self.authenticator)
                username, permissions = login_win.run() # Bloqueia até fechar

                if not username:
                    # Usuário fechou a janela de login sem logar
                    break

                # 2. CONFIGURA LOGGING
                logging.debug(f"DEBUG: Login bem-sucedido. Usuário: '{username}'")
                setup_logging(self.config.log_directory_path, self.config.log_level, username)

                self.logged_in_user = username
                self.user_permissions = permissions

                # 3. TELA DE MENU PRINCIPAL
                # MenuWindow agora deve bloquear a execução até o logout
                menu_win = MenuWindow(self.config, self.logged_in_user, self.user_permissions)
                wants_to_logout = menu_win.run(self) # Passa 'self' para callback das ferramentas

                # 4. LOGOUT
                logging.info(f"Usuário '{username}' fazendo logout. Resetando logging.")
                setup_logging(self.config.log_directory_path, self.config.log_level, "SYSTEM")

                self.logged_in_user = None
                self.user_permissions = []

                if not wants_to_logout:
                    break

            logging.info("Aplicação encerrada.")

        except Exception as e:
            logging.critical(f"Erro inesperado no loop principal:\n{traceback.format_exc()}", exc_info=True)
            popup_error(f"Erro inesperado na aplicação:\n{e}\nConsulte o log.")

    def _launch_tool(self, tool_key: str) -> None:
        """
        Inicia a janela da ferramenta.
        """
        logging.info(f"Tentando iniciar ferramenta: {tool_key}")

        if not self.logged_in_user:
            return

        try:
            # --- 1. ANALISADOR FISCAL ---
            if tool_key == '-ANALISADOR-':
                if 'run_analysis' in self.user_permissions:
                    # Janela não-modal (ou modal, dependendo da UX desejada).
                    # Se for não-modal, precisamos manter referência para não ser coletada pelo GC.
                    # Por simplicidade neste refactor, vamos fazer modal (.show() + loop ou .exec() se for dialog)
                    # O AnalyzerWindow herda de QWidget, então show() é o padrão.
                    self.current_tool = AnalyzerWindow(self.config, self.logged_in_user, self.user_permissions)
                    self.current_tool.show()
                    # Se quisermos bloquear o menu enquanto usa a ferramenta:
                    # Mas QWidget não tem exec().
                    # Opção: Usar um QDialog container ou apenas deixar aberto.
                    # O MenuWindow escondeu-se antes de chamar _launch_tool, então ok deixar aberto.
                    # Mas precisamos esperar fechar para o menu voltar.
                    # Truque do loop local novamente:
                    from PySide6.QtCore import QEventLoop
                    loop = QEventLoop()
                    self.current_tool.destroyed.connect(loop.quit)
                    # Hack para fechar ao clicar no botão voltar que chama close()
                    self.current_tool.setAttribute(Qt.WA_DeleteOnClose)
                    loop.exec()
                    self.current_tool = None

                else:
                    self._show_permission_denied()

            # --- OUTRAS FERRAMENTAS (Ainda não portadas totalmente ou placeholders) ---
            elif tool_key == '-INVEST-':
                popup_notify("Ferramenta em migração para nova interface.", "Aviso")
            elif tool_key == '-FILTRO_SPED-':
                 popup_notify("Ferramenta em migração para nova interface.", "Aviso")
            elif tool_key == '-EXTRATOR_CHAVES-':
                 popup_notify("Ferramenta em migração para nova interface.", "Aviso")
            elif tool_key == '-ADMIN_MENU-':
                 popup_notify("Ferramenta em migração para nova interface.", "Aviso")

            else:
                logging.warning(f"Ferramenta '{tool_key}' não reconhecida.")

        except Exception as e:
            error_msg = f"Erro CRÍTICO ao abrir ferramenta {tool_key}:\n{e}"
            logging.critical(f"{error_msg}\n{traceback.format_exc()}", exc_info=True)
            popup_error(f"Ocorreu um erro ao abrir a ferramenta:\n{e}")

    def _show_permission_denied(self, msg="Você não tem permissão para acessar esta ferramenta."):
        popup_notify(msg, title="Acesso Negado")

if __name__ == "__main__":
    print("Módulo controlador. Execute main.py.")
