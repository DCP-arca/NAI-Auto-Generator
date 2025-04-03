from PyQt5.QtWidgets import QRadioButton, QGroupBox, QFrame, QLabel, QCheckBox, QVBoxLayout, QHBoxLayout, QPushButton, QDialog, QMessageBox
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtCore import Qt, QEvent, QRectF, QSize

from gui.widget.result_image_view import ResultImageView
from gui.widget.custom_slider_widget import CustomSliderWidget

from gui.dialog.inpaint_dialog import InpaintDialog
from gui.dialog.etc_dialog import show_file_dialog, show_openfolder_dialog

from util.file_util import resource_path
from util.ui_util import create_empty

from config.paths import PATH_IMG_OPEN_IMAGE, PATH_IMG_OPEN_FOLDER
from config.themes import COLOR

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
            create_open_button(PATH_IMG_OPEN_IMAGE, func_open_img), stretch=1)
        before_inner_layout.addStretch(1)
        before_inner_layout.addWidget(
            create_open_button(PATH_IMG_OPEN_FOLDER, func_open_folder), stretch=1)
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


def on_click_tagcheckbox(self, mode):
    box = self.sender()
    if box.isChecked():
        if not self.settings.value("selected_tagger_model", ""):
            box.setChecked(False)
            QMessageBox.information(
                self, '경고', "먼저 옵션에서 태깅 모델을 다운/선택 해주세요.")
            return

        QMessageBox.information(
            self, '안내', "새로운 이미지를 불러올때마다 태그를 읽습니다.\n프롬프트 내에 @@" + mode + "@@를 입력해주세요.\n해당 자리에 삽입됩니다.")
        return


def init_image_options_layout(self):
    image_options_layout = QVBoxLayout()

    # I2I Settings Group
    i2i_settings_group = ImageSettingGroup(
        title="I2I Settings",
        slider_1=CustomSliderWidget(
            title="Strength:",
            min_value=1,
            max_value=99,
            default_value="0.01",
            ui_width=50,
            mag=100,
            slider_text_lambda=lambda value: "%.2f" % (value / 100),
            gui_nobackground=True
        ),
        slider_2=CustomSliderWidget(
            title="   Noise: ",
            min_value=0,
            max_value=99,
            default_value=0,
            ui_width=50,
            mag=100,
            slider_text_lambda=lambda value: "%.2f" % (value / 100),
            gui_nobackground=True
        ),
        func_open_img=lambda: show_file_dialog(self, "img2img"),
        func_open_folder=lambda: show_openfolder_dialog(self, "img2img"),
        func_tag_check=lambda: on_click_tagcheckbox(self, "img2img"),
        add_inpaint_button=True
    )

    def i2i_on_click_removebutton():
        self.dict_img_batch_target["img2img_foldersrc"] = ""
        i2i_settings_group.set_image()
        self.image_options_layout.setStretch(0, 0)
        if not self.vibe_settings_group.src:
            self.image_options_layout.setStretch(2, 9999)

    i2i_settings_group.on_click_removebutton = i2i_on_click_removebutton
    i2i_settings_group.connect_on_click_removebutton(i2i_on_click_removebutton)
    image_options_layout.addWidget(i2i_settings_group, stretch=0)

    vibe_settings_group = ImageSettingGroup(
        title="Vibe Settings",
        slider_1=CustomSliderWidget(
            title="Information Extracted:",
            min_value=1,
            max_value=100,
            default_value=0,
            ui_width=50,
            mag=100,
            slider_text_lambda=lambda value: "%.2f" % (value / 100),
            gui_nobackground=True
        ),
        slider_2=CustomSliderWidget(
            title="Reference Strength:   ",
            min_value=1,
            max_value=100,
            default_value=0,
            ui_width=50,
            mag=100,
            slider_text_lambda=lambda value: "%.2f" % (value / 100),
            gui_nobackground=True
        ),
        func_open_img=lambda: show_file_dialog(self, "vibe"),
        func_open_folder=lambda: show_openfolder_dialog(self, "vibe"),
        func_tag_check=lambda: on_click_tagcheckbox(self, "vibe"),
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
