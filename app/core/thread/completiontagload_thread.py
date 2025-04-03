from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QThread, pyqtSignal

from config.paths import PATH_CSV_TAG_COMPLETION

def _on_load_completiontag_success(window, tag_list):
    if tag_list:
        target_code = ["prompt", "negative_prompt"]
        for code in target_code:
            window.dict_ui_settings[code].start_complete_mode(tag_list)

class CompletionTagLoadThread(QThread):
    on_load_completiontag_success = pyqtSignal(QMainWindow, list)

    def __init__(self, parent):
        super(CompletionTagLoadThread, self).__init__(parent)
        self.parent = parent
        self.on_load_completiontag_success.connect(
            _on_load_completiontag_success)

    def run(self):
        try:
            with open(PATH_CSV_TAG_COMPLETION, "r", encoding='utf8') as f:
                tag_list = f.readlines()
                if tag_list:
                    self.on_load_completiontag_success.emit(self.parent, tag_list)
        except Exception:
            pass

    def stop(self):
        self.is_dead = True
        self.quit()
