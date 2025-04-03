
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QSplitter

from gui.layout.resolution_options_layout import init_resolution_options_layout
from gui.layout.parameter_options_layout import init_parameter_options_layout
from gui.layout.generate_buttons_layout import GenerateButtonsLayout
from gui.layout.prompt_layout import PromptLayout

from gui.widget.result_image_view import ResultImageView

from config.paths import PATH_IMG_NO_IMAGE
from config.themes import MAIN_STYLESHEET

from util.file_util import resource_path
from util.ui_util import create_empty, add_button

from gui.layout.image_options_layout import init_image_options_layout


def init_main_layout(self):
    widget = QWidget()
    widget.setStyleSheet(MAIN_STYLESHEET)

    hbox_headwidget = QHBoxLayout()
    widget.setLayout(hbox_headwidget)

    main_splitter = QSplitter()
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
    vbox_option.addLayout(init_parameter_options_layout(self), stretch=1)
    vbox_option.addLayout(init_image_options_layout(self), stretch=999)

    vbox_lower_settings.addWidget(create_empty(minimum_width=5))

    vbox_input = QVBoxLayout()
    vbox_lower_settings.addLayout(vbox_input, stretch=2000)

    vbox_input.addLayout(PromptLayout(self).init(), stretch=250)
    vbox_input.addWidget(create_empty(minimum_height=15), stretch=5)
    
    vbox_input.addLayout(GenerateButtonsLayout(self).init(), stretch=10)
    self.vbox_input = vbox_input

    #############################################
    # right - expand

    widget_right = QWidget()
    main_splitter.addWidget(widget_right)
    vbox_expand = QVBoxLayout()
    vbox_expand.setContentsMargins(30, 30, 30, 30)
    widget_right.setLayout(vbox_expand)

    image_result = ResultImageView(resource_path(PATH_IMG_NO_IMAGE))
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

    self.setCentralWidget(widget)


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

    return openfolder_group
