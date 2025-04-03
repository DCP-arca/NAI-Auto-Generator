from PyQt5.QtCore import QThread, pyqtSignal

class LoadingThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, func):
        super().__init__()
        self.func = func

    def run(self):
        try:
            self.finished.emit(self.func())
        except Exception as e:
            print(e)
            self.finished.emit("")