from PyQt5.QtWidgets import QCompleter, QTextEdit
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import Qt, QStringListModel


class CustomCompleter(QCompleter):
    def __init__(self, words, parent=None):
        super().__init__(words, parent)
        self.words = words
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterMode(Qt.MatchContains)
        self.model = QStringListModel(words, self)
        self.setModel(self.model)

    def setCompletionPrefix(self, prefix):
        self.prefix = prefix

        is_add_mode = len(self.prefix) > 3
        prefix_lower = self.prefix.lower()
        filtered_words = []
        contains_matches = []
        for word in self.words:
            word_lower = word.lower()
            if word_lower.startswith(prefix_lower):
                filtered_words.append(word)
            elif is_add_mode and prefix_lower in word_lower:
                contains_matches.append(word)

        if is_add_mode:
            filtered_words.extend(sorted(contains_matches))

        self.model.setStringList(filtered_words)
        super().setCompletionPrefix(prefix)
        self.complete()


class CompletionTextEdit(QTextEdit):
    def __init__(self):
        super().__init__()
        self.completer = None

    def start_complete_mode(self, tag_list):
        completer = CustomCompleter(tag_list)

        self.setCompleter(completer)

    def setCompleter(self, completer):
        if self.completer:
            self.disconnect(self.completer, self.insertCompletion)
        self.completer = completer
        if not self.completer:
            return
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(False)
        self.completer.activated.connect(self.insertCompletion)

    def insertCompletion(self, completion):
        actual_text = completion.split('[')[0]  # 'apple[30]' -> 'apple'
        actual_text = actual_text.replace("_", " ")
        tc = self.textCursor()
        extra = len(actual_text) - len(self.completer.completionPrefix())
        tc.movePosition(QTextCursor.Left)
        tc.movePosition(QTextCursor.EndOfWord)
        tc.insertText(actual_text[-extra:])
        self.setTextCursor(tc)

    def textUnderCursor(self):
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        return tc.selectedText()

    def keyPressEvent(self, event):
        if self.completer:
            if self.completer and self.completer.popup().isVisible():
                if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                    event.ignore()
                    return

            super().keyPressEvent(event)

            ctrlOrShift = event.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)
            if ctrlOrShift and event.text() == '':
                return

            if event.text():
                # eow = "~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-="
                eow = "{},<>|@"
                hasModifier = (event.modifiers() !=
                               Qt.NoModifier) and not ctrlOrShift
                completionPrefix = self.textUnderCursor()

                if not self.completer or (hasModifier and event.text() == '') or len(completionPrefix) < 1 or event.text()[-1] in eow:
                    self.completer.popup().hide()
                    return

                if completionPrefix != self.completer.completionPrefix():
                    self.completer.setCompletionPrefix(completionPrefix)
                    self.completer.popup().setCurrentIndex(
                        self.completer.completionModel().index(0, 0))

                cr = self.cursorRect()
                cr.setWidth(self.completer.popup().sizeHintForColumn(
                    0) + self.completer.popup().verticalScrollBar().sizeHint().width())
                self.completer.complete(cr)
        else:
            super().keyPressEvent(event)
