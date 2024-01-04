import os
import sys

from PyQt5.QtWidgets import QWidget, QLabel, QTextEdit, QLineEdit, QCheckBox, QStyledItemDelegate, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QGroupBox, QSlider, QFrame, QSplitter, QSizePolicy
from PyQt5.QtGui import QColor, QIntValidator, QFont, QPalette, QPixmap, QImage
from PyQt5.QtCore import Qt, QSize, QEvent, QTimer

from PIL import Image

from consts import COLOR, S

########################################################

SAMPLER_ITEMS = ['k_euler', 'k_euler_ancestral',
                 'k_dpmpp_2s_ancestral', 'k_dpmpp_sde']

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
    "Landscape (768x812)",
    "Square (640x640)",
    "CUSTOM",
    "Custom",
]
RESOLUTION_ITEMS_NOT_SELECTABLES = [0, 4, 8, 11, 15]
DEFAULT_RESOLUTION = "Square (640x640)"


########################################################


def create_empty(minimum_width=0, minimum_height=0):
    w = QWidget()
    w.setMinimumWidth(minimum_width)
    w.setMinimumHeight(minimum_height)
    return w


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


########################################################


def init_main_widget(self):
    widget = QWidget()
    widget.setStyleSheet("""
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
    """)

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
    widget_left = QWidget()
    main_splitter.addWidget(widget_left)
    vbox_input = QVBoxLayout()
    vbox_input.setContentsMargins(30, 30, 30, 30)
    widget_left.setLayout(vbox_input)

    self.dict_ui_settings = {}
    vbox_input.addLayout(init_prompt_layout(self), stretch=250)
    vbox_input.addStretch(6)
    vbox_input.addLayout(init_upper_options_layout(self), stretch=15)
    vbox_input.addStretch(6)
    vbox_input.addLayout(init_lower_options_layout(self), stretch=50)
    vbox_input.addWidget(create_empty(minimum_height=15), stretch=5)
    vbox_input.addLayout(init_buttons_layout(self), stretch=10)
    self.vbox_input = vbox_input

    #############################################
    # right - expand

    class CustomImageView(QLabel):
        def __init__(self, first_src):
            super(CustomImageView, self).__init__()
            self.set_custom_pixmap(first_src)

        def set_custom_pixmap(self, img_obj):
            if isinstance(img_obj, str):
                self.pixmap = QPixmap(img_obj)
            else:
                self.pixmap = pil2pixmap(img_obj)
            self.refresh_size()

        def refresh_size(self):
            self.setPixmap(self.pixmap.scaled(
                self.width(), self.height(),
                Qt.KeepAspectRatio))
            self.setMinimumWidth(100)

        def setFixedSize(self, qsize):
            super(CustomImageView, self).setFixedSize(qsize)
            QTimer.singleShot(20, self.refresh_size)

        def eventFilter(self, obj, event):
            if event.type() == QEvent.Resize:
                self.refresh_size()
                return True
            return super(CustomImageView, self).eventFilter(obj, event)

    widget_right = QWidget()
    main_splitter.addWidget(widget_right)
    vbox_expand = QVBoxLayout()
    vbox_expand.setContentsMargins(30, 30, 30, 30)
    widget_right.setLayout(vbox_expand)

    image_result = CustomImageView(resource_path("no_image.png"))
    image_result.setAlignment(Qt.AlignCenter)
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
    def add_titlelabel(vbox, text):
        label = QLabel(text, self)
        vbox.addWidget(label)

    def add_button(hbox, text, callback):
        button = QPushButton(text)
        button.pressed.connect(callback)
        hbox.addWidget(button, stretch=1)

        return button

    def add_textedit(vbox, code, placeholder, stretch):
        textedit = QTextEdit()
        textedit.setPlaceholderText(placeholder)
        textedit.setAcceptRichText(False)
        textedit.setAcceptDrops(False)
        vbox.addWidget(textedit, stretch=stretch)
        self.dict_ui_settings[code] = textedit

        return textedit

    stylesheet_button = """
        color:white;
        text-align: center;
        background-color:#00000000;
        border: 1px solid white;
    """

    vbox = QVBoxLayout()

    hbox_upper_buttons = QHBoxLayout()
    vbox.addLayout(hbox_upper_buttons)

    add_button(hbox_upper_buttons, "세팅 파일로 저장", self.on_click_save_settings)
    add_button(hbox_upper_buttons, "세팅 파일 불러오기", self.on_click_load_settings)
    hbox_upper_buttons.addStretch(2000)
    add_button(hbox_upper_buttons, "미리 뽑아 보기", self.on_click_preview_wildcard)

    vbox.addWidget(create_empty(minimum_height=5))

    hbox_prompt_title = QHBoxLayout()
    vbox.addLayout(hbox_prompt_title)

    add_titlelabel(hbox_prompt_title, S.LABEL_PROMPT)
    hbox_prompt_title.addStretch(2000)

    button_add = add_button(hbox_prompt_title, "Add",
                            lambda: self.on_click_prompt_button("add"))
    button_add.setStyleSheet(stylesheet_button)
    button_add.setFixedSize(QSize(45, 30))

    button_set = add_button(hbox_prompt_title, "Set",
                            lambda: self.on_click_prompt_button("set"))
    button_set.setStyleSheet(stylesheet_button)
    button_set.setFixedSize(QSize(45, 30))

    button_save = add_button(hbox_prompt_title, "Sav",
                             lambda: self.on_click_prompt_button("sav"))
    button_save.setStyleSheet(stylesheet_button)
    button_save.setFixedSize(QSize(45, 30))

    add_textedit(vbox, "prompt", S.LABEL_PROMPT_HINT, 15)

    vbox.addStretch(1)

    hbox_nprompt_title = QHBoxLayout()
    vbox.addLayout(hbox_nprompt_title)

    add_titlelabel(hbox_nprompt_title, S.LABEL_NPROMPT)
    hbox_nprompt_title.addStretch(2000)

    button_nadd = add_button(hbox_nprompt_title, "Add",
                             lambda: self.on_click_prompt_button("nadd"))
    button_nadd.setStyleSheet(stylesheet_button)
    button_nadd.setFixedSize(QSize(45, 30))

    button_nset = add_button(hbox_nprompt_title, "Set",
                             lambda: self.on_click_prompt_button("nset"))
    button_nset.setStyleSheet(stylesheet_button)
    button_nset.setFixedSize(QSize(45, 30))

    button_nsave = add_button(
        hbox_nprompt_title, "Sav", lambda: self.on_click_prompt_button("nsav"))
    button_nsave.setStyleSheet(stylesheet_button)
    button_nsave.setFixedSize(QSize(45, 30))

    add_textedit(vbox, "negative_prompt", S.LABEL_NPROMPT_HINT, 15)

    return vbox


def init_upper_options_layout(self):
    layout = QHBoxLayout()

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
    combo_resolution.setMaxVisibleItems(len(RESOLUTION_ITEMS))
    combo_resolution.addItems(RESOLUTION_ITEMS)
    combo_resolution.setCurrentIndex(
        RESOLUTION_ITEMS.index(self.settings.value(
            "resolution", DEFAULT_RESOLUTION))
    )

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

    self.dict_ui_settings["resolution"] = combo_resolution
    self.dict_ui_settings["width"] = self.width_edit
    self.dict_ui_settings["height"] = self.height_edit

    return layout


def init_lower_options_layout(self):
    def create_custom_lineedit(min_value, max_value, default_value, ui_width, target_slider, mag, slider_text_lambda):
        class CustomLineEdit(QLineEdit):
            def on_enter_or_focusout(self):
                value = self.text()
                if not value:
                    value = min_value
                value = max(min_value, min(
                    max_value, float(value)))
                value *= mag
                self.setText(slider_text_lambda(value))
                target_slider.setValue(int(value))

            def focusOutEvent(self, event):
                super(CustomLineEdit, self).focusOutEvent(event)
                self.on_enter_or_focusout()

            def setText(self, text):
                super(CustomLineEdit, self).setText(text)
                target_slider.setValue(int(float(text) * mag))

        custom_lineedit = CustomLineEdit(str(default_value))
        custom_lineedit.setMinimumWidth(ui_width)
        custom_lineedit.setMaximumWidth(ui_width)
        custom_lineedit.setAlignment(Qt.AlignCenter)
        custom_lineedit.setValidator(QIntValidator(0, 100))

        target_slider.valueChanged.connect(
            lambda value: custom_lineedit.setText(slider_text_lambda(value)))
        custom_lineedit.returnPressed.connect(
            custom_lineedit.on_enter_or_focusout)

        return custom_lineedit

    layout = QVBoxLayout()

    # AI Settings Group
    ai_settings_group = QGroupBox("AI Settings")
    layout.addWidget(ai_settings_group)

    ai_settings_layout = QVBoxLayout()
    ai_settings_group.setLayout(ai_settings_layout)

    ai_settings_layout.addStretch(1)

    # Steps Slider
    steps_layout = QHBoxLayout()
    steps_label = QLabel("Steps: ")
    steps_slider = QSlider(Qt.Horizontal)
    steps_slider.setMinimum(1)
    steps_slider.setMaximum(50)
    steps_slider.setValue(28)
    steps_edit = create_custom_lineedit(
        1, 50, 28, 35, steps_slider, 1, lambda value: "%d" % value)
    steps_layout.addWidget(steps_label)
    steps_layout.addWidget(steps_edit)
    steps_layout.addWidget(steps_slider)
    ai_settings_layout.addLayout(steps_layout, stretch=1)
    ai_settings_layout.addStretch(1)

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
    prompt_guidance_layout = QHBoxLayout()
    prompt_guidance_label = QLabel("Prompt Guidance(CFG):")
    prompt_guidance_slider = QSlider(Qt.Horizontal)
    prompt_guidance_slider.setMinimum(0)
    prompt_guidance_slider.setMaximum(100)
    prompt_guidance_slider.setValue(50)
    prompt_guidance_edit = create_custom_lineedit(
        0, 100, 5.0, 40, prompt_guidance_slider, 10, lambda value: "%.1f" % (value / 10))
    prompt_guidance_layout.addWidget(prompt_guidance_label)
    prompt_guidance_layout.addWidget(prompt_guidance_edit)
    prompt_guidance_layout.addWidget(prompt_guidance_slider)
    advanced_settings_layout.addLayout(prompt_guidance_layout)

    # Prompt Guidance Rescale
    prompt_rescale_layout = QHBoxLayout()
    prompt_rescale_label = QLabel("Prompt Guidance Rescale: ")
    prompt_rescale_slider = QSlider(Qt.Horizontal)
    prompt_rescale_slider.setMinimum(0)
    prompt_rescale_slider.setMaximum(100)
    prompt_rescale_slider.setValue(0)
    prompt_rescale_edit = create_custom_lineedit(
        0, 100, "0.00", 50, prompt_rescale_slider, 100, lambda value: "%.2f" % (value / 100))
    prompt_rescale_layout.addWidget(prompt_rescale_label)
    prompt_rescale_layout.addWidget(prompt_rescale_edit)
    prompt_rescale_layout.addWidget(prompt_rescale_slider)
    advanced_settings_layout.addLayout(prompt_rescale_layout)

    # Undesired Content Strength
    undesired_content_layout = QHBoxLayout()
    undesired_content_label = QLabel("Undesired Content Strength:")
    undesired_content_slider = QSlider(Qt.Horizontal)
    undesired_content_slider.setMinimum(0)
    undesired_content_slider.setMaximum(100)
    undesired_content_slider.setMinimumWidth(150)
    undesired_content_slider.setValue(100)
    undesired_content_edit = create_custom_lineedit(
        0, 100, 100, 40, undesired_content_slider, 1, lambda value: "%d" % value)
    undesired_content_percent_label = QLabel("%")
    undesired_content_layout.addWidget(undesired_content_label)
    undesired_content_layout.addWidget(undesired_content_edit)
    undesired_content_layout.addWidget(undesired_content_percent_label)
    undesired_content_layout.addWidget(undesired_content_slider)
    advanced_settings_layout.addLayout(undesired_content_layout)

    advanced_settings_group.setLayout(advanced_settings_layout)
    layout.addWidget(advanced_settings_group)

    self.dict_ui_settings["sampler"] = sampler_combo
    self.dict_ui_settings["steps"] = steps_edit
    self.dict_ui_settings["seed"] = seed_input
    self.dict_ui_settings["seed_fix_checkbox"] = seed_fix_checkbox
    self.dict_ui_settings["scale"] = prompt_guidance_edit
    self.dict_ui_settings["cfg_rescale"] = prompt_rescale_edit
    self.dict_ui_settings["sm"] = smea_checkbox
    self.dict_ui_settings["sm_dyn"] = dyn_checkbox
    self.dict_ui_settings["uncond_scale"] = undesired_content_edit

    return layout


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

    main_layout = QVBoxLayout()
    hbox_generate = QHBoxLayout()
    main_layout.addLayout(hbox_generate)

    openfolder_group = QGroupBox("폴더 열기")
    hbox_generate.addWidget(openfolder_group)

    buttons_layout = QHBoxLayout()
    openfolder_group.setLayout(buttons_layout)

    add_button(buttons_layout, "결과",
               lambda: self.on_click_open_folder("path_results"), 40, 40, 25)
    add_button(buttons_layout, "W.C",
               lambda: self.on_click_open_folder("path_wildcards"), 40, 40, 25)
    add_button(buttons_layout, "Set",
               lambda: self.on_click_open_folder("path_settings"), 40, 40, 25)
    add_button(buttons_layout, "P",
               lambda: self.on_click_open_folder("path_prompts"), 40, 40, 25)
    add_button(buttons_layout, "NP",
               lambda: self.on_click_open_folder("path_nprompts"), 40, 40, 25)

    hbox_generate.addStretch(2)
    self.label_loginstate = CustomQLabel()
    self.label_loginstate.set_logged_in(False)
    hbox_generate.addWidget(self.label_loginstate)
    self.button_generate_once = add_button(
        hbox_generate, "생성", self.on_click_generate_once, 200, 200)
    self.button_generate_auto = add_button(
        hbox_generate, "연속 생성", self.on_click_generate_auto, 200, 200)
    self.button_generate_once.setDisabled(True)
    self.button_generate_auto.setDisabled(True)

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
    """

    button_info = add_button(
        hbox_expand, "i", self.on_click_imageinfo)
    button_info.setStyleSheet(stylesheet_button)
    button_info.setFixedSize(QSize(30, 30))

    button_expand = add_button(
        hbox_expand, "<<", self.on_click_expand)
    button_expand.setStyleSheet(stylesheet_button)
    button_expand.setFixedSize(QSize(50, 30))
    self.button_expand = button_expand

    return main_layout
