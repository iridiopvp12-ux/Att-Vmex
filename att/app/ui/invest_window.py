import FreeSimpleGUI as sg
import threading
import logging
import sys
import subprocess
import os
from pathlib import Path
from typing import Optional, Tuple

# ... (Mesmos imports e try/except de configuração do seu código original) ...
try:
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
except Exception:
    pass

try:
    from app.config import ConfigLoader
except ImportError:
    class ConfigLoader: 
        def __init__(self):
            self.font_family = "Helvetica"
            self.theme_definition = {}
            self.btn_colors = {}
            self.app_icon_path = None

try:
    from app.fiscal.invest_logic import executar_apuracao_invest
except ImportError as e:
    logging.error(f"ERRO CRÍTICO ao importar invest_logic: {e}")
    def executar_apuracao_invest(*args, **kwargs): 
        raise ImportError(f"Falha ao carregar lógica.\nErro: {e}")

class InvestWindow:
    def __init__(self, config: ConfigLoader):
        self.config = config
        self.window: Optional[sg.Window] = None

    def _build_layout(self):
        try:
            font_family = self.config.font_family
        except AttributeError:
            font_family = "Helvetica"

        INPUT_BG_COLOR = getattr(self.config, 'theme_definition', {}).get('INPUT', '#1E293B')
        TEXT_COLOR = getattr(self.config, 'theme_definition', {}).get('TEXT', '#FAFAFA')
        BG_COLOR = getattr(self.config, 'theme_definition', {}).get('BACKGROUND', '#0F172A')
        
        btn_colors = getattr(self.config, 'btn_colors', {})
        btn_main = btn_colors.get('main', {'normal': '#007ACC', 'hover': '#0099FF', 'disabled': '#4A4A4A'})
        btn_exit = btn_colors.get('exit', {'normal': '#4B5563', 'hover': '#6B7280'})

        # --- Seção de Inputs ---
        input_section = [
            [sg.Text('Pasta dos XMLs:', size=(22, 1), justification='right', font=(font_family, 10), 
                     background_color=INPUT_BG_COLOR, text_color=TEXT_COLOR),
             sg.Input(key='-XML_FOLDER-', readonly=True, enable_events=True, background_color='#334155', text_color='#FFFFFF'),
             sg.FolderBrowse('📁 Procurar', font=(font_family, 10))],
            
            # >>> NOVO CAMPO: Arquivo NCM <<<
            [sg.Text('Tabela NCM (CSV/XLSX):', size=(22, 1), justification='right', font=(font_family, 10), 
                     background_color=INPUT_BG_COLOR, text_color=TEXT_COLOR),
             sg.Input(key='-FILE_NCM-', readonly=True, enable_events=True, background_color='#334155', text_color='#FFFFFF'),
             sg.FileBrowse('📁 Procurar', file_types=(("Arquivos de Dados", "*.csv *.xlsx"),), font=(font_family, 10),
                           tooltip='Obrigatório para regra de Perfumaria')],

            [sg.Text('Planilha SETE (Base):', size=(22, 1), justification='right', font=(font_family, 10), 
                     background_color=INPUT_BG_COLOR, text_color=TEXT_COLOR),
             sg.Input(key='-PLANILHA_SETE-', readonly=True, enable_events=True, background_color='#334155', text_color='#FFFFFF'),
             sg.FileBrowse('📁 Procurar', file_types=(("Excel Files", "*.xlsx"),), font=(font_family, 10),
                           tooltip='Opcional: Selecione a planilha para preenchimento')],
        ]

        # ... (Resto do layout permanece igual, botoes_rodape, layout principal) ...
        botoes_rodape = [
            sg.Button('✅ Abrir Pasta', key='-OPEN_FOLDER-', font=(font_family, 11, 'bold'),
                      button_color=btn_main.get('normal', '#007ACC'),
                      mouseover_colors=btn_main.get('hover', '#0099FF'),
                      disabled=True, visible=False),
            sg.Push(background_color=BG_COLOR),
            sg.Button('⬅️ Voltar', key='-CLOSE-', font=(font_family, 11, 'bold'),
                      button_color=btn_exit.get('normal', '#4B5563'),
                      mouseover_colors=btn_exit.get('hover', '#6B7280'))
        ]

        layout = [
            [sg.Text('Apuração Invest (SETE)', font=(font_family, 22, 'bold'), justification='center',
                     expand_x=True, pad=((0,0),(15,5)), background_color=BG_COLOR, text_color=TEXT_COLOR)],
            [sg.Text('Automação de conferência e preenchimento', font=(font_family, 11),
                     justification='center', expand_x=True, background_color=BG_COLOR, text_color=TEXT_COLOR)],
            [sg.HorizontalSeparator(pad=((0,0),(10,15)))],

            [sg.Frame('Dados de Entrada',
                      input_section,
                      font=(font_family, 12, 'bold'),
                      pad=(10, 10),
                      expand_x=True,
                      background_color=INPUT_BG_COLOR,
                      title_color=TEXT_COLOR,
                      border_width=1,
                      element_justification='left')],

            [sg.Button('▶️ INICIAR APURAÇÃO', key='-START-', font=(font_family, 14, 'bold'),
                       size=(35, 2), button_color=btn_main.get('normal', '#007ACC'),
                       mouseover_colors=btn_main.get('hover', '#0099FF'),
                       disabled_button_color=('#FAFAFA', btn_main.get('disabled', '#4A4A4A')),
                       pad=((0,0), (20, 20)))],

            [sg.Multiline(size=(90, 10), key='-OUTPUT-', background_color='#212121', text_color='#E0E0E0',
                          disabled=True, autoscroll=True, font=(font_family, 9), expand_x=True)],
            
            [sg.ProgressBar(100, orientation='h', size=(60, 20), key='-PROGRESS_BAR-', expand_x=True)],
            [sg.Text('Status: Aguardando arquivos...', key='-STATUS_TEXT-', font=(font_family, 10),
                     expand_x=True, background_color=BG_COLOR, text_color=TEXT_COLOR)],

            [sg.HorizontalSeparator(pad=((0,0),(15,5)))],
            botoes_rodape
        ]

        return layout, BG_COLOR

    def run(self):
        layout, bg_color = self._build_layout()
        icon = getattr(self.config, 'app_icon_path', None)

        self.window = sg.Window('Módulo Invest', layout, modal=True, finalize=True, icon=icon, background_color=bg_color, element_justification='center')

        while True:
            event, values = self.window.read()
            
            if event in (sg.WIN_CLOSED, "-CLOSE-"):
                break
            
            if event == "-START-":
                pasta_str = values["-XML_FOLDER-"]
                planilha_sete = values["-PLANILHA_SETE-"]
                arquivo_ncm = values["-FILE_NCM-"] # Pega o arquivo NCM
                
                if not pasta_str:
                    sg.popup_error("Selecione a pasta dos XMLs!", title="Atenção", background_color='#212121')
                    continue
                
                if not arquivo_ncm:
                    # Aviso opcional ou erro, dependendo se é obrigatório. Vou colocar como erro para garantir a regra.
                    sg.popup_error("Selecione o arquivo de Tabela NCM!", title="Atenção", background_color='#212121')
                    continue
                
                pasta_path = Path(pasta_str)
                if not pasta_path.exists():
                    sg.popup_error("A pasta selecionada não existe!", title="Erro", background_color='#212121')
                    continue

                self._iniciar_thread(pasta_path, planilha_sete, arquivo_ncm)
            
            if event == '-PROGRESS_UPDATE-':
                try:
                    current, total = values[event]
                    self.window['-PROGRESS_BAR-'].update(current, max=total)
                    percent = int((current / total) * 100) if total > 0 else 0
                    self.window['-STATUS_TEXT-'].update(f'Status: Processando XMLs... ({percent}%)')
                except: pass

            if event == "-DONE-":
                caminho_final = values[event]
                self.window['-PROGRESS_BAR-'].update(100, 100)
                self.window['-STATUS_TEXT-'].update("Status: Concluído!")
                self.window['-OUTPUT-'].print(f"\n[SUCESSO] Arquivo gerado em:\n{caminho_final}")
                self.window['-START-'].update(disabled=False)
                self.window['-OPEN_FOLDER-'].update(disabled=False, visible=True)
                self.last_output_path = Path(caminho_final).parent
                sg.popup(f"Apuração Concluída!\nArquivo salvo na pasta dos XMLs.", title="Sucesso")

            if event == "-ERROR-":
                msg_erro = values[event]
                self.window['-PROGRESS_BAR-'].update(0, 100)
                self.window['-STATUS_TEXT-'].update("Status: Erro fatal.")
                self.window['-OUTPUT-'].print(f"\n[ERRO] {msg_erro}")
                self.window['-START-'].update(disabled=False)
                sg.popup_error(f"Ocorreu um erro:\n{msg_erro}", title="Erro")

            if event == '-OPEN_FOLDER-':
                if hasattr(self, 'last_output_path') and self.last_output_path.exists():
                    self._abrir_pasta(self.last_output_path)

        self.window.close()

    def _iniciar_thread(self, pasta_xml, planilha_sete, arquivo_ncm):
        self.window["-START-"].update(disabled=True)
        self.window["-PROGRESS_BAR-"].update(0, 100)
        self.window["-STATUS_TEXT-"].update("Status: Iniciando motor de cálculo...")
        self.window["-OUTPUT-"].update("Iniciando processamento...\n")
        # Passa o arquivo_ncm para o backend
        threading.Thread(target=self._processar_backend, args=(pasta_xml, planilha_sete, arquivo_ncm), daemon=True).start()

    def _processar_backend(self, pasta_xml, planilha_sete, arquivo_ncm):
        try:
            caminho_sete = planilha_sete if planilha_sete else None
            # Passa arquivo_ncm para a função lógica
            caminho_arquivo = executar_apuracao_invest(pasta_xml, self.window, caminho_sete, arquivo_ncm)
            self.window.write_event_value("-DONE-", caminho_arquivo)
        except Exception as e:
            logging.exception("Erro na thread do InvestWindow")
            self.window.write_event_value("-ERROR-", str(e))

    def _abrir_pasta(self, path):
        try:
            if sys.platform == "win32":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.run(['open', str(path)])
            else:
                subprocess.run(['xdg-open', str(path)])
        except Exception as e:
            sg.popup_error(f"Erro ao abrir pasta: {e}")