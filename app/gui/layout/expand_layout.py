
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QTextEdit

from gui.widget.result_image_view import ResultImageView

from config.paths import PATH_IMG_NO_IMAGE

def init_expand_layout(self): 
    vbox_expand = QVBoxLayout()
    vbox_expand.setContentsMargins(30, 30, 30, 30)

    image_result = ResultImageView(PATH_IMG_NO_IMAGE)
    image_result.setStyleSheet("""
        background-color: white;
        background-position: center
    """)
    self.installEventFilter(image_result)
    self.image_result = image_result
    vbox_expand.addWidget(image_result, stretch=9)

    vbox_expand.addWidget(QLabel("결과창"))
    prompt_result = QTextEdit("")
    prompt_result.setPlaceholderText("이곳에 결과가 출력됩니다.")
    prompt_result.setReadOnly(True)
    prompt_result.setAcceptRichText(False)
    prompt_result.setAcceptDrops(False)
    vbox_expand.addWidget(prompt_result, stretch=1)
    self.prompt_result = prompt_result
        
    return vbox_expand