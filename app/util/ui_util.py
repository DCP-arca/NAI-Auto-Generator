from PyQt5.QtWidgets import QWidget, QPushButton, QGraphicsOpacityEffect

def create_empty(minimum_width=1, minimum_height=1, fixed_height=0, maximum_height=0):
    w = QWidget()
    w.setMinimumWidth(minimum_width)
    w.setMinimumHeight(minimum_height)
    w.setStyleSheet("background-color:#00000000")
    if fixed_height != 0:
        w.setFixedHeight(fixed_height)
    if maximum_height != 0:
        w.setMaximumHeight(maximum_height)
    return w


def add_button(hbox, text, callback, minimum_width=-1, maximum_width=-1, maximum_height=-1):
    button = QPushButton(text)
    button.pressed.connect(callback)
    if minimum_width != -1:
        button.setMinimumWidth(minimum_width)
    if maximum_width != -1:
        button.setMaximumWidth(maximum_width)
    if maximum_height != -1:
        button.setMaximumHeight(maximum_height)
    hbox.addWidget(button)
    return button


def set_opacity(widget, opacity):
    opacity_effect = QGraphicsOpacityEffect(widget)
    opacity_effect.setOpacity(opacity)  # 0은 완전히 투명함을 의미함
    widget.setGraphicsEffect(opacity_effect)