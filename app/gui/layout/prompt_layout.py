
from PyQt5.QtWidgets import QTextEdit, QLabel, QVBoxLayout, QHBoxLayout

from core.worker.completer import CompletionTextEdit

from util.ui_util import create_empty
from util.string_util import prettify_naidict

from config.strings import STRING

def create_prompt_layout(self, title_text, list_buttoncode):
    hbox_prompt_title = QHBoxLayout()

    label = QLabel(title_text)
    hbox_prompt_title.addWidget(label)

    return hbox_prompt_title

def create_prompt_edit(self, placeholder_text, code):
    textedit = CompletionTextEdit()
    textedit.setPlaceholderText(placeholder_text)
    textedit.setAcceptRichText(False)
    textedit.setAcceptDrops(False)
    self.dict_ui_settings[code] = textedit

    return textedit

class PromptLayout():
    def __init__(self, parent):
        self.parent = parent
        self.parent.prompt_layout = self

    def init(self):
        parent = self.parent

        vbox = QVBoxLayout()

        vbox.addLayout(create_prompt_layout(self, STRING.LABEL_PROMPT, ["add", "set", "sav"]))

        vbox.addWidget(create_prompt_edit(
            parent, STRING.LABEL_PROMPT_HINT, "prompt"), stretch=20)

        vbox.addWidget(create_empty(minimum_height=6))

        vbox.addLayout(create_prompt_layout(
            parent, STRING.LABEL_NPROMPT, ["nadd", "nset", "nsav"]))

        vbox.addWidget(create_prompt_edit(
            parent, STRING.LABEL_NPROMPT_HINT, "negative_prompt"), stretch=10)

        vbox.addWidget(create_empty(minimum_height=6))

        vbox.addWidget(QLabel("결과창"))
        prompt_result = QTextEdit("")
        prompt_result.setPlaceholderText("이곳에 결과가 출력됩니다.")
        prompt_result.setReadOnly(True)
        prompt_result.setAcceptRichText(False)
        prompt_result.setAcceptDrops(False)
        vbox.addWidget(prompt_result, stretch=5)

        self.prompt_result = prompt_result

        return vbox

    def set_result_text(self, nai_dict):
        content = prettify_naidict(nai_dict)

        self.prompt_result.setText(content)
