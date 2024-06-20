import os
import sys

from PyQt5.QtWidgets import QWidget, QRadioButton, QLabel, QTextEdit, QLineEdit, QCheckBox, QStyledItemDelegate, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QGroupBox, QSlider, QFrame, QSplitter, QSizePolicy, QDialog
from PyQt5.QtGui import QColor, QIntValidator, QFont, QPalette, QPixmap, QImage, QPainter
from PyQt5.QtCore import Qt, QSize, QEvent, QTimer, QRectF, pyqtSignal

from PIL import Image

from consts import COLOR, S

from gui_paint_dialog import InpaintDialog
from completer import CompletionTextEdit

########################################################

MAIN_STYLESHEET = """
        QWidget {
            color: white;
            background-color: """ + COLOR.BRIGHT + """;
        }
        QTextEdit {
            background-color: """ + COLOR.DARK + """;
        }
        QLineEdit {
            background-color: """ + COLOR.DARK + """;
            border: 1px solid """ + COLOR.GRAY + """;
        }
        QComboBox {
            background-color: """ + COLOR.DARK + """;
            border: 1px solid """ + COLOR.GRAY + """;
        }
        QComboBox QAbstractItemView {
            border: 2px solid """ + COLOR.GRAY + """;
            selection-background-color: black;
        }
        QPushButton {
            color:black;
            background-color: """ + COLOR.BUTTON + """;
        }
        QPushButton:disabled {
            background-color: """ + COLOR.BUTTON_DSIABLED + """;
        }
    """

SAMPLER_ITEMS = ['k_euler', 'k_euler_ancestral',
                 'k_dpmpp_2s_ancestral', "k_dpmpp_2m", 'k_dpmpp_sde', "ddim_v3"]

RESOLUTION_ITEMS = [
    "NORMAL",
    "Portrait (832x1216)",
    "Landscape (1216x832)",
    "Square (1024x1024)",
    "LARGE",
    "Portrait (1024x1536)",
    "Landscape (1536x1024)",
    "Square (1472x1472)",
    "WALLPAPER",
    "Portrait (1088x1920)",
    "Landscape (1920x1088)",
    "SMALL",
    "Portrait (512x768)",
    "Landscape (768x512)",
    "Square (640x640)",
    "CUSTOM",
    "Custom",
]
RESOLUTION_ITEMS_NOT_SELECTABLES = [0, 4, 8, 11, 15]
DEFAULT_RESOLUTION = "Square (640x640)"


########################################################


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


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path).replace("\\", "/")


def pil2pixmap(im):
    if im.mode == "RGB":
        r, g, b = im.split()
        im = Image.merge("RGB", (b, g, r))
    elif im.mode == "RGBA":
        r, g, b, a = im.split()
        im = Image.merge("RGBA", (b, g, r, a))
    elif im.mode == "L":
        im = im.convert("RGBA")
    # Bild in RGBA konvertieren, falls nicht bereits passiert
    im2 = im.convert("RGBA")
    data = im2.tobytes("raw", "RGBA")
    qim = QImage(
        data, im.size[0], im.size[1], QImage.Format_ARGB32)
    pixmap = QPixmap.fromImage(qim)
    return pixmap


def strtobool(val):
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    if isinstance(val, bool):
        return val

    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        raise ValueError("invalid truth value %r" % (val,))


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


class CustomSliderLayout(QHBoxLayout):
    def __init__(self, **option_dict):
        assert all(key in option_dict for key in [
                   "title", "min_value", "max_value", "default_value", "ui_width", "mag", "slider_text_lambda"])
        super(CustomSliderLayout, self).__init__()

        label = QLabel(option_dict["title"])
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(option_dict["min_value"])
        slider.setMaximum(option_dict["max_value"])
        slider.setValue(int(float(option_dict["default_value"])))

        edit = CustomSliderLayout.CustomLineEdit(option_dict, slider)

        if "gui_nobackground" in option_dict and option_dict["gui_nobackground"]:
            label.setStyleSheet("QLabel{background-color:#00000000}")
            slider.setStyleSheet("QSlider{background-color:#00000000}")

        self.addWidget(label)
        self.addWidget(edit)
        if "enable_percent_label" in option_dict and option_dict["enable_percent_label"]:
            self.addWidget(QLabel("%"))
        self.addWidget(slider)

        self.edit = edit

    class CustomLineEdit(QLineEdit):
        def __init__(self, option_dict, target_slider):
            super(QLineEdit, self).__init__(str(option_dict["default_value"]))
            self.min_value = option_dict["min_value"]
            self.max_value = option_dict["max_value"]
            self.mag = option_dict["mag"]
            self.target_slider = target_slider
            self.slider_text_lambda = option_dict["slider_text_lambda"]

            self.setMinimumWidth(option_dict["ui_width"])
            self.setMaximumWidth(option_dict["ui_width"])
            self.setAlignment(Qt.AlignCenter)
            self.setValidator(QIntValidator(0, 100))

            target_slider.valueChanged.connect(
                lambda value: self.setText(self.slider_text_lambda(value)))
            self.returnPressed.connect(
                self.on_enter_or_focusout)

        def on_enter_or_focusout(self):
            value = self.text()
            if not value:
                value = self.min_value
            value = max(self.min_value, min(
                self.max_value, float(value)))
            value *= self.mag
            self.setText(self.slider_text_lambda(value))
            self.target_slider.setValue(int(value))

        def focusOutEvent(self, event):
            super(CustomSliderLayout.CustomLineEdit, self).focusOutEvent(event)
            self.on_enter_or_focusout()

        def setText(self, text):
            super(CustomSliderLayout.CustomLineEdit, self).setText(text)
            self.target_slider.setValue(int(float(text) * self.mag))


class BackgroundFrame(QFrame):
    def __init__(self, parent=None):
        super(BackgroundFrame, self).__init__(parent)

        self.image = QImage()

    def set_background_image(self, image_path):
        self.image.load(image_path)
        self.update()

    def set_background_image_by_img(self, image):
        self.image = image
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        scaled_image = self.image.scaled(
            self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        target_rect = QRectF(
            (self.width() - scaled_image.width()) / 2,
            (self.height() - scaled_image.height()) / 2,
            scaled_image.width(),
            scaled_image.height())
        painter.setOpacity(0.5)
        painter.drawImage(target_rect, scaled_image)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            self.update()
            return True
        return super(BackgroundFrame, self).eventFilter(obj, event)


########################################################################


def init_main_widget(self):
    widget = QWidget()
    widget.setStyleSheet(MAIN_STYLESHEET)

    hbox_headwidget = QHBoxLayout()
    widget.setLayout(hbox_headwidget)

    main_splitter = QSplitter()
    main_splitter.setStyleSheet("""
        QSplitter::handle {
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(0, 0, 0, 0),
            stop:0.1 rgba(0, 0, 0, 0),
            stop:0.1001 rgba(255, 255, 255, 255),
            stop:0.2 rgba(255, 255, 255, 255),
            stop:0.2001 rgba(0, 0, 0, 0),
            stop:0.8 rgba(0, 0, 0, 0),
            stop:0.8001 rgba(255, 255, 255, 255),
            stop:0.9 rgba(255, 255, 255, 255),
            stop:0.9001 rgba(0, 0, 0, 0));
            image: url(:/images/splitter.png);
         }
    """)
    main_splitter.setHandleWidth(0)
    main_splitter.setSizes([9999, 1])
    self.main_splitter = main_splitter
    hbox_headwidget.addWidget(main_splitter)

    # left - input
    self.dict_ui_settings = {}

    widget_left = QWidget()
    main_splitter.addWidget(widget_left)

    hbox_left = QVBoxLayout()
    hbox_left.setContentsMargins(30, 20, 30, 30)
    widget_left.setLayout(hbox_left)

    hbox_upper_buttons = QHBoxLayout()
    hbox_left.addLayout(hbox_upper_buttons)

    hbox_upper_buttons.addLayout(init_setting_buttonlayout(self), stretch=1)
    hbox_upper_buttons.addStretch(9999)
    hbox_upper_buttons.addWidget(init_openfolder_group(self), stretch=1)

    vbox_lower_settings = QHBoxLayout()
    hbox_left.addLayout(vbox_lower_settings)

    vbox_option = QVBoxLayout()
    vbox_lower_settings.addLayout(vbox_option, stretch=1)

    vbox_option.addLayout(init_resolution_options_layout(self), stretch=1)
    vbox_option.addLayout(init_paramater_options_layout(self), stretch=1)
    vbox_option.addLayout(init_image_options_layout(self), stretch=999)

    vbox_lower_settings.addWidget(create_empty(minimum_width=5))

    vbox_input = QVBoxLayout()
    vbox_lower_settings.addLayout(vbox_input, stretch=2000)

    vbox_input.addLayout(init_prompt_layout(self), stretch=250)
    vbox_input.addWidget(create_empty(minimum_height=15), stretch=5)
    vbox_input.addLayout(init_buttons_layout(self), stretch=10)
    self.vbox_input = vbox_input

    #############################################
    # right - expand

    widget_right = QWidget()
    main_splitter.addWidget(widget_right)
    vbox_expand = QVBoxLayout()
    vbox_expand.setContentsMargins(30, 30, 30, 30)
    widget_right.setLayout(vbox_expand)

    image_result = ResultImageView(resource_path("no_image.png"))
    image_result.setStyleSheet("""
        background-color: white;
        background-position: center
    """)
    self.installEventFilter(image_result)
    self.image_result = image_result
    vbox_expand.addWidget(image_result)

    # main_splitter.setCollapsible(0, False)
    main_splitter.widget(1).setMaximumSize(0, 0)

    def on_splitter_move(pos, index):
        if self.is_expand:
            image_result.refresh_size()
            if pos > self.size().width() * 0.9:
                self.on_click_expand()
                self.settings.setValue("splitterSizes", None)

    main_splitter.splitterMoved.connect(on_splitter_move)

    return widget


def init_prompt_layout(self):
    stylesheet_button = """
        color:white;
        text-align: center;
        background-color:#00000000;
        border: 1px solid white;
    """

    def create_prompt_layout(self, title_text, list_buttoncode):
        hbox_prompt_title = QHBoxLayout()

        label = QLabel(title_text)
        hbox_prompt_title.addWidget(label)

        return hbox_prompt_title

    def create_prompt_edit(self, placeholder_text, code):
        textedit = CompletionTextEdit()
        textedit.setPlaceholderText(placeholder_text)
        textedit.setAcceptRichText(False)
        textedit.setAcceptDrops(False)
        self.dict_ui_settings[code] = textedit

        return textedit

    ############################################################

    vbox = QVBoxLayout()

    vbox.addLayout(create_prompt_layout(
        self, S.LABEL_PROMPT, ["add", "set", "sav"]))

    vbox.addWidget(create_prompt_edit(
        self, S.LABEL_PROMPT_HINT, "prompt"), stretch=20)

    vbox.addWidget(create_empty(minimum_height=6))

    vbox.addLayout(create_prompt_layout(
        self, S.LABEL_NPROMPT, ["nadd", "nset", "nsav"]))

    vbox.addWidget(create_prompt_edit(
        self, S.LABEL_NPROMPT_HINT, "negative_prompt"), stretch=10)

    vbox.addWidget(create_empty(minimum_height=6))

    vbox.addWidget(QLabel("결과창"))
    prompt_result = QTextEdit("")
    prompt_result.setPlaceholderText("이곳에 결과가 출력됩니다.")
    prompt_result.setReadOnly(True)
    prompt_result.setAcceptRichText(False)
    prompt_result.setAcceptDrops(False)
    vbox.addWidget(prompt_result, stretch=5)
    self.prompt_result = prompt_result

    return vbox


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
    def create_custom_whlineedit(custom_func):
        class CustomWHLineEdit(QLineEdit):
            def focusOutEvent(self, event):
                custom_func()
                super(CustomWHLineEdit, self).focusOutEvent(event)

            def setText(self, text):
                super(CustomWHLineEdit, self).setText(text)
                custom_func()

        whle = CustomWHLineEdit("640")
        whle.setMinimumWidth(50)
        whle.setValidator(QIntValidator(0, 2000))
        whle.setAlignment(Qt.AlignCenter)
        whle.returnPressed.connect(custom_func)

        return whle

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

    # Width and height labels and line edits
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


def init_paramater_options_layout(self):
    layout = QVBoxLayout()

    # AI Settings Group
    ai_settings_group = QGroupBox("AI Settings")
    layout.addWidget(ai_settings_group)

    ai_settings_layout = QVBoxLayout()
    ai_settings_group.setLayout(ai_settings_layout)

    # Steps Slider
    steps_layout = CustomSliderLayout(
        title="Steps: ",
        min_value=1,
        max_value=50,
        default_value=28,
        ui_width=35,
        mag=1,
        slider_text_lambda=lambda value: "%d" % value
    )
    ai_settings_layout.addLayout(steps_layout, stretch=1)

    lower_layout = QHBoxLayout()
    ai_settings_layout.addLayout(lower_layout, stretch=1)

    lower_slider_layout = QVBoxLayout()
    lower_checkbox_layout = QVBoxLayout()
    lower_layout.addLayout(lower_slider_layout, stretch=2)
    lower_layout.addLayout(lower_checkbox_layout, stretch=1)

    # Seed and Sampler
    seed_layout = QVBoxLayout()
    seed_label_layout = QHBoxLayout()
    seed_label_layout.addWidget(QLabel("시드(Seed)"))
    seed_label_layout.addStretch(1)
    seed_layout.addLayout(seed_label_layout)
    seed_input = QLineEdit()
    seed_input.setPlaceholderText("여기에 시드 입력")
    seed_layout.addWidget(seed_input)
    sampler_layout = QVBoxLayout()
    sampler_layout.addWidget(QLabel("샘플러(Sampler)"))
    sampler_combo = QComboBox()
    sampler_combo.addItems(SAMPLER_ITEMS)
    self.dict_ui_settings["sampler"] = sampler_combo
    sampler_layout.addWidget(sampler_combo)
    lower_slider_layout.addLayout(seed_layout)
    lower_slider_layout.addLayout(sampler_layout)

    # SMEA Checkbox
    seed_opt_layout = QHBoxLayout()
    seed_opt_layout.setContentsMargins(10, 25, 0, 0)
    seed_fix_checkbox = QCheckBox("고정")
    seed_opt_layout.addWidget(seed_fix_checkbox)
    checkbox_layout = QHBoxLayout()
    checkbox_layout.setContentsMargins(10, 30, 0, 0)
    smea_checkbox = QCheckBox("SMEA")
    dyn_checkbox = QCheckBox("+DYN")
    checkbox_layout.addWidget(smea_checkbox, stretch=1)
    checkbox_layout.addWidget(dyn_checkbox, stretch=1)
    lower_checkbox_layout.addLayout(seed_opt_layout)
    lower_checkbox_layout.addLayout(checkbox_layout)

    ########

    # Advanced Settings
    advanced_settings_group = QGroupBox("Advanced Settings")
    advanced_settings_layout = QVBoxLayout()

    # Prompt Guidance Slider

    prompt_guidance_layout = CustomSliderLayout(
        title="Prompt Guidance(CFG):",
        min_value=0,
        max_value=100,
        default_value=5.0,
        ui_width=40,
        mag=10,
        slider_text_lambda=lambda value: "%.1f" % (value / 10)
    )
    advanced_settings_layout.addLayout(prompt_guidance_layout)

    # Prompt Guidance Rescale
    prompt_rescale_layout = CustomSliderLayout(
        title="Prompt Guidance Rescale: ",
        min_value=0,
        max_value=100,
        default_value="0.00",
        ui_width=50,
        mag=100,
        slider_text_lambda=lambda value: "%.2f" % (value / 100)
    )
    advanced_settings_layout.addLayout(prompt_rescale_layout)

    # Undesired Content Strength
    undesired_content_layout = CustomSliderLayout(
        title="Undesired Content Strength:",
        min_value=0,
        max_value=100,
        default_value=100,
        ui_width=40,
        mag=1,
        slider_text_lambda=lambda value: "%d" % value,
        enable_percent_label=True
    )
    advanced_settings_layout.addLayout(undesired_content_layout)

    advanced_settings_group.setLayout(advanced_settings_layout)
    layout.addWidget(advanced_settings_group)

    self.dict_ui_settings["sampler"] = sampler_combo
    self.dict_ui_settings["steps"] = steps_layout.edit
    self.dict_ui_settings["seed"] = seed_input
    self.dict_ui_settings["seed_fix_checkbox"] = seed_fix_checkbox
    self.dict_ui_settings["scale"] = prompt_guidance_layout.edit
    self.dict_ui_settings["cfg_rescale"] = prompt_rescale_layout.edit
    self.dict_ui_settings["sm"] = smea_checkbox
    self.dict_ui_settings["sm_dyn"] = dyn_checkbox
    self.dict_ui_settings["uncond_scale"] = undesired_content_layout.edit

    return layout


def init_image_options_layout(self):
    class ImageSettingGroup(QGroupBox):
        def __init__(self, title, slider_1, slider_2, func_open_img, func_open_folder, func_tag_check, add_inpaint_button):
            super(ImageSettingGroup, self).__init__(title)
            self.setAcceptDrops(True)

            settings_layout = QVBoxLayout()
            self.setLayout(settings_layout)

            ###################################
            # Before
            before_frame = QFrame()
            settings_layout.addWidget(before_frame)

            before_layout = QVBoxLayout()
            before_layout.setAlignment(Qt.AlignCenter)
            before_frame.setLayout(before_layout)

            before_layout.addStretch(1)
            before_inner_layout = QHBoxLayout()
            before_layout.addLayout(before_inner_layout, stretch=1)
            before_layout.addStretch(1)

            def create_open_button(img_src, func):
                open_button = ResultImageView(
                    resource_path(img_src))
                open_button.setStyleSheet("""
                    background-color: """ + COLOR.BRIGHT + """;
                    background-position: center
                """)
                open_button.setFixedSize(QSize(80, 80))
                open_button.clicked.connect(func)
                return open_button
            before_inner_layout.addStretch(1)
            before_inner_layout.addWidget(
                create_open_button("open_image.png", func_open_img), stretch=1)
            before_inner_layout.addStretch(1)
            before_inner_layout.addWidget(
                create_open_button("open_folder.png", func_open_folder), stretch=1)
            before_inner_layout.addStretch(1)

            ###################################
            # After
            # background frame
            after_frame = BackgroundFrame()
            self.installEventFilter(after_frame)
            after_frame.setMinimumHeight(200)
            settings_layout.addWidget(after_frame)

            after_layout = QVBoxLayout()
            after_frame.setLayout(after_layout)

            # slider
            after_layout.addWidget(create_empty(maximum_height=20), stretch=99)
            after_layout.addLayout(slider_1, stretch=1)
            after_layout.addWidget(create_empty(maximum_height=20), stretch=99)
            after_layout.addLayout(slider_2, stretch=1)

            # stretch
            after_layout.addStretch(99)

            folder_layout = QHBoxLayout()
            after_layout.addLayout(folder_layout, stretch=1)
            after_layout.addWidget(create_empty(maximum_height=20), stretch=99)

            # radio_sort
            groupBox_loadmode = QGroupBox("정렬 모드 선택")
            groupBox_loadmode.setStyleSheet("""
                QGroupBox{background-color:#00000000}
                QRadioButton{background-color:#00000000}
                """)
            self.groupBox_loadmode = groupBox_loadmode
            folder_layout.addWidget(groupBox_loadmode)

            groupBoxLayout_loadmode = QHBoxLayout()
            groupBox_loadmode.setLayout(groupBoxLayout_loadmode)

            self.folder_radio1 = QRadioButton("오름차순")
            self.folder_radio1.setChecked(True)
            self.folder_radio2 = QRadioButton("내림차순")
            self.folder_radio3 = QRadioButton("랜덤")
            groupBoxLayout_loadmode.addWidget(self.folder_radio1)
            groupBoxLayout_loadmode.addWidget(self.folder_radio2)
            groupBoxLayout_loadmode.addWidget(self.folder_radio3)

            # folder_label
            folder_label = QLabel()
            folder_label.setStyleSheet("background-color:#00000000")
            folder_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            folder_layout.addWidget(folder_label)

            # target_layout
            target_layout = QHBoxLayout()
            target_title = QLabel("현재 대상: ")
            target_title.setStyleSheet("background-color:#00000000")
            target_layout.addWidget(target_title)

            target_content_label = QLabel()
            target_content_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            target_content_label.setMinimumWidth(360)
            target_content_label.setWordWrap(False)  # 텍스트 줄 바꿈 설정
            target_content_label.setStyleSheet("background-color:#00000000")
            target_layout.addWidget(target_content_label)

            target_remove_button = QPushButton("제거")
            target_layout.addWidget(target_remove_button)

            target_layout.label = target_content_label
            target_layout.button = target_remove_button
            after_layout.addLayout(target_layout, stretch=1)
            after_layout.addWidget(create_empty(maximum_height=20), stretch=99)

            # tagcheck_layout
            tagcheck_layout = QHBoxLayout()

            # inpaint
            if add_inpaint_button:
                inpaint_button = QPushButton("인페인트")
                inpaint_button.clicked.connect(self.on_click_inpaint_button)
                tagcheck_layout.addWidget(inpaint_button)

            tagcheck_layout.addStretch(999)

            tagcheck_checkbox = QCheckBox("이미지 태그 자동 추가: ")
            tagcheck_checkbox.setLayoutDirection(Qt.RightToLeft)
            tagcheck_checkbox.setStyleSheet("background-color:#00000000")
            tagcheck_checkbox.clicked.connect(func_tag_check)
            tagcheck_layout.addWidget(tagcheck_checkbox, stretch=1)

            after_layout.addLayout(tagcheck_layout, stretch=1)
            after_layout.addWidget(create_empty(maximum_height=20), stretch=99)

            self.tagcheck_checkbox = tagcheck_checkbox
            self.target_remove_button = target_remove_button
            self.folder_label = folder_label
            self.before_frame = before_frame
            self.after_frame = after_frame
            self.target_content_label = target_content_label
            self.slider_1 = slider_1
            self.slider_2 = slider_2

            self.set_image()

        def set_image(self, src=""):
            self.src = src
            self.mask = None
            if src:
                self.before_frame.hide()
                self.after_frame.show()

                self.after_frame.set_background_image(src)
                self.target_content_label.setText(src)
            else:
                self.before_frame.show()
                self.after_frame.hide()
                self.target_content_label.setText("")

        def set_folder_mode(self, is_folder_mode):
            self.folder_radio1.setChecked(True)
            self.folder_radio2.setChecked(False)
            self.folder_radio3.setChecked(False)
            self.groupBox_loadmode.setVisible(is_folder_mode)
            self.folder_label.setText("(폴더 모드)" if is_folder_mode else " ")

        def get_folder_sort_mode(self):
            if self.folder_radio1.isChecked():
                return "오름차순"
            elif self.folder_radio2.isChecked():
                return "내림차순"
            elif self.folder_radio3.isChecked():
                return "랜덤"

        def connect_on_click_removebutton(self, func):
            self.target_remove_button.pressed.connect(func)

        def on_click_inpaint_button(self):
            img = QImage(self.src)
            mask = self.mask if self.mask else None
            d = InpaintDialog(img, mask)
            if d.exec_() == QDialog.Accepted:
                self.after_frame.set_background_image_by_img(d.mask_add)
                self.mask = d.mask_only

    image_options_layout = QVBoxLayout()

    # I2I Settings Group
    i2i_settings_group = ImageSettingGroup(
        title="I2I Settings",
        slider_1=CustomSliderLayout(
            title="Strength:",
            min_value=1,
            max_value=99,
            default_value="0.01",
            ui_width=50,
            mag=100,
            slider_text_lambda=lambda value: "%.2f" % (value / 100),
            gui_nobackground=True
        ),
        slider_2=CustomSliderLayout(
            title="   Noise: ",
            min_value=0,
            max_value=99,
            default_value=0,
            ui_width=50,
            mag=100,
            slider_text_lambda=lambda value: "%.2f" % (value / 100),
            gui_nobackground=True
        ),
        func_open_img=lambda: self.show_file_dialog("img2img"),
        func_open_folder=lambda: self.show_openfolder_dialog("img2img"),
        func_tag_check=lambda: self.on_click_tagcheckbox("img2img"),
        add_inpaint_button=True
    )

    def i2i_on_click_removebutton():
        self.dict_img_batch_target["img2img_foldersrc"] = ""
        i2i_settings_group.set_image()
        self.image_options_layout.setStretch(0, 0)
        if not self.vibe_settings_group.src:
            self.image_options_layout.setStretch(2, 9999)
        print(self.i2i_settings_group.mask)
    i2i_settings_group.on_click_removebutton = i2i_on_click_removebutton
    i2i_settings_group.connect_on_click_removebutton(i2i_on_click_removebutton)
    image_options_layout.addWidget(i2i_settings_group, stretch=0)

    vibe_settings_group = ImageSettingGroup(
        title="Vibe Settings",
        slider_1=CustomSliderLayout(
            title="Information Extracted:",
            min_value=1,
            max_value=100,
            default_value=0,
            ui_width=50,
            mag=100,
            slider_text_lambda=lambda value: "%.2f" % (value / 100),
            gui_nobackground=True
        ),
        slider_2=CustomSliderLayout(
            title="Reference Strength:   ",
            min_value=1,
            max_value=100,
            default_value=0,
            ui_width=50,
            mag=100,
            slider_text_lambda=lambda value: "%.2f" % (value / 100),
            gui_nobackground=True
        ),
        func_open_img=lambda: self.show_file_dialog("vibe"),
        func_open_folder=lambda: self.show_openfolder_dialog("vibe"),
        func_tag_check=lambda: self.on_click_tagcheckbox("vibe"),
        add_inpaint_button=False
    )

    def vibe_on_click_removebutton():
        self.dict_img_batch_target["vibe_foldersrc"] = ""
        vibe_settings_group.set_image()
        self.image_options_layout.setStretch(1, 0)
        if not self.i2i_settings_group.src:
            self.image_options_layout.setStretch(2, 9999)
    vibe_settings_group.on_click_removebutton = vibe_on_click_removebutton
    vibe_settings_group.connect_on_click_removebutton(
        vibe_on_click_removebutton)
    image_options_layout.addWidget(vibe_settings_group, stretch=0)

    image_options_layout.addWidget(
        create_empty(minimum_height=1), stretch=9999)

    # Assign
    self.image_options_layout = image_options_layout
    self.i2i_settings_group = i2i_settings_group
    self.vibe_settings_group = vibe_settings_group
    self.dict_ui_settings["strength"] = i2i_settings_group.slider_1.edit
    self.dict_ui_settings["noise"] = i2i_settings_group.slider_2.edit
    self.dict_ui_settings["reference_information_extracted"] = vibe_settings_group.slider_1.edit
    self.dict_ui_settings["reference_strength"] = vibe_settings_group.slider_2.edit

    return image_options_layout


def init_buttons_layout(self):
    class CustomQLabel(QLabel):
        def set_logged_in(self, is_loggedin):
            if is_loggedin:
                super(CustomQLabel, self).setText("")
                self.setStyleSheet("""
                    QLabel {
                        color: white;
                        font-size: 15px;
                    }
                """)
            else:
                super(CustomQLabel, self).setText("로그인 안됨")
                self.setStyleSheet("""
                    QLabel {
                        color: red;
                        font-size: 15px;
                    }
                """)

    main_layout = QVBoxLayout()
    hbox_generate = QHBoxLayout()
    main_layout.addLayout(hbox_generate)

    self.label_loginstate = CustomQLabel()
    self.label_loginstate.set_logged_in(False)
    hbox_generate.addWidget(self.label_loginstate)
    self.button_generate_once = add_button(
        hbox_generate, "생성", self.on_click_generate_once, 200, 200)
    self.button_generate_auto = add_button(
        hbox_generate, "연속 생성", self.on_click_generate_auto, 200, 200)
    self.button_generate_sett = add_button(
        hbox_generate, "연속 세팅 생성", self.on_click_generate_sett, 200, 200)
    self.button_generate_once.setDisabled(True)
    self.button_generate_auto.setDisabled(True)
    self.button_generate_sett.setDisabled(True)

    main_layout.addWidget(create_empty(minimum_height=5))

    hbox_expand = QHBoxLayout()
    main_layout.addLayout(hbox_expand)

    hbox_anlas = QHBoxLayout()
    label_anlas = QLabel("Anlas: ")
    label_anlas.setStyleSheet("""
        font: bold;
        color: """ + COLOR.BUTTON + """;
    """)
    self.label_anlas = label_anlas
    hbox_anlas.addWidget(label_anlas)
    hbox_expand.addLayout(hbox_anlas, stretch=1)

    hbox_expand.addStretch(9)

    stylesheet_button = """
        color:white;
        text-align: center;
        font-weight: bold;
        background-color:#00000000;
        border: 1px solid white;
        padding: 8px;
    """
    button_getter = QPushButton("Info")
    hbox_expand.addWidget(button_getter)
    button_getter.clicked.connect(self.on_click_getter)
    button_getter.setStyleSheet(stylesheet_button)

    button_tagger = QPushButton("Tag")
    hbox_expand.addWidget(button_tagger)
    button_tagger.clicked.connect(self.on_click_tagger)
    button_tagger.setStyleSheet(stylesheet_button)

    button_expand = QPushButton("<<")
    hbox_expand.addWidget(button_expand)
    button_expand.clicked.connect(self.on_click_expand)
    button_expand.setStyleSheet(stylesheet_button)
    self.button_expand = button_expand

    return main_layout


def init_setting_buttonlayout(self,):
    hbox_upper_buttons = QHBoxLayout()

    add_button(hbox_upper_buttons, "세팅 파일로 저장", self.on_click_save_settings)
    add_button(hbox_upper_buttons, "세팅 파일 불러오기", self.on_click_load_settings)

    return hbox_upper_buttons


def init_openfolder_group(self,):
    openfolder_group = QGroupBox("폴더 열기")

    buttons_layout = QHBoxLayout()
    openfolder_group.setLayout(buttons_layout)

    add_button(buttons_layout, "생성 결과",
               lambda: self.on_click_open_folder("path_results"))
    add_button(buttons_layout, "와일드 카드",
               lambda: self.on_click_open_folder("path_wildcards"))
    add_button(buttons_layout, "세팅 파일",
               lambda: self.on_click_open_folder("path_settings"))
    # add_button(buttons_layout, "P",
    #            lambda: self.on_click_open_folder("path_prompts"), 40, 40, 25)
    # add_button(buttons_layout, "NP",
    #            lambda: self.on_click_open_folder("path_nprompts"), 40, 40, 25)

    return openfolder_group
