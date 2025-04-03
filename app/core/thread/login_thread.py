from PyQt5.QtCore import QThread, pyqtSignal

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
