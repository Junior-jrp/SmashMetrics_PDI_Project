import sys
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from core.telas import SmashMetricsUI
from core.funcionalidades import Funcionalidades

if __name__ == "__main__":

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SmashMetrics")
    app = QApplication(sys.argv)
    icon_path = "logo_smashmetrics_removebg_preview_CD6_icon.ico"
    app.setWindowIcon(QIcon(icon_path))

    try:
        with open("assets/styles.css", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("⚠ Arquivo 'styles.css' não encontrado. O aplicativo usará o estilo padrão.")

    window = SmashMetricsUI()
    window.funcionalidades = Funcionalidades()
    window.setWindowIcon(QIcon(icon_path))

    window.show()
    sys.exit(app.exec())
