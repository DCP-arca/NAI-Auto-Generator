import sys
import os

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QSettings

from gui_dialog import MiniUtilDialog

if __name__ == "__main__":
    app = QApplication(sys.argv)
    qw = QMainWindow()
    qw.move(200, 200)
    MiniUtilDialog(qw, "getter").exec_()
