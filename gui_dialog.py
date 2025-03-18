import os
import re
import webbrowser
import time

from PyQt5.QtWidgets import (QDialog, QLabel, QPushButton, QVBoxLayout,
                             QHBoxLayout, QGroupBox, QFormLayout, QLineEdit,
                             QFileDialog, QMessageBox, QRadioButton,
                             QButtonGroup, QDialogButtonBox, QWidget, QCheckBox,
                             QComboBox, QSlider, QApplication, QSpinBox, QDoubleSpinBox,
                             QColorDialog)  # QColorDialog 추가
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor

from consts import DEFAULT_PATH


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.exec_()

    def setup_ui(self):
        self.setWindowTitle('NAI API 로그인')
        self.setFixedWidth(480)

        main_layout = QVBoxLayout()

        # 로그인 상태 확인
        is_logged_in = hasattr(self.parent, 'nai') and self.parent.nai and self.parent.nai.access_token

        if is_logged_in:
            # 로그인 상태일 때 UI
            login_label = QLabel("현재 Novel AI 계정으로 로그인되어 있습니다.")
            login_label.setAlignment(Qt.AlignCenter)
            
            username_label = QLabel(f"사용자: {self.parent.nai.username if hasattr(self.parent.nai, 'username') else '알 수 없음'}")
            username_label.setAlignment(Qt.AlignCenter)
            
            main_layout.addWidget(login_label)
            main_layout.addSpacing(15)
            main_layout.addWidget(username_label)
            main_layout.addSpacing(15)
            
            # 로그아웃 버튼
            logout_button = QPushButton("로그아웃하기")
            logout_button.clicked.connect(self.on_logout_click)
            
            buttons_layout = QHBoxLayout()
            buttons_layout.addStretch()
            buttons_layout.addWidget(logout_button)
            
            main_layout.addLayout(buttons_layout)
        else:
            # 로그인되지 않은 상태일 때 UI (기존 UI)
            login_label = QLabel("안녕하세요!\nNovel AI 계정으로 로그인해 주세요.")
            login_label.setAlignment(Qt.AlignCenter)

            username_label = QLabel("아이디:")
            password_label = QLabel("암호:")

            self.username_field = QLineEdit()
            self.password_field = QLineEdit()
            self.password_field.setEchoMode(QLineEdit.Password)

            info_label = QLabel(
                "※ 입력하신 아이디와 비밀번호는 Novel AI 서버에만 전송되며,\n이 앱의 서버로 전송되지 않습니다.")
            auto_login_checkbox = QCheckBox("다음에도 자동 로그인")

            form_layout = QFormLayout()
            form_layout.addRow(username_label, self.username_field)
            form_layout.addRow(password_label, self.password_field)

            login_button = QPushButton("로그인하기")

            buttons_layout = QHBoxLayout()
            buttons_layout.addStretch()
            buttons_layout.addWidget(login_button)

            main_layout.addWidget(login_label)
            main_layout.addSpacing(15)
            main_layout.addLayout(form_layout)
            main_layout.addWidget(auto_login_checkbox)
            main_layout.addSpacing(15)
            main_layout.addLayout(buttons_layout)
            main_layout.addSpacing(15)
            main_layout.addWidget(info_label)

            # 이벤트 연결
            login_button.clicked.connect(self.on_login_click)
            auto_login_checkbox.stateChanged.connect(self.on_auto_login)
            self.password_field.returnPressed.connect(self.on_login_click)

            # 자동 로그인 체크박스 초기 상태
            auto_login_value = self.parent.settings.value("auto_login", False)
            if isinstance(auto_login_value, str):
                auto_login_value = auto_login_value.lower() in ('true', 'yes', '1', 't', 'y')
            auto_login_checkbox.setChecked(auto_login_value)

            # 이전 아이디 로딩
            self.username_field.setText(self.parent.settings.value("username", ""))

        self.setLayout(main_layout)

    def on_auto_login(self, state):
        self.auto_login = state == Qt.Checked

    def on_login_click(self):
        username = self.username_field.text()
        password = self.password_field.text()

        if username and password:
            self.parent.set_statusbar_text("LOGGINGIN")

            # 로그인 스레드 생성
            self.login_thread = LoginThread(self.parent, self.parent.nai, username, password)
            self.login_thread.login_result.connect(self.on_login_result)
            self.login_thread.start()

            # 여기서 바로 닫지 않도록 수정
            # self.close()  # 이 줄 주석 처리
        else:
            QMessageBox.critical(self, "오류", "아이디와 비밀번호를 입력해주세요.")
            
    def on_logout_click(self):
        # 로그아웃 처리
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setText("정말 로그아웃 하시겠습니까?")
        msg_box.setWindowTitle("로그아웃 확인")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        
        if msg_box.exec_() == QMessageBox.Yes:
            try:
                # 로그아웃 처리 (NAIGenerator에 logout 메서드가 없으므로 직접 처리)
                # 기존 로그인 정보를 리셋합니다
                self.parent.nai.access_token = None
                self.parent.nai.username = None
                self.parent.nai.password = None
                
                # 부모 클래스에서 로그아웃 처리
                self.parent.on_logout()
                self.parent.set_auto_login(False)
                QMessageBox.information(self, "로그아웃 완료", "로그아웃 되었습니다.")
                self.close()
            except Exception as e:
                QMessageBox.critical(self, "로그아웃 오류", f"로그아웃 처리 중 오류가 발생했습니다:\n{str(e)}")

    def on_login_result(self, error_code):
        if error_code == 0:
            QMessageBox.information(self, "로그인 성공", "로그인에 성공했습니다.")
            
            # 로그인 상태 업데이트
            self.parent.label_loginstate.set_logged_in(True)
            self.parent.set_statusbar_text("LOGINED")
            self.parent.set_disable_button(False)
            self.parent.refresh_anlas()
            
            # 로그인 성공 후 창 닫기
            self.close()
        else:
            QMessageBox.critical(
                self, "로그인 실패", "로그인에 실패했습니다.\n아이디와 비밀번호를 확인해주세요.")
            self.close()  # 실패 시에도 창 닫기

    def apply_login_settings(self):
        """로그인 성공 후 UI 설정 적용"""
        if self.auto_login:
            self.parent.set_auto_login(True)
        
        # 로그인 상태 업데이트
        self.parent.set_statusbar_text("LOGINED")
        self.parent.label_loginstate.set_logged_in(True)
        self.parent.set_disable_button(False)
        
        # ANLAS 잔액 새로고침
        self.parent.refresh_anlas()

class OptionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle('옵션')
        self.setup_ui()

    def setup_ui(self):
        self.resize(800, 600)

        # 메인 레이아웃
        main_layout = QVBoxLayout()

      
 
        # 폴더 경로 설정 그룹
        path_group = QGroupBox("폴더 경로 설정")
        path_layout = QVBoxLayout()
        
        

        # 결과 저장 폴더
        output_label = QLabel("결과 저장 폴더:")
        self.output_path = QLineEdit(
            self.parent.settings.value("path_results", DEFAULT_PATH["path_results"]))
        output_button = QPushButton("찾아보기")
        output_button.clicked.connect(lambda: self.browse_folder("path_results"))
        output_layout = QHBoxLayout()
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(output_button)
        path_layout.addLayout(output_layout)

        # 세팅 파일 저장 폴더
        settings_label = QLabel("세팅 파일 저장 폴더:")
        self.settings_path = QLineEdit(
            self.parent.settings.value("path_settings", DEFAULT_PATH["path_settings"]))
        settings_button = QPushButton("찾아보기")
        settings_button.clicked.connect(lambda: self.browse_folder("path_settings"))
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(settings_label)
        settings_layout.addWidget(self.settings_path)
        settings_layout.addWidget(settings_button)
        path_layout.addLayout(settings_layout)

        # 와일드카드 파일 폴더
        wildcards_label = QLabel("와일드카드 파일 폴더:")
        self.wildcards_path = QLineEdit(
            self.parent.settings.value("path_wildcards", DEFAULT_PATH["path_wildcards"]))
        wildcards_button = QPushButton("찾아보기")
        wildcards_button.clicked.connect(lambda: self.browse_folder("path_wildcards"))
        wildcards_layout = QHBoxLayout()
        wildcards_layout.addWidget(wildcards_label)
        wildcards_layout.addWidget(self.wildcards_path)
        wildcards_layout.addWidget(wildcards_button)
        path_layout.addLayout(wildcards_layout)

        # 모델 파일 폴더
        models_label = QLabel("모델 파일 폴더:")
        self.models_path = QLineEdit(
            self.parent.settings.value("path_models", DEFAULT_PATH["path_models"]))
        models_button = QPushButton("찾아보기")
        models_button.clicked.connect(lambda: self.browse_folder("path_models"))
        models_layout = QHBoxLayout()
        models_layout.addWidget(models_label)
        models_layout.addWidget(self.models_path)
        models_layout.addWidget(models_button)
        path_layout.addLayout(models_layout)

        path_group.setLayout(path_layout)
        main_layout.addWidget(path_group)
        
        # === Theme Settings Group ===
        theme_group = QGroupBox("테마 설정 (Theme Settings)")
        theme_layout = QVBoxLayout()
    
        # Theme selection
        theme_selector_layout = QHBoxLayout()
        theme_selector_layout.addWidget(QLabel("테마 모드:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["기본 테마 (System Default)", "어두운 모드 (Dark)", "밝은 모드 (Light)"])
        # Load saved theme
        saved_theme = self.parent.settings.value("theme_mode", "기본 테마 (System Default)")
        self.theme_combo.setCurrentText(saved_theme)
        theme_selector_layout.addWidget(self.theme_combo, 1)
        theme_layout.addLayout(theme_selector_layout)

        # Accent color
        self.accent_color_btn = QPushButton("액센트 색상 변경")
        self.accent_color_btn.clicked.connect(self.pick_accent_color)
        theme_layout.addWidget(self.accent_color_btn)
        theme_group.setLayout(theme_layout)        
        main_layout.insertWidget(1, theme_group)  # Insert after font settings
        

        # V4 모델 설정 그룹
        v4_group = QGroupBox("이미지 모델 설정")
        v4_layout = QVBoxLayout()
        
        # V4 프리셋 설정
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("모델 프리셋:"))
        
        self.v4_preset = QComboBox()
        self.v4_preset.addItems(["Normal", "Artistic", "Anime"])
        current_preset = self.parent.settings.value("v4_model_preset", "Artistic")
        self.v4_preset.setCurrentText(current_preset)
        
        preset_layout.addWidget(self.v4_preset)
        v4_layout.addLayout(preset_layout)
        
        # 품질 관련 설정
        quality_layout = QVBoxLayout()
        
        self.quality_toggle = QCheckBox("품질 향상 활성화")
        self.quality_toggle.setChecked(bool(self.parent.settings.value("quality_toggle", True)))
        quality_layout.addWidget(self.quality_toggle)
        
        self.dynamic_thresholding = QCheckBox("동적 임계처리 활성화")
        self.dynamic_thresholding.setChecked(bool(self.parent.settings.value("dynamic_thresholding", False)))
        quality_layout.addWidget(self.dynamic_thresholding)
        
        # 아티팩트 제거 슬라이더
        artifacts_layout = QHBoxLayout()
        artifacts_layout.addWidget(QLabel("아티팩트 제거 강도:"))
        
        self.artifacts_slider = QSlider(Qt.Horizontal)
        self.artifacts_slider.setRange(0, 100)
        self.artifacts_slider.setValue(int(float(self.parent.settings.value("anti_artifacts", 0.0)) * 100))
        
        self.artifacts_value = QLabel(f"{float(self.parent.settings.value('anti_artifacts', 0.0)):.2f}")
        self.artifacts_slider.valueChanged.connect(self.update_artifacts_value)
        
        artifacts_layout.addWidget(self.artifacts_slider)
        artifacts_layout.addWidget(self.artifacts_value)
        
        quality_layout.addLayout(artifacts_layout)
        v4_layout.addLayout(quality_layout)
        
        v4_group.setLayout(v4_layout)
        main_layout.addWidget(v4_group)

        # 태거 모델 선택 그룹
        tagger_group = QGroupBox("태거 모델 선택")
        tagger_layout = QVBoxLayout()

        self.tagger_combo = QComboBox()
        self.tagger_combo.addItem("-- 모델 없음 --")
        self.tagger_check = QCheckBox("Tag 자동완성 활성화")
        self.tagger_check.setChecked(bool(self.parent.settings.value("will_complete_tag", True)))

        # 다운로드 가능 모델 리스트
        # list_available_models = self.parent.dtagger.get_available_models()
        
        try:
            list_available_models = self.parent.dtagger.get_available_models()
        except AttributeError:
            # Fallback: LIST_MODEL 상수를 직접 사용
            from danbooru_tagger import LIST_MODEL
            list_installed_models = [model.replace(".onnx", "") for model in self.parent.dtagger.get_installed_models()]
            list_available_models = [model for model in LIST_MODEL if model not in list_installed_models]
        
        # 설치된 모델 리스트
        list_installed_models = self.parent.dtagger.get_installed_models()
        
        if list_installed_models:
            for model in list_installed_models:
                self.tagger_combo.addItem(model + " (설치됨)")

        selected_model = self.parent.settings.value("selected_tagger_model", "")

        for i in range(self.tagger_combo.count()):
            model_name = self.tagger_combo.itemText(i).split(" (설치됨)")[0]
            if model_name == selected_model:
                self.tagger_combo.setCurrentIndex(i)
                break

        tagger_combo_layout = QHBoxLayout()
        tagger_combo_layout.addWidget(QLabel("현재 모델:"))
        tagger_combo_layout.addWidget(self.tagger_combo, 1)
        tagger_layout.addLayout(tagger_combo_layout)
        tagger_layout.addWidget(self.tagger_check)

        # 다운로드 가능한 모델 리스트
        download_label = QLabel("다운로드 가능한 모델:")
        tagger_layout.addWidget(download_label)

        download_layout = QVBoxLayout()
        for model_name in list_available_models:
            if model_name not in list_installed_models:
                model_layout = QHBoxLayout()
                model_layout.addWidget(QLabel(model_name))
                download_button = QPushButton("다운로드")
                download_button.clicked.connect(lambda ch, mn=model_name: self.parent.install_model(mn))
                model_layout.addWidget(download_button)
                download_layout.addLayout(model_layout)

        tagger_layout.addLayout(download_layout)
        tagger_group.setLayout(tagger_layout)
        main_layout.addWidget(tagger_group)

        # 파일 이름 정책 그룹
        filename_group = QGroupBox("파일 이름 정책")
        filename_layout = QVBoxLayout()

        # 저장 파일 이름에 프롬프트 포함 옵션
        self.save_with_prompt = QCheckBox("저장 파일 이름에 프롬프트 포함")
        self.save_with_prompt.setChecked(bool(self.parent.settings.value("will_savename_prompt", True)))
        filename_layout.addWidget(self.save_with_prompt)

        # img2img 이름 유지 옵션
        self.save_with_i2iname = QCheckBox("img2img 이름 유지")
        self.save_with_i2iname.setChecked(bool(self.parent.settings.value("will_savename_i2i", False)))
        filename_layout.addWidget(self.save_with_i2iname)

        filename_group.setLayout(filename_layout)
        main_layout.addWidget(filename_group)

        # 글꼴 설정 그룹
        font_group = QGroupBox("글꼴 설정")
        font_layout = QHBoxLayout()

        font_layout.addWidget(QLabel("글꼴 크기:"))
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 32)
        self.font_size_spinbox.setValue(int(self.parent.settings.value("nag_font_size", 18)))
        font_layout.addWidget(self.font_size_spinbox)
        font_layout.addStretch()

        font_group.setLayout(font_layout)
        main_layout.addWidget(font_group)

        # 저장 & 취소 버튼
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_option)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)

    def pick_accent_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.parent.settings.setValue("accent_color", color.name())
            self.parent.apply_theme()  # Refresh immediately   
    
    def update_artifacts_value(self):
        value = self.artifacts_slider.value() / 100.0
        self.artifacts_value.setText(f"{value:.2f}")

    def browse_folder(self, key):
        current_path = getattr(self, key + "_path").text()
        folder = QFileDialog.getExistingDirectory(self, "폴더 선택", current_path)
        if folder:
            getattr(self, key + "_path").setText(folder)

    def save_option(self):
        # V4 모델 설정 저장
        self.parent.settings.setValue("v4_model_preset", self.v4_preset.currentText())
        self.parent.settings.setValue("quality_toggle", self.quality_toggle.isChecked())
        self.parent.settings.setValue("dynamic_thresholding", self.dynamic_thresholding.isChecked())
        self.parent.settings.setValue("anti_artifacts", self.artifacts_slider.value() / 100.0)
        
        # 테마 설정 저장
        old_theme = self.parent.settings.value("theme_mode", "기본 테마 (System Default)")
        new_theme = self.theme_combo.currentText()
        self.parent.settings.setValue("theme_mode", new_theme)
        
        # 테마가 변경되었다면 즉시 적용
        if old_theme != new_theme:
            if "어두운" in new_theme:
                # 어두운 테마 설정
                dark_style = """
                QWidget {
                    background-color: #2D2D2D;
                    color: #FFFFFF;
                }
                QLineEdit, QTextEdit, QPlainTextEdit {
                    background-color: #404040;
                    color: #FFFFFF;
                    border: 1px solid #555555;
                }
                QComboBox, QComboBox QAbstractItemView {
                    background-color: #404040;
                    color: #FFFFFF;
                }
                QLabel, QCheckBox, QRadioButton, QGroupBox {
                    color: #FFFFFF;
                }
                """
                self.parent.app.setStyleSheet(dark_style)
                
                # 팔레트 설정
                dark_palette = QPalette()
                dark_palette.setColor(QPalette.Window, QColor("#2D2D2D"))
                dark_palette.setColor(QPalette.WindowText, QColor("#FFFFFF"))
                dark_palette.setColor(QPalette.Base, QColor("#404040"))
                dark_palette.setColor(QPalette.Text, QColor("#FFFFFF"))
                dark_palette.setColor(QPalette.Button, QColor("#353535"))
                dark_palette.setColor(QPalette.ButtonText, QColor("#FFFFFF"))
                self.parent.app.setPalette(dark_palette)
            else:
                # 밝은 테마나 기본 테마로 복원
                self.parent.app.setStyleSheet("")
                self.parent.app.setPalette(self.parent.palette)
        
        # 폴더 경로 저장
        self.parent.change_path("path_results", self.output_path.text())
        self.parent.change_path("path_settings", self.settings_path.text())
        self.parent.change_path("path_wildcards", self.wildcards_path.text())
        self.parent.change_path("path_models", self.models_path.text())

        # 태거 모델 선택 저장
        model_text = self.tagger_combo.currentText()
        selected_model = model_text.split(" (설치됨)")[0] if "(설치됨)" in model_text else ""
        if selected_model == "-- 모델 없음 --":
            selected_model = ""
        self.parent.settings.setValue("selected_tagger_model", selected_model)
        self.parent.settings.setValue("will_complete_tag", self.tagger_check.isChecked())

        # 파일 이름 정책 저장
        self.parent.settings.setValue("will_savename_prompt", self.save_with_prompt.isChecked())
        self.parent.settings.setValue("will_savename_i2i", self.save_with_i2iname.isChecked())

        # 글꼴 설정 저장
        self.parent.settings.setValue("nag_font_size", self.font_size_spinbox.value())
        self.parent.apply_theme()

        self.accept()
        
    def on_model_downloaded(self, model_name):
        # 다운로드 완료 후 모델 리스트 업데이트
        self.tagger_combo.addItem(model_name + " (설치됨)")
        self.tagger_combo.setCurrentText(model_name + " (설치됨)")
        QMessageBox.information(self, "모델 다운로드", f"{model_name} 모델이 성공적으로 다운로드되었습니다.")


class GenerateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.setWindowTitle('연속 생성 옵션')

    def setup_ui(self):
        main_layout = QVBoxLayout()

        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel('생성 횟수:'))
        self.count_edit = QLineEdit('100')
        count_layout.addWidget(self.count_edit)
        count_desc = QLabel('(-1 = 무제한)')
        count_layout.addWidget(count_desc)
        main_layout.addLayout(count_layout)

        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel('생성 간격(초):'))
        self.delay_edit = QLineEdit('3')
        delay_layout.addWidget(self.delay_edit)
        main_layout.addLayout(delay_layout)

        self.ignore_error = QCheckBox('생성 오류 무시하기')
        main_layout.addWidget(self.ignore_error)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept_and_set)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)

    def accept_and_set(self):
        self.count = self.count_edit.text()
        self.delay = self.delay_edit.text()
        self.ignore_error = self.ignore_error.isChecked()
        self.accept()


class MiniUtilDialog(QDialog):
    def __init__(self, parent=None, mode="getter"):
        super().__init__(parent)
        self.parent = parent
        self.mode = mode
        self.setup_ui()

    def setup_ui(self):
        if self.mode == "getter":
            self.setWindowTitle('이미지 정보 확인기')
            self.resize(800, 400)

            main_layout = QVBoxLayout()

            info_label = QLabel(
                "Novel AI로 생성된 이미지 파일을 드래그앤드롭 해보세요.")
            info_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(info_label)

            self.result_box = QLabel("")
            self.result_box.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(self.result_box)

            close_button = QPushButton("닫기")
            close_button.clicked.connect(self.close)
            main_layout.addWidget(close_button)

            self.setLayout(main_layout)
            self.setAcceptDrops(True)

        elif self.mode == "tagger":
            self.setWindowTitle('단부루 태거')
            self.resize(800, 400)

            main_layout = QVBoxLayout()
            
            info_label = QLabel(
                "태그를 확인할 이미지를 드래그앤드롭 해보세요. 오래 걸릴 수 있습니다.")
            info_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(info_label)

            self.result_box = QLabel("")
            self.result_box.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(self.result_box)

            close_button = QPushButton("닫기")
            close_button.clicked.connect(self.close)
            main_layout.addWidget(close_button)

            self.setLayout(main_layout)
            self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u for u in event.mimeData().urls()]

        if len(files) != 1:
            QMessageBox.information(self, '경고', "파일을 하나만 옮겨주세요.")
            return

        file_path = files[0].toLocalFile()
        if not (file_path.endswith(".png") or file_path.endswith(".webp") or file_path.endswith(".jpg")):
            QMessageBox.information(self, '경고', "이미지 파일만 가능합니다.")
            return

        if self.mode == "getter":
            try:
                self.result_box.setText("정보를 불러오는 중...")
                QApplication.processEvents()

                self.parent.get_image_info_bysrc(file_path)
                self.result_box.setText("정보를 불러왔습니다.")
            except Exception as e:
                QMessageBox.critical(
                    self, "오류", f"파일을 처리하는 중 오류가 발생했습니다:\n{str(e)}")
                self.result_box.setText("실패했습니다.")

        elif self.mode == "tagger":
            try:
                self.result_box.setText("태그 분석 중...")
                QApplication.processEvents()

                result = self.parent.predict_tag_from("src", file_path, True)
                self.result_box.setText(result if result else "태그를 찾을 수 없습니다.")
            except Exception as e:
                QMessageBox.critical(
                    self, "오류", f"파일을 처리하는 중 오류가 발생했습니다:\n{str(e)}")
                self.result_box.setText("실패했습니다.")


class FileIODialog(QDialog):
    def __init__(self, message, function):
        super().__init__()
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.message = message
        self.function = function
        self.result = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("처리 중...")
        self.resize(300, 100)

        layout = QVBoxLayout()
        self.label = QLabel(self.message)
        layout.addWidget(self.label)

        self.setLayout(layout)

    def showEvent(self, event):
        super().showEvent(event)
        self.thread = WorkerThread(self.function)
        self.thread.finished.connect(self.on_finished)
        self.thread.start()

    def on_finished(self):
        self.result = self.thread.result
        self.accept()


class LoginThread(QThread):
    login_result = pyqtSignal(int)

    def __init__(self, parent, nai, username, password):
        super(LoginThread, self).__init__(parent)
        self.nai = nai
        self.username = username
        self.password = password
        self.auto_login = parent.settings.value("auto_login", False)

    def run(self):
        is_login_success = self.nai.try_login(self.username, self.password)

        if is_login_success:
            self.parent().set_auto_login(self.auto_login)
            self.login_result.emit(0)  # 성공
        else:
            self.login_result.emit(1)  # 실패


class WorkerThread(QThread):
    def __init__(self, function):
        super(WorkerThread, self).__init__()
        self.function = function
        self.result = None

    def run(self):
        self.result = self.function()