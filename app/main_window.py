import json
import sys
import os
import time
import random
from io import BytesIO
from PIL import Image
from urllib import request

from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QDialog
from PyQt5.QtCore import QSettings, QPoint, QSize, QCoreApplication, QTimer

from core.thread.generate_thread import GenerateThread
from core.thread.token_thread import TokenValidateThread
from core.thread.anlas_thread import AnlasThread
from core.thread.completiontagload_thread import CompletionTagLoadThread

from gui.layout.main_layout import init_main_layout
from gui.widget.status_bar import StatusBar
from gui.widget.menu_bar import MenuBar

from gui.dialog.generate_dialog import GenerateDialog
from gui.dialog.miniutil_dialog import MiniUtilDialog
from gui.dialog.fileio_dialog import FileIODialog
from gui.dialog.login_dialog import LoginDialog
from gui.dialog.option_dialog import OptionDialog
from gui.dialog.etc_dialog import show_setting_load_dialog, show_setting_save_dialog

from util.common_util import strtobool
from util.string_util import apply_wc_and_lessthan
from util.file_util import create_folder_if_not_exists
from util.ui_util import set_opacity

from core.worker.naiinfo_getter import get_naidict_from_file, get_naidict_from_txt, get_naidict_from_img
from core.worker.nai_generator import NAIGenerator, is_now_model_v4, TARGET_PARAMETERS, SAMPLER_ITEMS_V4, SAMPLER_ITEMS_V3
from core.worker.wildcard_applier import WildcardApplier
from core.worker.danbooru_tagger import DanbooruTagger

from config.strings import STRING
from config.consts import RESOLUTION_FAMILIY_MASK, RESOLUTION_FAMILIY, TITLE_NAME, TOP_NAME, APP_NAME
from config.paths import DEFAULT_PATH


class NAIAutoGeneratorWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.init_variable()
        self.init_window()
        self.init_statusbar()
        self.init_menubar()
        self.init_content()
        self.check_folders()
        self.show()

        self.init_nai()
        self.init_wc()
        self.init_tagger()
        self.init_completion()
        
        self.load_data()

    def init_variable(self):
        self.is_expand = False
        self.trying_auto_login = False
        self.autogenerate_thread = None
        self.list_settings_batch_target = []
        self.index_settings_batch_target = -1

    def init_window(self):
        self.setWindowTitle(TITLE_NAME)
        self.setAcceptDrops(True)

        self.settings = QSettings(TOP_NAME, APP_NAME)
        self.move(self.settings.value("pos", QPoint(500, 200)))
        self.resize(self.settings.value("size", QSize(1179, 1044)))
        self.settings.setValue("splitterSizes", None)
        font_size = self.settings.value("nag_font_size", 18)
        self.app.setStyleSheet("QWidget{font-size:" + str(font_size) + "px}")

    def init_statusbar(self):
        self.statusbar = StatusBar(self.statusBar())
        self.statusbar.set_statusbar_text("BEFORE_LOGIN")

    def init_menubar(self):
        self.menubar = MenuBar(self)

    def init_content(self):
        init_main_layout(self)

    def init_nai(self):
        self.nai = NAIGenerator()

        if self.settings.value("auto_login", False):
            access_token = self.settings.value("access_token", "")
            username = self.settings.value("username", "")
            password = self.settings.value("password", "")
            if not access_token or not username or not password:
                return

            self.statusbar.set_statusbar_text("LOGGINGIN")
            self.nai.access_token = access_token
            self.nai.username = username
            self.nai.password = password

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
            CompletionTagLoadThread(self).start()

    def save_data(self):
        data_dict = self.get_data_from_savetarget_ui()

        data_dict["seed_fix_checkbox"] = self.dict_ui_settings["seed_fix_checkbox"].isChecked()

        for k, v in data_dict.items():
            self.settings.setValue(k, v)

    def set_data(self, data_dict):
        dict_ui = self.dict_ui_settings

        list_ui_using_setcurrenttext = ["model", "sampler"]
        for key in list_ui_using_setcurrenttext:
            if key in data_dict:
                dict_ui[key].setCurrentText(str(data_dict[key]))
            else:
                print("[set_data] 없는 키가 있습니다. 키 : ",key)

        list_ui_using_settext = ["prompt", "negative_prompt", "width", "height",
                                 "steps", "seed", "scale", "cfg_rescale"]
        for key in list_ui_using_settext:
            if key in data_dict:
                dict_ui[key].setText(str(data_dict[key]))
            else:
                print("[set_data] 없는 키가 있습니다. 키 : ",key)

        list_ui_using_setchecked = ["sm", "sm_dyn"]
        for key in list_ui_using_setchecked:
            if key in data_dict:
                dict_ui[key].setChecked(strtobool(data_dict[key]))
            else:
                print("[set_data] 없는 키가 있습니다. 키 : ",key)

    def load_data(self):
        data_dict = {}
        for key in TARGET_PARAMETERS:
            data_dict[key] = str(self.settings.value(key, TARGET_PARAMETERS[key]))

        self.set_data(data_dict)

    def check_folders(self):
        for key, default_path in DEFAULT_PATH.items():
            path = self.settings.value(key, os.path.abspath(default_path))
            create_folder_if_not_exists(path)

    # 저장 대상인 항목만 이곳에 담는다.
    def get_data_from_savetarget_ui(self, do_convert_type=False):
        data = {
            "model": self.dict_ui_settings["model"].currentText(),
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
            "variety_plus": str(self.dict_ui_settings["variety_plus"].isChecked()),
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
            data["variety_plus"] = strtobool(data["variety_plus"])

        return data

    # Warning! Don't interact with pyqt gui in this function
    # ui에서 데이터를 가져온 다음에 생성전 수정을 가한다.
    def _get_data_for_generate(self):
        data = self.get_data_from_savetarget_ui(True)
        self.save_data()

        # data precheck
        self.check_folders()
        data["prompt"] = apply_wc_and_lessthan(self.wcapplier, data["prompt"])
        data["negative_prompt"] = apply_wc_and_lessthan(
            self.wcapplier, data["negative_prompt"])

        # seed pick
        if not self.dict_ui_settings["seed_fix_checkbox"].isChecked() or data["seed"] == -1:
            data["seed"] = random.randint(0, 9999999999)

        # resolution pick
        if strtobool(self.checkbox_random_resolution.isChecked()):
            fl = self.get_now_resolution_familly_list()
            if fl:
                text = fl[random.randrange(0, len(fl))]

                res_text = text.split("(")[1].split(")")[0]
                width, height = res_text.split("x")
                data["width"], data["height"] = int(width), int(height)

        # image option check
        i2i_param = self.i2i_settings_group.get_nai_param()
        vibe_param = self.vibe_settings_group.get_nai_param()
        if i2i_param:
            data["image"] = i2i_param[0]
            data["strength"] = float(i2i_param[1])
            data["noise"] = float(i2i_param[2])

            # mask 체크
            # if self.i2i_settings_group.mask:
            #     data['mask'] = convert_qimage_to_imagedata(
            #         self.i2i_settings_group.mask)
        if vibe_param:
            image_tuple, info_tuple, strength_tuple = zip(*vibe_param)
            data["reference_image_multiple"]= list(image_tuple)
            data["reference_information_extracted_multiple"]= [float(x) for x in info_tuple]
            data["reference_strength_multiple"]= [float(x) for x in strength_tuple]
        
        return data
        
    def on_model_changed(self, text):
        isV4 = is_now_model_v4(text)

        # sampler
        sampler_ui = self.dict_ui_settings["sampler"]
        prevText = sampler_ui.currentText()

        sampler_ui.clear()
        targetItems = SAMPLER_ITEMS_V4 if isV4 else SAMPLER_ITEMS_V3
        sampler_ui.addItems(targetItems)

        if prevText in targetItems:
            sampler_ui.setCurrentText(prevText)
        
        # vibe off
        self.vibe_settings_group.setVisible(not isV4)

        # settings off
        opacity = 0 if isV4 else 1
        set_opacity(self.dict_ui_settings["sm"], opacity)
        set_opacity(self.dict_ui_settings["sm_dyn"], opacity)
        set_opacity(self.dict_ui_settings["variety_plus"], opacity)

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
        self.prompt_layout.set_result_text(data)

    def on_click_generate_once(self):
        self.list_settings_batch_target = []

        data = self._get_data_for_generate()
        self.nai.set_param_dict(data)
        self._on_after_create_data_apply_gui()

        generate_thread = GenerateThread(self, False)
        generate_thread.generate_result.connect(self._on_result_generate)
        generate_thread.start()

        self.statusbar.set_statusbar_text("GENEARTING")
        self.generate_buttons_layout.set_disable_button(True)
        self.generate_thread = generate_thread

    def _on_result_generate(self, error_code, result):
        self.generate_thread = None
        self.generate_buttons_layout.set_disable_button(False)
        self.statusbar.set_statusbar_text("IDLE")
        self.refresh_anlas()

        if error_code == 0:
            self.image_result.set_custom_pixmap(result)
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

                agt = GenerateThread(
                    self, True, d.count, d.delay, d.ignore_error)
                agt.on_data_created.connect(
                    self._on_after_create_data_apply_gui)
                agt.on_error.connect(self._on_error_autogenerate)
                agt.on_end.connect(self._on_end_autogenerate)
                agt.on_statusbar_change.connect(
                    self.statusbar.set_statusbar_text)
                agt.on_success.connect(self._on_success_autogenerate)
                agt.start()

                self.generate_buttons_layout.set_autogenerate_mode(True)
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
        self.generate_buttons_layout.set_autogenerate_mode(False)
        self.statusbar.set_statusbar_text("IDLE")
        self.refresh_anlas()

    def _on_success_autogenerate(self, result_str):
        self._on_refresh_anlas(self.nai.get_anlas() or -1)

        self.image_result.set_custom_pixmap(result_str)

        if self.list_settings_batch_target:
            self.proceed_settings_batch()

    def on_click_open_folder(self, target_pathcode):
        path = self.settings.value(
            target_pathcode, DEFAULT_PATH[target_pathcode])
        path = os.path.abspath(path)
        create_folder_if_not_exists(path)
        os.startfile(path)

    def on_click_save_settings(self):
        show_setting_save_dialog(self)

    def on_click_load_settings(self):
        show_setting_load_dialog(self)

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

    def on_change_path(self, code, src):
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
        nai_dict, error_code = get_naidict_from_file(file_src)

        self._get_image_info_byinfo(nai_dict, error_code, file_src)

    def get_image_info_bytxt(self, file_src):
        nai_dict, error_code = get_naidict_from_txt(file_src)

        self._get_image_info_byinfo(nai_dict, error_code, None)

    def get_image_info_byimg(self, img):
        nai_dict, error_code = get_naidict_from_img(img)

        self._get_image_info_byinfo(nai_dict, error_code, img)

    def _get_image_info_byinfo(self, nai_dict, error_code, img_obj):
        if error_code == 1:
            QMessageBox.information(self, '경고', "EXIF가 존재하지 않는 파일입니다.")
            self.statusbar.set_statusbar_text("IDLE")
        elif error_code == 2 or error_code == 3:
            QMessageBox.information(
                self, '경고', "EXIF는 존재하나 NAI로부터 만들어진 것이 아닌 듯 합니다.")
            self.statusbar.set_statusbar_text("IDLE")
        elif error_code == 0:
            new_dict = {
                "prompt": nai_dict["prompt"], "negative_prompt": nai_dict["negative_prompt"]}
            new_dict.update(nai_dict["option"])
            new_dict.update(nai_dict["etc"])

            self.set_data(new_dict)
            if img_obj:
                self.image_result.set_custom_pixmap(img_obj)
            self.statusbar.set_statusbar_text("LOAD_COMPLETE")

    def show_login_dialog(self):
        self.login_dialog = LoginDialog(self)
        self.login_dialog.exec_()

    def show_option_dialog(self):
        self.option_dialog = OptionDialog(self)
        self.option_dialog.exec_()

    def show_about_dialog(self):
        QMessageBox.about(self, 'About', STRING.ABOUT)

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
            self.statusbar.set_statusbar_text("LOGINED")
            self.label_loginstate.set_logged_in(True)
            self.generate_buttons_layout.set_disable_button(False)
            self.refresh_anlas()
        else:
            self.nai = NAIGenerator()  # reset
            self.statusbar.set_statusbar_text("BEFORE_LOGIN")
            self.label_loginstate.set_logged_in(False)
            self.generate_buttons_layout.set_disable_button(True)
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
        self.statusbar.set_statusbar_text("BEFORE_LOGIN")

        self.label_loginstate.set_logged_in(False)

        self.generate_buttons_layout.set_disable_button(True)

        self.set_auto_login(False)

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
                if not fname.endswith(".jpg"):
                    self.get_image_info_bysrc(fname)
                    return
            elif fname.endswith(".txt"):
                self.get_image_info_bytxt(fname)
                return

            QMessageBox.information(
                self, '경고', "세팅 불러오기는 png, webp, txt 파일만 가능합니다.")
        else:
            self.statusbar.set_statusbar_text("LOADING")
            try:
                url = furl.url()
                res = request.urlopen(url).read()
                img = Image.open(BytesIO(res))
                if img:
                    self.get_image_info_byimg(img)

            except Exception as e:                             # 바이브 이미지
                print(e)
                self.statusbar.set_statusbar_text("IDLE")
                QMessageBox.information(self, '경고', "이미지 파일 다운로드에 실패했습니다.")
                return

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


if __name__ == '__main__':
    input_list = sys.argv
    app = QApplication(sys.argv)

    widget = NAIAutoGeneratorWindow(app)

    time.sleep(0.1)

    sys.exit(app.exec_())
