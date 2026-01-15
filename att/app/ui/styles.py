
# att/app/ui/styles.py

def get_stylesheet(font_family="Segoe UI"):
    """
    Retorna o QSS (Qt Style Sheet) para a aplicação, aplicando o tema Professional Dark.
    """

    # Cores
    bg_color = "#18181b"
    text_color = "#f4f4f5"
    input_bg = "#27272a"
    input_border = "#3f3f46"

    btn_primary = "#1e3a8a"
    btn_primary_hover = "#1e40af"
    btn_primary_pressed = "#172554"

    btn_secondary = "#3f3f46"
    btn_secondary_hover = "#52525b"

    btn_danger = "#b91c1c"
    btn_danger_hover = "#991b1b"

    # CSS
    qss = f"""
    QWidget {{
        background-color: {bg_color};
        color: {text_color};
        font-family: "{font_family}";
        font-size: 14px;
    }}

    /* Labels */
    QLabel {{
        color: {text_color};
    }}

    QLabel#Title {{
        font-size: 24px;
        font-weight: bold;
        color: {text_color};
    }}

    QLabel#Subtitle {{
        font-size: 16px;
        color: #a1a1aa; /* Zinc-400 */
    }}

    /* Inputs (LineEdit, TextEdit, etc) */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {input_bg};
        border: 1px solid {input_border};
        border-radius: 4px;
        padding: 5px;
        color: {text_color};
        selection-background-color: {btn_primary};
    }}

    QLineEdit:focus, QTextEdit:focus {{
        border: 1px solid {btn_primary};
    }}

    QLineEdit:disabled {{
        background-color: #1f1f22;
        color: #71717a;
    }}

    /* Buttons */
    QPushButton {{
        background-color: {btn_secondary};
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        color: {text_color};
        font-weight: bold;
    }}

    QPushButton:hover {{
        background-color: {btn_secondary_hover};
    }}

    QPushButton:pressed {{
        background-color: {input_bg};
    }}

    QPushButton:disabled {{
        background-color: {input_bg};
        color: #52525b;
    }}

    /* Primary Button Style (Blue) */
    QPushButton#Primary {{
        background-color: {btn_primary};
    }}

    QPushButton#Primary:hover {{
        background-color: {btn_primary_hover};
    }}

    QPushButton#Primary:pressed {{
        background-color: {btn_primary_pressed};
    }}

    /* Danger Button Style (Red) */
    QPushButton#Danger {{
        background-color: {btn_danger};
    }}
    QPushButton#Danger:hover {{
        background-color: {btn_danger_hover};
    }}

    /* GroupBox */
    QGroupBox {{
        border: 1px solid {input_border};
        border-radius: 6px;
        margin-top: 20px;
        font-weight: bold;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }}

    /* Table Widget */
    QTableWidget {{
        background-color: {input_bg};
        alternate-background-color: {bg_color};
        gridline-color: {input_border};
        border: none;
    }}

    QHeaderView::section {{
        background-color: {input_bg};
        padding: 5px;
        border: 1px solid {input_border};
        font-weight: bold;
    }}

    /* ScrollBar */
    QScrollBar:vertical {{
        border: none;
        background: {bg_color};
        width: 10px;
        margin: 0px 0px 0px 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {btn_secondary};
        min-height: 20px;
        border-radius: 5px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        background: none;
    }}

    /* ProgressBar */
    QProgressBar {{
        border: 1px solid {input_border};
        border-radius: 4px;
        text-align: center;
        background-color: {input_bg};
    }}

    QProgressBar::chunk {{
        background-color: {btn_primary};
        border-radius: 3px;
    }}
    """
    return qss
