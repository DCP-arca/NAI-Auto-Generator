import sys

from PyQt5.QtWidgets import QApplication, QMainWindow

from gui.dialog.miniutil_dialog import MiniUtilDialog

if __name__ == "__main__":
    app = QApplication(sys.argv)
    qw = QMainWindow()
    qw.move(200, 200)
    MiniUtilDialog(qw, "getter").exec_()
