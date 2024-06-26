import json
import sys
import os
import io
import zipfile
import time
import datetime
import random
import base64
from io import BytesIO
from PIL import Image
from urllib import request

from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog, QMessageBox, QDialog
from PyQt5.QtCore import QSettings, QPoint, QSize, QCoreApplication, QThread, pyqtSignal, QTimer, QBuffer
from gui_init import init_main_widget
from gui_dialog import LoginDialog, OptionDialog, GenerateDialog, MiniUtilDialog, FileIODialog

from consts import COLOR, S, DEFAULT_PARAMS, DEFAULT_PATH, RESOLUTION_FAMILIY_MASK, RESOLUTION_FAMILIY, prettify_naidict, DEFAULT_TAGCOMPLETION_PATH

import naiinfo_getter
from nai_generator import NAIGenerator, NAIAction
from wildcard_applier import WildcardApplier
from danbooru_tagger import DanbooruTagger

TITLE_NAME = "NAI Auto Generator"
TOP_NAME = "dcp_arca"
APP_NAME = "nag_gui"

MAX_COUNT_FOR_WHILE = 10

#############################################


def create_folder_if_not_exists(foldersrc):
    if not os.path.exists(foldersrc):
        os.makedirs(foldersrc)


def prettify_dict(d):
    return json.dumps(d, sort_keys=True, indent=4)


def get_imgcount_from_foldersrc(foldersrc):
    return len([file for file in os.listdir(foldersrc) if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))])


def pick_imgsrc_from_foldersrc(foldersrc, index, sort_order):
    files = [file for file in os.listdir(foldersrc) if file.lower(
    ).endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]

    is_reset = False
    if index != 0 and index % len(files) == 0:
        is_reset = True

    # 파일들을 정렬
    if sort_order == '오름차순':
        files.sort()
    elif sort_order == '내림차순':
        files.sort(reverse=True)
    elif sort_order == '랜덤':
        random.seed(random.randint(0, 1000000))
        random.shuffle(files)
        is_reset = False

    # 인덱스가 파일 개수를 초과하는 경우
    while index >= len(files):
        index -= len(files)

    # 정렬된 파일 리스트에서 인덱스에 해당하는 파일의 주소 반환
    return os.path.join(foldersrc, files[index]), is_reset


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


def pickedit_lessthan_str(original_str):
    try_count = 0

    edited_str = original_str
    while try_count < MAX_COUNT_FOR_WHILE:
        try_count += 1

        before_edit_str = edited_str
        pos_prev = 0
        while True:
            pos_r = edited_str.find(">", pos_prev + 1)
            if pos_r == -1:
                break

            pos_l = edited_str.rfind("<", pos_prev, pos_r)
            if pos_l != -1:
                left = edited_str[0:pos_l]
                center = edited_str[pos_l + 1:pos_r]
                right = edited_str[pos_r + 1:len(edited_str)]

                center_splited = center.split("|")
                center_picked = center_splited[random.randrange(
                    0, len(center_splited))]

                result_left = left + center_picked
                pos_prev = len(result_left)
                edited_str = result_left + right
            else:
                pos_prev = pos_r

        if before_edit_str == edited_str:
            break

    return edited_str


def create_windows_filepath(base_path, filename, extension, max_length=150):
    # 파일 이름으로 사용할 수 없는 문자 제거
    cleaned_filename = filename.replace("\n", "")
    cleaned_filename = cleaned_filename.replace("\\", "")

    invalid_chars = r'<>:"/\|?*'
    cleaned_filename = ''.join(
        char for char in cleaned_filename if char not in invalid_chars)

    # 파일 이름의 최대 길이 제한 (확장자 길이 고려)
    max_filename_length = max_length - len(base_path) - len(extension) - 1
    if max_filename_length < 5:
        return None
    cleaned_filename = cleaned_filename[:max_filename_length]

    # 경로, 파일 이름, 확장자 합치기
    filepath = os.path.join(base_path, cleaned_filename + extension)

    return filepath


def inject_imagetag(original_str, tagname, additional_str):
    result_str = original_str[:]

    tag_str_left = "@@" + tagname
    left_pos = original_str.find(tag_str_left)
    if left_pos != -1:
        right_pos = original_str.find("@@", left_pos + 1)
        except_tag_list = [x.strip() for x in original_str[left_pos +
                                                           len(tag_str_left) + 1:right_pos].split(",")]
        original_tag_list = [x.strip() for x in additional_str.split(',')]
        target_tag_list = [
            x for x in original_tag_list if x not in except_tag_list]

        result_str = original_str[0:left_pos] + ", ".join(target_tag_list) + \
            original_str[right_pos + 2:len(original_str)]

    return result_str


def get_filename_only(path):
    filename, _ = os.path.splitext(os.path.basename(path))
    return filename


def convert_qimage_to_imagedata(qimage):
    try:
        buf = QBuffer()
        buf.open(QBuffer.ReadWrite)
        qimage.save(buf, "PNG")
        pil_im = Image.open(io.BytesIO(buf.data()))

        buf = io.BytesIO()
        pil_im.save(buf, format='png', quality=100)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception as e:
        return ""


class NAIAutoGeneratorWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.init_variable()
        self.init_window()
        self.init_statusbar()
        self.init_menubar()
        self.init_content()
        self.load_data()
        self.check_folders()
        self.apply_theme()
        self.show()

        self.init_nai()
        self.init_wc()
        self.init_tagger()
        self.init_completion()

    def apply_theme(self):
        font_size = self.settings.value("nag_font_size", 18)
        self.app.setStyleSheet("QWidget{font-size:" + str(font_size) + "px}")

    def init_variable(self):
        self.is_expand = False
        self.trying_auto_login = False
        self.autogenerate_thread = None
        self.list_settings_batch_target = []
        self.index_settings_batch_target = -1
        self.dict_img_batch_target = {
            "img2img_foldersrc": "",
            "img2img_index": -1,
            "i2i_last_src": "",
            "i2i_last_dst": "",
            "vibe_foldersrc": "",
            "vibe_index": -1,
            "vibe_last_src": "",
            "vibe_last_dst": "",
        }

    def init_window(self):
        self.setWindowTitle(TITLE_NAME)
        self.settings = QSettings(TOP_NAME, APP_NAME)
        self.move(self.settings.value("pos", QPoint(500, 200)))
        self.resize(self.settings.value("size", QSize(1179, 1044)))
        self.settings.setValue("splitterSizes", None)
        self.setAcceptDrops(True)

    def init_statusbar(self):
        statusbar = self.statusBar()
        statusbar.messageChanged.connect(self.on_statusbar_message_changed)
        self.set_statusbar_text("BEFORE_LOGIN")

    def init_menubar(self):
        openAction = QAction('파일 열기(Open file)', self)
        openAction.setShortcut('Ctrl+O')
        openAction.triggered.connect(lambda: self.show_file_dialog("file"))

        loginAction = QAction('로그인(Log in)', self)
        loginAction.setShortcut('Ctrl+L')
        loginAction.triggered.connect(self.show_login_dialog)

        optionAction = QAction('옵션(Option)', self)
        optionAction.setShortcut('Ctrl+U')
        optionAction.triggered.connect(self.show_option_dialog)

        exitAction = QAction('종료(Exit)', self)
        exitAction.setShortcut('Ctrl+W')
        exitAction.triggered.connect(self.quit_app)

        aboutAction = QAction('만든 이(About)', self)
        aboutAction.triggered.connect(self.show_about_dialog)

        getterAction = QAction('이미지 정보 확인기(Info Getter)', self)
        getterAction.setShortcut('Ctrl+I')
        getterAction.triggered.connect(self.on_click_getter)

        taggerAction = QAction('태그 확인기(Danbooru Tagger)', self)
        taggerAction.setShortcut('Ctrl+T')
        taggerAction.triggered.connect(self.on_click_tagger)

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        filemenu_file = menubar.addMenu('&파일(Files)')
        filemenu_file.addAction(openAction)
        filemenu_file.addAction(loginAction)
        filemenu_file.addAction(optionAction)
        filemenu_file.addAction(exitAction)
        filemenu_tool = menubar.addMenu('&도구(Tools)')
        filemenu_tool.addAction(getterAction)
        filemenu_tool.addAction(taggerAction)
        filemenu_etc = menubar.addMenu('&기타(Etc)')
        filemenu_etc.addAction(aboutAction)

    def init_content(self):
        widget = init_main_widget(self)
        self.setCentralWidget(widget)

    def init_nai(self):
        self.nai = NAIGenerator()

        if self.settings.value("auto_login", False):
            access_token = self.settings.value("access_token", "")
            username = self.settings.value("username", "")
            password = self.settings.value("password", "")
            if not access_token or not username or not password:
                return

            self.set_statusbar_text("LOGGINGIN")
            self.nai.access_token = access_token
            self.nai.username = username
            self.nai.password = password

            # self.trying_auto_login = True
            # validate_thread = LoginThread(self, self.nai, username, password)
            # validate_thread.login_result.connect(self.on_login_result)
            # validate_thread.start()
            self.trying_auto_login = True
            validate_thread = TokenValidateThread(self)
            validate_thread.validation_result.connect(self.on_login_result)
            validate_thread.start()

    def init_wc(self):
        self.wcapplier = WildcardApplier(self.settings.value(
            "path_wildcards", os.path.abspath(DEFAULT_PATH["path_wildcards"])))

    def init_tagger(self):
        self.dtagger = DanbooruTagger(self.settings.value(
            "path_models", os.path.abspath(DEFAULT_PATH["path_models"])))

    def init_completion(self):
        if strtobool(self.settings.value("will_complete_tag", True)):
            generate_thread = CompletionTagLoadThread(self)
            generate_thread.on_load_completiontag_sucess.connect(
                self._on_load_completiontag_sucess)
            generate_thread.start()

    def save_data(self):
        data_dict = self.get_data()

        data_dict["seed_fix_checkbox"] = self.dict_ui_settings["seed_fix_checkbox"].isChecked()

        for k, v in data_dict.items():
            self.settings.setValue(k, v)

    def set_data(self, data_dict):
        # uncond_scale shown as * 100
        uncond_scale = data_dict['uncond_scale']
        data_dict['uncond_scale'] = str(int(float(uncond_scale) * 100))

        dict_ui = self.dict_ui_settings

        dict_ui["sampler"].setCurrentText(data_dict["sampler"])

        list_ui_using_settext = ["prompt", "negative_prompt", "width", "height",
                                 "steps", "seed", "scale", "uncond_scale", "cfg_rescale",
                                 "strength", "noise", "reference_information_extracted", "reference_strength"]
        for key in list_ui_using_settext:
            if key in data_dict:
                dict_ui[key].setText(str(data_dict[key]))
            else:
                print(key)

        list_ui_using_setchecked = ["sm", "sm_dyn"]
        for key in list_ui_using_setchecked:
            dict_ui[key].setChecked(strtobool(data_dict[key]))

    def load_data(self):
        data_dict = {}
        for key in DEFAULT_PARAMS:
            data_dict[key] = str(self.settings.value(key, DEFAULT_PARAMS[key]))

        self.set_data(data_dict)

        # seed_fix_checkbox will reset on start
        # self.dict_ui_settings["seed_fix_checkbox"].setChecked(
        #     strtobool(self.settings.value("seed_fix_checkbox", False)))

    def check_folders(self):
        for key, default_path in DEFAULT_PATH.items():
            path = self.settings.value(key, os.path.abspath(default_path))
            create_folder_if_not_exists(path)

    def _on_load_completiontag_sucess(self, tag_list):
        if tag_list:
            target_code = ["prompt", "negative_prompt"]
            for code in target_code:
                self.dict_ui_settings[code].start_complete_mode(tag_list)

    def get_data(self, do_convert_type=False):
        data = {
            "prompt": self.dict_ui_settings["prompt"].toPlainText(),
            "negative_prompt": self.dict_ui_settings["negative_prompt"].toPlainText(),
            "width": self.dict_ui_settings["width"].text(),
            "height": self.dict_ui_settings["height"].text(),
            "sampler": self.dict_ui_settings["sampler"].currentText(),
            "steps": self.dict_ui_settings["steps"].text(),
            "seed": self.dict_ui_settings["seed"].text(),
            "scale": self.dict_ui_settings["scale"].text(),
            "cfg_rescale": self.dict_ui_settings["cfg_rescale"].text(),
            "sm": str(self.dict_ui_settings["sm"].isChecked()),
            "sm_dyn": str(self.dict_ui_settings["sm_dyn"].isChecked()),
            "uncond_scale": str(float(self.dict_ui_settings["uncond_scale"].text()) / 100),
            "strength": self.dict_ui_settings["strength"].text(),
            "noise": self.dict_ui_settings["noise"].text(),
            "reference_information_extracted": self.dict_ui_settings["reference_information_extracted"].text(),
            "reference_strength": self.dict_ui_settings["reference_strength"].text(),
        }

        if do_convert_type:
            data["width"] = int(data["width"])
            data["height"] = int(data["height"])
            data["steps"] = int(data["steps"])
            data["seed"] = int(data["seed"] or 0)
            data["scale"] = float(data["scale"])
            data["cfg_rescale"] = float(data["cfg_rescale"])
            data["sm"] = strtobool(data["sm"])
            data["sm_dyn"] = strtobool(data["sm_dyn"])
            data["uncond_scale"] = float(data["uncond_scale"])
            data["strength"] = float(data["strength"])
            data["noise"] = float(data["noise"])
            data["reference_information_extracted"] = float(
                data["reference_information_extracted"])
            data["reference_strength"] = float(data["reference_strength"])

        return data

    # Warning! Don't interact with pyqt gui in this function
    def _get_data_for_generate(self):
        data = self.get_data(True)
        self.save_data()

        # sampler check
        if data['sampler'] == 'ddim_v3':
            data['sm'] = False
            data['sm_dyn'] = False

        # data precheck
        data["prompt"], data["negative_prompt"] = self._preedit_prompt(
            data["prompt"], data["negative_prompt"])

        # seed pick
        if not self.dict_ui_settings["seed_fix_checkbox"].isChecked() or data["seed"] == -1:
            data["seed"] = random.randint(0, 9999999999)

        # wh pick
        if strtobool(self.checkbox_random_resolution.isChecked()):
            fl = self.get_now_resolution_familly_list()
            if fl:
                text = fl[random.randrange(0, len(fl))]

                res_text = text.split("(")[1].split(")")[0]
                width, height = res_text.split("x")
                data["width"], data["height"] = int(width), int(height)

        # image option check
        data["image"] = None
        data["reference_image"] = None
        data["mask"] = None
        if self.i2i_settings_group.src:
            imgdata_i2i = self.nai.convert_src_to_imagedata(
                self.i2i_settings_group.src)
            if imgdata_i2i:
                data["image"] = imgdata_i2i
                # 만약 i2i가 켜져있다면
                # sm설정을 반드시 꺼야함. 안그러면 흐릿하게 나옴.
                data['sm'] = False
                data['sm_dyn'] = False

                # mask 체크
                if self.i2i_settings_group.mask:
                    data['mask'] = convert_qimage_to_imagedata(
                        self.i2i_settings_group.mask)
            else:
                self.i2i_settings_group.on_click_removebutton()
        if self.vibe_settings_group.src:
            imgdata_vibe = self.nai.convert_src_to_imagedata(
                self.vibe_settings_group.src)
            if imgdata_vibe:
                data["reference_image"] = imgdata_vibe
            else:
                self.vibe_settings_group.on_click_removebutton()

        # i2i 와 vibe 세팅
        batch = self.dict_img_batch_target
        for mode_str in ["i2i", "vibe"]:
            target_group = self.i2i_settings_group if mode_str == "i2i" else self.vibe_settings_group

            if target_group.tagcheck_checkbox.isChecked():
                if target_group.src:
                    if batch[mode_str + "_last_src"] != target_group.src:
                        batch[mode_str + "_last_src"] = target_group.src
                        batch[mode_str + "_last_dst"] = self.predict_tag_from(
                            "src", target_group.src, False)
                        if not batch[mode_str + "_last_dst"]:
                            batch[mode_str + "_last_src"] = ""
                            batch[mode_str + "_last_dst"] = ""

                    data["prompt"] = inject_imagetag(
                        data["prompt"], "img2img" if mode_str == "i2i" else "vibe", batch[mode_str + "_last_dst"])
                    data["negative_prompt"] = inject_imagetag(
                        data["negative_prompt"], "img2img" if mode_str == "i2i" else "vibe", batch[mode_str + "_last_dst"])
            else:
                batch[mode_str + "_last_src"] = ""
                batch[mode_str + "_last_dst"] = ""

        return data

    def _preedit_prompt(self, prompt, nprompt):
        try_count = 0
        edited_prompt = prompt
        while try_count < MAX_COUNT_FOR_WHILE:
            try_count += 1

            before_edit_prompt = edited_prompt

            edited_prompt = pickedit_lessthan_str(edited_prompt)
            edited_prompt = self.apply_wildcards(edited_prompt)

            if before_edit_prompt == edited_prompt:
                break

        try_count = 0
        edited_nprompt = nprompt
        while try_count < MAX_COUNT_FOR_WHILE:
            try_count += 1

            before_edit_nprompt = edited_nprompt
            # lessthan pick
            edited_nprompt = pickedit_lessthan_str(edited_nprompt)
            # wildcards pick
            edited_nprompt = self.apply_wildcards(edited_nprompt)

            if before_edit_nprompt == edited_nprompt:
                break

        return edited_prompt, edited_nprompt

    def _on_after_create_data_apply_gui(self):
        data = self.nai.parameters

        # resolution text
        fl = self.get_now_resolution_familly_list()
        if fl:
            for resol in fl:
                if str(data["width"]) + "x" + str(data["height"]) in resol:
                    self.combo_resolution.setCurrentText(resol)
                    break

        # seed text
        self.dict_ui_settings["seed"].setText(str(data["seed"]))

        # result text
        self.set_result_text(data)

    def on_click_generate_once(self):
        self.list_settings_batch_target = []

        data = self._get_data_for_generate()
        self.nai.set_param_dict(data)
        self._on_after_create_data_apply_gui()

        generate_thread = GenerateThread(self)
        generate_thread.generate_result.connect(self._on_result_generate)
        generate_thread.start()

        self.set_statusbar_text("GENEARTING")
        self.set_disable_button(True)
        self.generate_thread = generate_thread

    def _on_result_generate(self, error_code, result):
        self.generate_thread = None
        self.set_disable_button(False)
        self.set_statusbar_text("IDLE")
        self.refresh_anlas()

        if error_code == 0:
            self.image_result.set_custom_pixmap(result)

            if self.dict_img_batch_target["img2img_foldersrc"]:
                self.proceed_image_batch("img2img")
            if self.dict_img_batch_target["vibe_foldersrc"]:
                self.proceed_image_batch("vibe")
        else:
            QMessageBox.information(
                self, '경고', "이미지를 생성하는데 문제가 있습니다.\n\n" + str(result))

    def on_click_generate_sett(self):
        path_list, _ = QFileDialog().getOpenFileNames(self,
                                                      caption="불러올 세팅 파일들을 선택해주세요",
                                                      filter="Txt File (*.txt)")
        if path_list:
            if len(path_list) < 2:
                QMessageBox.information(
                    self, '경고', "두개 이상 선택해주세요.")
                return

            for path in path_list:
                if not path.endswith(".txt") or not os.path.isfile(path):
                    QMessageBox.information(
                        self, '경고', ".txt로 된 세팅 파일만 선택해주세요.")
                    return

            self.on_click_generate_auto(path_list)

    def proceed_settings_batch(self):
        self.index_settings_batch_target += 1

        while len(self.list_settings_batch_target) <= self.index_settings_batch_target:
            self.index_settings_batch_target -= len(
                self.list_settings_batch_target)

        path = self.list_settings_batch_target[self.index_settings_batch_target]
        is_success = self._load_settings(path)

        return is_success

    def on_click_generate_auto(self, setting_batch_target=[]):
        if not self.autogenerate_thread:
            d = GenerateDialog(self)
            if d.exec_() == QDialog.Accepted:
                self.list_settings_batch_target = setting_batch_target
                if setting_batch_target:
                    self.index_settings_batch_target = -1
                    is_success = self.proceed_settings_batch()
                    if not is_success:
                        QMessageBox.information(
                            self, '경고', "세팅을 불러오는데 실패했습니다.")
                        return

                agt = AutoGenerateThread(
                    self, d.count, d.delay, d.ignore_error)
                agt.on_data_created.connect(
                    self._on_after_create_data_apply_gui)
                agt.on_error.connect(self._on_error_autogenerate)
                agt.on_end.connect(self._on_end_autogenerate)
                agt.on_statusbar_change.connect(self.set_statusbar_text)
                agt.on_success.connect(self._on_success_autogenerate)
                agt.start()

                self.set_autogenerate_mode(True)
                self.autogenerate_thread = agt
        else:
            self._on_end_autogenerate()

    def _on_error_autogenerate(self, error_code, result):
        QMessageBox.information(
            self, '경고', "이미지를 생성하는데 문제가 있습니다.\n\n" + str(result))
        self._on_end_autogenerate()

    def _on_end_autogenerate(self):
        self.autogenerate_thread.stop()
        self.autogenerate_thread = None
        self.set_autogenerate_mode(False)
        self.set_statusbar_text("IDLE")
        self.refresh_anlas()

    def _on_success_autogenerate(self, result_str):
        self._on_refresh_anlas(self.nai.get_anlas() or -1)

        self.image_result.set_custom_pixmap(result_str)

        if self.dict_img_batch_target["img2img_foldersrc"]:
            self.proceed_image_batch("img2img")
        if self.dict_img_batch_target["vibe_foldersrc"]:
            self.proceed_image_batch("vibe")
        if self.list_settings_batch_target:
            self.proceed_settings_batch()

    def set_autogenerate_mode(self, is_autogenrate):
        self.button_generate_once.setDisabled(is_autogenrate)
        self.button_generate_sett.setDisabled(is_autogenrate)

        stylesheet = """
            color:black;
            background-color: """ + COLOR.BUTTON_AUTOGENERATE + """;
        """ if is_autogenrate else ""
        self.button_generate_auto.setStyleSheet(stylesheet)
        self.button_generate_auto.setText(
            "생성 중지" if is_autogenrate else "연속 생성")
        self.button_generate_auto.setDisabled(False)

    def apply_wildcards(self, prompt):
        self.check_folders()

        try:
            return self.wcapplier.apply_wildcards(prompt)
        except Exception as e:
            print(e)

        return prompt

    def on_click_open_folder(self, target_pathcode):
        path = self.settings.value(
            target_pathcode, DEFAULT_PATH[target_pathcode])
        path = os.path.abspath(path)
        create_folder_if_not_exists(path)
        os.startfile(path)

    def on_click_save_settings(self):
        path = self.settings.value(
            "path_settings", DEFAULT_PATH["path_settings"])
        path, _ = QFileDialog.getSaveFileName(
            self, "세팅 파일을 저장할 곳을 선택해주세요", path, "Txt File (*.txt)")
        if path:
            try:
                json_str = json.dumps(self.get_data(True))
                with open(path, "w", encoding="utf8") as f:
                    f.write(json_str)
            except Exception as e:
                print(e)
                QMessageBox.information(
                    self, '경고', "세팅 저장에 실패했습니다.\n\n" + str(e))

    def on_click_load_settings(self):
        path = self.settings.value(
            "path_settings", DEFAULT_PATH["path_settings"])

        select_dialog = QFileDialog()
        select_dialog.setFileMode(QFileDialog.ExistingFile)
        path, _ = select_dialog.getOpenFileName(
            self, "불러올 세팅 파일을 선택해주세요", path, "Txt File (*.txt)")
        if path:
            is_success = self._load_settings(path)

            if not is_success:
                QMessageBox.information(
                    self, '경고', "세팅을 불러오는데 실패했습니다.\n\n" + str(e))

    def _load_settings(self, path):
        try:
            with open(path, "r", encoding="utf8") as f:
                json_str = f.read()
            json_obj = json.loads(json_str)

            self.set_data(json_obj)

            return True
        except Exception as e:
            print(e)

        return False

    def show_prompt_dialog(self, title, prompt, nprompt):
        QMessageBox.about(self, title,
                          "프롬프트:\n" +
                          prompt +
                          "\n\n" +
                          "네거티브 프롬프트:\n" +
                          nprompt)

    def on_random_resolution_checked(self, is_checked):
        if is_checked == 2:
            fl = self.get_now_resolution_familly_list()
            if not fl:
                QMessageBox.information(
                    self, '이미지 크기 랜덤', "랜덤이 지원되지 않는 형식입니다.\n")
            else:
                s = ""
                for f in fl:
                    s += f + "\n"
                QMessageBox.information(
                    self, '이미지 크기 랜덤', "다음 크기 중 하나가 랜덤으로 선택됩니다.\n\n" + s)

        self.settings.setValue("image_random_checkbox", is_checked == 2)

    def get_now_resolution_familly_list(self):
        family_mask = RESOLUTION_FAMILIY_MASK[self.combo_resolution.currentIndex(
        )]

        if family_mask == -1:
            return []

        return RESOLUTION_FAMILIY[family_mask]

    def change_path(self, code, src):
        path = os.path.abspath(src)

        self.settings.setValue(code, path)

        create_folder_if_not_exists(path)

        if code == "path_wildcards":
            self.init_wc()
        elif code == "path_models":
            self.init_tagger()

    def on_click_getter(self):
        MiniUtilDialog(self, "getter").show()

    def on_click_tagger(self):
        MiniUtilDialog(self, "tagger").show()

    def on_click_expand(self):
        if self.is_expand:
            self.is_expand = False
            self.button_expand.setText("<<")

            self.settings.setValue(
                "splitterSizes", self.main_splitter.saveState())
            self.main_splitter.setHandleWidth(0)
            self.main_splitter.widget(1).setMaximumSize(0, 0)
        else:
            self.is_expand = True
            self.button_expand.setText(">>")

            self.main_splitter.setHandleWidth(8)
            self.main_splitter.widget(1).setMaximumSize(16777215, 16777215)

            try:
                self.main_splitter.restoreState(
                    self.settings.value("splitterSizes"))
            except Exception as e:
                self.main_splitter.setSizes([16777215, 16777215])
            QTimer.singleShot(20, self.image_result.refresh_size)

    def install_model(self, model_name):
        loading_dialog = FileIODialog(
            "모델 다운 받는 중...\n이 작업은 오래 걸릴 수 있습니다.", lambda: str(self.dtagger.download_model(model_name)))
        if loading_dialog.exec_() == QDialog.Accepted:
            if loading_dialog.result == "True":
                self.option_dialog.on_model_downloaded(model_name)

    def get_image_info_bysrc(self, file_src):
        nai_dict, error_code = naiinfo_getter.get_naidict_from_file(file_src)

        self._get_image_info_byinfo(nai_dict, error_code, file_src)

    def get_image_info_bytxt(self, file_src):
        nai_dict, error_code = naiinfo_getter.get_naidict_from_txt(file_src)

        self._get_image_info_byinfo(nai_dict, error_code, None)

    def get_image_info_byimg(self, img):
        nai_dict, error_code = naiinfo_getter.get_naidict_from_img(img)

        self._get_image_info_byinfo(nai_dict, error_code, img)

    def _get_image_info_byinfo(self, nai_dict, error_code, img_obj):
        if error_code == 0:
            QMessageBox.information(self, '경고', "EXIF가 존재하지 않는 파일입니다.")
            self.set_statusbar_text("IDLE")
        elif error_code == 1 or error_code == 2:
            QMessageBox.information(
                self, '경고', "EXIF는 존재하나 NAI로부터 만들어진 것이 아닌 듯 합니다.")
            self.set_statusbar_text("IDLE")
        elif error_code == 3:
            new_dict = {
                "prompt": nai_dict["prompt"], "negative_prompt": nai_dict["negative_prompt"]}
            new_dict.update(nai_dict["option"])
            new_dict.update(nai_dict["etc"])

            self.set_data(new_dict)
            if img_obj:
                self.image_result.set_custom_pixmap(img_obj)
            self.set_statusbar_text("LOAD_COMPLETE")

    def show_login_dialog(self):
        LoginDialog(self)

    def show_option_dialog(self):
        self.option_dialog = OptionDialog(self)

        self.option_dialog.exec_()

    def show_about_dialog(self):
        QMessageBox.about(self, 'About', S.ABOUT)

    def set_disable_button(self, will_disable):
        self.button_generate_once.setDisabled(will_disable)
        self.button_generate_sett.setDisabled(will_disable)
        self.button_generate_auto.setDisabled(will_disable)

    def set_result_text(self, nai_dict):
        additional_dict = {}

        if 'image' in nai_dict and nai_dict['image']:
            additional_dict["image_src"] = self.i2i_settings_group.src or ""
        if 'reference_image' in nai_dict and nai_dict['reference_image']:
            additional_dict["reference_image_src"] = self.vibe_settings_group.src or ""

        if self.dict_img_batch_target["i2i_last_dst"]:
            additional_dict["image_tag"] = self.dict_img_batch_target["i2i_last_dst"]
        if self.dict_img_batch_target["vibe_last_dst"]:
            additional_dict["reference_image_tag"] = self.dict_img_batch_target["vibe_last_dst"]

        content = prettify_naidict(nai_dict, additional_dict)

        self.prompt_result.setText(content)

    def refresh_anlas(self):
        anlas_thread = AnlasThread(self)
        anlas_thread.anlas_result.connect(self._on_refresh_anlas)
        anlas_thread.start()

    def _on_refresh_anlas(self, anlas):
        if anlas == -1:
            anlas = "?"
        self.label_anlas.setText("Anlas: " + str(anlas))

    def on_login_result(self, error_code):
        if error_code == 0:
            self.set_statusbar_text("LOGINED")
            self.label_loginstate.set_logged_in(True)
            self.set_disable_button(False)
            self.refresh_anlas()
        else:
            self.nai = NAIGenerator()  # reset
            self.set_statusbar_text("BEFORE_LOGIN")
            self.label_loginstate.set_logged_in(False)
            self.set_disable_button(True)
            self.set_auto_login(False)

        self.trying_auto_login = False

    def set_auto_login(self, is_auto_login):
        self.settings.setValue("auto_login",
                               True if is_auto_login else False)
        self.settings.setValue("access_token",
                               self.nai.access_token if is_auto_login else None)
        self.settings.setValue("username",
                               self.nai.username if is_auto_login else None)
        self.settings.setValue("password",
                               self.nai.password if is_auto_login else None)

    def on_logout(self):
        self.set_statusbar_text("BEFORE_LOGIN")

        self.label_loginstate.set_logged_in(False)

        self.set_disable_button(True)

        self.set_auto_login(False)

    def show_file_dialog(self, mode):
        select_dialog = QFileDialog()
        select_dialog.setFileMode(QFileDialog.ExistingFile)
        target_type = '이미지, 텍스트 파일(*.txt *.png *.webp)' if mode == 'file' else '이미지 파일(*.jpg *.png *.webp)'
        fname = select_dialog.getOpenFileName(
            self, '불러올 파일을 선택해 주세요.', '', target_type)

        if fname[0]:
            fname = fname[0]

            if mode == "file":
                if fname.endswith(".png") or fname.endswith(".webp"):
                    self.get_image_info_bysrc(fname)
                elif fname.endswith(".txt"):
                    self.get_image_info_bytxt(fname)
                else:
                    QMessageBox.information(
                        self, '경고', "png, webp, txt 파일만 가능합니다.")
                    return
            else:
                if fname.endswith(".png") or fname.endswith(".webp") or fname.endswith(".jpg"):
                    self.set_image_as_param(mode, fname)
                elif os.path.isdir(fname):
                    self.set_imagefolder_as_param(mode, fname)
                else:
                    QMessageBox.information(
                        self, '경고', "불러오기는 폴더, jpg, png, webp만 가능합니다.")
                    return

    def show_openfolder_dialog(self, mode):
        select_dialog = QFileDialog()
        select_dialog.setFileMode(QFileDialog.Directory)
        select_dialog.setOption(QFileDialog.Option.ShowDirsOnly)
        fname = select_dialog.getExistingDirectory(
            self, mode + '모드로 열 폴더를 선택해주세요.', '')

        if fname:
            if os.path.isdir(fname):
                self.set_imagefolder_as_param(mode, fname)
            else:
                QMessageBox.information(
                    self, '경고', "폴더만 선택 가능합니다.")

    def _set_image_gui(self, mode, src):
        if mode == "img2img":
            self.i2i_settings_group.set_image(src)
            self.image_options_layout.setStretch(0, 1)
        if mode == "vibe":
            self.vibe_settings_group.set_image(src)
            self.image_options_layout.setStretch(1, 1)
        self.image_options_layout.setStretch(2, 0)

    def set_image_as_param(self, mode, src):
        self.dict_img_batch_target[mode + "_foldersrc"] = ""
        target_group = self.i2i_settings_group if mode == "img2img" else self.vibe_settings_group
        target_group.set_folder_mode(False)
        self._set_image_gui(mode, src)

    def set_imagefolder_as_param(self, mode, foldersrc):
        if get_imgcount_from_foldersrc(foldersrc) == 0:
            QMessageBox.information(
                self, '경고', "이미지 파일이 없는 폴더입니다")
            return

        target_group = self.i2i_settings_group if mode == "img2img" else self.vibe_settings_group
        target_group.set_folder_mode(True)

        self.dict_img_batch_target[mode + "_foldersrc"] = foldersrc
        self.dict_img_batch_target[mode + "_index"] = -1

        self.proceed_image_batch(mode)

    def proceed_image_batch(self, mode):
        self.dict_img_batch_target[mode + "_index"] += 1
        target_group = self.i2i_settings_group if mode == "img2img" else self.vibe_settings_group

        src, is_reset = pick_imgsrc_from_foldersrc(
            foldersrc=self.dict_img_batch_target[mode + "_foldersrc"],
            index=self.dict_img_batch_target[mode + "_index"],
            sort_order=target_group.get_folder_sort_mode()
        )

        if is_reset:
            seed = random.randint(0, 9999999999)
            self.dict_ui_settings["seed"].setText(str(seed))

        self._set_image_gui(mode, src)

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

    # warning! Don't use this function in thread if with_dialog==True
    def predict_tag_from(self, filemode, target, with_dialog):
        result = ""

        target_model_name = self.settings.value("selected_tagger_model", '')
        if not target_model_name:
            QMessageBox.information(
                self, '경고', "먼저 옵션에서 태깅 모델을 다운/선택 해주세요.")
            return ""
        else:
            self.dtagger.options["model_name"] = target_model_name

        if filemode == "src":
            target = Image.open(target)

        if with_dialog:
            loading_dialog = FileIODialog(
                "태그하는 중...", lambda: self.dtagger.tag(target))
            if loading_dialog.exec_() == QDialog.Accepted:
                result = loading_dialog.result
                if not result:
                    list_installed_model = self.dtagger.get_installed_models()
                    if not (target_model_name in list_installed_model):
                        self.settings.setValue("selected_tagger_model", '')
        else:
            try:
                result = self.dtagger.tag(target)
            except Exception as e:
                print(e)

        return result

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u for u in event.mimeData().urls()]

        if len(files) != 1:
            QMessageBox.information(self, '경고', "파일을 하나만 옮겨주세요.")
            return

        furl = files[0]
        if furl.isLocalFile():
            fname = furl.toLocalFile()
            if fname.endswith(".png") or fname.endswith(".webp") or fname.endswith(".jpg"):
                if self.i2i_settings_group.geometry().contains(event.pos()):
                    self.set_image_as_param("img2img", fname)
                    return
                elif self.vibe_settings_group.geometry().contains(event.pos()):
                    self.set_image_as_param("vibe", fname)
                    return
                elif not fname.endswith(".jpg"):
                    self.get_image_info_bysrc(fname)
                    return
            elif fname.endswith(".txt"):
                self.get_image_info_bytxt(fname)
                return
            elif os.path.isdir(fname):
                if self.i2i_settings_group.geometry().contains(event.pos()):
                    self.set_imagefolder_as_param("img2img", fname)
                    return
                elif self.vibe_settings_group.geometry().contains(event.pos()):
                    self.set_imagefolder_as_param("vibe", fname)
                    return

            QMessageBox.information(
                self, '경고', "세팅 불러오기는 png, webp, txt 파일만 가능합니다.\ni2i와 vibe를 사용하고 싶다면 해당 칸에 떨어트려주세요.")
        else:
            self.set_statusbar_text("LOADING")
            try:
                url = furl.url()
                res = request.urlopen(url).read()
                img = Image.open(BytesIO(res))
                if img:
                    self.get_image_info_byimg(img)

            except Exception as e:
                print(e)
                self.set_statusbar_text("IDLE")
                QMessageBox.information(self, '경고', "이미지 파일 다운로드에 실패했습니다.")
                return

    def set_statusbar_text(self, status_key="", list_format=[]):
        statusbar = self.statusBar()

        if status_key:
            self.status_state = status_key
            self.status_list_format = list_format
        else:
            status_key = self.status_state
            list_format = self.status_list_format

        statusbar.showMessage(
            S.LIST_STATSUBAR_STATE[status_key].format(*list_format))

    def on_statusbar_message_changed(self, t):
        if not t:
            self.set_statusbar_text()

    def closeEvent(self, e):
        size = self.size()
        size.setWidth(
            int(size.width() / 2 if self.is_expand else size.width()))
        self.settings.setValue("size", size)
        self.settings.setValue("pos", self.pos())
        self.save_data()
        e.accept()

    def quit_app(self):
        time.sleep(0.1)
        self.close()
        self.app.closeAllWindows()
        QCoreApplication.exit(0)


class CompletionTagLoadThread(QThread):
    on_load_completiontag_sucess = pyqtSignal(list)

    def __init__(self, parent):
        super(CompletionTagLoadThread, self).__init__(parent)

    def run(self):
        try:
            with open(DEFAULT_TAGCOMPLETION_PATH, "r", encoding='utf8') as f:
                tag_list = f.readlines()
                if tag_list:
                    self.on_load_completiontag_sucess.emit(tag_list)
        except Exception:
            pass

    def stop(self):
        self.is_dead = True
        self.quit()


class AutoGenerateThread(QThread):
    on_data_created = pyqtSignal()
    on_error = pyqtSignal(int, str)
    on_success = pyqtSignal(str)
    on_end = pyqtSignal()
    on_statusbar_change = pyqtSignal(str, list)

    def __init__(self, parent, count, delay, ignore_error):
        super(AutoGenerateThread, self).__init__(parent)
        self.count = int(count or -1)
        self.delay = float(delay or 0.01)
        self.ignore_error = ignore_error
        self.is_dead = False

    def run(self):
        parent = self.parent()

        count = self.count
        delay = float(self.delay)

        temp_preserve_data_once = False
        while count != 0:
            # 1. Generate

            # generate data
            if not temp_preserve_data_once:
                data = parent._get_data_for_generate()
                parent.nai.set_param_dict(data)
                self.on_data_created.emit()
            temp_preserve_data_once = False

            # set status bar
            if count <= -1:
                self.on_statusbar_change.emit("AUTO_GENERATING_INF", [])
            else:
                self.on_statusbar_change.emit("AUTO_GENERATING_COUNT", [
                    self.count, self.count - count + 1])

            # before generate, if setting batch
            path = parent.settings.value(
                "path_results", DEFAULT_PATH["path_results"])
            create_folder_if_not_exists(path)
            if parent.list_settings_batch_target:
                setting_path = parent.list_settings_batch_target[parent.index_settings_batch_target]
                setting_name = get_filename_only(setting_path)
                path = path + "/" + setting_name
                create_folder_if_not_exists(path)

            # generate image
            error_code, result_str = _threadfunc_generate_image(
                self, path)
            if self.is_dead:
                return
            if error_code == 0:
                self.on_success.emit(result_str)
            else:
                if self.ignore_error:
                    for t in range(int(delay), 0, -1):
                        self.on_statusbar_change.emit("AUTO_ERROR_WAIT", [t])
                        time.sleep(1)
                        if self.is_dead:
                            return

                    temp_preserve_data_once = True
                    continue
                else:
                    self.on_error.emit(error_code, result_str)
                    return

            # 2. Wait
            count -= 1
            if count != 0:
                temp_delay = delay
                for x in range(int(delay)):
                    self.on_statusbar_change.emit("AUTO_WAIT", [temp_delay])
                    time.sleep(1)
                    if self.is_dead:
                        return
                    temp_delay -= 1

        self.on_end.emit()

    def stop(self):
        self.is_dead = True
        self.quit()


def _threadfunc_generate_image(thread_self, path):
    # 1 : get image
    parent = thread_self.parent()
    nai = parent.nai
    action = NAIAction.generate
    if nai.parameters["image"]:
        action = NAIAction.img2img
    if nai.parameters['mask']:
        action = NAIAction.infill
    data = nai.generate_image(action)
    if not data:
        return 1, "서버에서 정보를 가져오는데 실패했습니다."

    # 2 : open image
    try:
        zipped = zipfile.ZipFile(io.BytesIO(data))
        image_bytes = zipped.read(zipped.infolist()[0])
        img = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        return 2, str(e) + str(data)

    # 3 : save image
    create_folder_if_not_exists(path)
    dst = ""
    if parent.dict_img_batch_target["img2img_foldersrc"] and strtobool(thread_self.parent().settings.value("will_savename_i2i", False)):
        filename = get_filename_only(parent.i2i_settings_group.src)
        extension = ".png"
        dst = os.path.join(path, filename + extension)
        while os.path.isfile(dst):
            filename += "_"
            dst = os.path.join(path, filename + extension)
    else:
        timename = datetime.datetime.now().strftime(
            "%y%m%d_%H%M%S%f")[:-4]
        filename = timename
        if strtobool(thread_self.parent().settings.value("will_savename_prompt", True)):
            filename += "_" + nai.parameters["prompt"]
        dst = create_windows_filepath(path, filename, ".png")
        if not dst:
            dst = timename
    try:
        img.save(dst)
    except Exception as e:
        return 3, str(e)

    return 0, dst


class GenerateThread(QThread):
    generate_result = pyqtSignal(int, str)

    def __init__(self, parent):
        super(GenerateThread, self).__init__(parent)

    def run(self):
        path = self.parent().settings.value(
            "path_results", DEFAULT_PATH["path_results"])
        error_code, result_str = _threadfunc_generate_image(self, path)

        self.generate_result.emit(error_code, result_str)


class TokenValidateThread(QThread):
    validation_result = pyqtSignal(int)

    def __init__(self, parent):
        super(TokenValidateThread, self).__init__(parent)

    def run(self):
        is_login_success = self.parent().nai.check_logged_in()

        self.validation_result.emit(0 if is_login_success else 1)


class AnlasThread(QThread):
    anlas_result = pyqtSignal(int)

    def __init__(self, parent):
        super(AnlasThread, self).__init__(parent)

    def run(self):
        anlas = self.parent().nai.get_anlas() or -1

        self.anlas_result.emit(anlas)


if __name__ == '__main__':
    input_list = sys.argv
    app = QApplication(sys.argv)

    widget = NAIAutoGeneratorWindow(app)

    time.sleep(0.1)

    sys.exit(app.exec_())
