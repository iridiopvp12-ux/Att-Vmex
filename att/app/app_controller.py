# att/app/app_controller.py

import sys
import FreeSimpleGUI as sg
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
    # Fallback caso o logging falhe criticamente
    def setup_logging(*args, **kwargs):
        print(f"ERRO CRÍTICO: Função setup_logging não importada. Detalhe: {e}")

# --- Importações da Estrutura da Aplicação (usando 'app.') ---
try:
    from app.config import ConfigLoader
    from app.auth import AuthManager
    
    # Janelas de Autenticação e Menu
    from app.ui.login_window import LoginWindow
    from app.ui.menu_window import MenuWindow
    
    # Janelas das Ferramentas
    from app.ui.analyzer_window import AnalyzerWindow
    from app.ui.admin_window import AdminWindow
    from app.ui.admin_menu_window import AdminMenuWindow
    from app.ui import sped_filter_window
    from app.ui.keys_extractor_window import KeysExtractorWindow
    from app.ui.invest_window import InvestWindow



except ImportError as e:
    sg.popup_error(f"Erro crítico de importação no Controlador:\n{e}\n\n"
                   f"Verifique as dependências e a estrutura de pastas.\n"
                   f"Python Path atual: {sys.path}",
                   title="Erro de Importação")
    print(f"Erro de importação no app_controller: {e}")
    traceback.print_exc()
    sys.exit(1)


class AppController:
    """
    Classe principal que gerencia o ciclo de vida e o fluxo da aplicação.
    Responsável por ligar o Menu às Janelas das ferramentas.
    """
    def __init__(self, config: ConfigLoader) -> None:
        self.config: ConfigLoader = config
        self.authenticator: Optional[AuthManager] = None
        self.logged_in_user: str | None = None
        self.user_permissions: List[str] = []
        
        try:
            logging.info(f"[DEBUG] Inicializando AuthManager. Arquivo de usuários: {self.config.db_usuarios_path}")
            self.authenticator = AuthManager(
                self.config.db_usuarios_path,
                self.config.admin_user
            )
        except Exception as e:
            sg.popup_error(f"Erro ao inicializar o AuthManager:\n{e}", title="Erro de Autenticação")
            traceback.print_exc()
            sys.exit(1)

    def run(self) -> None:
        """Inicia o loop principal da aplicação (Login -> Menu -> Ferramentas -> Logout)."""
        if not self.config or not self.authenticator:
            logging.error("Falha na inicialização do controller (config ou auth). Encerrando.")
            sg.popup_error("Falha na inicialização do controller. Verifique os logs.")
            return

        try:
            while True:
                # 1. TELA DE LOGIN
                login_win = LoginWindow(self.config, self.authenticator)
                username, permissions = login_win.run()

                if not username:
                    # Usuário fechou a janela de login
                    break 
                
                # 2. CONFIGURA LOGGING PARA O USUÁRIO LOGADO
                logging.debug(f"DEBUG: Login bem-sucedido. Usuário: '{username}'")
                setup_logging(self.config.log_directory_path, self.config.log_level, username)

                self.logged_in_user = username
                self.user_permissions = permissions

                # 3. TELA DE MENU PRINCIPAL
                # O menu_win.run recebe 'self' para poder chamar _launch_tool quando um botão for clicado
                menu_win = MenuWindow(self.config, self.logged_in_user, self.user_permissions)
                wants_to_logout = menu_win.run(self)

                # 4. LOGOUT
                logging.info(f"Usuário '{username}' fazendo logout. Resetando logging para 'SYSTEM'.")
                setup_logging(self.config.log_directory_path, self.config.log_level, "SYSTEM")

                self.logged_in_user = None
                self.user_permissions = []

                if not wants_to_logout:
                    break 
            
            logging.info("Aplicação encerrada pelo usuário.")
            
        except Exception as e:
            logging.critical(f"Erro inesperado no loop principal do AppController:\n{traceback.format_exc()}", exc_info=True)
            sg.popup_error(f"Erro inesperado na aplicação:\n{e}\nConsulte o log.", title="Erro Fatal")

    def _launch_tool(self, tool_key: str) -> None:
        """
        Inicia a janela da ferramenta correspondente à key do botão clicado no menu.
        Verifica as permissões antes de abrir a janela.
        """
        logging.info(f"Tentando iniciar ferramenta: {tool_key}")

        if not self.logged_in_user or not self.config:
            sg.popup_error("Erro de sessão: Usuário não logado ou configuração perdida.", title="Erro")
            return

        try:
            # --- 1. ANALISADOR FISCAL ---
            if tool_key == '-ANALISADOR-':
                if 'run_analysis' in self.user_permissions:
                    logging.info("[INFO] Abrindo AnalyzerWindow...")
                    analyzer = AnalyzerWindow(self.config, self.logged_in_user, self.user_permissions)
                    analyzer.run()
                    logging.info("[INFO] AnalyzerWindow fechada.")
                else:
                    self._show_permission_denied()

          

            # --- 3. APURAÇÃO INVEST ---
            elif tool_key == '-INVEST-':
                if 'run_apuracao_invest' in self.user_permissions:
                    logging.info("[INFO] Abrindo InvestWindow...")
                    invest_win = InvestWindow(self.config)
                    invest_win.run()
                    logging.info("[INFO] InvestWindow fechada.")
                else:
                    self._show_permission_denied()

            # --- 4. FILTRO SPED ---
            elif tool_key == '-FILTRO_SPED-':
                if 'run_filtro_sped' in self.user_permissions:
                    logging.info("[INFO] Abrindo SpedFilterWindow...")
                    sped_filter = sped_filter_window.SpedFilterWindow(self.config, self.logged_in_user)
                    sped_filter.run()
                    logging.info("[INFO] SpedFilterWindow fechada.")
                else:
                    self._show_permission_denied()
            
            # --- 5. EXTRATOR DE CHAVES ---
            elif tool_key == '-EXTRATOR_CHAVES-':
                if 'run_key_extractor' in self.user_permissions:
                    logging.info("[INFO] Abrindo KeysExtractorWindow...")
                    extractor = KeysExtractorWindow(self.config, self.logged_in_user)
                    extractor.run()
                    logging.info("[INFO] KeysExtractorWindow fechada.")
                else:
                    self._show_permission_denied()

            # --- 6. MENU ADMINISTRATIVO ---
            elif tool_key == '-ADMIN_MENU-':
                if 'manage_users' in self.user_permissions or 'view_logs' in self.user_permissions:
                    logging.info("[INFO] Abrindo AdminMenuWindow...")
                    admin_menu = AdminMenuWindow(self.config, self.logged_in_user)
                    admin_menu.run()
                    logging.info("[INFO] AdminMenuWindow fechada.")
                else:
                    self._show_permission_denied("Você não tem permissão de administrador.")

            # --- CASO PADRÃO / ERRO ---
            else:
                # O Admin Empresas às vezes é tratado dentro do AdminMenu, mas se vier direto:
                if tool_key != '-ADMIN_EMPRESAS-': 
                    logging.warning(f"Ferramenta '{tool_key}' não reconhecida pelo AppController.")
                    sg.popup_ok(f"Ferramenta '{tool_key}' ainda em desenvolvimento ou não vinculada.", title="Aviso")

        except Exception as e:
            error_msg = f"Erro CRÍTICO ao abrir ferramenta {tool_key}:\n{e}"
            logging.critical(f"{error_msg}\n{traceback.format_exc()}", exc_info=True)
            sg.popup_error(f"Ocorreu um erro ao abrir a ferramenta:\n{e}\n\nConsulte o log para detalhes.", title="Erro na Ferramenta")

    def _show_permission_denied(self, msg="Você não tem permissão para acessar esta ferramenta."):
        """Helper para exibir mensagem de acesso negado e logar o evento."""
        logging.warning(f"Acesso negado para usuário '{self.logged_in_user}'.")
        sg.popup_notify(msg, title="Acesso Negado")

if __name__ == "__main__":
    # Apenas para teste isolado, normalmente chamado pelo main.py
    print("Este arquivo é um módulo do controlador e deve ser chamado pelo main.py")