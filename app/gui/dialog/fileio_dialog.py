from PyQt5.QtWidgets import QLabel, QVBoxLayout, QDialog
from PyQt5.QtCore import Qt, QTimer

from core.thread.loading_thread import LoadingThread

class FileIODialog(QDialog):
    def __init__(self, text, func):
        super().__init__()
        self.text = text
        self.func = func
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("작업 중")

        layout = QVBoxLayout()
        self.progress_label = QLabel(self.text)
        layout.addWidget(self.progress_label)

        self.setLayout(layout)

        self.resize(200, 100)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)

    def showEvent(self, event):
        QTimer.singleShot(100, self.start_work)
        super().showEvent(event)

    def start_work(self):
        self.worker_thread = LoadingThread(self.func)
        self.worker_thread.finished.connect(self.on_finished)
        self.worker_thread.start()

    def on_finished(self, result):
        self.result = result
        self.accept()