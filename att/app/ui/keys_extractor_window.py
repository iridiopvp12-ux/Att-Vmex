import FreeSimpleGUI as sg
from pathlib import Path
import threading
from typing import Any
import traceback

from app.config import ConfigLoader

# Tenta importar a lógica de forma segura
try:
    from app.keys_extractor_logic import KeysExtractorLogic
except ImportError:
    print("Erro ao importar KeysExtractorLogic.")
    KeysExtractorLogic = Any

class KeysExtractorWindow:
    """Janela para extrair chaves de entrada do SPED."""

    def __init__(self, config: ConfigLoader, username: str):
        self.config = config
        self.username = username
        self.logic = KeysExtractorLogic()
        self.window: sg.Window | None = None
        self.is_processing = False
        
        # Configurações visuais
        self.font_family = self.config.font_family
        self.font_std = (self.font_family, 10)
        self.font_bold = (self.font_family, 11, 'bold')
        self.BG_COLOR = self.config.theme_definition.get('BACKGROUND', '#1E1E1E')
        self.TEXT_COLOR = self.config.theme_definition.get('TEXT', '#E0E0E0')
        self.INPUT_BG = self.config.theme_definition.get('INPUT', '#4A5568')

    def _build_layout(self) -> list:
        file_frame = [
            sg.Text("Arquivo SPED:", font=self.font_std, background_color=self.BG_COLOR, text_color=self.TEXT_COLOR),
            sg.Input(key='-IN_FILE-', readonly=True, font=self.font_std, size=(50, 1),
                     background_color=self.INPUT_BG, text_color=self.TEXT_COLOR),
            sg.FileBrowse("Procurar", font=self.font_std, target='-IN_FILE-',
                          file_types=(("Arquivos de Texto", "*.txt"),))
        ]

        progress_frame = [
            sg.Text("Aguardando...", key='-STATUS-', font=self.font_std,
                    background_color=self.BG_COLOR, text_color=self.TEXT_COLOR, size=(50, 2)),
            sg.ProgressBar(100, orientation='h', size=(45, 20), key='-PROGRESS-', bar_color=('#007ACC', '#4A5568'))
        ]

        layout = [
            [sg.Text("Extrator de Chaves (Apenas Entradas)", font=(self.font_family, 16, 'bold'),
                     background_color=self.BG_COLOR, text_color=self.TEXT_COLOR, justification='center', expand_x=True)],
            
            [sg.Frame("1. Selecione o SPED", [file_frame], font=self.font_bold,
                      background_color=self.BG_COLOR, title_color=self.TEXT_COLOR, expand_x=True, pad=(0, 10))],
            
            [sg.Button("EXTRAIR CHAVES", key='-RUN-', font=self.font_bold,
                       button_color=self.config.btn_colors.get('main',{}).get('normal','#007ACC'), expand_x=True, pad=(0, 15), size=(0, 2))],
            
            [sg.Frame("Status", [progress_frame], font=self.font_bold,
                      background_color=self.BG_COLOR, title_color=self.TEXT_COLOR, expand_x=True, pad=(0, 10))],
            
            [sg.Button("Voltar", key='-BACK-', font=self.font_std,
                       button_color=self.config.btn_colors.get('exit',{}).get('normal','#6C757D'), size=(10, 1))]
        ]
        return layout

    def set_processing_state(self, processing: bool):
        """Habilita/desabilita botões durante o processamento."""
        self.is_processing = processing
        if not self.window: return
        
        state_txt = "Extraindo..." if processing else "EXTRAIR CHAVES"
        self.window['-RUN-'].update(disabled=processing, text=state_txt)
        self.window['-BACK-'].update(disabled=processing)
        self.window['-IN_FILE-'].update(disabled=processing)
        self.window['Procurar'].update(disabled=processing)

    def _run_thread(self, input_path: str, output_path: str):
        """Roda a lógica em uma thread separada."""
        try:
            def callback(pct):
                if self.window: 
                    self.window.write_event_value('-UPDATE-', pct)

            # Chama a lógica criada no passo 1
            success, msg = self.logic.extract_keys(input_path, output_path, callback)
            
            if self.window: 
                self.window.write_event_value('-DONE-', (success, msg))
        except Exception as e:
            if self.window: 
                self.window.write_event_value('-DONE-', (False, f"Erro crítico: {e}"))

    def run(self):
        """Loop principal da janela."""
        self.window = sg.Window("Extrator de Chaves XML", self._build_layout(), modal=True, 
                                background_color=self.BG_COLOR, finalize=True, icon=self.config.app_icon_path)
        
        while True:
            event, values = self.window.read()
            
            if event in (sg.WIN_CLOSED, '-BACK-'):
                if self.is_processing:
                    sg.popup("Aguarde o término do processo.")
                else:
                    break
            
            elif event == '-RUN-':
                path = values['-IN_FILE-']
                if not path:
                    sg.popup_error("Selecione um arquivo SPED primeiro!")
                    continue

                # Pergunta onde salvar
                save_path = sg.popup_get_file("Salvar lista de chaves como", 
                                              save_as=True, 
                                              default_extension=".txt", 
                                              file_types=(("Texto", "*.txt"),),
                                              title="Salvar Arquivo")
                if not save_path: continue

                self.set_processing_state(True)
                self.window['-STATUS-'].update("Lendo SPED e filtrando chaves...")
                
                # Inicia a Thread
                threading.Thread(target=self._run_thread, args=(path, save_path), daemon=True).start()

            # --- Eventos da Thread ---
            elif event == '-UPDATE-':
                pct = values[event]
                self.window['-PROGRESS-'].update(pct)
                self.window['-STATUS-'].update(f"Processando... {pct}%")
            
            elif event == '-DONE-':
                success, msg = values[event]
                self.set_processing_state(False)
                self.window['-STATUS-'].update("Concluído." if success else "Erro.")
                self.window['-PROGRESS-'].update(100 if success else 0)
                if success: 
                    sg.popup(msg, title="Sucesso")
                else: 
                    sg.popup_error(msg, title="Erro")

        self.window.close()