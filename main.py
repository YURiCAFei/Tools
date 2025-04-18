import sys
from PyQt5.QtWidgets import QApplication
from config.qgis_env import init_qgis
from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    init_qgis()

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
