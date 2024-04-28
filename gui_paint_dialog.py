import sys
from collections import deque
from PyQt5.QtWidgets import QMainWindow, QDialog, QApplication, QLabel, QSlider, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QCheckBox, QShortcut
from PyQt5.QtGui import QPainter, QPen, QImage, qRgb, qRgba, QKeySequence
from PyQt5.QtCore import Qt, QPoint, QSize, QEvent

DEFAULT_WINDOW_SIZE = 400


def convert_coord(point, original_image_size, now_image_rect):
    wseed = original_image_size.width() / now_image_rect.width()
    hseed = original_image_size.height() / now_image_rect.height()

    x = int((point.x() - now_image_rect.left()) * wseed)
    y = int((point.y() - now_image_rect.top()) * hseed)

    return QPoint(x, y)


def convert_brush_coord(brush_size, original_image_size, now_image_rect):
    if original_image_size.width() > original_image_size.height():
        seed = original_image_size.width() / now_image_rect.width()
    else:
        seed = original_image_size.height() / now_image_rect.height()
    return brush_size * seed * 2


# 빈곳은 검게, 있는 곳은 하얗게 만든다. 투명도가 없어진다.
# 하얀곳이 하나도 없으면 False를 내뱉는다.
def convert_pixel_fit_to_mask(image):
    is_empty = True
    for y in range(image.height()):
        for x in range(image.width()):
            pixel = image.pixel(x, y)
            if pixel >> 24 == 0:
                image.setPixel(x, y, qRgb(0, 0, 0))
            else:
                image.setPixel(x, y, qRgb(255, 255, 255))
                is_empty = False

    return is_empty


def convert_mask_to_pixel_fit(image):
    for y in range(image.height()):
        for x in range(image.width()):
            pixel = image.pixel(x, y)
            if pixel == 4278190080:
                image.setPixel(x, y, qRgba(0, 0, 0, 0))
            else:
                image.setPixel(x, y, qRgba(0, 0, 0, 255))


"""
img = QImage('target.png')
# mask = QImage('mask.png')
# d = InpaintDialog(img, mask)
d = InpaintDialog(img)
if d.exec_() == QDialog.Accepted:
    print(d.mask_add)
    print(d.mask_only)

이때, 변화가 없으면 d.mask_only=None
"""


class InpaintDialog(QDialog):
    def __init__(self, img: QImage, mask: QImage = None, undo_max_length=10):
        super().__init__()
        self.image_original_size = QSize()

        self.initUI(undo_max_length)
        self.load_image(img, mask)

    def initUI(self, undo_max_length):
        self.image = QImage()
        self.draw_image = QImage()
        self.drawing = False
        self.is_erase_mod = False
        self.last_image_deque = deque(maxlen=undo_max_length)
        self.last_point = QPoint()
        self.brush_size = 40
        self.now_mouse_pos = QPoint(0, 0)

        # Label for Image
        self.image_label = QLabel(self)
        self.image_label.setMinimumSize(
            QSize(DEFAULT_WINDOW_SIZE, DEFAULT_WINDOW_SIZE))
        self.image_label.installEventFilter(self)
        self.image_label.setMouseTracking(True)

        # Slider for brush size
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(10, 200)
        self.slider.setValue(40)
        self.slider.valueChanged.connect(self.change_brush_size)

        layout_buttons = QHBoxLayout()
        erase_box = QCheckBox('지우개')
        erase_box.clicked.connect(self.on_check_erase)
        undo_button = QPushButton('되돌리기')
        undo_button.clicked.connect(self.on_click_undo)
        clear_button = QPushButton('모두 지우기')
        clear_button.clicked.connect(self.on_click_clear)

        # Button to save mask
        save_button = QPushButton('저장')
        save_button.clicked.connect(self.save_mask)

        quit_button = QPushButton('취소')
        quit_button.clicked.connect(self.on_quit_button)

        layout_buttons.addWidget(erase_box)
        layout_buttons.addWidget(undo_button)
        layout_buttons.addWidget(clear_button)
        layout_buttons.addWidget(save_button)
        layout_buttons.addWidget(quit_button)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.slider)
        layout.addLayout(layout_buttons)
        self.setLayout(layout)

        shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Z), self)
        shortcut.activated.connect(self.on_press_ctrlz)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.draw_image.isNull():
            self.drawing = True
            self.last_point = event.pos()
            self.last_image_deque.append(self.draw_image.copy())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.drawing:
            painter = QPainter(self.draw_image)
            painter.setBackgroundMode(Qt.BGMode.OpaqueMode)
            brush_size = convert_brush_coord(
                self.brush_size, self.image_original_size, self.now_image_rect)

            painter.setPen(QPen(Qt.black, brush_size,
                                Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

            p1 = convert_coord(
                event.pos(), self.image_original_size, self.now_image_rect)
            p2 = convert_coord(
                self.last_point, self.image_original_size, self.now_image_rect)

            if not self.is_erase_mod:
                painter.drawLine(p1, p2)
            else:
                brush_pos = QPoint(
                    int(p1.x() - brush_size / 4),
                    int(p2.y() - brush_size / 4)
                )

                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                painter.eraseRect(brush_pos.x(), brush_pos.y(), int(
                    brush_size/2), int(brush_size/2))

            self.last_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseMove:
            self.onHovered(event)
        return super(QWidget, self).eventFilter(obj, event)

    def onHovered(self, event):
        self.now_mouse_pos = event.pos()
        self.update()

    def paintEvent(self, event):
        rect = self.image_label.rect()
        rect.setWidth(self.width())

        w, h = self.image_original_size.width(), self.image_original_size.height()
        if rect.width() > rect.height():
            new_width = int(rect.height() * w / h)
            rect.moveLeft(int((rect.width() - new_width) * 0.5))
            rect.setWidth(new_width)
        else:
            new_height = int(rect.width() * h / w)
            rect.moveTop(int((rect.height() - new_height) * 0.5))
            rect.setHeight(new_height)
        self.now_image_rect = rect

        canvas_painter = QPainter(self)
        canvas_painter.drawImage(rect, self.image)
        canvas_painter.setOpacity(0.5)
        canvas_painter.drawImage(rect, self.draw_image)
        canvas_painter.setOpacity(0.3)
        canvas_painter.setPen(QPen(Qt.black))
        if not self.is_erase_mod:
            brush_size = self.brush_size
            # brush_pos = self.now_mouse_pos + 20
            brush_pos = QPoint(
                int(self.now_mouse_pos.x() + 15),
                int(self.now_mouse_pos.y() + 15)
            )
            canvas_painter.drawEllipse(brush_pos, brush_size, brush_size)
        else:
            brush_size = self.brush_size
            # brush_pos = self.now_mouse_pos + 20
            brush_pos = QPoint(
                int(self.now_mouse_pos.x() + 15 - brush_size / 2),
                int(self.now_mouse_pos.y() + 15 - brush_size / 2)
            )
            canvas_painter.drawRect(
                brush_pos.x(), brush_pos.y(), brush_size, brush_size)

    def resizeEvent(self, event):
        self.window_size = self.size()

    def load_image(self, img, mask=None):
        self.image = img
        w, h = self.image.width(), self.image.height()
        if mask:
            self.draw_image = mask
            convert_mask_to_pixel_fit(self.draw_image)
        else:
            self.draw_image = QImage(w, h, QImage.Format_ARGB32)
        # self.draw_image.invertPixels(QImage.InvertRgb);
        self.image_original_size = QSize(w, h)
        self.update()
        # self.resize(w, h)

    def save_mask(self):
        # Saving black mask
        mask_only = self.draw_image.copy()

        mask_add = self.image.copy()
        painter = QPainter(mask_add)
        painter.setOpacity(0.5)
        painter.drawImage(mask_only.rect(), mask_only)

        self.mask_add = mask_add
        is_empty = convert_pixel_fit_to_mask(mask_only)
        self.mask_only = None if is_empty else mask_only
        self.accept()

    def change_brush_size(self, value):
        self.brush_size = value
        self.update()

    def on_check_erase(self, is_erase_mod):
        self.is_erase_mod = is_erase_mod
        self.update()

    def on_click_undo(self):
        if len(self.last_image_deque) > 0:
            self.draw_image = self.last_image_deque.pop()
            self.update()

    def on_click_clear(self):
        self.last_image_deque.append(self.draw_image.copy())
        self.draw_image.fill(0)
        self.update()

    def on_press_ctrlz(self):
        self.on_click_undo()

    def on_quit_button(self):
        self.reject()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    qw = QMainWindow()
    qw.move(200, 200)
    img = QImage('getter.png')
    # mask = QImage('mask.png')
    # d = InpaintDialog(img, mask)
    d = InpaintDialog(img)
    if d.exec_() == QDialog.Accepted:
        print(d.mask_add)
        print(d.mask_only)
        # d.mask_add.save('mask1.png')
        # d.mask_only.save('mask2.png')
