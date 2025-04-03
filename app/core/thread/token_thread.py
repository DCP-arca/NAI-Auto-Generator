from PyQt5.QtCore import QThread, pyqtSignal

class TokenValidateThread(QThread):
    validation_result = pyqtSignal(int)

    def __init__(self, parent):
        super(TokenValidateThread, self).__init__(parent)

    def run(self):
        is_login_success = self.parent().nai.check_logged_in()

        self.validation_result.emit(0 if is_login_success else 1)