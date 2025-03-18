from PyQt5.QtWidgets import QCompleter, QTextEdit
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QFont, QColor
from PyQt5.QtCore import Qt, QStringListModel
import string

# complete_target_stringset = string.ascii_letters + string.digits + "~!#$%^&*_+?.-="


class CustomCompleter(QCompleter):
    def __init__(self, words, parent=None):
        print(f"CustomCompleter 초기화: {len(words)}개 단어")
        super().__init__(words, parent)
        self.words = words
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterMode(Qt.MatchContains)
        self.model = QStringListModel(words, self)
        self.setModel(self.model)

    def setCompletionPrefix(self, prefix):
        self.prefix = prefix
        
        # 최소 2글자 이상부터 검색 (성능 향상)
        if len(prefix) < 2:
            self.model.setStringList([])
            super().setCompletionPrefix(prefix)
            return
            
        is_add_mode = len(self.prefix) > 3
        prefix_lower = self.prefix.lower()
        filtered_words = []
        contains_matches = []
        
        # 제한된 개수만 검색 (성능 향상)
        words_count = min(3000, len(self.words))
        for i in range(words_count):
            word = self.words[i]
            word_lower = word.lower()
            if word_lower.startswith(prefix_lower):
                filtered_words.append(word)
                # 시작 일치 항목이 일정 수 이상이면 중단
                if len(filtered_words) > 50:
                    break
            elif is_add_mode and prefix_lower in word_lower:
                contains_matches.append(word)
                # 포함 일치 항목이 일정 수 이상이면 중단
                if len(contains_matches) > 50:
                    break

        # 최대 표시 항목 제한
        if is_add_mode:
            filtered_words.extend(sorted(contains_matches)[:50])
        
        # 목록 업데이트
        self.model.setStringList(filtered_words)
        super().setCompletionPrefix(prefix)
        self.complete()


class CompletionTextEdit(QTextEdit):
    def __init__(self):
        print("CompletionTextEdit 초기화")
        super().__init__()
        self.completer = None
        self.textChanged.connect(self.highlightBrackets)
    
    def insertFromMimeData(self, source):
        """클립보드에서 붙여넣기할 때 서식 없는 텍스트만 삽입"""
        if source.hasText():
            # 서식 없는 일반 텍스트만 가져와서 현재 커서 위치에 삽입
            cursor = self.textCursor()
            cursor.insertText(source.text())
        else:
            # 기본 처리 방식 사용 (텍스트가 없는 다른 형식의 데이터인 경우)
            super().insertFromMimeData(source)
        
    def highlightBrackets(self):
        text = self.toPlainText()

        # Stack to keep track of open brackets
        stack = []
        bracket_pairs = {'(': ')', '{': '}', '[': ']', '<': '>'}
        open_brackets = bracket_pairs.keys()
        close_brackets = bracket_pairs.values()

        # Dictionary to keep track of bracket positions
        bracket_positions = {}
        for i, char in enumerate(text):
            if char in open_brackets:
                stack.append((char, i))
                bracket_positions[i] = -1  # 기본 값으로 -1 설정
            elif char in close_brackets:
                if stack and bracket_pairs[stack[-1][0]] == char:
                    open_bracket, open_pos = stack.pop()
                    bracket_positions[open_pos] = i
                    bracket_positions[i] = open_pos
                else:
                    bracket_positions[i] = -1

        # Highlight unmatched brackets
        extraSelections = []
        unmatched_format = QTextCharFormat()
        unmatched_format.setFontWeight(QFont.Bold)
        unmatched_format.setForeground(QColor("red"))

        for pos, matching_pos in bracket_positions.items():
            if matching_pos == -1:
                selection = QTextEdit.ExtraSelection()
                selection.format = unmatched_format
                cursor = self.textCursor()
                cursor.setPosition(pos)
                cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
                selection.cursor = cursor
                extraSelections.append(selection)

        self.setExtraSelections(extraSelections)

    def start_complete_mode(self, tag_list):
        print(f"start_complete_mode 호출: {len(tag_list)}개 태그")
        if not tag_list:
            print("태그 목록이 비어 있어 자동 완성을 설정하지 않습니다.")
            return
            
        try:
            completer = CustomCompleter(tag_list)
            self.setCompleter(completer)
            print("자동 완성 설정 완료")
        except Exception as e:
            print(f"자동 완성 설정 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()

    
    def setCompleter(self, completer):
        if self.completer:
            try:
                self.disconnect(self.completer, self.insertCompletion)
            except:
                pass  # 이전 연결이 없을 수 있으므로 예외 무시
        self.completer = completer
        if not self.completer:
            return
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(False)
        try:
            self.completer.activated.connect(self.insertCompletion)
        except:
            print("자동완성 신호 연결 실패")

    def insertCompletion(self, completion):
        # CSV 형식 처리 (태그[숫자] => 태그)
        actual_text = completion.split('[')[0] if '[' in completion else completion
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
