from PyQt5.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QPushButton

from util.ui_util import add_button, create_empty

from config.themes import COLOR

class CustomQLabel(QLabel):
    def set_logged_in(self, is_loggedin):
        if is_loggedin:
            super(CustomQLabel, self).setText("")
            self.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 15px;
                }
            """)
        else:
            super(CustomQLabel, self).setText("로그인 안됨")
            self.setStyleSheet("""
                QLabel {
                    color: red;
                    font-size: 15px;
                }
            """)


class GenerateButtonsLayout():
    def __init__(self, parent):
        self.parent = parent
        self.parent.generate_buttons_layout = self

    def init(self):
        parent = self.parent

        main_layout = QVBoxLayout()
        hbox_generate = QHBoxLayout()
        main_layout.addLayout(hbox_generate)

        parent.label_loginstate = CustomQLabel()
        parent.label_loginstate.set_logged_in(False)
        hbox_generate.addWidget(parent.label_loginstate)

        self.button_generate_once = add_button(
            hbox_generate, "생성", parent.on_click_generate_once, 200, 200)
        self.button_generate_auto = add_button(
            hbox_generate, "연속 생성", parent.on_click_generate_auto, 200, 200)
        self.button_generate_sett = add_button(
            hbox_generate, "연속 세팅 생성", parent.on_click_generate_sett, 200, 200)
        self.button_generate_once.setDisabled(True)
        self.button_generate_auto.setDisabled(True)
        self.button_generate_sett.setDisabled(True)

        main_layout.addWidget(create_empty(minimum_height=5))

        hbox_expand = QHBoxLayout()
        main_layout.addLayout(hbox_expand)

        hbox_anlas = QHBoxLayout()
        label_anlas = QLabel("Anlas: ")
        label_anlas.setStyleSheet("""
            font: bold;
            color: """ + COLOR.BUTTON + """;
        """)
        parent.label_anlas = label_anlas
        hbox_anlas.addWidget(label_anlas)
        hbox_expand.addLayout(hbox_anlas, stretch=1)

        hbox_expand.addStretch(9)

        stylesheet_button = """
            color:white;
            text-align: center;
            font-weight: bold;
            background-color:#00000000;
            border: 1px solid white;
            padding: 8px;
        """
        button_getter = QPushButton("Info")
        hbox_expand.addWidget(button_getter)
        button_getter.clicked.connect(parent.on_click_getter)
        button_getter.setStyleSheet(stylesheet_button)

        button_tagger = QPushButton("Tag")
        hbox_expand.addWidget(button_tagger)
        button_tagger.clicked.connect(parent.on_click_tagger)
        button_tagger.setStyleSheet(stylesheet_button)

        button_expand = QPushButton("<<")
        hbox_expand.addWidget(button_expand)
        button_expand.clicked.connect(parent.on_click_expand)
        button_expand.setStyleSheet(stylesheet_button)
        parent.button_expand = button_expand

        return main_layout

    def set_disable_button(self, will_disable):
        self.button_generate_once.setDisabled(will_disable)
        self.button_generate_sett.setDisabled(will_disable)
        self.button_generate_auto.setDisabled(will_disable)

    def set_autogenerate_mode(self, is_autogenrate):
        self.button_generate_once.setDisabled(is_autogenrate)
        self.button_generate_sett.setDisabled(is_autogenrate)

        stylesheet = """
            color:black;
            background-color: """ + COLOR.BUTTON_SELECTED + """;
        """ if is_autogenrate else ""
        self.button_generate_auto.setStyleSheet(stylesheet)
        self.button_generate_auto.setText(
            "생성 중지" if is_autogenrate else "연속 생성")
        self.button_generate_auto.setDisabled(False)