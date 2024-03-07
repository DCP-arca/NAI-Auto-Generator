import os
import sys
from PyQt5.QtWidgets import QApplication, QRadioButton, QTextEdit, QGroupBox, QWidget, QFrame, QFileDialog, QLabel, QLineEdit, QCheckBox, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QDialog, QMessageBox, QFileSystemModel, QListView, QSizePolicy
from PyQt5.QtGui import QImage, QPainter, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QEvent, QRectF, QSize, pyqtSignal, QTimer

from io import BytesIO
from PIL import Image
from urllib import request

from consts import DEFAULT_PATH, prettify_naidict

import naiinfo_getter

from danbooru_tagger import DEFAULT_MODEL, LIST_MODEL, DanbooruTagger


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


def create_empty(minimum_width=1, minimum_height=1, fixed_height=0):
    w = QWidget()
    w.setMinimumWidth(minimum_width)
    w.setMinimumHeight(minimum_height)
    w.setStyleSheet("background-color:#00000000")
    if fixed_height != 0:
        w.setFixedHeight(fixed_height)
    return w


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path).replace("\\", "/")


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


def get_key_from_dict(dictionary, value):
    return next((key for key, val in dictionary.items() if val == value), None)


class BackgroundFrame(QFrame):
    clicked = pyqtSignal()

    def __init__(self, parent, opacity):
        super(BackgroundFrame, self).__init__(parent)
        self.image = QImage()
        self.opacity = opacity

    def set_background_image_by_src(self, image_path):
        self.image.load(image_path)
        self.update()

    def set_background_image_by_img(self, image):
        self.image = pil2pixmap(image).toImage()
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
        painter.setOpacity(self.opacity)
        painter.drawImage(target_rect, scaled_image)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            self.update()
            return True
        return super(BackgroundFrame, self).eventFilter(obj, event)

    def mousePressEvent(self, ev):
        self.clicked.emit()


class LoginThread(QThread):
    login_result = pyqtSignal(int)

    def __init__(self, parent, nai, username, password):
        super(LoginThread, self).__init__(parent)
        self.nai = nai
        self.username = username
        self.password = password

    def run(self):
        if not self.username or not self.password:
            self.login_result.emit(1)
            return

        is_login_success = self.nai.try_login(
            self.username, self.password)

        self.login_result.emit(0 if is_login_success else 2)


class LoginDialog(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()
        self.check_already_login()
        super().exec_()

    def initUI(self):
        parent_pos = self.parent.pos()

        self.setWindowTitle('로그인')
        self.move(parent_pos.x() + 50, parent_pos.y() + 50)
        self.resize(400, 150)

        layout = QVBoxLayout()

        hbox_username = QHBoxLayout()
        username_label = QLabel('Username:')
        username_edit = QLineEdit(self)
        self.username_edit = username_edit
        hbox_username.addWidget(username_label)
        hbox_username.addWidget(username_edit)

        hbox_password = QHBoxLayout()
        password_label = QLabel('Password:')
        password_edit = QLineEdit(self)
        password_edit.setEchoMode(QLineEdit.Password)  # 비밀번호 입력시 마스킹 처리
        self.password_edit = password_edit
        hbox_password.addWidget(password_label)
        hbox_password.addWidget(password_edit)

        vbox_button = QGridLayout()
        autologin_check = QCheckBox("자동 로그인")
        self.autologin_check = autologin_check
        autologin_check.setChecked(True)
        login_button = QPushButton('Login')
        login_button.clicked.connect(self.try_login)
        self.login_button = login_button
        logout_button = QPushButton('Logout')
        logout_button.setDisabled(True)
        logout_button.clicked.connect(self.logout)
        self.logout_button = logout_button
        vbox_button.addWidget(autologin_check, 0, 0)
        vbox_button.addWidget(login_button, 0, 1)
        vbox_button.addWidget(logout_button, 1, 1)

        instruct_label = QLabel('Novel AI 계정을 입력해주세요.')
        instruct_label.setAlignment(Qt.AlignRight)
        self.instruct_label = instruct_label

        layout.addLayout(hbox_username)
        layout.addLayout(hbox_password)
        layout.addLayout(vbox_button)
        layout.addWidget(instruct_label)

        self.setLayout(layout)

    def set_login_result_ui(self, is_login_success):
        self.username_edit.setDisabled(is_login_success)
        self.password_edit.setDisabled(is_login_success)

        self.login_button.setDisabled(is_login_success)
        self.logout_button.setDisabled(not is_login_success)

        self.instruct_label.setText(
            "로그인 성공! 창을 닫아도 됩니다." if is_login_success else 'Novel AI 계정을 입력해주세요.')

    def check_already_login(self):
        if self.parent.trying_auto_login:
            self.username_edit.setDisabled(True)
            self.password_edit.setDisabled(True)

            self.login_button.setDisabled(True)
            self.logout_button.setDisabled(True)

            self.instruct_label.setText("자동로그인 시도중입니다. 창을 꺼주세요.")
        else:  # 오토 로그인 중이 아니라면 자동 로그인
            nai = self.parent.nai
            if nai.access_token:  # 자동로그인 성공
                self.username_edit.setText(nai.username)
                self.password_edit.setText(nai.password)

                self.set_login_result_ui(True)
            else:  # 자동로그인 실패
                self.set_login_result_ui(False)

    def try_login(self):
        username = self.username_edit.text()
        password = self.password_edit.text()

        self.instruct_label.setText("로그인 시도 중... 창을 닫지 마세요.")
        self.parent.set_statusbar_text("LOGGINGIN")
        self.login_button.setDisabled(True)
        self.logout_button.setDisabled(True)

        login_thread = LoginThread(self, self.parent.nai, username, password)
        login_thread.login_result.connect(self.on_login_result)
        login_thread.login_result.connect(self.parent.on_login_result)
        login_thread.start()
        self.login_thread = login_thread

    def logout(self):
        self.parent.on_logout()
        self.set_login_result_ui(False)

    def on_login_result(self, error_code):
        if error_code == 0:
            self.set_login_result_ui(True)

            if self.autologin_check.isChecked():
                self.parent.set_auto_login(True)
        elif error_code == 1:
            self.set_login_result_ui(False)
            self.instruct_label.setText("잘못된 아이디 또는 비번입니다.")
        elif error_code == 2:
            self.set_login_result_ui(False)
            self.instruct_label.setText("로그인에 실패했습니다.")


class GenerateDialog(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        parent_pos = self.parent.pos()

        self.setWindowTitle('자동 생성')
        self.move(parent_pos.x() + 50, parent_pos.y() + 50)
        self.setFixedSize(400, 200)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout_count = QHBoxLayout()
        layout.addLayout(layout_count)

        label_count = QLabel("생성 횟수(빈칸시 무한) : ", self)
        layout_count.addWidget(label_count, 1)
        lineedit_count = QLineEdit("")
        lineedit_count.setMaximumWidth(40)
        self.lineedit_count = lineedit_count
        layout_count.addWidget(lineedit_count, 1)

        layout_delay = QHBoxLayout()
        layout.addLayout(layout_delay)

        label_delay = QLabel("지연 시간(매 생성시, 에러시 대기시간) : ", self)
        layout_delay.addWidget(label_delay, 1)
        lineedit_delay = QLineEdit("3")
        lineedit_delay.setMaximumWidth(40)
        self.lineedit_delay = lineedit_delay
        layout_delay.addWidget(lineedit_delay, 1)

        checkbox_ignoreerror = QCheckBox("에러 발생 시에도 계속 하기")
        checkbox_ignoreerror.setChecked(True)
        self.checkbox_ignoreerror = checkbox_ignoreerror
        layout.addWidget(checkbox_ignoreerror, 1)

        layout_buttons = QHBoxLayout()
        layout.addLayout(layout_buttons)

        start_button = QPushButton("시작")
        start_button.clicked.connect(self.on_start_button_clicked)
        layout_buttons.addWidget(start_button)
        self.start_button = start_button

        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.on_close_button_clicked)
        layout_buttons.addWidget(close_button)
        self.close_button = close_button

    def on_start_button_clicked(self):
        self.count = self.lineedit_count.text()
        self.delay = self.lineedit_delay.text()
        self.ignore_error = self.checkbox_ignoreerror.isChecked()
        self.accept()

    def on_close_button_clicked(self):
        self.reject()


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
        for index, model_name in enumerate(LIST_MODEL):
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

        checkbox_savepname = QCheckBox("파일 생성시 이름에 프롬프트 넣기")
        checkbox_savepname.setChecked(strtobool(
            parent.settings.value("will_savename_prompt", True)))
        self.checkbox_savepname = checkbox_savepname
        layout.addWidget(checkbox_savepname)

        button_close = QPushButton("닫기")
        button_close.clicked.connect(self.on_click_close_button)
        self.button_close = button_close

        layout.addStretch(2)

        qhl_close = QHBoxLayout()
        qhl_close.addStretch(4)
        qhl_close.addWidget(self.button_close, 2)
        layout.addLayout(qhl_close)

        self.setLayout(layout)

    def on_click_select_button(self, code):
        select_dialog = QFileDialog()
        save_loc = select_dialog.getExistingDirectory(
            self, '저장할 위치를 골라주세요.')

        if save_loc:
            self.parent().change_path(code, save_loc)

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
        self.parent().change_path(code, DEFAULT_PATH[code])

        self.refresh_label(code)

    def on_model_downloaded(self, model_name):
        self.dict_tagger_model_radio[model_name].setEnabled(True)
        self.dict_tagger_model_button[model_name].setEnabled(False)

    def refresh_label(self, code):
        path = self.parent().settings.value(code, DEFAULT_PATH[code])
        self.dict_label_loc[code].setText(path)

    def on_click_close_button(self):
        self.parent().settings.setValue(
            "will_savename_prompt", self.checkbox_savepname.isChecked())
        self.reject()


class LoadingWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, func):
        super().__init__()
        self.func = func

    def run(self):
        try:
            self.finished.emit(self.func())
        except Exception as e:
            print(e)
            self.finished.emit("")


class FileIODialog(QDialog):
    def __init__(self, text, func):
        super().__init__()
        self.text = text
        self.func = func
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("작업 중")

        layout = QVBoxLayout()
        self.progress_label = QLabel(self.text)
        layout.addWidget(self.progress_label)

        self.setLayout(layout)

        self.resize(200, 100)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)

    def showEvent(self, event):
        QTimer.singleShot(100, self.start_work)
        super().showEvent(event)

    def start_work(self):
        self.worker_thread = LoadingWorker(self.func)
        self.worker_thread.finished.connect(self.on_finished)
        self.worker_thread.start()

    def on_finished(self, result):
        self.result = result
        self.accept()


class DoubleClickableTextEdit(QTextEdit):
    doubleclicked = pyqtSignal()

    def mouseDoubleClickEvent(self, ev):
        self.doubleclicked.emit()


class MiniUtilDialog(QDialog):
    def __init__(self, parent, mode):
        super(MiniUtilDialog, self).__init__(parent)
        self.mode = mode
        self.setAcceptDrops(True)
        self.setWindowTitle("태그 확인기" if self.mode ==
                            "tagger" else "이미지 정보 확인기")

        # 레이아웃 설정
        layout = QVBoxLayout()
        frame = BackgroundFrame(self, opacity=0.3)
        frame.set_background_image_by_src(resource_path(self.mode + ".png"))
        self.frame = frame
        self.parent().installEventFilter(frame)
        frame.setFixedSize(QSize(512, 512))
        frame.setStyleSheet("""QLabel{
            font-size:30px;
            }
            QTextEdit{
            font-size:20px;
            background-color:#00000000;
            }""")

        inner_layout = QVBoxLayout()
        label1 = QLabel("Double Click Me")
        label1.setAlignment(Qt.AlignCenter)
        inner_layout.addWidget(label1)
        label_content = DoubleClickableTextEdit("")
        label_content.setReadOnly(True)
        label_content.setAcceptRichText(False)
        label_content.setFrameStyle(QFrame.NoFrame)
        label_content.setAlignment(Qt.AlignCenter)
        inner_layout.addWidget(label_content, stretch=999)
        label2 = QLabel("Or Drag-Drop Here")
        label2.setAlignment(Qt.AlignCenter)
        inner_layout.addWidget(label2)
        frame.setLayout(inner_layout)

        label_content.doubleclicked.connect(self.show_file_dialog)

        self.label_content = label_content
        self.label1 = label1
        self.label2 = label2

        layout.addWidget(frame)
        self.setLayout(layout)

    def set_content(self, src, nai_dict):
        if isinstance(src, str) and os.path.isfile(src):
            self.frame.set_background_image_by_src(src)
        else:
            self.frame.set_background_image_by_img(src)
        self.frame.opacity = 0.1
        self.label1.setVisible(False)
        self.label2.setVisible(False)
        self.label_content.setEnabled(True)
        self.label_content.setText(nai_dict)

    def execute(self, filemode, target):
        if self.mode == "getter":
            if filemode == "src":
                nai_dict, error_code = naiinfo_getter.get_naidict_from_file(
                    target)
            elif filemode == "img":
                nai_dict, error_code = naiinfo_getter.get_naidict_from_img(
                    target)
            elif filemode == "txt":
                nai_dict, error_code = naiinfo_getter.get_naidict_from_txt(
                    target)

            if nai_dict:
                target_dict = {
                    "prompt": nai_dict["prompt"],
                    "negative_prompt": nai_dict["negative_prompt"]
                }
                target_dict.update(nai_dict["option"])
                target_dict.update(nai_dict["etc"])

                if 'reference_strength' in target_dict:
                    rs_float = 0.0
                    try:
                        rs_float = float(target_dict['reference_strength'])
                    except Exception as e:
                        pass
                    if rs_float > 0:
                        target_dict["reference_image"] = "True"
                if "request_type" in target_dict and target_dict["request_type"] == "Img2ImgRequest":
                    target_dict["image"] = "True"

                self.set_content(target, prettify_naidict(target_dict))

                return
        elif self.mode == "tagger":
            result = self.parent().predict_tag_from(filemode, target, True)

            if result:
                self.set_content(target, result)
                return
        QMessageBox.information(
            self, '경고', "불러오는 중에 오류가 발생했습니다.")

    def show_file_dialog(self):
        select_dialog = QFileDialog()
        select_dialog.setFileMode(QFileDialog.ExistingFile)
        fname, _ = select_dialog.getOpenFileName(
            self, '불러올 파일을 선택해 주세요.', '',
            '이미지 파일(*.png *.webp)' if self.mode == "tagger" else
            '이미지, 텍스트 파일(*.txt *.png *.webp)')

        if fname:
            if self.mode == "tagger":
                if fname.endswith(".png") or fname.endswith(".webp"):
                    self.execute("src", fname)
                else:
                    QMessageBox.information(
                        self, '경고', "png, webp, txt 파일만 가능합니다.")
                    return
            else:
                if fname.endswith(".png") or fname.endswith(".webp"):
                    self.execute("src", fname)
                elif fname.endswith(".txt"):
                    self.execute("txt", fname)
                    QMessageBox.information(
                        self, '경고', "png, webp 또는 폴더만 가능합니다.")
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
                self.execute("src", fname)
                return
            elif fname.endswith(".txt"):
                if self.mode == "getter":
                    self.execute("txt", fname)
                    return

            if self.mode == "getter":
                QMessageBox.information(
                    self, '경고', "세팅 불러오기는 png, webp, txt 파일만 가능합니다.")
            else:
                QMessageBox.information(
                    self, '경고', "태그 불렁오기는 png, webp 파일만 가능합니다.")
        else:
            try:
                url = furl.url()
                res = request.urlopen(url).read()
                img = Image.open(BytesIO(res))
                if img:
                    self.execute("img", img)

            except Exception as e:
                print(e)
                QMessageBox.information(self, '경고', "이미지 파일 다운로드에 실패했습니다.")
                return


if __name__ == '__main__':
    app = QApplication(sys.argv)

    DEBUG_MODE = MiniUtilDialog

    if DEBUG_MODE == MiniUtilDialog:
        from PyQt5.QtWidgets import QMainWindow
        from PyQt5.QtCore import QSettings
        qw = QMainWindow()
        qw.move(200, 200)
        TOP_NAME = "dcp_arca"
        APP_NAME = "nag_gui"
        qw.settings = QSettings(TOP_NAME, APP_NAME)
        qw.dtagger = DanbooruTagger(qw.settings.value(
            "path_models", os.path.abspath(DEFAULT_PATH["path_models"])))
        loading_dialog = MiniUtilDialog(qw, "getter")
        if loading_dialog.exec_() == QDialog.Accepted:
            print(len(loading_dialog.result))
    elif DEBUG_MODE == OptionDialog:
        from PyQt5.QtWidgets import QMainWindow
        from PyQt5.QtCore import QSettings
        TOP_NAME = "dcp_arca"
        APP_NAME = "nag_gui"
        qw = QMainWindow()
        qw.move(200, 200)
        qw.settings = QSettings(TOP_NAME, APP_NAME)
        qw.dtagger = DanbooruTagger(qw.settings.value(
            "path_models", os.path.abspath(DEFAULT_PATH["path_models"])))
        OptionDialog(qw).exec_()
