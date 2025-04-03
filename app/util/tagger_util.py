
from PyQt5.QtWidgets import QMessageBox, QDialog
from PIL import Image

from gui.dialog.fileio_dialog import FileIODialog

def predict_tag_from(window, filemode, target, with_dialog):
    result = ""

    target_model_name = window.settings.value("selected_tagger_model", '')
    if not target_model_name:
        QMessageBox.information(
            window, '경고', "먼저 본체 어플의 옵션에서 태깅 모델을 다운/선택 해주세요.")
        return ""
    else:
        window.dtagger.options["model_name"] = target_model_name

    if filemode == "src":
        target = Image.open(target)

    if with_dialog:
        loading_dialog = FileIODialog(
            "태그하는 중...", lambda: window.dtagger.tag(target))
        if loading_dialog.exec_() == QDialog.Accepted:
            result = loading_dialog.result
            if not result:
                list_installed_model = window.dtagger.get_installed_models()
                if not (target_model_name in list_installed_model):
                    window.settings.setValue("selected_tagger_model", '')
    else:
        try:
            result = window.dtagger.tag(target)
        except Exception as e:
            print(e)

    return result
