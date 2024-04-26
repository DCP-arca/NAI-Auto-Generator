import sys
import os

from PIL import Image

from PyQt5.QtWidgets import QMessageBox, QApplication, QMainWindow
from PyQt5.QtCore import QSettings

from gui_dialog import MiniUtilDialog, FileIODialog, QDialog
from danbooru_tagger import DanbooruTagger
from consts import DEFAULT_PATH

class TaggerWindow(QMainWindow):
    def predict_tag_from(self, filemode, target, with_dialog):
        result = ""

        target_model_name = self.settings.value("selected_tagger_model", '')
        if not target_model_name:
            QMessageBox.information(
                self, '경고', "먼저 본체 어플의 옵션에서 태깅 모델을 다운/선택 해주세요.")
            return ""
        else:
            self.dtagger.options["model_name"] = target_model_name

        if filemode == "src":
            target = Image.open(target)

        if with_dialog:
            loading_dialog = FileIODialog(
                "태그하는 중...", lambda: self.dtagger.tag(target))
            if loading_dialog.exec_() == QDialog.Accepted:
                result = loading_dialog.result
                if not result:
                    list_installed_model = self.dtagger.get_installed_models()
                    if not (target_model_name in list_installed_model):
                        self.settings.setValue("selected_tagger_model", '')
        else:
            try:
                result = self.dtagger.tag(target)
            except Exception as e:
                print(e)

        return result

if __name__ == "__main__":
    app = QApplication(sys.argv)
    qw = TaggerWindow()
    qw.move(200, 200)
    TOP_NAME = "dcp_arca"
    APP_NAME = "nag_gui"
    qw.settings = QSettings(TOP_NAME, APP_NAME)
    qw.dtagger = DanbooruTagger(qw.settings.value(
        "path_models", os.path.abspath(DEFAULT_PATH["path_models"])))
    MiniUtilDialog(qw, "tagger").exec_()
