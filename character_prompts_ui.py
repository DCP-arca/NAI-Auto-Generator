import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                            QPushButton, QPlainTextEdit, QScrollArea, QFrame, 
                            QGridLayout, QDialog, QCheckBox, QButtonGroup, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPalette, QBrush
from completer import CompletionTextEdit

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
            
            # 설명 라벨
            info_label = QLabel("원하는 위치를 클릭하세요 (5x5 그리드)")
            layout.addWidget(info_label)
            
            # 그리드 생성 (5x5)
            grid_layout = QGridLayout()
            self.buttons = []
            
            for row in range(5):
                for col in range(5):
                    btn = QPushButton()
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
            import traceback
            traceback.print_exc()
    
    def on_position_selected(self, row, col):
        try:
            print(f"위치 선택: 행={row}, 열={col}")
            # 다른 버튼들은 원래 색으로 복원
            for btn in self.buttons:
                btn.setStyleSheet("")
            
            # 선택된 버튼 하이라이트
            index = row * 5 + col
            self.buttons[index].setStyleSheet("background-color: #559977;")
            
            # 위치 저장 (0~1 범위의 비율로 저장)
            self.selected_position = ((col + 0.5) / 5, (row + 0.5) / 5)
            print(f"저장된 위치: {self.selected_position}")
        except Exception as e:
            print(f"위치 선택 처리 오류: {e}")
            import traceback
            traceback.print_exc()

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
        self.setStyleSheet("background-color: #e6e6e6; border: 1px solid #cccccc; border-radius: 5px; padding: 5px;")
        
        # 수직 레이아웃으로 설계
        self.setup_ui()
        
        # 위젯 크기 정책 설정
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setMinimumWidth(250)  # 최소 너비 설정
    
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
        title_label.setStyleSheet("font-weight: bold; color: black;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 캐릭터 순서 이동 버튼
        move_up_btn = QPushButton("▲")
        move_up_btn.setFixedSize(30, 25)
        move_up_btn.clicked.connect(lambda: self.moved.emit(self, -1))
        
        move_down_btn = QPushButton("▼")
        move_down_btn.setFixedSize(30, 25)
        move_down_btn.clicked.connect(lambda: self.moved.emit(self, 1))
        
        # 위치 설정 버튼
        self.position_btn = QPushButton("위치")
        self.position_btn.setFixedWidth(50)
        self.position_btn.setStyleSheet("background-color: #f0f0f0; color: black;")
        self.position_btn.clicked.connect(self.show_position_dialog)
        
        # 삭제 버튼
        delete_btn = QPushButton("✕")
        delete_btn.setFixedSize(30, 25)
        delete_btn.clicked.connect(lambda: self.deleted.emit(self))
        
        header_layout.addWidget(move_up_btn)
        header_layout.addWidget(move_down_btn)
        header_layout.addWidget(self.position_btn)
        header_layout.addWidget(delete_btn)
        
        self.layout.addLayout(header_layout)
        
        # 캐릭터 프롬프트 입력
        prompt_label = QLabel("캐릭터 프롬프트:")
        prompt_label.setStyleSheet("color: black; font-weight: bold;")
        self.layout.addWidget(prompt_label)
        
        # QPlainTextEdit 대신 CompletionTextEdit 사용
        self.prompt_edit = CompletionTextEdit()
        self.prompt_edit.setPlaceholderText("이 캐릭터에 대한 프롬프트 입력...")
        self.prompt_edit.setMinimumHeight(80)
        self.prompt_edit.setStyleSheet("background-color: white; color: black; border: 1px solid #bbbbbb;")
        self.layout.addWidget(self.prompt_edit)
        
        # 네거티브 프롬프트 체크박스
        neg_checkbox_layout = QHBoxLayout()
        self.neg_checkbox = QCheckBox("네거티브 프롬프트 추가")
        self.neg_checkbox.setStyleSheet("color: black;")
        self.neg_checkbox.stateChanged.connect(self.toggle_negative_prompt)
        neg_checkbox_layout.addWidget(self.neg_checkbox)
        neg_checkbox_layout.addStretch()
        self.layout.addLayout(neg_checkbox_layout)
        
        # 네거티브 프롬프트 컨테이너 (처음에는 숨김)
        self.neg_container = QWidget()
        neg_container_layout = QVBoxLayout()
        neg_container_layout.setContentsMargins(0, 0, 0, 0)
        self.neg_container.setLayout(neg_container_layout)
        
        neg_prompt_label = QLabel("캐릭터 네거티브 프롬프트:")
        neg_prompt_label.setStyleSheet("color: black; font-weight: bold;")
        neg_container_layout.addWidget(neg_prompt_label)
        
        # 네거티브 프롬프트 입력에도 CompletionTextEdit 사용
        self.neg_prompt_edit = CompletionTextEdit()
        self.neg_prompt_edit.setPlaceholderText("이 캐릭터에 대한 네거티브 프롬프트 입력...")
        self.neg_prompt_edit.setMinimumHeight(50)
        self.neg_prompt_edit.setStyleSheet("background-color: white; color: black; border: 1px solid #bbbbbb;")
        neg_container_layout.addWidget(self.neg_prompt_edit)
        
        self.layout.addWidget(self.neg_container)
        self.neg_container.setVisible(False)  # 처음에는 숨김
    
    def toggle_negative_prompt(self, state):
        """네거티브 프롬프트 표시/숨김 전환"""
        self.show_negative = state == Qt.Checked
        self.neg_container.setVisible(self.show_negative)
    
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
                dialog.buttons[index].setStyleSheet("background-color: #559977;")
                dialog.selected_position = self.position
            
            # 다이얼로그 표시 및 결과 처리
            result = dialog.exec_()
            print(f"다이얼로그 결과: {result}, 선택된 위치: {dialog.selected_position}")
            
            if result == QDialog.Accepted and dialog.selected_position:
                self.position = dialog.selected_position
                self.position_btn.setStyleSheet("background-color: #559977; color: black;")
                self.position_btn.setToolTip(f"위치: {int(self.position[0]*100)}%, {int(self.position[1]*100)}%")
                print(f"위치 설정 완료: {self.position}")
        except Exception as e:
            print(f"위치 선택 다이얼로그 오류: {e}")
            import traceback
            traceback.print_exc()
    
    def get_data(self):
        """캐릭터 프롬프트 데이터 반환"""
        return {
            "prompt": self.prompt_edit.toPlainText(),
            "negative_prompt": self.neg_prompt_edit.toPlainText() if self.show_negative else "",
            "position": self.position,
            "show_negative": self.show_negative
        }
    
    def set_data(self, data):
        """캐릭터 프롬프트 데이터 설정"""
        if "prompt" in data:
            self.prompt_edit.setPlainText(data["prompt"])
        
        if "negative_prompt" in data and data["negative_prompt"]:
            self.neg_prompt_edit.setPlainText(data["negative_prompt"])
            self.show_negative = data.get("show_negative", True)
            self.neg_checkbox.setChecked(self.show_negative)
            self.neg_container.setVisible(self.show_negative)
        
        if "position" in data:
            self.position = data["position"]
            if self.position:
                self.position_btn.setStyleSheet("background-color: #559977; color: black;")
                self.position_btn.setToolTip(f"위치: {int(self.position[0]*100)}%, {int(self.position[1]*100)}%")

class CharacterPromptsContainer(QWidget):
    """캐릭터 프롬프트 컨테이너 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.character_widgets = []
        self.use_ai_positions = True
        self.setup_ui()
    
    def setup_ui(self):
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # 전체 컨테이너 스타일 설정
        self.setStyleSheet("QLabel { color: black; } QCheckBox { color: black; }")
        
        # 캐릭터 프롬프트 설명
        info_layout = QHBoxLayout()
        info_label = QLabel("캐릭터 프롬프트: V4 모델에서는 이미지 내 여러 캐릭터를 개별적으로 지정할 수 있습니다.")
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        self.main_layout.addLayout(info_layout)
        
        # AI 위치 선택 여부 체크박스
        controls_layout = QHBoxLayout()
        self.ai_position_checkbox = QCheckBox("AI 위치 선택")
        self.ai_position_checkbox.setChecked(True)
        self.ai_position_checkbox.stateChanged.connect(self.toggle_ai_positions)
        controls_layout.addWidget(self.ai_position_checkbox)
        
        # 캐릭터 추가 버튼
        self.add_button = QPushButton("+ 캐릭터 추가")
        self.add_button.clicked.connect(self.add_character)
        controls_layout.addWidget(self.add_button)
        
        # 모두 삭제 버튼
        self.clear_button = QPushButton("모두 삭제")
        self.clear_button.clicked.connect(self.clear_characters)
        controls_layout.addWidget(self.clear_button)
        
        self.main_layout.addLayout(controls_layout)
        
        # 수평 스크롤 영역
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 캐릭터 위젯들을 수평으로 배치할 컨테이너
        self.characters_container = QWidget()
        self.characters_layout = QHBoxLayout(self.characters_container)
        self.characters_layout.setContentsMargins(0, 0, 0, 0)
        self.characters_layout.setSpacing(10)  # 캐릭터 위젯 사이의 간격
        self.characters_layout.addStretch()  # 오른쪽 끝에 빈 공간 추가
        
        self.scroll_area.setWidget(self.characters_container)
        
        self.main_layout.addWidget(self.scroll_area)
    
    def toggle_ai_positions(self, state):
        """AI 위치 선택 여부 토글"""
        try:
            self.use_ai_positions = state == Qt.Checked
            print(f"AI 위치 선택 상태 변경: {self.use_ai_positions}")
            
            # 모든 캐릭터 위젯의 위치 버튼 활성화/비활성화
            for widget in self.character_widgets:
                enabled = not self.use_ai_positions
                widget.position_btn.setEnabled(enabled)
                
                # 버튼 스타일 업데이트 (시각적 피드백)
                if enabled:
                    if widget.position:
                        # 위치가 이미 설정된 경우
                        widget.position_btn.setStyleSheet("background-color: #559977; color: black;")
                    else:
                        # 위치가 설정되지 않은 경우
                        widget.position_btn.setStyleSheet("background-color: #f0f0f0; color: black;")
                else:
                    # 비활성화된 경우
                    widget.position_btn.setStyleSheet("background-color: #cccccc; color: #777777;")
        except Exception as e:
            print(f"AI 위치 토글 오류: {e}")
            import traceback
            traceback.print_exc()
    
    def add_character(self):
        """새 캐릭터 프롬프트 추가"""
        if len(self.character_widgets) >= 6:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "경고", "최대 6개의 캐릭터만 추가할 수 있습니다.")
            return
        
        widget = CharacterPromptWidget(self, len(self.character_widgets))
        widget.deleted.connect(self.remove_character)
        widget.moved.connect(self.move_character)
        widget.position_btn.setEnabled(not self.use_ai_positions)
        
        # 태그 자동 완성 적용 (태그 목록이 있는 경우)
        if hasattr(self, 'tag_list') and self.tag_list:
            if hasattr(widget.prompt_edit, 'start_complete_mode'):
                widget.prompt_edit.start_complete_mode(self.tag_list)
            if hasattr(widget.neg_prompt_edit, 'start_complete_mode'):
                widget.neg_prompt_edit.start_complete_mode(self.tag_list)
        
        # stretch 아이템 앞에 위젯 삽입
        self.characters_layout.insertWidget(self.characters_layout.count() - 1, widget)
        self.character_widgets.append(widget)
        
        # 각 캐릭터 위젯의 크기 제한 (너무 넓어지는 것 방지)
        widget.setMinimumWidth(250)
        widget.setMaximumWidth(350)
        
        # 인덱스 업데이트
        self.update_indices()
    
    def remove_character(self, widget):
        """캐릭터 프롬프트 삭제"""
        if widget in self.character_widgets:
            self.characters_layout.removeWidget(widget)
            self.character_widgets.remove(widget)
            widget.deleteLater()
            
            # 인덱스 업데이트
            self.update_indices()
    
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
    
    def get_data(self):
        """모든 캐릭터 프롬프트 데이터 반환"""
        return {
            "use_ai_positions": self.use_ai_positions,
            "characters": [widget.get_data() for widget in self.character_widgets]
        }
    
    def set_data(self, data):
        """캐릭터 프롬프트 데이터 설정"""
        self.clear_characters()
        
        if "use_ai_positions" in data:
            self.use_ai_positions = data["use_ai_positions"]
            self.ai_position_checkbox.setChecked(self.use_ai_positions)
        
        if "characters" in data:
            for char_data in data["characters"]:
                self.add_character()
                self.character_widgets[-1].set_data(char_data)
    
    def set_tag_completion(self, tag_list):
        """
        모든 캐릭터 프롬프트 에디터에 태그 자동 완성 설정
        """
        if not tag_list:
            return
            
        # 기존 캐릭터들에 자동 완성 적용
        for widget in self.character_widgets:
            if hasattr(widget.prompt_edit, 'start_complete_mode'):
                widget.prompt_edit.start_complete_mode(tag_list)
            if hasattr(widget.neg_prompt_edit, 'start_complete_mode'):
                widget.neg_prompt_edit.start_complete_mode(tag_list)
                
        # 이후 새로 추가되는 캐릭터에도 적용하기 위해 태그 목록 저장
        self.tag_list = tag_list