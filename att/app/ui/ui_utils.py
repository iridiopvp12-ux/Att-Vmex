
# att/app/ui/ui_utils.py
from PySide6.QtWidgets import QMessageBox, QWidget

def popup_error(message: str, title: str = "Erro"):
    """Exibe um popup de erro modal."""
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    # Aplicar estilo básico se necessário, mas o QSS global deve cuidar disso
    msg_box.exec()

def popup_warning(message: str, title: str = "Aviso"):
    """Exibe um popup de aviso modal."""
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.exec()

def popup_info(message: str, title: str = "Informação"):
    """Exibe um popup de informação modal."""
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Information)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.exec()

def popup_notify(message: str, title: str = "Notificação"):
    """Exibe uma notificação simples (popup de informação)."""
    popup_info(message, title)

def popup_yes_no(message: str, title: str = "Confirmação") -> str:
    """
    Exibe uma pergunta Sim/Não.
    Retorna 'Yes' se o usuário clicar em Yes, 'No' caso contrário (compatível com lógica antiga).
    """
    reply = QMessageBox.question(
        None, title, message,
        QMessageBox.Yes | QMessageBox.No, QMessageBox.No
    )
    return 'Yes' if reply == QMessageBox.Yes else 'No'

def popup_ok(message: str, title: str = "Sucesso"):
    """Alias para popup_info para compatibilidade."""
    popup_info(message, title)
