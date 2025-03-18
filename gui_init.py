from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QLabel, QLineEdit, QPushButton, QPlainTextEdit, 
                             QTextBrowser, QComboBox, QSplitter, QCheckBox, 
                             QRadioButton, QButtonGroup, QSizePolicy, QMessageBox, 
                             QFileDialog, QApplication, QCompleter)
from PyQt5.QtCore import Qt, pyqtSignal  # pyqtSignal 추가
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QMouseEvent, QBrush, QPalette
from consts import RESOLUTION_FAMILIY
from completer import CompletionTextEdit
from character_prompts_ui import CharacterPromptsContainer
import random
import os

def init_main_widget(parent):
    # 메인 위젯 초기화
    widget = QWidget()
    main_layout = QVBoxLayout()
    widget.setLayout(main_layout)

    # UI 사전 초기화
    parent.dict_ui_settings = {}
    
    # 스플리터 생성 (한 번만 초기화)
    parent.main_splitter = QSplitter(Qt.Horizontal)
    
    # 1: 왼쪽 레이아웃 - 설정
    left_widget = QWidget()
    left_layout = QVBoxLayout()
    left_widget.setLayout(left_layout)

    # 1.1: 프롬프트 입력 그룹
    prompt_group = QGroupBox("Text")
    prompt_layout = QVBoxLayout()
    prompt_group.setLayout(prompt_layout)

    # 프롬프트 입력
    prompt_layout.addWidget(QLabel("프롬프트(Prompt):"))
    parent.dict_ui_settings["prompt"] = CompletionTextEdit()  # 변경
    prompt_layout.addWidget(parent.dict_ui_settings["prompt"])

    # 네거티브 프롬프트 입력
    prompt_layout.addWidget(QLabel("네거티브 프롬프트(Negative Prompt):"))
    parent.dict_ui_settings["negative_prompt"] = CompletionTextEdit()  # 변경
    prompt_layout.addWidget(parent.dict_ui_settings["negative_prompt"])

    left_layout.addWidget(prompt_group)

    # 캐릭터 프롬프트 그룹
    character_prompts_group = QGroupBox("Character Prompts (V4)")
    character_prompts_layout = QVBoxLayout()
    character_prompts_group.setLayout(character_prompts_layout)
    
    parent.character_prompts_container = CharacterPromptsContainer(parent)
    character_prompts_layout.addWidget(parent.character_prompts_container)

    left_layout.addWidget(character_prompts_group)

    # 이미지 옵션과 고급 설정을 수평으로 배치할 컨테이너
    img_advanced_container = QHBoxLayout()

    # 1.2: 이미지 옵션 그룹
    img_option_group = QGroupBox("Image Options")
    img_option_layout = QVBoxLayout()
    img_option_group.setLayout(img_option_layout)

    # 이미지 크기 설정
    hbox_size = QHBoxLayout()
    combo_resolution = QComboBox()
    parent.combo_resolution = combo_resolution

    # 그룹 제목과 해상도 추가
    # Normal 그룹
    combo_resolution.addItem("--- Normal ---")
    combo_resolution.setItemData(0, 0, Qt.UserRole - 1)  # 선택 불가능하게 설정
    
    for resolution in RESOLUTION_FAMILIY[0]:
        combo_resolution.addItem(resolution)
    
    # Large 그룹
    combo_resolution.addItem("--- Large ---")
    large_idx = combo_resolution.count() - 1
    combo_resolution.setItemData(large_idx, 0, Qt.UserRole - 1)  # 선택 불가능하게 설정
    
    for resolution in RESOLUTION_FAMILIY[1]:
        combo_resolution.addItem(resolution)
    
    # Wallpaper 그룹
    combo_resolution.addItem("--- Wallpaper ---")
    wallpaper_idx = combo_resolution.count() - 1
    combo_resolution.setItemData(wallpaper_idx, 0, Qt.UserRole - 1)  # 선택 불가능하게 설정
    
    for resolution in RESOLUTION_FAMILIY[2]:
        combo_resolution.addItem(resolution)
    
    # Low Resolution 그룹
    combo_resolution.addItem("--- Low Resolution ---")
    low_res_idx = combo_resolution.count() - 1
    combo_resolution.setItemData(low_res_idx, 0, Qt.UserRole - 1)  # 선택 불가능하게 설정
    
    for resolution in RESOLUTION_FAMILIY[3]:
        combo_resolution.addItem(resolution)
    
    combo_resolution.addItem("Custom (직접 입력)")
    
    # 1.3: 고급 설정 그룹
    advanced_group = QGroupBox("Advanced")
    advanced_layout = QVBoxLayout()
    advanced_group.setLayout(advanced_layout)
    
    # Square (1024x1024) 항목을 기본으로 선택
    hd_index = -1
    for i in range(combo_resolution.count()):
        if "Square (1024x1024)" in combo_resolution.itemText(i):
            hd_index = i
            break
    
    if hd_index >= 0:
        combo_resolution.setCurrentIndex(hd_index)
    
    hbox_size.addWidget(QLabel("Size:"))
    hbox_size.addWidget(combo_resolution, 1)

    # 직접 입력 필드
    hbox_custom_size = QHBoxLayout()
    hbox_custom_size.addWidget(QLabel("W:"))
    parent.dict_ui_settings["width"] = QLineEdit()
    parent.dict_ui_settings["width"].setAlignment(Qt.AlignRight)
    hbox_custom_size.addWidget(parent.dict_ui_settings["width"])

    hbox_custom_size.addWidget(QLabel("H:"))
    parent.dict_ui_settings["height"] = QLineEdit()
    parent.dict_ui_settings["height"].setAlignment(Qt.AlignRight)
    hbox_custom_size.addWidget(parent.dict_ui_settings["height"])

    # 크기 랜덤 체크박스
    parent.checkbox_random_resolution = QCheckBox("랜덤 (Random)")
    parent.checkbox_random_resolution.stateChanged.connect(
        parent.on_random_resolution_checked)
    if parent.settings.value("image_random_checkbox", False):
        parent.checkbox_random_resolution.setChecked(True)
    hbox_custom_size.addWidget(parent.checkbox_random_resolution)

    img_option_layout.addLayout(hbox_size)
    img_option_layout.addLayout(hbox_custom_size)

    # 샘플러 설정
    hbox_sampler = QHBoxLayout()
    hbox_sampler.addWidget(QLabel("Sampler:"))
    parent.dict_ui_settings["sampler"] = QComboBox()
    parent.dict_ui_settings["sampler"].addItems(["k_euler", "k_euler_ancestral",
                                                "k_dpmpp_2s_ancestral", "k_dpmpp_2m", "k_dpmpp_sde", "ddim_v3"])
    hbox_sampler.addWidget(parent.dict_ui_settings["sampler"])
    img_option_layout.addLayout(hbox_sampler)

    # 스텝 설정
    hbox_steps = QHBoxLayout()
    hbox_steps.addWidget(QLabel("Steps:"))
    parent.dict_ui_settings["steps"] = QLineEdit()
    parent.dict_ui_settings["steps"].setAlignment(Qt.AlignRight)
    hbox_steps.addWidget(parent.dict_ui_settings["steps"])
    img_option_layout.addLayout(hbox_steps)

    # 시드 설정
    hbox_seed = QHBoxLayout()
    hbox_seed.addWidget(QLabel("Seed:"))
    parent.dict_ui_settings["seed"] = QLineEdit()
    parent.dict_ui_settings["seed"].setAlignment(Qt.AlignRight)
    hbox_seed.addWidget(parent.dict_ui_settings["seed"])
    parent.dict_ui_settings["seed_fix_checkbox"] = QCheckBox("고정 (Fix)")
    hbox_seed.addWidget(parent.dict_ui_settings["seed_fix_checkbox"])
    seed_random_button = QPushButton("랜덤 (Random)")
    seed_random_button.clicked.connect(
        lambda: parent.dict_ui_settings["seed"].setText(str(random.randint(0, 2**32-1))))
    hbox_seed.addWidget(seed_random_button)
    img_option_layout.addLayout(hbox_seed)

    # 레이아웃 여백과 간격 조정
    img_option_layout.setContentsMargins(5, 5, 5, 5)
    img_option_layout.setSpacing(3)
    advanced_layout.setContentsMargins(5, 5, 5, 5)
    advanced_layout.setSpacing(3)
    
    img_advanced_container.addWidget(img_option_group)

    # Scale 설정
    hbox_scale = QHBoxLayout()
    hbox_scale.addWidget(QLabel("CFG Scale:"))
    parent.dict_ui_settings["scale"] = QLineEdit()
    parent.dict_ui_settings["scale"].setAlignment(Qt.AlignRight)
    hbox_scale.addWidget(parent.dict_ui_settings["scale"])
    advanced_layout.addLayout(hbox_scale)

    # CFG Rescale 설정
    hbox_cfgrescale = QHBoxLayout()
    hbox_cfgrescale.addWidget(QLabel("CFG Rescale:"))
    parent.dict_ui_settings["cfg_rescale"] = QLineEdit()
    parent.dict_ui_settings["cfg_rescale"].setAlignment(Qt.AlignRight)
    hbox_cfgrescale.addWidget(parent.dict_ui_settings["cfg_rescale"])
    advanced_layout.addLayout(hbox_cfgrescale)
    
    # Auto SMEA 설정 (V4의 스마팅)
    hbox_smea = QHBoxLayout()
    parent.dict_ui_settings["autoSmea"] = QCheckBox("Auto SMEA (스마팅)")
    hbox_smea.addWidget(parent.dict_ui_settings["autoSmea"])
    advanced_layout.addLayout(hbox_smea)

    # Uncond Scale 설정
    #hbox_uncondscale = QHBoxLayout()
    #hbox_uncondscale.addWidget(QLabel("Uncond Scale:"))
    
    # 안쓰는 uncond_scale 주석처리
    #parent.dict_ui_settings["uncond_scale"] = QLineEdit()
    #parent.dict_ui_settings["uncond_scale"].setAlignment(Qt.AlignRight)
    #hbox_uncondscale.addWidget(parent.dict_ui_settings["uncond_scale"])
    
    #hbox_uncondscale.addWidget(QLabel("* 100"))
    #advanced_layout.addLayout(hbox_uncondscale)

    img_advanced_container.addWidget(advanced_group)
    
    # 좌우 균형 조정
    img_option_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    advanced_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    # 레이아웃 여백과 간격 조정
    img_option_layout.setContentsMargins(5, 5, 5, 5)
    img_option_layout.setSpacing(3)
    advanced_layout.setContentsMargins(5, 5, 5, 5)
    advanced_layout.setSpacing(3)
    
    # 좌우 균형 조정
    img_option_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    advanced_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    
    left_layout.addLayout(img_advanced_container)
        

    # 1.4: 이미지 옵션 (img2img, reference) 그룹
    image_options_group = QGroupBox("Image References")
    image_options_layout = QHBoxLayout()
    image_options_group.setLayout(image_options_layout)
    parent.image_options_layout = image_options_layout

    # img2img 옵션
    parent.i2i_settings_group = ImageToImageWidget("img2img", parent)
    image_options_layout.addWidget(parent.i2i_settings_group)

    # Reference Image 옵션
    parent.vibe_settings_group = ImageToImageWidget("vibe", parent)
    image_options_layout.addWidget(parent.vibe_settings_group)

    # img2img 전용 설정
    parent.i2i_settings = QGroupBox("img2img Settings")
    i2i_settings_layout = QVBoxLayout()
    parent.i2i_settings.setLayout(i2i_settings_layout)

    # strength, noise 설정
    hbox_strength = QHBoxLayout()
    hbox_strength.addWidget(QLabel("Strength:"))
    parent.dict_ui_settings["strength"] = QLineEdit()
    parent.dict_ui_settings["strength"].setAlignment(Qt.AlignRight)
    hbox_strength.addWidget(parent.dict_ui_settings["strength"])
    i2i_settings_layout.addLayout(hbox_strength)

    hbox_noise = QHBoxLayout()
    hbox_noise.addWidget(QLabel("Noise:"))
    parent.dict_ui_settings["noise"] = QLineEdit()
    parent.dict_ui_settings["noise"].setAlignment(Qt.AlignRight)
    hbox_noise.addWidget(parent.dict_ui_settings["noise"])
    i2i_settings_layout.addLayout(hbox_noise)

    image_options_layout.addWidget(parent.i2i_settings)
    parent.i2i_settings.setVisible(False)

    # Reference Image 전용 설정
    parent.vibe_settings = QGroupBox("References Settings")
    vibe_settings_layout = QVBoxLayout()
    parent.vibe_settings.setLayout(vibe_settings_layout)

    # reference image 관련 설정들
    hbox_reference_information_extracted = QHBoxLayout()
    hbox_reference_information_extracted.addWidget(
        QLabel("Reference Information Extracted:"))
    parent.dict_ui_settings["reference_information_extracted"] = QLineEdit()
    parent.dict_ui_settings["reference_information_extracted"].setAlignment(
        Qt.AlignRight)
    hbox_reference_information_extracted.addWidget(
        parent.dict_ui_settings["reference_information_extracted"])
    vibe_settings_layout.addLayout(hbox_reference_information_extracted)

    hbox_reference_strength = QHBoxLayout()
    hbox_reference_strength.addWidget(QLabel("Reference Strength:"))
    parent.dict_ui_settings["reference_strength"] = QLineEdit()
    parent.dict_ui_settings["reference_strength"].setAlignment(Qt.AlignRight)
    hbox_reference_strength.addWidget(parent.dict_ui_settings["reference_strength"])
    vibe_settings_layout.addLayout(hbox_reference_strength)

    image_options_layout.addWidget(parent.vibe_settings)
    parent.vibe_settings.setVisible(False)

    left_layout.addWidget(image_options_group)

    # 1.5: 버튼 레이아웃
    button_layout = QHBoxLayout()

    # 로그인 상태
    parent.label_loginstate = LoginStateWidget()
    button_layout.addWidget(parent.label_loginstate)

    # ANLAS 표시
    parent.label_anlas = QLabel("Anlas: ?")
    button_layout.addWidget(parent.label_anlas)

    button_layout.addStretch()

    # 생성 버튼들
    parent.button_generate_once = QPushButton("1회 생성 (Generate Once)")
    parent.button_generate_once.clicked.connect(parent.on_click_generate_once)
    button_layout.addWidget(parent.button_generate_once)

    parent.button_generate_sett = QPushButton("세팅별 연속 생성")
    parent.button_generate_sett.clicked.connect(parent.on_click_generate_sett)
    button_layout.addWidget(parent.button_generate_sett)

    parent.button_generate_auto = QPushButton("연속 생성 (Auto)")
    parent.button_generate_auto.clicked.connect(parent.on_click_generate_auto)
    button_layout.addWidget(parent.button_generate_auto)

    left_layout.addLayout(button_layout)

    # 2: 오른쪽 레이아웃 - 결과
    right_widget = QWidget()
    right_layout = QVBoxLayout()
    right_widget.setLayout(right_layout)

    # 2.1: 결과 이미지 그룹
    result_image_group = QGroupBox("결과 이미지 (Result Image)")
    result_image_layout = QVBoxLayout()
    result_image_group.setLayout(result_image_layout)

    # 이미지 보기
    parent.image_result = ImageResultWidget()
    result_image_layout.addWidget(parent.image_result)

    # 이미지 저장 버튼
    hbox_image_buttons = QHBoxLayout()
    button_save_image = QPushButton("이미지 저장 (Save Image)")
    button_save_image.clicked.connect(lambda: parent.image_result.save_image())
    hbox_image_buttons.addWidget(button_save_image)
    
    result_image_layout.addLayout(hbox_image_buttons)
    right_layout.addWidget(result_image_group)

    # 2.2: 결과 프롬프트 그룹
    result_prompt_group = QGroupBox("결과 프롬프트 (Result Prompt)")
    result_prompt_layout = QVBoxLayout()
    result_prompt_group.setLayout(result_prompt_layout)

    parent.prompt_result = QTextBrowser()
    result_prompt_layout.addWidget(parent.prompt_result)

    right_layout.addWidget(result_prompt_group)

    # 스플리터에 좌우 레이아웃 추가
    parent.main_splitter.addWidget(left_widget)
    parent.main_splitter.addWidget(right_widget)

    # 메인 레이아웃에 스플리터 추가
    main_layout.addWidget(parent.main_splitter)
    
    # 패널 접기/펼치기 버튼을 맨 아래에 배치
    expand_layout = QHBoxLayout()
    expand_layout.addStretch()  # 왼쪽 공간 확보
    
    # 버튼 생성 및 스타일 설정
    parent.button_expand = QPushButton("<>" if parent.is_expand else ">|<")
    parent.button_expand.setFixedWidth(50)
    parent.button_expand.setStyleSheet("""
        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 4px;
            font-weight: bold;
            min-width: 60px;
        }
        QPushButton:hover {
            background-color: #e0e0e0;
        }
        QPushButton:pressed {
            background-color: #d0d0d0;
        }
    """)
    parent.button_expand.clicked.connect(parent.on_click_expand)
    parent.button_expand.setToolTip("결과 패널 확장/축소")
    
    expand_layout.addWidget(parent.button_expand)
    expand_layout.addStretch()  # 오른쪽 공간 확보
    
    # 하단 레이아웃을 메인 레이아웃에 추가
    main_layout.addLayout(expand_layout)

    # 이벤트 연결
    combo_resolution.currentIndexChanged.connect(lambda idx: set_resolution(parent, idx))
    parent.i2i_settings_group.is_active_changed.connect(lambda is_active: parent.i2i_settings.setVisible(is_active))
    parent.vibe_settings_group.is_active_changed.connect(lambda is_active: parent.vibe_settings.setVisible(is_active))

    return widget

# gui_init.py 파일에 아래 함수 추가
def show_custom_message(parent, title, message, icon_type=None):
    """
    시스템 기본 스타일의 메시지 대화상자를 표시합니다.
    """
    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
    from PyQt5.QtGui import QIcon
    from PyQt5.QtCore import Qt
    
    # 커스텀 대화상자 생성
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
    dialog.setFixedWidth(400)
    
    # 명시적으로 모든 스타일 제거
    dialog.setStyleSheet("""
        QDialog {
            background-color: #F0F0F0;
        }
        QLabel {
            color: #000000;
            background-color: transparent;
        }
        QPushButton {
            background-color: #E0E0E0;
            color: #000000;
            padding: 6px 12px;
            border: 1px solid #CCCCCC;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #D0D0D0;
        }
    """)
    
    # 레이아웃 설정
    layout = QVBoxLayout(dialog)
    
    # 아이콘과 메시지 영역
    msg_layout = QHBoxLayout()
    
    # 아이콘 설정
    if icon_type:
        icon_label = QLabel()
        icon = QIcon.fromTheme("dialog-information")
        if icon_type == "warning":
            icon = QIcon.fromTheme("dialog-warning")
        elif icon_type == "error":
            icon = QIcon.fromTheme("dialog-error")
            
        icon_label.setPixmap(icon.pixmap(32, 32))
        icon_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        msg_layout.addWidget(icon_label)
    
    # 메시지 텍스트
    msg_label = QLabel(message)
    msg_label.setWordWrap(True)
    msg_layout.addWidget(msg_label, 1)
    
    layout.addLayout(msg_layout)
    
    # 버튼 영역
    btn_layout = QHBoxLayout()
    btn_layout.addStretch()
    
    ok_button = QPushButton("확인")
    ok_button.setAutoDefault(True)
    ok_button.setDefault(True)
    ok_button.clicked.connect(dialog.accept)
    btn_layout.addWidget(ok_button)
    
    layout.addLayout(btn_layout)
    
    dialog.exec_()

def set_resolution(parent, idx):
    if idx < 0:
        return

    text = parent.combo_resolution.currentText()
    if text == "Custom (직접 입력)":
        return

    try:
        res_text = text.split("(")[1].split(")")[0]
        width, height = res_text.split("x")

        parent.dict_ui_settings["width"].setText(width)
        parent.dict_ui_settings["height"].setText(height)
    except Exception as e:
        print(e)


class LoginStateWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.state_label = QLabel("로그인 필요")
        self.state_label.setStyleSheet("color:red;")
        layout.addWidget(self.state_label)
        self.setLayout(layout)

    def set_logged_in(self, is_logged_in):
        if is_logged_in:
            self.state_label.setText("로그인 됨")
            self.state_label.setStyleSheet("color:green;")
        else:
            self.state_label.setText("로그인 필요")
            self.state_label.setStyleSheet("color:red;")


class ImageToImageWidget(QGroupBox):
    is_active_changed = pyqtSignal(bool)

    def __init__(self, mode, parent):
        title = "이미지 to 이미지" if mode == "img2img" else "레퍼런스 이미지"
        super().__init__(title)
        self.parent = parent
        self.mode = mode
        self.src = None

        self.setMinimumHeight(150)
        self.mask = None
        self.init_ui()

        self.is_maskmode = False
        self.is_randompick = False
        self.random_index = -1

    def init_ui(self):
        layout = QVBoxLayout()

        # 이미지 부분
        self.image_label = QLabel("업로드된 이미지 없음")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setStyleSheet("background-color: rgba(0, 0, 0, 128);")
        layout.addWidget(self.image_label)

        # 버튼 부분
        button_layout = QHBoxLayout()

        # 왼쪽 버튼 부분
        left_button_layout = QHBoxLayout()

        self.upload_button = QPushButton("불러오기")
        self.upload_button.clicked.connect(
            lambda: self.parent.show_file_dialog(self.mode))
        left_button_layout.addWidget(self.upload_button)

        self.open_folder_button = QPushButton("폴더")
        self.open_folder_button.clicked.connect(
            lambda: self.parent.show_openfolder_dialog(self.mode))
        left_button_layout.addWidget(self.open_folder_button)

        button_layout.addLayout(left_button_layout)

        # 체크박스 부분
        check_layout = QHBoxLayout()
        if self.mode == "img2img":
            self.mask_checkbox = QCheckBox("마스크 그리기")
            self.mask_checkbox.stateChanged.connect(self.on_mask_checked)
            check_layout.addWidget(self.mask_checkbox)

        self.tagcheck_checkbox = QCheckBox("태그 읽기")
        self.tagcheck_checkbox.stateChanged.connect(
            lambda: self.parent.on_click_tagcheckbox(self.mode))
        check_layout.addWidget(self.tagcheck_checkbox)

        button_layout.addLayout(check_layout)

        # 오른쪽 버튼 부분
        self.remove_button = QPushButton("제거")
        self.remove_button.clicked.connect(self.on_click_removebutton)
        button_layout.addWidget(self.remove_button)

        layout.addLayout(button_layout)

        # 폴더 모드 UI
        self.folder_widget = QWidget()
        folder_layout = QHBoxLayout()
        folder_layout.setContentsMargins(0, 0, 0, 0)
        
        self.prev_button = QPushButton("이전")
        self.prev_button.clicked.connect(self.on_click_prev)
        folder_layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("다음")
        self.next_button.clicked.connect(self.on_click_next)
        folder_layout.addWidget(self.next_button)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["오름차순", "내림차순", "랜덤"])
        folder_layout.addWidget(self.sort_combo)
        
        self.folder_widget.setLayout(folder_layout)
        layout.addWidget(self.folder_widget)
        self.folder_widget.setVisible(False)
        
        self.setLayout(layout)

    def get_folder_sort_mode(self):
        return self.sort_combo.currentText()

    def set_folder_mode(self, is_folder_mode):
        self.folder_widget.setVisible(is_folder_mode)

    def set_image(self, src):
        self.src = src
        if src:
            pixmap = QPixmap(src)
            scaled_pixmap = pixmap.scaledToHeight(
                128, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("업로드된 이미지 없음")
            self.image_label.setPixmap(QPixmap())

        self.is_active_changed.emit(bool(src))

    def on_click_removebutton(self):
        self.src = None
        self.mask = None
        self.is_maskmode = False
        if hasattr(self, 'mask_checkbox'):
            self.mask_checkbox.setChecked(False)
        self.image_label.setText("업로드된 이미지 없음")
        self.image_label.setPixmap(QPixmap())
        self.image_label.setCursor(Qt.ArrowCursor)
        self.is_active_changed.emit(False)

    def on_mask_checked(self, state):
        self.is_maskmode = (state == Qt.Checked)
        if self.is_maskmode:
            if self.src:
                self.mask = QImage(QPixmap(self.src).toImage().size(), QImage.Format_ARGB32)
                self.mask.fill(Qt.black)
                self.image_label.setCursor(Qt.CrossCursor)
                self.image_label.mousePressEvent = self.mousePressEvent
                self.image_label.mouseMoveEvent = self.mouseMoveEvent
                self.image_label.mouseReleaseEvent = self.mouseReleaseEvent
                self.mousePressPos = None
        else:
            self.mask = None
            self.image_label.setCursor(Qt.ArrowCursor)
            self.image_label.mousePressEvent = None
            self.image_label.mouseMoveEvent = None
            self.image_label.mouseReleaseEvent = None

    def on_click_prev(self):
        if self.mode == "img2img":
            self.parent.dict_img_batch_target["img2img_index"] -= 2
            self.parent.proceed_image_batch("img2img")
        else:
            self.parent.dict_img_batch_target["vibe_index"] -= 2
            self.parent.proceed_image_batch("vibe")

    def on_click_next(self):
        if self.mode == "img2img":
            self.parent.proceed_image_batch("img2img")
        else:
            self.parent.proceed_image_batch("vibe")

    def mousePressEvent(self, event: QMouseEvent):
        if not self.is_maskmode or not self.src:
            return
        self.mousePressPos = event.pos()
        self.drawMask(event.pos())

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.is_maskmode or not self.mousePressPos:
            return
        self.drawMask(event.pos())

    def mouseReleaseEvent(self, event: QMouseEvent):
        if not self.is_maskmode:
            return
        self.mousePressPos = None

    def drawMask(self, pos):
        if not self.mask:
            return

        # 원본 이미지 크기와 라벨 크기 비율 계산
        pixmap = QPixmap(self.src)
        img_w, img_h = pixmap.width(), pixmap.height()
        label_w, label_h = self.image_label.width(), self.image_label.height()

        # 이미지가 라벨 내 어떻게 스케일되는지 계산
        ratio = min(label_w / img_w, label_h / img_h)
        scaled_w, scaled_h = img_w * ratio, img_h * ratio

        # 라벨 내 이미지 위치 계산
        offset_x = (label_w - scaled_w) / 2
        offset_y = (label_h - scaled_h) / 2

        # 라벨 좌표를 이미지 좌표로 변환
        x = (pos.x() - offset_x) / ratio if ratio > 0 else 0
        y = (pos.y() - offset_y) / ratio if ratio > 0 else 0

        if 0 <= x < img_w and 0 <= y < img_h:
            # 마스크에 그리기
            painter = QPainter(self.mask)
            painter.setPen(QPen(Qt.white, 10, Qt.SolidLine, Qt.RoundCap))
            
            if self.mousePressPos:
                prev_x = (self.mousePressPos.x() - offset_x) / ratio
                prev_y = (self.mousePressPos.y() - offset_y) / ratio
                painter.drawLine(prev_x, prev_y, x, y)
            else:
                painter.drawPoint(x, y)
            
            painter.end()
            self.mousePressPos = pos

            # 마스크 오버레이와 함께 이미지 표시
            self.updateMaskOverlay()

    def updateMaskOverlay(self):
        if not self.src or not self.mask:
            return

        pixmap = QPixmap(self.src)
        overlay = QImage(pixmap.size(), QImage.Format_ARGB32)
        overlay.fill(Qt.transparent)

        # 마스크를 반투명 빨간색 오버레이로 변환
        for y in range(self.mask.height()):
            for x in range(self.mask.width()):
                if self.mask.pixelColor(x, y).value() > 0:  # 마스크에 그려진 부분
                    overlay.setPixelColor(x, y, QColor(255, 0, 0, 128))

        # 원본 이미지와 오버레이 합성
        result = QPixmap(pixmap.size())
        result.fill(Qt.transparent)

        painter = QPainter(result)
        painter.drawPixmap(0, 0, pixmap)
        painter.drawImage(0, 0, overlay)
        painter.end()

        # 결과 표시
        scaled_pixmap = result.scaledToHeight(128, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)


class ImageResultWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(512, 512)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 128);")
        self.setText("결과 이미지가 없습니다")
        self.image_path = None
        self.original_image_data = None  # 원본 이미지 데이터 저장 변수

    def set_custom_pixmap(self, src):
        self.image_path = src
        self.original_image_data = None  # 초기화

        try:
            if isinstance(src, str):
                pixmap = QPixmap(src)
                if not pixmap.isNull():
                    # 원본 이미지 데이터 저장
                    with open(src, 'rb') as f:
                        self.original_image_data = f.read()
                    self.setPixmap(pixmap.scaled(
                        self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    self.setText("이미지 로드 실패")
                    self.image_path = None
            else:
                # 바이트 데이터인 경우
                self.original_image_data = src  # 원본 이미지 데이터 저장
                image = QImage()
                image.loadFromData(src)
                pixmap = QPixmap.fromImage(image)
                if not pixmap.isNull():
                    self.setPixmap(pixmap.scaled(
                        self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    self.setText("이미지 로드 실패")
                    self.image_path = None
                    self.original_image_data = None
        except Exception as e:
            print(e)
            self.setText("이미지 로드 오류: " + str(e))
            self.image_path = None
            self.original_image_data = None

    def refresh_size(self):
        if not self.image_path and not self.original_image_data:
            return  # 이미지가 없으면 아무 작업도 하지 않음
            
        try:
            if isinstance(self.image_path, str) and os.path.isfile(self.image_path):
                # 파일 경로가 있는 경우
                pixmap = QPixmap(self.image_path)
                if not pixmap.isNull():
                    self.setPixmap(pixmap.scaled(
                        self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            elif self.original_image_data:
                # 저장된 원본 데이터가 있는 경우
                image = QImage()
                image.loadFromData(self.original_image_data)
                pixmap = QPixmap.fromImage(image)
                if not pixmap.isNull():
                    self.setPixmap(pixmap.scaled(
                        self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            print(f"Error refreshing image size: {e}")

    def save_image(self):
        """이미지 저장 기능"""
        if not self.image_path and not self.original_image_data:
            show_custom_message(self, "경고", "저장할 이미지가 없습니다.", "warning")
            return
            
        # 파일 저장 대화상자 열기
        from datetime import datetime
        default_name = f"nai_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filename, _ = QFileDialog.getSaveFileName(
            self, "이미지 저장", default_name, "Images (*.png *.jpg *.jpeg)"
        )
        
        if filename:
            # 이미지 저장
            try:
                if self.image_path and os.path.isfile(self.image_path):
                    # 파일 경로가 있는 경우, 해당 파일을 복사
                    import shutil
                    shutil.copy2(self.image_path, filename)
                elif self.original_image_data:
                    # 원본 이미지 데이터가 있는 경우
                    from PIL import Image
                    import io
                    if isinstance(self.original_image_data, bytes):
                        # 바이트 데이터인 경우
                        img = Image.open(io.BytesIO(self.original_image_data))
                        img.save(filename)
                    else:
                        # pixmap에서 이미지 저장
                        pixmap = self.pixmap()
                        if pixmap and not pixmap.isNull():
                            pixmap.save(filename)
                
                # 성공 메시지 표시
                show_custom_message(self, "정보", f"이미지가 성공적으로 저장되었습니다.\n{filename}")
            except Exception as e:
                # 오류 메시지 표시
                show_custom_message(self, "오류", f"이미지 저장 중 오류가 발생했습니다.\n{str(e)}", "error")
    

class CompletePlainTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.completion_prefix = ""
        self.tag_list = []
        self.is_complete_mode = False
        self.current_completions = []
        self.selected_index = -1

    #def start_complete_mode(self, tag_list):
        """자동 완성 모드 시작"""
        from completer import CustomCompleter
        self.completer = CustomCompleter(tag_list)
        self.is_complete_mode = True
        self.setCompleter(self.completer)
        print(f"자동 완성 모드 시작: {len(tag_list)}개 태그")

    #def setCompleter(self, completer):
        """자동 완성기 설정"""
        if self.completer:
            self.completer.activated.disconnect(self.insertCompletion)
        self.completer = completer
        if not self.completer:
            return
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated.connect(self.insertCompletion)

    #def insertCompletion(self, completion):
        """자동 완성 텍스트 삽입"""
        if self.completer.widget() != self:
            return
        
        tc = self.textCursor()
        extra = len(completion) - len(self.completer.completionPrefix())
        tc.movePosition(QTextCursor.Left)
        tc.movePosition(QTextCursor.EndOfWord)
        tc.insertText(completion[-extra:])
        self.setTextCursor(tc)

    #def get_word_under_cursor(self):
        """커서 아래 단어 가져오기"""
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        return tc.selectedText()
    
    
    #def get_word_under_cursor(self):
        cursor = self.textCursor()
        cursor.select(cursor.WordUnderCursor)
        return cursor.selectedText()

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if not self.is_complete_mode:
            return
            
        # 자동 완성 기능 처리
        ctrlOrShift = event.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)
        if ctrlOrShift and event.text() == '':
            return

        # Enter, Return, Escape, Tab 등의 키는 무시
        if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
            if self.completer and self.completer.popup().isVisible():
                event.ignore()
                return

        # 특수 문자 처리
        eow = "~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-="
        hasModifier = (event.modifiers() != Qt.NoModifier) and not ctrlOrShift
        
        # 자동 완성 조건 체크
        if (not self.completer or 
            (hasModifier and event.text() == '') or 
            (not event.text()) or 
            (len(self.get_word_under_cursor()) < 1) or 
            (event.text()[-1] in eow)):
            if self.completer:
                self.completer.popup().hide()
            return

        # 자동 완성 팝업 표시
        completionPrefix = self.get_word_under_cursor()
        
        if completionPrefix != self.completion_prefix:
            self.completion_prefix = completionPrefix
            if self.completer:
                self.completer.setCompletionPrefix(completionPrefix)
                self.completer.popup().setCurrentIndex(
                    self.completer.completionModel().index(0, 0))
                
                cr = self.cursorRect()
                cr.setWidth(self.completer.popup().sizeHintForColumn(0) + 
                            self.completer.popup().verticalScrollBar().sizeHint().width())
                self.completer.complete(cr)