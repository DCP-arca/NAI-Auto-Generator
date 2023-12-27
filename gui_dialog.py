import os

from PyQt5.QtWidgets import QFileDialog, QLabel, QLineEdit, QCheckBox, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QDialog, QMessageBox, QFileSystemModel, QListView, QSizePolicy
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from consts import DEFAULT_PATH


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


class TextSaveDialog(QDialog):
    def __init__(self, parent, path, str_title):
        super().__init__()
        self.parent = parent
        self.path = path
        self.str_title = str_title
        self.filename = ""
        self.initUI()

    def initUI(self):
        parent_pos = self.parent.pos()

        self.setWindowTitle(self.str_title)
        self.move(parent_pos.x() + 50, parent_pos.y() + 50)
        self.setFixedSize(335, 200)

        layout = QVBoxLayout()
        self.setLayout(layout)

        lineedit_name = QLineEdit()
        lineedit_name.setPlaceholderText("여기에 파일 이름 입력")
        self.lineedit_name = lineedit_name
        layout.addWidget(lineedit_name)

        layout_buttons = QHBoxLayout()
        layout.addLayout(layout_buttons)

        start_button = QPushButton("확인")
        start_button.clicked.connect(self.on_okay_button_clicked)
        layout_buttons.addWidget(start_button)
        self.start_button = start_button

        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.on_close_button_clicked)
        layout_buttons.addWidget(close_button)
        self.close_button = close_button

    def on_okay_button_clicked(self):
        filename = self.lineedit_name.text()

        # filename check
        if not filename:
            QMessageBox.information(self, '경고', "파일 이름을 입력해주세요.")
            return
        else:
            list_invaild = ["\\", "\/", "\:",
                            "\*", "\?", "\"",
                            "\<", "\>", "\|"]
            for s in list_invaild:
                if s in filename:
                    QMessageBox.information(self, '경고', "저장할 수 없는 문자가 들어있습니다.")
                    return

        # actual file check
        self.filename = filename
        target_path = os.path.join(self.path, self.filename + ".txt")
        if os.path.isfile(target_path):
            reply = QMessageBox.question(self, '경고', '해당 이름의 파일이 이미 존재합니다.\n계속 진행합니까?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        self.accept()

    def on_close_button_clicked(self):
        self.reject()


class TextLoadDialog(QDialog):
    def __init__(self, parent, path, str_title):
        super().__init__()
        self.parent = parent
        self.path = path
        self.str_title = str_title
        self.selected_filepath = ""
        self.initUI()

    def initUI(self):
        parent_pos = self.parent.pos()

        self.setWindowTitle(self.str_title)
        self.move(parent_pos.x() + 50, parent_pos.y() + 50)

        model = QFileSystemModel()
        model.setRootPath(self.path)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("경로: {}".format(self.path)))
        list_view = QListView()
        list_view.setModel(model)
        list_view.setRootIndex(model.index(self.path))
        self.list_view = list_view
        layout.addWidget(list_view)

        layout_buttons = QHBoxLayout()
        layout.addLayout(layout_buttons)

        start_button = QPushButton("확인")
        start_button.clicked.connect(self.on_okay_button_clicked)
        layout_buttons.addWidget(start_button)
        self.start_button = start_button

        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.on_close_button_clicked)
        layout_buttons.addWidget(close_button)
        self.close_button = close_button

    def on_okay_button_clicked(self):
        selected_indexes = self.list_view.selectedIndexes()

        if selected_indexes:
            selected_index = selected_indexes[0]

            self.selected_filepath = os.path.join(
                self.path, selected_index.data())

            self.accept()

    def on_close_button_clicked(self):
        self.reject()


class GenerateDialog(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        parent_pos = self.parent.pos()

        self.setWindowTitle('자동 생성')
        self.move(parent_pos.x() + 50, parent_pos.y() + 50)
        self.setFixedSize(335, 200)

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

        label_delay = QLabel("지연 시간(매 생성마다 대기) : ", self)
        layout_delay.addWidget(label_delay, 1)
        lineedit_delay = QLineEdit("3")
        lineedit_delay.setMaximumWidth(40)
        self.lineedit_delay = lineedit_delay
        layout_delay.addWidget(lineedit_delay, 1)

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
        self.accept()

    def on_close_button_clicked(self):
        self.reject()


class OptionDialog(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()
        super().exec_()

    def initUI(self):
        parent_pos = self.parent.pos()

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

            path = self.parent.settings.value(
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

        add_item(layout, "path_results", "생성이미지 저장 위치 : ")
        add_item(layout, "path_wildcards", "와일드카드 저장 위치 : ")
        add_item(layout, "path_prompts", "프롬프트 저장 위치 : ")
        add_item(layout, "path_nprompts", "네거티브 프롬프트 저장 위치 : ")
        add_item(layout, "path_settings", "세팅 파일 저장 위치 : ")

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
            self.parent.change_path(code, save_loc)

            self.refresh_label(code)

    def on_click_reset_button(self, code):
        self.parent.change_path(code, DEFAULT_PATH[code])

        self.refresh_label(code)

    def refresh_label(self, code):
        path = self.parent.settings.value(code, DEFAULT_PATH[code])
        self.dict_label_loc[code].setText(path)

    def on_click_close_button(self):
        self.reject()
