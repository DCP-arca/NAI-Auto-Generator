from PyQt5.QtCore import QThread, pyqtSignal

class CompletionTagLoadThread(QThread):
    on_load_completiontag_sucess = pyqtSignal(list)

    def __init__(self, parent):
        super(CompletionTagLoadThread, self).__init__(parent)

    def run(self):
        try:
            with open(PATH_CSV_TAG_COMPLETION, "r", encoding='utf8') as f:
                tag_list = f.readlines()
                if tag_list:
                    self.on_load_completiontag_sucess.emit(tag_list)
        except Exception:
            pass

    def stop(self):
        self.is_dead = True
        self.quit()