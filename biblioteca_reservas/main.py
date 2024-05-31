from ui import ReservaUI
import sys
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ReservaUI()
    window.show()
    sys.exit(app.exec_())