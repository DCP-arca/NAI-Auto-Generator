from PyQt5.QtWidgets import QGroupBox, QLabel, QLineEdit, QCheckBox, QVBoxLayout, QHBoxLayout, QStyledItemDelegate, QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QFont, QIntValidator

from util.common_util import strtobool

from config.themes import COLOR
from config.consts import RESOLUTION_ITEMS, DEFAULT_RESOLUTION, RESOLUTION_ITEMS_NOT_SELECTABLES

class CustomDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, special_indexes=None):
        super(CustomDelegate, self).__init__(parent)
        self.special_indexes = special_indexes or set()
        self.parent = parent

    def paint(self, painter, option, index):
        if index.row() == self.parent.currentIndex():
            painter.save()

            painter.fillRect(option.rect, QColor(COLOR.BUTTON))
            palette = QPalette()
            palette.setColor(
                QPalette.Text, QColor('black'))  # Text color
            option.palette = palette
            option.font.setBold(True)
            super(CustomDelegate, self).paint(painter, option, index)
            painter.restore()
            palette.setColor(
                QPalette.Text, QColor('white'))  # Text color
            option.palette = palette
            option.font.setBold(False)
        elif index.row() in self.special_indexes:
            # Save the original state of the painter to restore it later
            painter.save()
            # Apply custom styles
            painter.setPen(QColor(COLOR.GRAY))
            painter.fillRect(option.rect, QColor(COLOR.GRAY))
            painter.setFont(QFont('Arial', 10, QFont.Bold))
            painter.restore()
            super(CustomDelegate, self).paint(painter, option, index)
        else:
            super(CustomDelegate, self).paint(painter, option, index)


class CustomWHLineEdit(QLineEdit):
    def __init__(self, size, custom_func):
        super(CustomWHLineEdit, self).__init__(size)
        self.custom_func = custom_func

    def focusOutEvent(self, event):
        self.custom_func()
        super(CustomWHLineEdit, self).focusOutEvent(event)

    def setText(self, text):
        super(CustomWHLineEdit, self).setText(text)
        self.custom_func()


def create_custom_whlineedit(custom_func):
    whle = CustomWHLineEdit("640", custom_func)
    whle.setMinimumWidth(50)
    whle.setValidator(QIntValidator(0, 2000))
    whle.setAlignment(Qt.AlignCenter)
    whle.returnPressed.connect(custom_func)

    return whle



def init_resolution_options_layout(self):
    layout = QVBoxLayout()

    image_settings_group = QGroupBox("Image Settings")
    layout.addWidget(image_settings_group)

    image_settings_layout = QHBoxLayout()
    image_settings_group.setLayout(image_settings_layout)

    left_layout = QVBoxLayout()
    right_layout = QHBoxLayout()
    image_settings_layout.addStretch(2)
    image_settings_layout.addLayout(left_layout, stretch=10)
    image_settings_layout.addStretch(1)
    image_settings_layout.addLayout(right_layout, stretch=10)
    image_settings_layout.addStretch(2)

    combo_resolution = QComboBox()
    combo_resolution.setMinimumWidth(220)
    combo_resolution.setMaxVisibleItems(len(RESOLUTION_ITEMS))
    combo_resolution.addItems(RESOLUTION_ITEMS)
    combo_resolution.setCurrentIndex(
        RESOLUTION_ITEMS.index(self.settings.value(
            "resolution", DEFAULT_RESOLUTION))
    )
    self.combo_resolution = combo_resolution

    combo_resolution.setItemDelegate(CustomDelegate(
        combo_resolution, special_indexes=RESOLUTION_ITEMS_NOT_SELECTABLES)
    )

    for nselectable in RESOLUTION_ITEMS_NOT_SELECTABLES:
        combo_resolution.setItemData(
            nselectable, 0, Qt.UserRole - 1)

    def update_resolutions(text):
        # Custom이 아닌경우에만 적용
        if "(" in text and ")" in text:
            res_text = text.split("(")[1].split(")")[0]
            width, height = res_text.split("x")
            self.width_edit.setText(width)
            self.height_edit.setText(height)
    combo_resolution.currentTextChanged.connect(update_resolutions)

    left_layout.addWidget(combo_resolution)

    # Right side layout

    def on_enter_or_focusout():
        now_width = self.width_edit.text()
        now_height = self.height_edit.text()

        # 일치하는 경우 확인
        found = False
        if now_width and now_height:
            for text in RESOLUTION_ITEMS:
                if "(" in text and ")" in text:
                    res_text = text.split("(")[1].split(")")[0]
                    width, height = res_text.split("x")
                    if now_width == width.strip() and now_height == height.strip():
                        combo_resolution.setCurrentText(text)
                        found = True

        # 그 외 모든 경우 맨마지막 - Custom으로 감
        if not found:
            combo_resolution.setCurrentIndex(combo_resolution.count() - 1)
        
    self.width_edit = create_custom_whlineedit(on_enter_or_focusout)
    self.height_edit = create_custom_whlineedit(on_enter_or_focusout)

    # Add widgets to the right layout
    right_layout.addWidget(QLabel("너비(Width)"))
    right_layout.addWidget(self.width_edit)
    right_layout.addWidget(QLabel("높이(Height)"))
    right_layout.addWidget(self.height_edit)

    # Check Box Layout
    checkbox_layout = QHBoxLayout()
    checkbox_layout.addStretch(2000)
    checkbox_random_resolution = QCheckBox("이미지 크기 랜덤")
    prev_value_checkbox = strtobool(
        self.settings.value("image_random_checkbox", False))
    checkbox_random_resolution.setChecked(prev_value_checkbox)
    checkbox_layout.addWidget(checkbox_random_resolution)
    checkbox_random_resolution.stateChanged.connect(
        self.on_random_resolution_checked)
    self.checkbox_random_resolution = checkbox_random_resolution
    layout.addLayout(checkbox_layout)

    self.dict_ui_settings["resolution"] = combo_resolution
    self.dict_ui_settings["width"] = self.width_edit
    self.dict_ui_settings["height"] = self.height_edit

    return layout