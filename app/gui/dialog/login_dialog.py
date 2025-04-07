
from PyQt5.QtWidgets import QLabel, QLineEdit, QCheckBox, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QDialog
from PyQt5.QtCore import Qt

from core.thread.login_thread import LoginThread

class LoginDialog(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()
        self.check_already_login()

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
        self.parent.statusbar.set_statusbar_text("LOGGINGIN")
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
