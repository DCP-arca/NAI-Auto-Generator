import sys
import os

from PIL import Image

from PyQt5.QtWidgets import QMessageBox, QApplication, QMainWindow
from PyQt5.QtCore import QSettings

from gui.dialog.miniutil_dialog import MiniUtilDialog
from core.worker.danbooru_tagger import DanbooruTagger
from config.paths import DEFAULT_PATH

if __name__ == "__main__":
    app = QApplication(sys.argv)
    qw = QMainWindow()
    qw.move(200, 200)
    TOP_NAME = "dcp_arca"
    APP_NAME = "nag_gui"
    qw.settings = QSettings(TOP_NAME, APP_NAME)
    qw.dtagger = DanbooruTagger(qw.settings.value(
        "path_models", os.path.abspath(DEFAULT_PATH["path_models"])))
    MiniUtilDialog(qw, "tagger").exec_()
