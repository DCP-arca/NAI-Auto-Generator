import json
import sys
import os
import shutil
import io
import zipfile
import time
import datetime
import random
from io import BytesIO
from PIL import Image
from urllib import request


from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog, QMessageBox, QDialog
from PyQt5.QtCore import QSettings, QPoint, QSize, QCoreApplication, QThread, pyqtSignal, QTimer
from gui_init import init_main_widget
from gui_dialog import LoginDialog, OptionDialog, GenerateDialog, TextSaveDialog, TextLoadDialog

from consts import COLOR, S, DEFAULT_PARAMS, DEFAULT_PATH, DEFAULT_SETTING, RESOLUTION_FAMILIY_MASK, RESOLUTION_FAMILIY

import naiinfo_getter
from nai_generator import NAIGenerator
from wildcard_applier import WildcardApplier

TITLE_NAME = "NAI Auto Generator"
TOP_NAME = "dcp_arca"
APP_NAME = "nag_gui"

#############################################


def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def prettify_dict(d):
    return json.dumps(d, sort_keys=True, indent=4)


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


def pickedit_lessthan_str(s):
    edited_str = s
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

    return edited_str


def create_windows_filepath(base_path, filename, extension, max_length=260):
    # 파일 이름으로 사용할 수 없는 문자 제거
    cleaned_filename = filename.replace("\n", "")
    cleaned_filename = cleaned_filename.replace("\\", "")
    
    invalid_chars = r'<>:"/\|?*'
    cleaned_filename = ''.join(
        char for char in cleaned_filename if char not in invalid_chars)

    # 파일 이름의 최대 길이 제한 (확장자 길이 고려)
    max_filename_length = max_length - len(base_path) - len(extension) - 20
    cleaned_filename = cleaned_filename[:max_filename_length]

    # 경로, 파일 이름, 확장자 합치기
    filepath = os.path.join(base_path, cleaned_filename + extension)

    return filepath


class MyWidget(QMainWindow):

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
        self.show()

        self.init_nai()
        self.init_wc()

    def init_variable(self):
        self.is_expand = False
        self.trying_auto_login = False
        self.autogenerate_thread = None
        self.last_parameter = DEFAULT_SETTING

    def init_window(self):
        self.setWindowTitle(TITLE_NAME)
        self.settings = QSettings(TOP_NAME, APP_NAME)
        self.move(self.settings.value("pos", QPoint(500, 200)))
        self.resize(self.settings.value("size", QSize(1000, 1200)))
        self.settings.setValue("splitterSizes", None)
        self.setAcceptDrops(True)

    def init_statusbar(self):
        statusbar = self.statusBar()
        statusbar.messageChanged.connect(self.on_statusbar_message_changed)
        self.set_statusbar_text("BEFORE_LOGIN")

    def init_menubar(self):
        openAction = QAction('파일 열기(Open file)', self)
        openAction.setShortcut('Ctrl+O')
        openAction.triggered.connect(self.show_file_dialog)

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

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        filemenu = menubar.addMenu('&File')
        filemenu.addAction(openAction)
        filemenu.addAction(loginAction)
        filemenu.addAction(optionAction)
        filemenu.addAction(exitAction)
        filemenu = menubar.addMenu('&Etc')
        filemenu.addAction(aboutAction)

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
            "path_wildcards", DEFAULT_PATH["path_wildcards"]))

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
                                 "steps", "seed", "scale", "uncond_scale", "cfg_rescale"]
        for key in list_ui_using_settext:
            dict_ui[key].setText(str(data_dict[key]))

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
            "uncond_scale": str(float(self.dict_ui_settings["uncond_scale"].text()) / 100)
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

        return data

    def _get_data_for_generate(self):
        data = self.get_data(True)
        self.save_data()

        # data precheck
        data["prompt"], data["negative_prompt"] = self._preedit_prompt(
            data["prompt"], data["negative_prompt"])

        # seed pick
        if not self.dict_ui_settings["seed_fix_checkbox"].isChecked() or data["seed"] == -1:
            data["seed"] = random.randint(0, 9999999999)
            self.dict_ui_settings["seed"].setText(str(data["seed"]))

        # wh pick
        if strtobool(self.checkbox_random_resolution.isChecked()):
            fl = self.get_now_resolution_familly_list()
            if fl:
                text = fl[random.randrange(0, len(fl))]

                self.combo_resolution.setCurrentText(text)

                res_text = text.split("(")[1].split(")")[0]
                width, height = res_text.split("x")
                data["width"], data["height"] = int(width), int(height)

        return data

    def _preedit_prompt(self, prompt, nprompt):
        # lessthan pick
        prompt = pickedit_lessthan_str(prompt)
        nprompt = pickedit_lessthan_str(nprompt)
        # wildcards pick
        prompt = self.apply_wildcards(prompt)
        nprompt = self.apply_wildcards(nprompt)

        return prompt, nprompt

    def on_click_generate_once(self):
        self.nai.set_param_dict(self._get_data_for_generate())

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
        else:
            QMessageBox.information(
                self, '경고', "이미지를 생성하는데 문제가 있습니다.\n\n" + str(result))

    def on_click_generate_auto(self):
        if not self.autogenerate_thread:
            d = GenerateDialog(self)
            if d.exec_() == QDialog.Accepted:
                autogenerate_thread = AutoGenerateThread(
                    self, d.count, d.delay, d.ignore_error)
                autogenerate_thread.autogenerate_error.connect(
                    self._on_error_autogenerate)
                autogenerate_thread.autogenerate_end.connect(
                    self._on_end_autogenerate)
                autogenerate_thread.start()

                self.set_autogenerate_mode(True)
                self.autogenerate_thread = autogenerate_thread
        else:
            self.autogenerate_thread.stop()
            self._on_end_autogenerate()

    def _on_error_autogenerate(self, error_code, result):
        QMessageBox.information(
            self, '경고', "이미지를 생성하는데 문제가 있습니다.\n\n" + str(result))
        self._on_end_autogenerate()

    def _on_end_autogenerate(self):
        self.autogenerate_thread = None
        self.set_autogenerate_mode(False)
        self.set_statusbar_text("IDLE")
        self.refresh_anlas()

    def set_autogenerate_mode(self, is_autogenrate):
        self.button_generate_once.setDisabled(is_autogenrate)

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
        os.startfile(path)

    def on_click_save_settings(self):
        path = self.settings.value(
            "path_settings", DEFAULT_PATH["path_settings"])
        path = os.path.abspath(path)
        d = TextSaveDialog(self, path, "세팅 파일 저장")
        if d.exec_() == QDialog.Accepted:
            path = os.path.join(path, d.filename + ".txt")

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
        path = os.path.abspath(path)
        d = TextLoadDialog(self, path, '세팅 파일 불러오기')
        if d.exec_() == QDialog.Accepted:
            try:
                with open(d.selected_filepath, "r", encoding="utf8") as f:
                    json_str = f.read()
                json_obj = json.loads(json_str)

                self.set_data(json_obj)
            except Exception as e:
                print(e)
                QMessageBox.information(
                    self, '경고', "세팅을 불러오는데 실패했습니다.\n\n" + str(e))

    def on_click_prompt_button(self, key):
        if key[0] == "n":
            target_textedit = self.dict_ui_settings["negative_prompt"]
            target_path = "path_nprompts"
        else:
            target_textedit = self.dict_ui_settings["prompt"]
            target_path = "path_prompts"
        mode = key[-3:]

        path = self.settings.value(target_path, DEFAULT_PATH[target_path])
        path = os.path.abspath(path)

        if mode == "add" or mode == "set":
            str_title = '추가하기' if mode == "add" else "덮어쓰기"
            d = TextLoadDialog(self, path, str_title)
            if d.exec_() == QDialog.Accepted:
                try:
                    with open(d.selected_filepath, "r", encoding="utf8") as f:
                        txt = f.read()

                        if mode == "add":
                            target_textedit.textCursor(
                            ).insertText(txt)
                        else:
                            target_textedit.setText(txt)
                except Exception as e:
                    print(e)
                    str_warning = ('추가' if mode == "add" else '덮어쓰는') + \
                        " 중 문제가 발생했습니다."
                    QMessageBox.information(
                        self, '경고', str_warning + "\n\n" + str(e))
        elif mode == "sav":
            d = TextSaveDialog(self, path, "저장하기")
            if d.exec_() == QDialog.Accepted:
                path = os.path.join(path, d.filename + ".txt")

                try:
                    with open(path, "w", encoding="utf8") as f:
                        f.write(target_textedit.toPlainText())
                except Exception as e:
                    print(e)
                    QMessageBox.information(
                        self, '경고', "저장에 실패했습니다.\n\n" + str(e))

    def on_click_preview_wildcard(self):
        prompt = self.dict_ui_settings["prompt"].toPlainText()
        nprompt = self.dict_ui_settings["negative_prompt"].toPlainText()

        wc_prompt, wc_nprompt = self._preedit_prompt(prompt, nprompt)

        self.show_prompt_dialog("미리 뽑아 보기", wc_prompt, wc_nprompt)

    def show_prompt_dialog(self, title, prompt, nprompt):
        QMessageBox.about(self, title,
                          "프롬프트:\n" +
                          prompt +
                          "\n\n" +
                          "네거티브 프롬프트:\n" +
                          nprompt)

    def on_click_imageinfo(self):
        try:
            prompt = self.last_parameter["prompt"]
            nprompt = self.last_parameter["negative_prompt"]
            self.show_prompt_dialog("생성 이미지 프롬프트 보기", prompt, nprompt)
        except Exception as e:
            print(e)
            QMessageBox.information(
                self, '경고', "정보를 읽는데 실패했습니다.\n\n" + str(e))

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
            self.wcapplier = WildcardApplier(self.settings.value(
                "path_wildcards", DEFAULT_PATH["path_wildcards"]))

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
        OptionDialog(self)

    def show_about_dialog(self):
        QMessageBox.about(self, 'About', S.ABOUT)

    def set_disable_button(self, will_disable):
        self.button_generate_once.setDisabled(will_disable)
        self.button_generate_auto.setDisabled(will_disable)

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

    def show_file_dialog(self):
        select_dialog = QFileDialog()
        select_dialog.setFileMode(QFileDialog.ExistingFile)
        fname = select_dialog.getOpenFileName(
            self, 'Open image file or txt file to get nai data', '', 'Image File, Text File(*.txt *.png *.webp)')

        if fname[0]:
            fname = fname[0]
            if fname.endswith(".png") or fname.endswith(".webp"):
                self.get_image_info_bysrc(fname)
            elif fname.endswith(".txt"):
                self.get_image_info_bytxt(fname)
            else:
                QMessageBox.information(
                    self, '경고', "png, webp, txt 파일만 가능합니다.")
                return

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
            if fname.endswith(".png") or fname.endswith(".webp"):
                self.get_image_info_bysrc(fname)
            elif fname.endswith(".txt"):
                self.get_image_info_bytxt(fname)
            else:
                QMessageBox.information(
                    self, '경고', "png, webp, txt 파일만 가능합니다.")
                return
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


class AutoGenerateThread(QThread):
    autogenerate_error = pyqtSignal(int, str)
    autogenerate_end = pyqtSignal()

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
            temp_preserve_data_once = False

            # set status bar
            if count <= -1:
                parent.set_statusbar_text("AUTO_GENERATING_INF")
            else:
                parent.set_statusbar_text("AUTO_GENERATING_COUNT", [
                    self.count, self.count - count + 1])

            # generate image
            error_code, result_str = _threadfunc_generate_image(self)
            if self.is_dead:
                return
            if error_code == 0:
                # same as parent.refresh_anlas()
                parent._on_refresh_anlas(parent.nai.get_anlas() or -1)

                parent.image_result.set_custom_pixmap(result_str)

                parent.last_parameter = data
            else:
                if self.ignore_error:
                    for t in range(5, 0, -1):
                        parent.set_statusbar_text("AUTO_ERROR_WAIT", [t])
                        time.sleep(1)
                        if self.is_dead:
                            return

                    temp_preserve_data_once = True
                    continue
                else:
                    self.autogenerate_error.emit(error_code, result_str)
                    return

            # 2. Wait
            count -= 1
            if count != 0:
                temp_delay = delay
                for x in range(int(delay)):
                    parent.set_statusbar_text("AUTO_WAIT", [temp_delay])
                    time.sleep(1)
                    if self.is_dead:
                        return
                    temp_delay -= 1

        self.autogenerate_end.emit()

    def stop(self):
        self.is_dead = True
        self.quit()


def _threadfunc_generate_image(thread_self):
    # 1 : get image
    nai = thread_self.parent().nai
    data = nai.generate_image()
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
    path = thread_self.parent().settings.value(
        "path_results", DEFAULT_PATH["path_results"])
    create_folder_if_not_exists(path)
    filename = datetime.datetime.now().strftime(
        "%y%m%d_%H%M%S%f")[:-4]
    if strtobool(thread_self.parent().settings.value("will_savename_prompt", True)):
        filename += "_" + nai.parameters["prompt"]
    dst = create_windows_filepath(path, filename, ".png")
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
        error_code, result_str = _threadfunc_generate_image(self)

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
    widget = MyWidget(app)

    time.sleep(0.1)

    sys.exit(app.exec_())
