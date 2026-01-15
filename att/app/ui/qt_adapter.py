
# att/app/ui/qt_adapter.py
from PySide6.QtCore import QObject, Signal

class WorkerSignals(QObject):
    """
    Define os sinais Qt que serão emitidos pelos workers (threads) para atualizar a UI.
    """
    # Para atualizar barras de progresso: (current, total)
    progress_update = Signal(tuple)

    # Para atualizar logs de texto: (mensagem)
    log_update = Signal(str)

    # Quando uma thread termina com sucesso: (result_data)
    # result_data pode ser uma tupla (path_relatorio, count_erros) ou similar
    thread_done = Signal(object)

    # Quando ocorre erro na thread: (mensagem_erro)
    thread_error = Signal(str)

    # Erro específico de parse XML
    xml_parse_error = Signal(str)


class WindowAdapter:
    """
    Adaptador que imita o comportamento de 'window.write_event_value' do FreeSimpleGUI,
    mas emite sinais Qt para que a interface PySide6 possa reagir.

    É passado para as funções de lógica (ex: xml_parser, fiscal_logic) no lugar do objeto 'window' do SG.
    """
    def __init__(self, signals: WorkerSignals):
        self.signals = signals

    def write_event_value(self, key: str, value: object):
        """
        Mapeia os eventos do FreeSimpleGUI para os Sinais do Qt.
        """
        if key == '-PROGRESS_UPDATE-':
            # value deve ser uma tupla (current, total)
            self.signals.progress_update.emit(value)

        elif key == '-THREAD_DONE-':
            self.signals.thread_done.emit(value)

        elif key == '-THREAD_ERROR-':
            self.signals.thread_error.emit(str(value))

        elif key == '-XML_PARSE_ERROR-':
            self.signals.xml_parse_error.emit(str(value))

        elif key == '-LOG_UPDATE-': # Caso a gente adapte o logging para usar write_event
            self.signals.log_update.emit(str(value))

        else:
            # Fallback para debug
            print(f"[WindowAdapter] Evento não mapeado recebido: key={key}, value={value}")
