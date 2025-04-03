import os
import sys

from PyQt5.QtWidgets import QApplication, QRadioButton, QSlider, QGroupBox, QFileDialog, QLabel, QCheckBox, QVBoxLayout, QHBoxLayout, QPushButton, QDialog, QSizePolicy
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import QApplication, QMainWindow,  QFileDialog, QDialog

from core.worker.danbooru_tagger import DanbooruTagger

from util.common_util import strtobool, get_key_from_dict
from util.ui_util import create_empty

from config.paths import DEFAULT_PATH
from config.consts import LIST_TAGGER_MODEL

class OptionDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        parent = self.parent()
        parent_pos = parent.pos()

        self.setWindowTitle('옵션')
        self.move(parent_pos.x() + 50, parent_pos.y() + 50)
        self.resize(600, 200)
        layout = QVBoxLayout()

        self.dict_label_loc = {}

        def add_item(layout, code, text):
            hbox_item = QHBoxLayout()
            layout.addLayout(hbox_item)

            label_title = QLabel(text)
            hbox_item.addWidget(label_title)

            path = parent.settings.value(
                code, DEFAULT_PATH[code])
            label_loc = QLabel(os.path.abspath(path))
            label_loc.setStyleSheet("font-size: 14px")
            self.dict_label_loc[code] = label_loc
            hbox_item.addWidget(label_loc, stretch=999)

            button_select_loc = QPushButton("위치 변경")
            button_select_loc.setSizePolicy(
                QSizePolicy.Minimum, QSizePolicy.Minimum)
            button_select_loc.clicked.connect(
                lambda: self.on_click_select_button(code))
            hbox_item.addWidget(button_select_loc)

            button_reset_loc = QPushButton("리셋")
            button_reset_loc.setSizePolicy(
                QSizePolicy.Minimum, QSizePolicy.Minimum)
            button_reset_loc.clicked.connect(
                lambda: self.on_click_reset_button(code))
            hbox_item.addWidget(button_reset_loc)

        folderloc_group = QGroupBox("폴더 위치")
        layout.addWidget(folderloc_group)

        folderloc_group_layout = QVBoxLayout()
        folderloc_group.setLayout(folderloc_group_layout)

        add_item(folderloc_group_layout, "path_results", "생성이미지 저장 위치 : ")
        add_item(folderloc_group_layout, "path_wildcards", "와일드카드 저장 위치 : ")
        add_item(folderloc_group_layout, "path_settings", "세팅 파일 저장 위치 : ")
        add_item(folderloc_group_layout, "path_models", "태거 모델 저장 위치 : ")

        layout.addWidget(create_empty(minimum_height=6))

        groupBox_tagger = QGroupBox("태그 모델 설치 및 선택")
        self.groupBox_tagger = groupBox_tagger
        layout.addWidget(groupBox_tagger)

        groupBox_tagger_layout = QVBoxLayout()
        groupBox_tagger.setLayout(groupBox_tagger_layout)

        list_installed_model = parent.dtagger.get_installed_models()
        self.dict_tagger_model_radio = {}
        self.dict_tagger_model_button = {}
        for index, model_name in enumerate(LIST_TAGGER_MODEL):
            radio_layout = QHBoxLayout()
            groupBox_tagger_layout.addLayout(radio_layout)

            radio = QRadioButton(model_name + ("(추천)" if index == 0 else ""))
            radio.setEnabled(False)
            radio.clicked.connect(self.on_click_modelradio_button)
            self.dict_tagger_model_radio[model_name] = radio
            radio_layout.addWidget(radio)

            download_button = QPushButton("다운로드")
            download_button.clicked.connect(self.on_click_download_button)
            self.dict_tagger_model_button[model_name] = download_button
            radio_layout.addWidget(download_button)

            if model_name + ".onnx" in list_installed_model:
                radio.setEnabled(True)
                download_button.setEnabled(False)

        now_selected = parent.settings.value("selected_tagger_model", '')
        if now_selected and now_selected in list_installed_model:
            self.dict_tagger_model_radio[now_selected].setChecked(True)
        else:
            for k, v in self.dict_tagger_model_radio.items():
                if v.isEnabled():
                    v.setChecked(True)
                    parent.settings.setValue("selected_tagger_model", k)
                    break

        layout.addWidget(create_empty(minimum_height=6))

        font_layout = QHBoxLayout()
        layout.addLayout(font_layout)

        now_font_size = self.parent().settings.value("nag_font_size", 18)
        font_label = QLabel(f'글꼴 크기(종료시 적용, 기본 18): {now_font_size}')
        self.font_label = font_label
        font_layout.addWidget(font_label)

        font_progress_bar = QSlider(self)
        font_progress_bar.setMinimum(14)
        font_progress_bar.setMaximum(50)
        font_progress_bar.setValue(now_font_size)
        font_progress_bar.setOrientation(Qt.Horizontal)
        font_progress_bar.valueChanged.connect(self.on_fontlabel_updated)
        font_layout.addWidget(font_progress_bar)

        checkbox_completeoff = QCheckBox("태그 자동완성 키기")
        checkbox_completeoff.setChecked(strtobool(
            parent.settings.value("will_complete_tag", True)))
        self.checkbox_completeoff = checkbox_completeoff
        layout.addWidget(checkbox_completeoff)

        checkbox_savepname = QCheckBox("파일 생성시 이름에 프롬프트 넣기")
        checkbox_savepname.setChecked(strtobool(
            parent.settings.value("will_savename_prompt", True)))
        self.checkbox_savepname = checkbox_savepname
        layout.addWidget(checkbox_savepname)

        checkbox_savei2iname = QCheckBox("i2i 폴더모드 적용시 원본 파일 이름 사용하기")
        checkbox_savei2iname.setChecked(strtobool(
            parent.settings.value("will_savename_i2i", False)))
        self.checkbox_savei2iname = checkbox_savei2iname
        layout.addWidget(checkbox_savei2iname)

        button_close = QPushButton("닫기")
        button_close.clicked.connect(self.on_click_close_button)
        self.button_close = button_close

        layout.addStretch(2)

        qhl_close = QHBoxLayout()
        qhl_close.addStretch(4)
        qhl_close.addWidget(self.button_close, 2)
        layout.addLayout(qhl_close)

        self.setLayout(layout)

    def on_fontlabel_updated(self, value):
        self.font_label.setText(f'폰트 사이즈(종료시 적용, 기본 18): {value}')
        self.parent().settings.setValue("nag_font_size", int(value))

    def on_click_select_button(self, code):
        select_dialog = QFileDialog()
        save_loc = select_dialog.getExistingDirectory(
            self, '저장할 위치를 골라주세요.')

        if save_loc:
            self.parent().on_change_path(code, save_loc)

            self.refresh_label(code)

    def on_click_download_button(self):
        button = self.sender()
        model_name = get_key_from_dict(self.dict_tagger_model_button, button)

        self.parent().install_model(model_name)

    def on_click_modelradio_button(self):
        radio = self.sender()
        model_name = get_key_from_dict(self.dict_tagger_model_radio, radio)

        self.parent().settings.setValue("selected_tagger_model", model_name)

    def on_click_reset_button(self, code):
        self.parent().on_change_path(code, DEFAULT_PATH[code])

        self.refresh_label(code)

    def on_model_downloaded(self, model_name):
        self.dict_tagger_model_radio[model_name].setEnabled(True)
        self.dict_tagger_model_button[model_name].setEnabled(False)

    def refresh_label(self, code):
        path = self.parent().settings.value(code, DEFAULT_PATH[code])
        self.dict_label_loc[code].setText(path)

    def on_click_close_button(self):
        self.parent().settings.setValue(
            "will_complete_tag", self.checkbox_completeoff.isChecked())
        self.parent().settings.setValue(
            "will_savename_prompt", self.checkbox_savepname.isChecked())
        self.parent().settings.setValue(
            "will_savename_i2i", self.checkbox_savei2iname.isChecked())
        self.reject()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    from PyQt5.QtWidgets import QMainWindow
    from PyQt5.QtCore import QSettings
    TOP_NAME = "dcp_arca"
    APP_NAME = "nag_gui"
    qw = QMainWindow()
    qw.move(200, 200)
    qw.settings = QSettings(TOP_NAME, APP_NAME)
    qw.dtagger = DanbooruTagger(qw.settings.value(
        "path_models", os.path.abspath(DEFAULT_PATH["path_models"])))
    OptionDialog(qw)