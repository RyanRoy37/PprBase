"""A warm, clean Qt stylesheet for PprBase.

The palette is soft and approachable rather than clinical: off-white canvas,
muted teal accents, generous spacing and readable type — chosen for a teacher,
not an engineer.
"""

# Palette
CANVAS = "#FAF7F2"        # soft off-white
SURFACE = "#FFFFFF"
INK = "#33312E"           # warm near-black text
MUTED = "#8A8580"
ACCENT = "#2F8F83"        # muted teal
ACCENT_DARK = "#256F66"
ACCENT_SOFT = "#E3F0EE"
BORDER = "#E5DFD6"
GREEN = "#3F9D5A"
ORANGE = "#D98A3D"
GREY = "#B9B4AD"


def app_stylesheet(font_size: int = 11) -> str:
    return f"""
    QWidget {{
        background-color: {CANVAS};
        color: {INK};
        font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        font-size: {font_size}pt;
    }}

    QMainWindow, QDialog {{ background-color: {CANVAS}; }}

    /* Top navigation bar */
    QFrame#NavBar {{
        background-color: {SURFACE};
        border-bottom: 1px solid {BORDER};
    }}
    QLabel#AppTitle {{
        font-size: {font_size + 5}pt;
        font-weight: 700;
        color: {ACCENT_DARK};
    }}
    QLabel#Crumb {{ color: {MUTED}; }}

    /* Cards */
    QFrame#Card {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 12px;
    }}
    QFrame#Card:hover {{ border: 1px solid {ACCENT}; }}
    QLabel#CardTitle {{ font-size: {font_size + 2}pt; font-weight: 600; }}
    QLabel#CardSub {{ color: {MUTED}; }}

    /* Buttons */
    QPushButton {{
        background-color: {ACCENT};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
    }}
    QPushButton:hover {{ background-color: {ACCENT_DARK}; }}
    QPushButton:disabled {{ background-color: {GREY}; color: #F0F0F0; }}
    QPushButton#Ghost {{
        background-color: transparent;
        color: {ACCENT_DARK};
        border: 1px solid {ACCENT};
    }}
    QPushButton#Ghost:hover {{ background-color: {ACCENT_SOFT}; }}
    QPushButton#Danger {{ background-color: #C0573F; }}
    QPushButton#Danger:hover {{ background-color: #A4452F; }}

    /* Inputs */
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 6px 8px;
        selection-background-color: {ACCENT_SOFT};
    }}
    QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
        border: 1px solid {ACCENT};
    }}
    QLabel#FieldLabel {{ font-weight: 600; color: {INK}; }}
    QLabel#Hint {{ color: {MUTED}; }}

    /* Tabs */
    QTabBar::tab {{
        background: transparent;
        padding: 8px 16px;
        margin-right: 4px;
        border-radius: 8px;
        color: {MUTED};
        font-weight: 600;
    }}
    QTabBar::tab:selected {{ background: {ACCENT_SOFT}; color: {ACCENT_DARK}; }}
    QTabWidget::pane {{ border: none; }}

    /* Tree / preview */
    QTreeWidget {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 4px;
    }}
    QTreeWidget::item {{ padding: 4px 2px; }}
    QTreeWidget::item:selected {{ background: {ACCENT_SOFT}; color: {INK}; }}

    QScrollArea {{ border: none; background: transparent; }}

    QGroupBox {{
        border: 1px solid {BORDER};
        border-radius: 10px;
        margin-top: 14px;
        padding: 10px;
        background-color: {SURFACE};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 4px;
        font-weight: 700;
        color: {ACCENT_DARK};
    }}
    """
