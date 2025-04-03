from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, pyqtSignal, QTimer

from util.image_util import pil2pixmap


class ResultImageView(QLabel):
    clicked = pyqtSignal()

    def __init__(self, first_src):
        super(ResultImageView, self).__init__()
        self.set_custom_pixmap(first_src)
        self.setAlignment(Qt.AlignCenter)

    def set_custom_pixmap(self, img_obj):
        if isinstance(img_obj, str):
            self.pixmap = QPixmap(img_obj)
        else:
            self.pixmap = pil2pixmap(img_obj)
        self.refresh_size()

    def refresh_size(self):
        self.setPixmap(self.pixmap.scaled(
            self.width(), self.height(),
            aspectRatioMode=Qt.KeepAspectRatio,
            transformMode=Qt.SmoothTransformation))
        self.setMinimumWidth(100)

    def setFixedSize(self, qsize):
        super(ResultImageView, self).setFixedSize(qsize)
        QTimer.singleShot(20, self.refresh_size)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            self.refresh_size()
            return True
        return super(ResultImageView, self).eventFilter(obj, event)

    def mousePressEvent(self, ev):
        self.clicked.emit()