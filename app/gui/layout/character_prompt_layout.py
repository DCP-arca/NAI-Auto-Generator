from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame, 
                            QGridLayout, QDialog, QCheckBox, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal

from core.worker.completer import CompletionTextEdit

from util.ui_util import add_button

from config.themes import COLOR

WIDTH_CHARITEM = 400
HEIGHT_CHARITEM = 270
HEIGHT_CONTAINER_EXPAND = 400
HEIGHT_CONTAINER_REDUCE = 80

def _get_position_text(position):
    return f"{int(position[0] * 5)-2}, {(4 - int(position[1] * 5 )- 2)}"

# stateChanged와는 다르게 값이 변경이 되든 안되든 콜백이 호출한다.
class CustomCheckBox(QCheckBox):
    onSetCheckedCalled = pyqtSignal(bool)

    def setChecked(self, checked):
        super().setChecked(checked)
        self.onSetCheckedCalled.emit(checked)

class PositionSelectorDialog(QDialog):
    """캐릭터 위치 선택 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("캐릭터 위치 선택")
        self.selected_position = None
        self.setup_ui()

    def setup_ui(self):
        try:
            layout = QVBoxLayout()
            self.setLayout(layout)
            self.setStyleSheet("QVBoxLayout{background-color: "+COLOR.DARK+"};}")

            # 설명 라벨
            info_label = QLabel("원하는 위치를 클릭하세요 (5x5 그리드)")
            layout.addWidget(info_label)

            # 그리드 생성 (5x5)
            grid_layout = QGridLayout()
            self.buttons = []

            for row in range(5):
                for col in range(5):
                    btn = QPushButton()
                    btn.setStyleSheet("background-color: "+ COLOR.WHITE)
                    btn.setText(_get_position_text(((col + 0.5) / 5, (row + 0.5) / 5)))
                    btn.setFixedSize(50, 50)
                    # 람다 함수에 위치 정보를 명시적으로 전달
                    btn.clicked.connect(lambda checked=False, r=row, c=col: self.on_position_selected(r, c))
                    grid_layout.addWidget(btn, row, col)
                    self.buttons.append(btn)

            layout.addLayout(grid_layout)

            # 완료/취소 버튼
            buttons_layout = QHBoxLayout()
            done_button = QPushButton("완료")
            done_button.clicked.connect(self.accept)
            cancel_button = QPushButton("취소")
            cancel_button.clicked.connect(self.reject)

            buttons_layout.addStretch()
            buttons_layout.addWidget(done_button)
            buttons_layout.addWidget(cancel_button)
            layout.addLayout(buttons_layout)
        except Exception as e:
            print(f"위치 선택자 UI 초기화 오류: {e}")

    def on_position_selected(self, row, col):
        try:
            print(f"위치 선택: 행={row}, 열={col}")
            # 다른 버튼들은 원래 색으로 복원
            for btn in self.buttons:
                btn.setStyleSheet("background-color: "+ COLOR.WHITE)

            # 선택된 버튼 하이라이트
            index = row * 5 + col
            self.buttons[index].setStyleSheet(f"background-color: {COLOR.BUTTON_SELECTED};")

            # 위치 저장 (0~1 범위의 비율로 저장)
            self.selected_position = ((col + 0.5) / 5, (row + 0.5) / 5)
            print(f"저장된 위치: {self.selected_position}")
        except Exception as e:
            print(f"위치 선택 처리 오류: {e}")

class CharacterPromptWidget(QFrame):
    """캐릭터 프롬프트를 입력하고 관리하는 위젯"""

    deleted = pyqtSignal(object)  # 삭제 시그널
    moved = pyqtSignal(object, int)  # 이동 시그널 (위젯, 방향)

    def __init__(self, parent=None, index=0):
        super().__init__(parent)
        self.parent = parent
        self.index = index
        self.position = None  # 캐릭터 위치 (None = AI 선택)
        self.show_negative = False  # 네거티브 프롬프트 표시 여부

        # 스타일 설정
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)

        # 수직 레이아웃으로 설계
        self.setup_ui()

        # 위젯 크기 정책 설정
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setFixedWidth(WIDTH_CHARITEM)  # 최소 너비 설정
        self.setFixedHeight(HEIGHT_CHARITEM)  # 최소 너비 설정

    # 새로운 메서드 추가
    def update_title(self):
        """타이틀 업데이트"""
        try:
            header_layout = self.layout.itemAt(0).layout()
            if header_layout:
                title_label = header_layout.itemAt(0).widget()
                if title_label:
                    title_label.setText(f"캐릭터 {self.index + 1}")
        except Exception as e:
            print(f"타이틀 업데이트 중 오류: {e}")

    def setup_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # 헤더 (타이틀 + 컨트롤 버튼)
        header_layout = QHBoxLayout()

        title_label = QLabel(f"캐릭터 {self.index + 1}")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # 네거 버튼
        self.negative_btn = QPushButton("네거")
        self.negative_btn.setFixedWidth(50)
        self.negative_btn.clicked.connect(self.toggle_negative_prompt)

        # 캐릭터 순서 이동 버튼
        move_up_btn = QPushButton("◀")
        move_up_btn.setFixedWidth(50)
        move_up_btn.clicked.connect(lambda: self.moved.emit(self, -1))

        move_down_btn = QPushButton("▶")
        move_down_btn.setFixedWidth(50)
        move_down_btn.clicked.connect(lambda: self.moved.emit(self, 1))

        # 위치 설정 버튼
        self.position_btn = QPushButton("위치")
        self.position_btn.setFixedWidth(50)
        self.position_btn.setEnabled(True)
        self.position_btn.clicked.connect(self.show_position_dialog)

        # 삭제 버튼
        delete_btn = QPushButton("✕")
        delete_btn.setFixedWidth(50)
        delete_btn.clicked.connect(lambda: self.deleted.emit(self))

        header_layout.addWidget(self.negative_btn)
        header_layout.addWidget(move_up_btn)
        header_layout.addWidget(move_down_btn)
        header_layout.addWidget(self.position_btn)
        header_layout.addWidget(delete_btn)

        self.layout.addLayout(header_layout)

        # QPlainTextEdit 대신 CompletionTextEdit 사용
        self.prompt_edit = CompletionTextEdit()
        self.prompt_edit.setPlaceholderText("프롬프트 입력...")
        self.prompt_edit.setMinimumHeight(80)
        self.layout.addWidget(self.prompt_edit)

        # 네거티브 프롬프트 입력에도 CompletionTextEdit 사용
        self.neg_prompt_edit = CompletionTextEdit()
        self.neg_prompt_edit.setPlaceholderText("네거티브 프롬프트 입력...")
        self.neg_prompt_edit.setMinimumHeight(80)
        self.neg_prompt_edit.setVisible(False)
        self.layout.addWidget(self.neg_prompt_edit)

    def toggle_negative_prompt(self, state):
        """네거티브 프롬프트 표시/숨김 전환"""
        promptVisible = self.prompt_edit.isVisible()
        npromptVisible = self.neg_prompt_edit.isVisible()
        self.prompt_edit.setVisible(npromptVisible)
        self.neg_prompt_edit.setVisible(promptVisible)

        nowPromptVisible = npromptVisible

        self.negative_btn.setStyleSheet(f"background-color: {COLOR.BUTTON if nowPromptVisible else COLOR.BUTTON_SELECTED};")

    def show_position_dialog(self):
        """캐릭터 위치 선택 다이얼로그 표시"""
        try:
            print("위치 선택 다이얼로그 열기 시도")
            dialog = PositionSelectorDialog(self)

            # 기존 위치 선택된 상태로 표시
            if self.position:
                print(f"기존 위치: {self.position}")
                col = int(self.position[0] * 5)
                row = int(self.position[1] * 5)
                index = row * 5 + col
                dialog.buttons[index].setStyleSheet(f"background-color: {COLOR.BUTTON_SELECTED};")
                dialog.selected_position = self.position

            # 다이얼로그 표시 및 결과 처리
            result = dialog.exec_()
            print(f"다이얼로그 결과: {result}, 선택된 위치: {dialog.selected_position}")

            if result == QDialog.Accepted and dialog.selected_position:
                self.position = dialog.selected_position
                self.position_btn.setStyleSheet(f"background-color: {COLOR.BUTTON_SELECTED};")
                self.position_btn.setText(_get_position_text(self.position))
                print(f"위치 설정 완료: {self.position}")
        except Exception as e:
            print(f"위치 선택 다이얼로그 오류: {e}")


    # return {
    #     "prompt": "girl, ",
    #     "uc": "lowres, aliasing, ",
    #     "center": {
    #         "x": 0.5,
    #         "y": 0.5
    #     },
    # }
    def get_data(self):
        """캐릭터 프롬프트 데이터 반환"""
        return {
            "prompt": self.prompt_edit.toPlainText() or "",
            "uc": self.neg_prompt_edit.toPlainText() or "",
            "center": {
                "x": float(self.position[0]) if self.position else 0.5,
                "y": float(self.position[1]) if self.position else 0.5
            }
        }

    def set_data(self, data):
        """캐릭터 프롬프트 데이터 설정"""
        if "prompt" in data:
            self.prompt_edit.setPlainText(data["prompt"])

        if "uc" in data:
            self.neg_prompt_edit.setPlainText(data["uc"])

        if "center" in data and data["center"]["x"] and data["center"]["y"]:
            self.position = (float(data["center"]["x"]), float(data["center"]["y"]))
            if self.position:
                self.position_btn.setStyleSheet(f"background-color: {COLOR.BUTTON_SELECTED};")
                self.position_btn.setText(_get_position_text(self.position))

class CharacterPromptsContainer(QWidget):
    """캐릭터 프롬프트 컨테이너 위젯"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.character_widgets = []
        self.not_use_ai_positions = True
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.main_layout)

        # 캐릭터 프롬프트 설명
        info_layout = QHBoxLayout()
        info_label = QLabel("캐릭터 프롬프트 (V4에만 적용)")
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        self.main_layout.addLayout(info_layout)

        # AI 위치 선택 여부 체크박스
        controls_layout = QHBoxLayout()
        self.ai_position_checkbox = CustomCheckBox("직접 위치 선택하기")
        self.ai_position_checkbox.setChecked(False)
        self.ai_position_checkbox.onSetCheckedCalled.connect(self.toggle_ai_positions)
        self.ai_position_checkbox.stateChanged.connect(self.toggle_ai_positions)
        controls_layout.addWidget(self.ai_position_checkbox)

        # 모두 삭제 버튼
        self.clear_button = add_button(controls_layout, "모두 삭제", self.clear_characters, 200, 200)
        self.clear_button.setMinimumHeight(30)

        # 캐릭터 추가 버튼
        add_button(controls_layout, "캐릭터 추가", self.add_character, 200, 200).setMinimumHeight(30)

        self.main_layout.addLayout(controls_layout)

        # 수평 스크롤 영역
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
        QTextEdit {
            background-color: """ + COLOR.DARK + """;
        }""")

        # 캐릭터 위젯들을 수평으로 배치할 컨테이너
        self.characters_container = QWidget()
        self.characters_layout = QHBoxLayout(self.characters_container)
        self.characters_layout.setContentsMargins(0, 0, 0, 0)
        self.characters_layout.setSpacing(10)  # 캐릭터 위젯 사이의 간격
        self.characters_layout.addStretch()  # 오른쪽 끝에 빈 공간 추가

        self.scroll_area.setWidget(self.characters_container)

        self.main_layout.addWidget(self.scroll_area)

        self.on_update_character_count()

        self.parent.dict_ui_settings["use_coords"] = self.ai_position_checkbox
        self.parent.dict_ui_settings["characterPrompts"] = self

    def toggle_ai_positions(self, state):
        """AI 위치 선택 여부 토글"""
        try:
            self.not_use_ai_positions = state == Qt.Checked

            print("toggle_ai_positions", self.not_use_ai_positions)

            # 모든 캐릭터 위젯의 위치 버튼 활성화/비활성화
            for widget in self.character_widgets:
                enabled = self.not_use_ai_positions
                widget.position_btn.setEnabled(enabled)

                # 버튼 스타일 업데이트 (시각적 피드백)
                if enabled:
                    if widget.position:
                        # 위치가 이미 설정된 경우
                        widget.position_btn.setStyleSheet(f"background-color: {COLOR.BUTTON_SELECTED};")
                        widget.position_btn.setText(_get_position_text(widget.position))
                    else:
                        # 위치가 설정되지 않은 경우
                        widget.position_btn.setStyleSheet(f"background-color: {COLOR.BUTTON};")
                        widget.position_btn.setText("위치")
                else:
                    # 비활성화된 경우
                    widget.position_btn.setStyleSheet(f"background-color: {COLOR.BUTTON_DSIABLED};")
                    widget.position_btn.setText("위치")
        except Exception as e:
            print(f"AI 위치 토글 오류: {e}")
            
    def on_update_character_count(self):
        """캐릭터 위젯 유무에 따라 ui를 업데이트함"""
        is_there_charater =  len(self.character_widgets) > 0

        self.setFixedHeight(HEIGHT_CONTAINER_EXPAND if is_there_charater else HEIGHT_CONTAINER_REDUCE)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn if is_there_charater else Qt.ScrollBarAlwaysOff)

        self.clear_button.setVisible(is_there_charater)

    def add_character(self):
        """새 캐릭터 프롬프트 추가"""
        if len(self.character_widgets) >= 6:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "경고", "최대 6개의 캐릭터만 추가할 수 있습니다.")
            return

        widget = CharacterPromptWidget(self, len(self.character_widgets))
        widget.deleted.connect(self.remove_character)
        widget.moved.connect(self.move_character)
        widget.position_btn.setEnabled(self.not_use_ai_positions)

        # 켜져있다면, 태그 자동 완성 적용 (로딩 전이라면 다 로딩된 다음에 따로 적용됨.)
        if self.parent.completiontag_list:
            widget.prompt_edit.start_complete_mode(self.parent.completiontag_list)
            widget.neg_prompt_edit.start_complete_mode(self.parent.completiontag_list)

        # stretch 아이템 앞에 위젯 삽입
        self.characters_layout.insertWidget(self.characters_layout.count() - 1, widget)
        self.character_widgets.append(widget)

        # 인덱스 업데이트
        self.update_indices()
        
        self.on_update_character_count()

    def remove_character(self, widget):
        """캐릭터 프롬프트 삭제"""
        if widget in self.character_widgets:
            self.characters_layout.removeWidget(widget)
            self.character_widgets.remove(widget)
            widget.deleteLater()

            # 인덱스 업데이트
            self.update_indices()
            
        self.on_update_character_count()

    def move_character(self, widget, direction):
        """캐릭터 프롬프트 순서 이동"""
        if widget not in self.character_widgets:
            return

        index = self.character_widgets.index(widget)
        new_index = index + direction

        if 0 <= new_index < len(self.character_widgets):
            # 위젯 순서 변경
            self.character_widgets.pop(index)
            self.character_widgets.insert(new_index, widget)

            # 레이아웃에서 제거 후 재배치
            for i, w in enumerate(self.character_widgets):
                self.characters_layout.removeWidget(w)

            # stretch 아이템 제거
            stretch_item = self.characters_layout.takeAt(self.characters_layout.count() - 1)

            # 위젯 추가
            for i, w in enumerate(self.character_widgets):
                self.characters_layout.addWidget(w)

            # stretch 아이템 다시 추가
            self.characters_layout.addStretch()

            # 인덱스 업데이트
            self.update_indices()

    def update_indices(self):
        """캐릭터 인덱스 업데이트"""
        for i, widget in enumerate(self.character_widgets):
            widget.index = i
            try:
                widget.update_title()
            except:
                # 예전 방식으로도 시도
                try:
                    header_layout = widget.layout.itemAt(0).layout()
                    if header_layout:
                        title_label = header_layout.itemAt(0).widget()
                        if title_label:
                            title_label.setText(f"캐릭터 {i + 1}")
                except:
                    pass

    def clear_characters(self):
        """모든 캐릭터 프롬프트 삭제"""
        for widget in self.character_widgets[:]:
            self.remove_character(widget)
            
        self.on_update_character_count()

    # 로딩 전에 생성된 오브젝트에게 list를 삽입한다.
    def refresh_completiontag_list(self):
        for char_widget in self.character_widgets:
            char_widget.prompt_edit.start_complete_mode(self.parent.completiontag_list)
            char_widget.neg_prompt_edit.start_complete_mode(self.parent.completiontag_list)

    # return [{
    #     "prompt": "girl, ",
    #     "uc": "lowres, aliasing, ",
    #     "center": {
    #         "x": 0.5,
    #         "y": 0.5
    #     },
    # }]
    def get_data(self):
        """모든 캐릭터 프롬프트 데이터 반환"""
        return [widget.get_data() for widget in self.character_widgets]

    # data = [{
    #     "prompt": "girl, ",
    #     "uc": "lowres, aliasing, ",
    #     "center": {
    #         "x": 0.5,
    #         "y": 0.5
    #     },
    # }]
    def set_data(self, data):
        """캐릭터 프롬프트 데이터 설정"""
        self.clear_characters()

        for char_data in data:
            self.add_character()
            self.character_widgets[-1].set_data(char_data)