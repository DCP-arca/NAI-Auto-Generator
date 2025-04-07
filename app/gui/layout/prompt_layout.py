
from PyQt5.QtWidgets import QTextEdit, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy

from core.worker.completer import CompletionTextEdit

from util.ui_util import create_empty
from util.string_util import prettify_naidict

from gui.layout.character_prompt_layout import CharacterPromptsContainer

from config.strings import STRING

def create_prompt_layout(self, title_text):
    hbox_prompt_title = QHBoxLayout()

    label = QLabel(title_text)
    hbox_prompt_title.addWidget(label)

    return hbox_prompt_title

def create_prompt_edit(self, placeholder_text, code, minimum_height):
    textedit = CompletionTextEdit()
    textedit.setPlaceholderText(placeholder_text)
    textedit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    textedit.setMinimumHeight(minimum_height)
    self.dict_ui_settings[code] = textedit

    return textedit

class PromptLayout():
    def __init__(self, parent):
        self.parent = parent
        self.parent.prompt_layout = self

    def init(self):
        parent = self.parent

        vbox = QVBoxLayout()

        vbox.addLayout(create_prompt_layout(self, STRING.LABEL_PROMPT))

        vbox.addWidget(create_prompt_edit(parent, STRING.LABEL_PROMPT_HINT, "prompt",
                                          minimum_height=200), stretch=3)

        vbox.addWidget(create_empty(minimum_height=4))

        vbox.addLayout(create_prompt_layout(
            parent, STRING.LABEL_NPROMPT))

        vbox.addWidget(create_prompt_edit(
            parent, STRING.LABEL_NPROMPT_HINT, "negative_prompt",
                                          minimum_height=100), stretch=2)

        vbox.addWidget(create_empty(minimum_height=4))

        parent.character_prompts_container = CharacterPromptsContainer(parent)
        vbox.addWidget(parent.character_prompts_container, stretch=1)

        vbox.addWidget(create_empty(minimum_height=4))

        return vbox