from PyQt5.QtWidgets import QLabel, QLineEdit, QCheckBox, QVBoxLayout, QHBoxLayout, QPushButton, QDialog

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
        self.count = self.lineedit_count.text() or None
        self.delay = self.lineedit_delay.text() or None
        self.ignore_error = self.checkbox_ignoreerror.isChecked()
        self.accept()

    def on_close_button_clicked(self):
        self.reject()
