# status_bar.py
from config.strings import STRING

class StatusBar:
    def __init__(self, status_bar):
        self.status_bar = status_bar
        self.status_state = None
        self.status_list_format = []
        self.status_bar.messageChanged.connect(
            self.on_statusbar_message_changed)

    def set_statusbar_text(self, status_key="", list_format=[]):
        if status_key:
            self.status_state = status_key
            self.status_list_format = list_format
        else:
            status_key = self.status_state
            list_format = self.status_list_format

        message = STRING.LIST_STATSUBAR_STATE[status_key].format(
            *list_format)
        self.status_bar.showMessage(message)

    def on_statusbar_message_changed(self, t):
        if not t:
            self.set_statusbar_text()
