import json
import sys
import os
import io
import zipfile
import time
import datetime
import random
import base64
import requests
from io import BytesIO
from PIL import Image
from urllib import request

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                            QPushButton, QPlainTextEdit, QScrollArea, QFrame, 
                            QGridLayout, QDialog, QCheckBox, QButtonGroup, QSizePolicy,
                            QMainWindow, QAction, QFileDialog, QMessageBox, QApplication)
from PyQt5.QtCore import (Qt, pyqtSignal, QObject, QTimer, QSettings, QPoint, QSize, 
                          QCoreApplication, QThread)
from PyQt5.QtGui import QColor, QPalette, QFont

from gui_init import init_main_widget
from gui_dialog import LoginDialog, OptionDialog, GenerateDialog, MiniUtilDialog, FileIODialog

from consts import COLOR, S, DEFAULT_PARAMS, DEFAULT_PATH, RESOLUTION_FAMILIY_MASK, RESOLUTION_FAMILIY, prettify_naidict, DEFAULT_TAGCOMPLETION_PATH

import naiinfo_getter
from nai_generator import NAIGenerator, NAIAction
from wildcard_applier import WildcardApplier
from danbooru_tagger import DanbooruTagger


TITLE_NAME = "NAI Auto Generator V4"
TOP_NAME = "dcp_arca"
APP_NAME = "nag_gui"

MAX_COUNT_FOR_WHILE = 10

#############################################

def resource_path(relative_path):
    """실행 파일 또는 Python 스크립트에서 리소스 경로 가져오기"""
    try:
        # PyInstaller 번들 실행 시
        base_path = sys._MEIPASS
    except Exception:
        # 일반 Python 실행 시
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 디버깅용 로그 추가
print(f"Current directory: {os.getcwd()}")
print(f"MEIPASS exists: {'sys._MEIPASS' in dir(sys)}")
if 'sys._MEIPASS' in dir(sys):
    print(f"MEIPASS path: {sys._MEIPASS}")
    
    
def create_folder_if_not_exists(foldersrc):
    if not os.path.exists(foldersrc):
        os.makedirs(foldersrc)


def prettify_dict(d):
    return json.dumps(d, sort_keys=True, indent=4)


def get_imgcount_from_foldersrc(foldersrc):
    return len([file for file in os.listdir(foldersrc) if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))])


def pick_imgsrc_from_foldersrc(foldersrc, index, sort_order):
    files = [file for file in os.listdir(foldersrc) if file.lower(
    ).endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]

    is_reset = False
    if index != 0 and index % len(files) == 0:
        is_reset = True

    # 파일들을 정렬
    if sort_order == '오름차순':
        files.sort()
    elif sort_order == '내림차순':
        files.sort(reverse=True)
    elif sort_order == '랜덤':
        random.seed(random.randint(0, 1000000))
        random.shuffle(files)
        is_reset = False

    # 인덱스가 파일 개수를 초과하는 경우
    while index >= len(files):
        index -= len(files)

    # 정렬된 파일 리스트에서 인덱스에 해당하는 파일의 주소 반환
    return os.path.join(foldersrc, files[index]), is_reset


def strtobool(val):
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    if isinstance(val, bool):
        return val

    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        raise ValueError("invalid truth value %r" % (val,))


def pickedit_lessthan_str(original_str):
    try_count = 0

    edited_str = original_str
    while try_count < MAX_COUNT_FOR_WHILE:
        try_count += 1

        before_edit_str = edited_str
        pos_prev = 0
        while True:
            pos_r = edited_str.find(">", pos_prev + 1)
            if pos_r == -1:
                break

            pos_l = edited_str.rfind("<", pos_prev, pos_r)
            if pos_l != -1:
                left = edited_str[0:pos_l]
                center = edited_str[pos_l + 1:pos_r]
                right = edited_str[pos_r + 1:len(edited_str)]

                center_splited = center.split("|")
                center_picked = center_splited[random.randrange(
                    0, len(center_splited))]

                result_left = left + center_picked
                pos_prev = len(result_left)
                edited_str = result_left + right
            else:
                pos_prev = pos_r

        if before_edit_str == edited_str:
            break

    return edited_str


def create_windows_filepath(base_path, filename, extension, max_length=150):
    # 파일 이름으로 사용할 수 없는 문자 제거
    cleaned_filename = filename.replace("\n", "")
    cleaned_filename = cleaned_filename.replace("\\", "")

    invalid_chars = r'<>:"/\|?*'
    cleaned_filename = ''.join(
        char for char in cleaned_filename if char not in invalid_chars)

    # 파일 이름의 최대 길이 제한 (확장자 길이 고려)
    max_filename_length = max_length - len(base_path) - len(extension) - 1
    if max_filename_length < 5:
        return None
    cleaned_filename = cleaned_filename[:max_filename_length]

    # 경로, 파일 이름, 확장자 합치기
    filepath = os.path.join(base_path, cleaned_filename + extension)

    return filepath


def inject_imagetag(original_str, tagname, additional_str):
    result_str = original_str[:]

    tag_str_left = "@@" + tagname
    left_pos = original_str.find(tag_str_left)
    if left_pos != -1:
        right_pos = original_str.find("@@", left_pos + 1)
        except_tag_list = [x.strip() for x in original_str[left_pos +
                                                           len(tag_str_left) + 1:right_pos].split(",")]
        original_tag_list = [x.strip() for x in additional_str.split(',')]
        target_tag_list = [
            x for x in original_tag_list if x not in except_tag_list]

        result_str = original_str[0:left_pos] + ", ".join(target_tag_list) + \
            original_str[right_pos + 2:len(original_str)]

    return result_str


def get_filename_only(path):
    filename, _ = os.path.splitext(os.path.basename(path))
    return filename


def convert_qimage_to_imagedata(qimage):
    try:
        buf = QBuffer()
        buf.open(QBuffer.ReadWrite)
        qimage.save(buf, "PNG")
        pil_im = Image.open(io.BytesIO(buf.data()))

        buf = io.BytesIO()
        pil_im.save(buf, format='png', quality=100)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception as e:
        return ""


class NetworkMonitor(QObject):
    """네트워크 연결 상태를 모니터링하는 클래스"""
    connection_status_changed = pyqtSignal(bool, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.url = "https://image.novelai.net"
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_connection)
        
    def start_monitoring(self, interval=30000):  # 30초 간격으로 체크
        """모니터링 시작"""
        self.timer.start(interval)
        
    def stop_monitoring(self):
        """모니터링 중지"""
        self.timer.stop()
        
    def check_connection(self):
        """연결 상태 확인"""
        try:
            import requests
            response = requests.get(self.url, timeout=5)
            if response.status_code == 200:
                self.connection_status_changed.emit(True, "연결됨")
            else:
                self.connection_status_changed.emit(False, f"연결 문제 (상태 코드: {response.status_code})")
        except Exception as e:
            self.connection_status_changed.emit(False, f"연결 오류: {str(e)}")


class NAIAutoGeneratorWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.palette = self.palette()
        self.is_initializing = True
        self.is_expand = True  # Default to expanded view
        
        self.init_variable()
        self.init_window()
        self.init_statusbar()
        self.init_menubar()
        self.init_content()
        self.load_data()
        self.check_folders()
        self.apply_theme()
        
        # 라벨 생성 - 상태바에 추가
        self.label_connection_status = QLabel("서버: 확인 중...")
        self.statusBar().addPermanentWidget(self.label_connection_status)
        
        # 네트워크 모니터 설정
        self.network_monitor = NetworkMonitor(self)
        self.network_monitor.connection_status_changed.connect(self.update_connection_status)
        self.network_monitor.start_monitoring()
        
        theme_mode = self.settings.value("theme_mode", "기본 테마 (System Default)")
        if "어두운" in theme_mode:
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
            self.app.setStyleSheet(dark_style)
            
            # 팔레트 설정
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor("#2D2D2D"))
            dark_palette.setColor(QPalette.WindowText, QColor("#FFFFFF"))
            dark_palette.setColor(QPalette.Base, QColor("#404040"))
            dark_palette.setColor(QPalette.Text, QColor("#FFFFFF"))
            dark_palette.setColor(QPalette.Button, QColor("#353535"))
            dark_palette.setColor(QPalette.ButtonText, QColor("#FFFFFF"))
            self.app.setPalette(dark_palette)
        
        # 스플리터 상태 초기화
        QTimer.singleShot(100, self.initialize_splitter_state)
        
        self.is_initializing = False  # 초기화 완료 표시
        self.show()

        self.init_nai()
        self.init_wc()
        self.init_tagger()
        self.init_completion()
    
    def update_connection_status(self, is_connected, message):
        """네트워크 연결 상태 업데이트"""
        if is_connected:
            self.label_connection_status.setText("서버: 연결됨")
            self.label_connection_status.setStyleSheet("color: green;")
        else:
            self.label_connection_status.setText(f"서버: {message}")
            self.label_connection_status.setStyleSheet("color: red;")
            print(f"네트워크 연결 문제: {message}")  # logger 대신 print 사용
                
        theme_mode = self.settings.value("theme_mode", "기본 테마 (System Default)")
        if "어두운" in theme_mode:
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
            self.app.setStyleSheet(dark_style)
            
            # 팔레트 설정
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor("#2D2D2D"))
            dark_palette.setColor(QPalette.WindowText, QColor("#FFFFFF"))
            dark_palette.setColor(QPalette.Base, QColor("#404040"))
            dark_palette.setColor(QPalette.Text, QColor("#FFFFFF"))
            dark_palette.setColor(QPalette.Button, QColor("#353535"))
            dark_palette.setColor(QPalette.ButtonText, QColor("#FFFFFF"))
            self.app.setPalette(dark_palette)
        
        
        # 스플리터 상태 초기화
        QTimer.singleShot(100, self.initialize_splitter_state)
        
        self.is_initializing = False  # 초기화 완료 표시
        self.show()

        self.init_nai()
        self.init_wc()
        self.init_tagger()
        self.init_completion()
    
    def create_collapsible_section(self, title, content_widget):
        """접기/펼치기 가능한 섹션 위젯 생성"""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 헤더 (클릭 가능)
        header = QPushButton(f"▼ {title}")
        header.setStyleSheet("text-align: left; padding: 5px;")
        
        # 내용물
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(content_widget)
        
        # 레이아웃에 추가
        layout.addWidget(header)
        layout.addWidget(content)
        
        # 접기/펼치기 토글 기능
        header.clicked.connect(lambda: self.toggle_section(header, content))
        
        return section
        
    def toggle_section(self, header, content):
        """섹션 접기/펼치기 토글"""
        if content.isVisible():
            content.hide()
            header.setText(header.text().replace("▼", "▶"))
        else:
            content.show()
            header.setText(header.text().replace("▶", "▼"))
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        # 화면 크기에 따라 UI 조정
        width = event.size().width()
        
        if width < 800:  # 좁은 화면
            self.adjust_for_small_screen()
        elif width < 1200:  # 중간 화면
            self.adjust_for_medium_screen()
        else:  # 넓은 화면
            self.adjust_for_large_screen()
        
        # 이미지 크기 조정
        QTimer.singleShot(100, self.image_result.refresh_size)

    def adjust_for_small_screen(self):
        """좁은 화면에 맞게 UI 조정 (너비 < 800px)"""
        # 캐릭터 프롬프트 컨테이너 높이 제한
        if hasattr(self, 'character_prompts_container'):
            self.character_prompts_container.setMaximumHeight(150)
        
        # 버튼 크기 조정
        for btn in [self.button_generate_once, self.button_generate_sett, self.button_generate_auto]:
            btn.setMinimumWidth(100)
            try:
                # 짧은 텍스트만 표시 (괄호 이전까지)
                text = btn.text()
                if '(' in text:
                    btn.setText(text.split('(')[0])
            except:
                pass

    def adjust_for_medium_screen(self):
        """중간 크기 화면에 맞게 UI 조정 (800px <= 너비 < 1200px)"""
        # 캐릭터 프롬프트 컨테이너 높이 제한 (소형보다는 크게)
        if hasattr(self, 'character_prompts_container'):
            self.character_prompts_container.setMaximumHeight(200)
        
        # 버튼 기본 설정으로 복원
        for btn in [self.button_generate_once, self.button_generate_sett, self.button_generate_auto]:
            btn.setMinimumWidth(120)

    def adjust_for_large_screen(self):
        """큰 화면에 맞게 UI 조정 (너비 >= 1200px)"""
        # 캐릭터 프롬프트 컨테이너 높이 제한 해제
        if hasattr(self, 'character_prompts_container'):
            self.character_prompts_container.setMaximumHeight(16777215)  # QWIDGETSIZE_MAX
        
        # 버튼 기본 설정으로 복원
        for btn in [self.button_generate_once, self.button_generate_sett, self.button_generate_auto]:
            btn.setMinimumWidth(150)

    def adjust_for_small_screen(self):
        """좁은 화면에 맞게 UI 조정"""
        # 캐릭터 프롬프트 컨테이너 높이 제한
        if hasattr(self, 'character_prompts_container'):
            self.character_prompts_container.setMaximumHeight(150)
        
        # 버튼 크기 조정
        for btn in [self.button_generate_once, self.button_generate_sett, self.button_generate_auto]:
            btn.setMinimumWidth(100)
            btn.setText(btn.text().split('(')[0])  # 짧은 텍스트만 표시
    
    def setup_layout_modes(self):
        """다양한 레이아웃 모드 설정"""
        # 메뉴에 레이아웃 모드 선택 추가
        layouts_menu = self.menuBar().addMenu("레이아웃")
        
        horizontal_action = QAction("가로 분할 모드", self)
        horizontal_action.triggered.connect(lambda: self.change_layout_mode("horizontal"))
        layouts_menu.addAction(horizontal_action)
        
        vertical_action = QAction("세로 분할 모드", self)
        vertical_action.triggered.connect(lambda: self.change_layout_mode("vertical"))
        layouts_menu.addAction(vertical_action)
        
        tabbed_action = QAction("탭 모드", self)
        tabbed_action.triggered.connect(lambda: self.change_layout_mode("tabbed"))
        layouts_menu.addAction(tabbed_action)

    def change_layout_mode(self, mode):
        """레이아웃 모드 변경"""
        # 현재 위젯 추출
        left_widget = self.main_splitter.widget(0)
        right_widget = self.main_splitter.widget(1)
        
        # 기존 레이아웃 제거
        self.main_splitter.setParent(None)
        
        if mode == "horizontal":  # 가로 분할 (기본)
            self.main_splitter = QSplitter(Qt.Horizontal)
            self.main_splitter.addWidget(left_widget)
            self.main_splitter.addWidget(right_widget)
            
        elif mode == "vertical":  # 세로 분할
            self.main_splitter = QSplitter(Qt.Vertical)
            self.main_splitter.addWidget(left_widget)
            self.main_splitter.addWidget(right_widget)
            
        elif mode == "tabbed":  # 탭 모드
            tab_widget = QTabWidget()
            tab_widget.addTab(left_widget, "설정")
            tab_widget.addTab(right_widget, "결과")
            
            self.main_splitter = QSplitter()  # 더미 스플리터
            self.main_splitter.addWidget(tab_widget)
        
        # 새 레이아웃 적용
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.main_splitter)
        
        # 중앙 위젯에 설정
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
    
    
    def initialize_splitter_state(self):
        # 최소 사이즈 설정으로 컨텐츠가 너무 작아지지 않도록 함
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(6)  # 구분선 두께 증가
        
        # 좌우 패널 최소 너비 설정
        left_widget = self.main_splitter.widget(0)
        left_widget.setMinimumWidth(350)  # 좌측 패널 최소 너비
        
        right_widget = self.main_splitter.widget(1)
        right_widget.setMinimumWidth(300)  # 우측 패널 최소 너비
        
        saved_state = self.settings.value("splitterSizes")
        if saved_state:
            try:
                self.main_splitter.restoreState(saved_state)
                # Ensure right panel visibility matches is_expand state
                right_visible = sum(self.main_splitter.sizes()[1:]) > 0
                self.is_expand = right_visible
            except Exception as e:
                print(f"Error restoring splitter: {e}")
                self.set_default_splitter()
        else:
            self.set_default_splitter()
        
        self.update_expand_button()

    def set_default_splitter(self):
        total = self.main_splitter.width()
        self.main_splitter.setSizes([int(total*0.6), int(total*0.4)])
        
    def apply_theme(self):  # ← Properly indented under the class
        theme_mode = self.settings.value("theme_mode", "기본 테마 (System Default)")
        accent_color = self.settings.value("accent_color", "#2196F3")
        font_size = self.settings.value("nag_font_size", 18)
        # Add this at the end
        self.app.setPalette(self.palette)  # Reset to default first
        if "어두운" in theme_mode:
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor(45, 45, 45))
            # ... set other palette colors ...
            self.app.setPalette(dark_palette)

    def init_variable(self):
        self.trying_auto_login = False
        self.autogenerate_thread = None
        self.list_settings_batch_target = []
        self.index_settings_batch_target = -1
        self.dict_img_batch_target = {
            "img2img_foldersrc": "",
            "img2img_index": -1,
            "i2i_last_src": "",
            "i2i_last_dst": "",
            "vibe_foldersrc": "",
            "vibe_index": -1,
            "vibe_last_src": "",
            "vibe_last_dst": "",
        }
        # is_expand 변수는 여기서 초기화하지 않음

    def init_window(self):
        self.setWindowTitle(TITLE_NAME)
        self.settings = QSettings(TOP_NAME, APP_NAME)
        self.move(self.settings.value("pos", QPoint(500, 200)))
        self.resize(self.settings.value("size", QSize(1179, 1044)))
        self.settings.setValue("splitterSizes", None)
        self.setAcceptDrops(True)

    def init_statusbar(self):
        statusbar = self.statusBar()
        statusbar.messageChanged.connect(self.on_statusbar_message_changed)
        self.set_statusbar_text("BEFORE_LOGIN")

    def init_menubar(self):
        openAction = QAction('파일 열기(Open file)', self)
        openAction.setShortcut('Ctrl+O')
        openAction.triggered.connect(lambda: self.show_file_dialog("file"))

        loginAction = QAction('로그인(Log in)', self)
        loginAction.setShortcut('Ctrl+L')
        loginAction.triggered.connect(self.show_login_dialog)

        optionAction = QAction('옵션(Option)', self)
        optionAction.setShortcut('Ctrl+U')
        optionAction.triggered.connect(self.show_option_dialog)

        exitAction = QAction('종료(Exit)', self)
        exitAction.setShortcut('Ctrl+W')
        exitAction.triggered.connect(self.quit_app)

        aboutAction = QAction('만든 이(About)', self)
        aboutAction.triggered.connect(self.show_about_dialog)

        getterAction = QAction('이미지 정보 확인기(Info Getter)', self)
        getterAction.setShortcut('Ctrl+I')
        getterAction.triggered.connect(self.on_click_getter)

        taggerAction = QAction('태그 확인기(Danbooru Tagger)', self)
        taggerAction.setShortcut('Ctrl+T')
        taggerAction.triggered.connect(self.on_click_tagger)
        
        # 결과 패널 토글 액션
        togglePanelAction = QAction('결과 패널 토글', self)
        togglePanelAction.setShortcut('F11')
        togglePanelAction.triggered.connect(self.on_click_expand)
        
        # 먼저 menubar를 정의
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        
        # 보기 메뉴 추가
        viewMenu = menubar.addMenu('&보기')
        viewMenu.addAction(togglePanelAction)
        
        # 기존 메뉴 추가
        filemenu_file = menubar.addMenu('&파일(Files)')
        filemenu_file.addAction(openAction)
        filemenu_file.addAction(loginAction)
        filemenu_file.addAction(optionAction)
        filemenu_file.addAction(exitAction)
        
        filemenu_tool = menubar.addMenu('&도구(Tools)')
        filemenu_tool.addAction(getterAction)
        filemenu_tool.addAction(taggerAction)
        
        filemenu_etc = menubar.addMenu('&기타(Etc)')
        filemenu_etc.addAction(aboutAction)

    def init_content(self):
        widget = init_main_widget(self)
        self.setCentralWidget(widget)

    def init_nai(self):
        self.nai = NAIGenerator()

        if self.settings.value("auto_login", False):
            access_token = self.settings.value("access_token", "")
            username = self.settings.value("username", "")
            password = self.settings.value("password", "")
            if not access_token or not username or not password:
                return

            self.set_statusbar_text("LOGGINGIN")
            self.nai.access_token = access_token
            self.nai.username = username
            self.nai.password = password

            self.trying_auto_login = True
            validate_thread = TokenValidateThread(self)
            validate_thread.validation_result.connect(self.on_login_result)
            validate_thread.start()

    def init_wc(self):
        self.wcapplier = WildcardApplier(self.settings.value(
            "path_wildcards", os.path.abspath(DEFAULT_PATH["path_wildcards"])))

    def init_tagger(self):
        self.dtagger = DanbooruTagger(self.settings.value(
            "path_models", os.path.abspath(DEFAULT_PATH["path_models"])))

    def init_completion(self):
        # 이미 태그가 로드되었는지 확인하는 플래그 추가
        if not hasattr(self, '_tags_loaded') and strtobool(self.settings.value("will_complete_tag", True)):
            print("태그 자동 완성 초기화 시작")
            generate_thread = CompletionTagLoadThread(self)
            generate_thread.on_load_completiontag_sucess.connect(self._on_load_completiontag_sucess)
            generate_thread.start()
            # 태그가 로드되었음을 표시
            self._tags_loaded = True
        else:
            print("태그 자동 완성 이미 초기화됨")

    def save_data(self):
        data_dict = self.get_data()

        data_dict["seed_fix_checkbox"] = self.dict_ui_settings["seed_fix_checkbox"].isChecked()

        for k, v in data_dict.items():
            self.settings.setValue(k, v)
        
        # 캐릭터 프롬프트 데이터 저장
        if hasattr(self, 'character_prompts_container'):
            character_data = self.character_prompts_container.get_data()
            self.settings.setValue("character_prompts", character_data)

    def set_data(self, data_dict):
        # uncond_scale shown as * 100
        # 제거
        #uncond_scale = data_dict['uncond_scale']
        #data_dict['uncond_scale'] = str(int(float(uncond_scale) * 100))

        dict_ui = self.dict_ui_settings

        dict_ui["sampler"].setCurrentText(data_dict["sampler"])

        # 텍스트 필드별 다른 메서드 사용
        dict_ui["prompt"].setPlainText(str(data_dict["prompt"]))
        dict_ui["negative_prompt"].setPlainText(str(data_dict["negative_prompt"]))

        # 일반 텍스트 필드용
        text_fields = ["width", "height", "steps", "seed", "scale", "cfg_rescale",
                      "strength", "noise", "reference_information_extracted", "reference_strength"]
        for key in text_fields:
            if key in data_dict:
                dict_ui[key].setText(str(data_dict[key]))
            else:
                print(key)

        # 체크박스 설정
        dict_ui["autoSmea"].setChecked(bool(data_dict.get("autoSmea", True)))

    def load_data(self):
        data_dict = {}
        for key in DEFAULT_PARAMS:
            data_dict[key] = str(self.settings.value(key, DEFAULT_PARAMS[key]))

        self.set_data(data_dict)
        
        # 캐릭터 프롬프트 데이터 로드
        if hasattr(self, 'character_prompts_container'):
            character_data = self.settings.value("character_prompts", {"use_ai_positions": True, "characters": []})
            if character_data and "characters" in character_data:
                try:
                    self.character_prompts_container.set_data(character_data)
                except Exception as e:
                    print(f"캐릭터 프롬프트 데이터 로드 중 오류: {e}")

    def check_folders(self):
        for key, default_path in DEFAULT_PATH.items():
            path = self.settings.value(key, os.path.abspath(default_path))
            create_folder_if_not_exists(path)

    def _on_load_completiontag_sucess(self, tag_list):
        print(f"----- 자동 완성 적용 시작 -----")
        print(f"태그 로딩 완료: {len(tag_list)}개")
        if tag_list:
            target_code = ["prompt", "negative_prompt"]
            for code in target_code:
                try:
                    # CompletionTextEdit 클래스의 start_complete_mode 메서드 호출
                    if hasattr(self.dict_ui_settings[code], 'start_complete_mode'):
                        print(f"{code} 필드에 자동 완성 적용 시도...")
                        # 태그 목록을 직접 전달 
                        self.dict_ui_settings[code].start_complete_mode(tag_list)
                        print(f"{code} 필드에 자동 완성 활성화됨 ({len(tag_list)}개 태그)")
                    else:
                        print(f"{code} 필드에 start_complete_mode 메서드가 없음")
                except Exception as e:
                    print(f"{code} 필드 자동 완성 설정 실패: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            # 캐릭터 프롬프트 컨테이너에도 태그 자동 완성 적용
            if hasattr(self, 'character_prompts_container'):
                try:
                    print("캐릭터 프롬프트 필드에 자동 완성 적용 시도...")
                    self.character_prompts_container.set_tag_completion(tag_list)
                    print(f"캐릭터 프롬프트 필드에 자동 완성 활성화됨 ({len(tag_list)}개 태그)")
                except Exception as e:
                    print(f"캐릭터 프롬프트 필드 자동 완성 설정 실패: {str(e)}")
                    import traceback
                    traceback.print_exc()
        else:
            print("태그 목록이 비어 있음")
        print(f"----- 자동 완성 적용 종료 -----")

    def get_data(self, do_convert_type=False):
        data = {
            "prompt": self.dict_ui_settings["prompt"].toPlainText(),
            "negative_prompt": self.dict_ui_settings["negative_prompt"].toPlainText(),
            "width": self.dict_ui_settings["width"].text(),
            "height": self.dict_ui_settings["height"].text(),
            "sampler": self.dict_ui_settings["sampler"].currentText(),
            "steps": self.dict_ui_settings["steps"].text(),
            "seed": self.dict_ui_settings["seed"].text(),
            "scale": self.dict_ui_settings["scale"].text(),
            "cfg_rescale": self.dict_ui_settings["cfg_rescale"].text(),
            "autoSmea": str(self.dict_ui_settings["autoSmea"].isChecked()),
            #"uncond_scale": str(float(self.dict_ui_settings["uncond_scale"].text()) / 100),
            "strength": self.dict_ui_settings["strength"].text(),
            "noise": self.dict_ui_settings["noise"].text(),
            "reference_information_extracted": self.dict_ui_settings["reference_information_extracted"].text(),
            "reference_strength": self.dict_ui_settings["reference_strength"].text(),
            "quality_toggle": str(self.settings.value("quality_toggle", True)),
            "dynamic_thresholding": str(self.settings.value("dynamic_thresholding", False)),
            "anti_artifacts": str(self.settings.value("anti_artifacts", 0.0)),
            "v4_model_preset": self.settings.value("v4_model_preset", "Artistic")
        }

        if do_convert_type:
            data["width"] = int(data["width"])
            data["height"] = int(data["height"])
            data["steps"] = int(data["steps"])
            data["seed"] = int(data["seed"] or 0)
            data["scale"] = float(data["scale"])
            data["cfg_rescale"] = float(data["cfg_rescale"])
            data["autoSmea"] = bool(data["autoSmea"] == "True")
            #data["uncond_scale"] = float(data["uncond_scale"])
            data["strength"] = float(data["strength"])
            data["noise"] = float(data["noise"])
            data["reference_information_extracted"] = float(data["reference_information_extracted"])
            data["reference_strength"] = float(data["reference_strength"])
            data["quality_toggle"] = bool(data["quality_toggle"] == "True")
            data["dynamic_thresholding"] = bool(data["dynamic_thresholding"] == "True")
            data["anti_artifacts"] = float(data["anti_artifacts"])

        return data

    def save_all_data(self):
        """모든 데이터 저장 (캐릭터 프롬프트 포함)"""
        self.save_data()
        
        # 캐릭터 프롬프트 데이터 저장
        if hasattr(self, 'character_prompts_container'):
            character_data = self.character_prompts_container.get_data()
            self.settings.setValue("character_prompts", character_data)

    def load_all_data(self):
        """모든 데이터 로드 (캐릭터 프롬프트 포함)"""
        self.load_data()
        
        # 캐릭터 프롬프트 데이터 로드
        if hasattr(self, 'character_prompts_container'):
            character_data = self.settings.value("character_prompts", {})
            if character_data:
                self.character_prompts_container.set_data(character_data)

    # Warning! Don't interact with pyqt gui in this function
    def _get_data_for_generate(self):
        data = self.get_data(True)
        self.save_data()

        # sampler check
        if data['sampler'] == 'ddim_v3':
            data['autoSmea'] = False

        # data precheck
        data["prompt"], data["negative_prompt"] = self._preedit_prompt(
            data["prompt"], data["negative_prompt"])

        # seed pick
        if not self.dict_ui_settings["seed_fix_checkbox"].isChecked() or data["seed"] == -1:
            data["seed"] = random.randint(0, 2**32-1)

        # wh pick
        if self.checkbox_random_resolution.isChecked():
            fl = self.get_now_resolution_familly_list()
            if fl:
                text = fl[random.randrange(0, len(fl))]

                res_text = text.split("(")[1].split(")")[0]
                width, height = res_text.split("x")
                data["width"], data["height"] = int(width), int(height)

        # image option check
        data["image"] = None
        data["reference_image"] = None
        data["mask"] = None
        if self.i2i_settings_group.src:
            imgdata_i2i = self.nai.convert_src_to_imagedata(
                self.i2i_settings_group.src)
            if imgdata_i2i:
                data["image"] = imgdata_i2i
                # 만약 i2i가 켜져있다면
                # autoSmea 설정을 반드시 꺼야함. 안그러면 흐릿하게 나옴.
                data['autoSmea'] = False

                # mask 체크
                if self.i2i_settings_group.mask:
                    data['mask'] = convert_qimage_to_imagedata(
                        self.i2i_settings_group.mask)
            else:
                self.i2i_settings_group.on_click_removebutton()
                
        if self.vibe_settings_group.src:
            imgdata_vibe = self.nai.convert_src_to_imagedata(
                self.vibe_settings_group.src)
            if imgdata_vibe:
                data["reference_image"] = imgdata_vibe
            else:
                self.vibe_settings_group.on_click_removebutton()

        # i2i 와 vibe 세팅
        batch = self.dict_img_batch_target
        for mode_str in ["i2i", "vibe"]:
            target_group = self.i2i_settings_group if mode_str == "i2i" else self.vibe_settings_group

            if target_group.tagcheck_checkbox.isChecked():
                if target_group.src:
                    if batch[mode_str + "_last_src"] != target_group.src:
                        batch[mode_str + "_last_src"] = target_group.src
                        batch[mode_str + "_last_dst"] = self.predict_tag_from(
                            "src", target_group.src, False)
                        if not batch[mode_str + "_last_dst"]:
                            batch[mode_str + "_last_src"] = ""
                            batch[mode_str + "_last_dst"] = ""

                    data["prompt"] = inject_imagetag(
                        data["prompt"], "img2img" if mode_str == "i2i" else "vibe", batch[mode_str + "_last_dst"])
                    data["negative_prompt"] = inject_imagetag(
                        data["negative_prompt"], "img2img" if mode_str == "i2i" else "vibe", batch[mode_str + "_last_dst"])
            else:
                batch[mode_str + "_last_src"] = ""
                batch[mode_str + "_last_dst"] = ""

        # V4 특화 설정 추가
        data["params_version"] = 3
        data["add_original_image"] = True
        data["legacy"] = False
        data["legacy_v3_extend"] = False
        data["prefer_brownian"] = True
        data["ucPreset"] = 0
        data["noise_schedule"] = "karras"

        # 캐릭터 프롬프트 데이터 추가
        character_data = self.character_prompts_container.get_data()
        if character_data["characters"]:
            # characterPrompts 배열 생성
            data["characterPrompts"] = []
            data["use_character_coords"] = not character_data["use_ai_positions"]
            
            for char in character_data["characters"]:
                # 프롬프트와 네거티브 프롬프트에 처리 적용
                prompt = self._process_prompt_with_wildcards(char["prompt"])
                negative_prompt = self._process_prompt_with_wildcards(char["negative_prompt"])
                
                char_prompt = {
                    "prompt": prompt,
                    "negative_prompt": negative_prompt
                }
                
                # 위치 정보가 있으면 추가
                if char["position"] and not character_data["use_ai_positions"]:
                    char_prompt["position"] = char["position"]
                
                data["characterPrompts"].append(char_prompt)

        return data

    def _preedit_prompt(self, prompt, nprompt):
        try_count = 0
        edited_prompt = prompt
        while try_count < MAX_COUNT_FOR_WHILE:
            try_count += 1

            before_edit_prompt = edited_prompt

            # 줄바꿈을 공백으로 대체
            edited_prompt = edited_prompt.replace("\n", " ")
            
            edited_prompt = pickedit_lessthan_str(edited_prompt)
            edited_prompt = self.apply_wildcards(edited_prompt)

            if before_edit_prompt == edited_prompt:
                break

        try_count = 0
        edited_nprompt = nprompt
        while try_count < MAX_COUNT_FOR_WHILE:
            try_count += 1

            before_edit_nprompt = edited_nprompt
            
            # 줄바꿈을 공백으로 대체
            edited_nprompt = edited_nprompt.replace("\n", " ")
            
            # lessthan pick
            edited_nprompt = pickedit_lessthan_str(edited_nprompt)
            # wildcards pick
            edited_nprompt = self.apply_wildcards(edited_nprompt)

            if before_edit_nprompt == edited_nprompt:
                break

        return edited_prompt, edited_nprompt

    def _on_after_create_data_apply_gui(self):
        data = self.nai.parameters

        # resolution text
        fl = self.get_now_resolution_familly_list()
        if fl:
            for resol in fl:
                if str(data["width"]) + "x" + str(data["height"]) in resol:
                    self.combo_resolution.setCurrentText(resol)
                    break

        # seed text
        self.dict_ui_settings["seed"].setText(str(data["seed"]))

        # result text
        self.set_result_text(data)

    def on_click_generate_once(self):
        self.list_settings_batch_target = []

        data = self._get_data_for_generate()
        self.nai.set_param_dict(data)
        self._on_after_create_data_apply_gui()

        generate_thread = GenerateThread(self)
        generate_thread.generate_result.connect(self._on_result_generate)
        generate_thread.start()

        self.set_statusbar_text("GENEARTING")
        self.set_disable_button(True)
        self.generate_thread = generate_thread

    def _on_result_generate(self, error_code, result):
        self.generate_thread = None
        self.set_disable_button(False)
        self.set_statusbar_text("IDLE")
        self.refresh_anlas()

        if error_code == 0 and isinstance(result, bytes):
            # 성공적인 응답 처리
            try:
                self.image_result.set_custom_pixmap(result)
                
                # 생성 정보 로깅
                logger.info(f"이미지 생성 성공 - 크기: {len(result)} 바이트")
                
                # 배치 처리 계속
                if self.dict_img_batch_target["img2img_foldersrc"]:
                    self.proceed_image_batch("img2img")
                if self.dict_img_batch_target["vibe_foldersrc"]:
                    self.proceed_image_batch("vibe")
            except Exception as e:
                # 이미지 처리 중 오류
                logger.error(f"이미지 처리 오류: {str(e)}", exc_info=True)
                self.show_error_dialog("이미지 처리 오류", f"이미지를 처리하는 중 오류가 발생했습니다:\n{str(e)}")
        else:
            # API 오류 처리
            if isinstance(result, tuple) and len(result) == 2:
                error_code, error_message = result
                self.show_api_error_dialog(error_code, error_message)
            else:
                self.show_error_dialog("API 오류", f"이미지를 생성하는데 문제가 있습니다.\n\n{str(result)}")

    def show_api_error_dialog(self, error_code, error_message):
        """API 오류를 사용자 친화적으로 표시"""
        title = "API 요청 오류"
        
        # 오류 코드별 사용자 친화적 메시지
        friendly_messages = {
            401: "인증에 실패했습니다. 다시 로그인해 주세요.",
            402: "Anlas가 부족합니다. 충전 후 다시 시도해 주세요.",
            429: "너무 많은 요청을 보냈습니다. 잠시 후 다시 시도해 주세요.",
            500: "Novel AI 서버에 문제가 있습니다. 잠시 후 다시 시도해 주세요.",
            503: "Novel AI 서비스를 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해 주세요."
        }
        
        # 사용자 친화적 메시지
        if error_code in friendly_messages:
            friendly_message = friendly_messages[error_code]
            message = f"{friendly_message}\n\n기술적 정보: {error_message}"
        else:
            message = f"이미지를 생성하는데 문제가 있습니다.\n\n{error_message}"
        
        QMessageBox.critical(self, title, message)

    def show_error_dialog(self, title, message):
        """일반 오류 메시지 표시"""
        QMessageBox.critical(self, title, message)

    def on_click_generate_sett(self):
        path_list, _ = QFileDialog().getOpenFileNames(self,
                                                      caption="불러올 세팅 파일들을 선택해주세요",
                                                      filter="Txt File (*.txt)")
        if path_list:
            if len(path_list) < 2:
                QMessageBox.information(
                    self, '경고', "두개 이상 선택해주세요.")
                return

            for path in path_list:
                if not path.endswith(".txt") or not os.path.isfile(path):
                    QMessageBox.information(
                        self, '경고', ".txt로 된 세팅 파일만 선택해주세요.")
                    return

            self.on_click_generate_auto(path_list)

    def proceed_settings_batch(self):
        self.index_settings_batch_target += 1

        while len(self.list_settings_batch_target) <= self.index_settings_batch_target:
            self.index_settings_batch_target -= len(
                self.list_settings_batch_target)

        path = self.list_settings_batch_target[self.index_settings_batch_target]
        is_success = self._load_settings(path)

        return is_success

    def on_click_generate_auto(self, setting_batch_target=[]):
        if not self.autogenerate_thread:
            d = GenerateDialog(self)
            if d.exec_() == QDialog.Accepted:
                self.list_settings_batch_target = setting_batch_target
                if setting_batch_target:
                    self.index_settings_batch_target = -1
                    is_success = self.proceed_settings_batch()
                    if not is_success:
                        QMessageBox.information(
                            self, '경고', "세팅을 불러오는데 실패했습니다.")
                        return

                agt = AutoGenerateThread(
                    self, d.count, d.delay, d.ignore_error)
                agt.on_data_created.connect(
                    self._on_after_create_data_apply_gui)
                agt.on_error.connect(self._on_error_autogenerate)
                agt.on_end.connect(self._on_end_autogenerate)
                agt.on_statusbar_change.connect(self.set_statusbar_text)
                agt.on_success.connect(self._on_success_autogenerate)
                agt.start()

                self.set_autogenerate_mode(True)
                self.autogenerate_thread = agt
        else:
            self._on_end_autogenerate()

    def _on_error_autogenerate(self, error_code, result):
        QMessageBox.information(
            self, '경고', "이미지를 생성하는데 문제가 있습니다.\n\n" + str(result))
        self._on_end_autogenerate()

    def _on_end_autogenerate(self):
        self.autogenerate_thread.stop()
        self.autogenerate_thread = None
        self.set_autogenerate_mode(False)
        self.set_statusbar_text("IDLE")
        self.refresh_anlas()

    def _on_success_autogenerate(self, result_str):
        self._on_refresh_anlas(self.nai.get_anlas() or -1)

        self.image_result.set_custom_pixmap(result_str)

        if self.dict_img_batch_target["img2img_foldersrc"]:
            self.proceed_image_batch("img2img")
        if self.dict_img_batch_target["vibe_foldersrc"]:
            self.proceed_image_batch("vibe")
        if self.list_settings_batch_target:
            self.proceed_settings_batch()

    def set_autogenerate_mode(self, is_autogenrate):
        self.button_generate_once.setDisabled(is_autogenrate)
        self.button_generate_sett.setDisabled(is_autogenrate)

        stylesheet = """
            color:black;
            background-color: """ + COLOR.BUTTON_AUTOGENERATE + """;
        """ if is_autogenrate else ""
        self.button_generate_auto.setStyleSheet(stylesheet)
        self.button_generate_auto.setText(
            "생성 중지" if is_autogenrate else "연속 생성")
        self.button_generate_auto.setDisabled(False)

    def apply_wildcards(self, prompt):
        self.check_folders()

        try:
            return self.wcapplier.apply_wildcards(prompt)
        except Exception as e:
            print(e)

        return prompt

    def on_click_open_folder(self, target_pathcode):
        path = self.settings.value(
            target_pathcode, DEFAULT_PATH[target_pathcode])
        path = os.path.abspath(path)
        create_folder_if_not_exists(path)
        os.startfile(path)

    def on_click_save_settings(self):
        path = self.settings.value(
            "path_settings", DEFAULT_PATH["path_settings"])
        path, _ = QFileDialog.getSaveFileName(
            self, "세팅 파일을 저장할 곳을 선택해주세요", path, "Txt File (*.txt)")
        if path:
            try:
                # 기본 데이터 가져오기
                data = self.get_data(True)
                
                # 캐릭터 프롬프트 데이터 추가
                if hasattr(self, 'character_prompts_container'):
                    character_data = self.character_prompts_container.get_data()
                    
                    if character_data["characters"]:
                        # characterPrompts 배열 생성
                        data["characterPrompts"] = []
                        data["use_character_coords"] = not character_data["use_ai_positions"]
                        
                        for char in character_data["characters"]:
                            char_prompt = {
                                "prompt": char["prompt"],
                                "negative_prompt": char["negative_prompt"]
                            }
                            
                            # 위치 정보가 있으면 추가
                            if char["position"] and not character_data["use_ai_positions"]:
                                char_prompt["position"] = char["position"]
                            
                            data["characterPrompts"].append(char_prompt)
                
                json_str = json.dumps(data)
                with open(path, "w", encoding="utf8") as f:
                    f.write(json_str)
            except Exception as e:
                print(e)
                QMessageBox.information(
                    self, '경고', "세팅 저장에 실패했습니다.\n\n" + str(e))

    def _process_prompt_with_wildcards(self, prompt_text):
        """프롬프트 텍스트에 와일드카드와 <> 처리를 적용"""
        edited_text = prompt_text
        try_count = 0
        while try_count < MAX_COUNT_FOR_WHILE:
            try_count += 1
            before_edit = edited_text
            edited_text = pickedit_lessthan_str(edited_text)
            edited_text = self.apply_wildcards(edited_text)
            if before_edit == edited_text:
                break
        
        # 줄바꿈 제거
        return edited_text.replace("\n", " ")
        

    def on_click_load_settings(self):
        path = self.settings.value(
            "path_settings", DEFAULT_PATH["path_settings"])

        select_dialog = QFileDialog()
        select_dialog.setFileMode(QFileDialog.ExistingFile)
        path, _ = select_dialog.getOpenFileName(
            self, "불러올 세팅 파일을 선택해주세요", path, "Txt File (*.txt)")
        if path:
            is_success = self._load_settings(path)

            if not is_success:
                QMessageBox.information(
                    self, '경고', "세팅을 불러오는데 실패했습니다.\n\n" + str(e))

    def _load_settings(self, path):
        try:
            with open(path, "r", encoding="utf8") as f:
                json_str = f.read()
            json_obj = json.loads(json_str)

            self.set_data(json_obj)
            
            # 캐릭터 프롬프트 데이터가 있으면 로드
            if "characterPrompts" in json_obj and hasattr(self, 'character_prompts_container'):
                # API 형식에서 GUI 형식으로 변환
                characters = []
                for char in json_obj["characterPrompts"]:
                    character = {
                        "prompt": char.get("prompt", ""),
                        "negative_prompt": char.get("negative_prompt", ""),
                        "position": char.get("position", None)
                    }
                    characters.append(character)
                
                character_data = {
                    "use_ai_positions": not json_obj.get("use_character_coords", True),
                    "characters": characters
                }
                
                self.character_prompts_container.set_data(character_data)

            return True
        except Exception as e:
            print(e)

        return False

    def show_prompt_dialog(self, title, prompt, nprompt):
        QMessageBox.about(self, title,
                          "프롬프트:\n" +
                          prompt +
                          "\n\n" +
                          "네거티브 프롬프트:\n" +
                          nprompt)

    def on_random_resolution_checked(self, is_checked):
        # 초기화 중이면 다이얼로그를 표시하지 않음
        if self.is_initializing:
            self.settings.setValue("image_random_checkbox", is_checked == 2)
            return
            
        if is_checked == 2:
            fl = self.get_now_resolution_familly_list()
            if not fl:
                QMessageBox.information(
                    self, '이미지 크기 랜덤', "랜덤이 지원되지 않는 형식입니다.\n")
            else:
                s = ""
                for f in fl:
                    s += f + "\n"
                QMessageBox.information(
                    self, '이미지 크기 랜덤', "다음 크기 중 하나가 랜덤으로 선택됩니다.\n\n" + s)

        self.settings.setValue("image_random_checkbox", is_checked == 2)

    def get_now_resolution_familly_list(self):
        try:
            current_text = self.combo_resolution.currentText()
            if current_text == "Custom (직접 입력)":
                return []
                
            # 현재 선택된 해상도가 어느 패밀리에 속하는지 확인
            for family_idx, resolutions in RESOLUTION_FAMILIY.items():
                if current_text in resolutions:
                    return resolutions
                    
            # 만약 찾지 못했다면 기본 HD 패밀리 반환
            return RESOLUTION_FAMILIY[0]  # 기본 해상도 모음 (HD 포함)
        except Exception as e:
            print(f"Resolution family error: {e}")
            return []

    def change_path(self, code, src):
        path = os.path.abspath(src)

        self.settings.setValue(code, path)

        create_folder_if_not_exists(path)

        if code == "path_wildcards":
            self.init_wc()
        elif code == "path_models":
            self.init_tagger()

    def on_click_getter(self):
        MiniUtilDialog(self, "getter").show()

    def on_click_tagger(self):
        MiniUtilDialog(self, "tagger").show()

    def on_click_expand(self):
        self.is_expand = not self.is_expand
        
        if self.is_expand:
            # Save current state before collapsing
            self.settings.setValue("splitterSizes", self.main_splitter.saveState())
            
            # Restore or set default sizes
            if self.main_splitter.sizes()[1] == 0:
                self.set_default_splitter()
                
            self.main_splitter.handle(1).setEnabled(True)
            self.main_splitter.widget(1).show()
        else:
            # Collapse right panel
            self.settings.setValue("splitterSizes", self.main_splitter.saveState())
            self.main_splitter.setSizes([self.main_splitter.width(), 0])
            self.main_splitter.handle(1).setEnabled(False)
            self.main_splitter.widget(1).hide()
        
        self.update_expand_button()
        QTimer.singleShot(50, self.image_result.refresh_size)

    def update_expand_button(self):
        self.button_expand.setText("◀▶" if self.is_expand else "▶◀")
        self.button_expand.setToolTip("Collapse right panel" if self.is_expand else "Expand right panel")

    def update_ui_after_expand(self):
        # UI 갱신 및 이미지 크기 조정
        self.repaint()
        if self.is_expand:
            self.image_result.refresh_size()

    def install_model(self, model_name):
        loading_dialog = FileIODialog(
            "모델 다운 받는 중...\n이 작업은 오래 걸릴 수 있습니다.", lambda: str(self.dtagger.download_model(model_name)))
        if loading_dialog.exec_() == QDialog.Accepted:
            if loading_dialog.result == "True":
                self.option_dialog.on_model_downloaded(model_name)

    def get_image_info_bysrc(self, file_src):
        nai_dict, error_code = naiinfo_getter.get_naidict_from_file(file_src)

        self._get_image_info_byinfo(nai_dict, error_code, file_src)

    def get_image_info_bytxt(self, file_src):
        nai_dict, error_code = naiinfo_getter.get_naidict_from_txt(file_src)

        self._get_image_info_byinfo(nai_dict, error_code, None)

    def get_image_info_byimg(self, img):
        nai_dict, error_code = naiinfo_getter.get_naidict_from_img(img)

        self._get_image_info_byinfo(nai_dict, error_code, img)

    def _get_image_info_byinfo(self, nai_dict, error_code, img_obj):
        if error_code == 0:
            QMessageBox.information(self, '경고', "EXIF가 존재하지 않는 파일입니다.")
            self.set_statusbar_text("IDLE")
        elif error_code == 1 or error_code == 2:
            QMessageBox.information(
                self, '경고', "EXIF는 존재하나 NAI로부터 만들어진 것이 아닌 듯 합니다.")
            self.set_statusbar_text("IDLE")
        elif error_code == 3:
            new_dict = {
                "prompt": nai_dict["prompt"], "negative_prompt": nai_dict["negative_prompt"]}
            new_dict.update(nai_dict["option"])
            new_dict.update(nai_dict["etc"])

            self.set_data(new_dict)
            if img_obj:
                self.image_result.set_custom_pixmap(img_obj)
            self.set_statusbar_text("LOAD_COMPLETE")

    def show_login_dialog(self):
        dialog = LoginDialog(self)
        # 여기서 dialog가 모달로 실행되고 완료됩니다
        # 로그인 성공/실패 처리는 dialog에서 이루어집니다

    def show_option_dialog(self):
        self.option_dialog = OptionDialog(self)

        self.option_dialog.exec_()

    def show_about_dialog(self):
        QMessageBox.about(self, 'About', S.ABOUT)

    def set_disable_button(self, will_disable):
        self.button_generate_once.setDisabled(will_disable)
        self.button_generate_sett.setDisabled(will_disable)
        self.button_generate_auto.setDisabled(will_disable)

    def set_result_text(self, nai_dict):
        additional_dict = {}

        if 'image' in nai_dict and nai_dict['image']:
            additional_dict["image_src"] = self.i2i_settings_group.src or ""
        if 'reference_image' in nai_dict and nai_dict['reference_image']:
            additional_dict["reference_image_src"] = self.vibe_settings_group.src or ""

        if self.dict_img_batch_target["i2i_last_dst"]:
            additional_dict["image_tag"] = self.dict_img_batch_target["i2i_last_dst"]
        if self.dict_img_batch_target["vibe_last_dst"]:
            additional_dict["reference_image_tag"] = self.dict_img_batch_target["vibe_last_dst"]
        
        # 캐릭터 프롬프트도 처리된 형태로 표시
        if 'characterPrompts' in nai_dict and nai_dict['characterPrompts']:
            additional_dict["processed_characters"] = nai_dict['characterPrompts']

        content = prettify_naidict(nai_dict, additional_dict)

        self.prompt_result.setText(content)

    def refresh_anlas(self):
        anlas_thread = AnlasThread(self)
        anlas_thread.anlas_result.connect(self._on_refresh_anlas)
        anlas_thread.start()

    def _on_refresh_anlas(self, anlas):
        if anlas == -1:
            anlas = "?"
        self.label_anlas.setText("Anlas: " + str(anlas))

    def on_login_result(self, error_code):
        if error_code == 0:
            self.set_statusbar_text("LOGINED")
            self.label_loginstate.set_logged_in(True)
            self.set_disable_button(False)
            self.refresh_anlas()  # 이 부분이 제대로 실행되는지 확인
        else:
            self.nai = NAIGenerator()  # reset
            self.set_statusbar_text("BEFORE_LOGIN")
            self.label_loginstate.set_logged_in(False)
            self.set_disable_button(True)
            self.set_auto_login(False)

        self.trying_auto_login = False

    def set_auto_login(self, is_auto_login):
        self.settings.setValue("auto_login",
                               True if is_auto_login else False)
        self.settings.setValue("access_token",
                               self.nai.access_token if is_auto_login else None)
        self.settings.setValue("username",
                               self.nai.username if is_auto_login else None)
        self.settings.setValue("password",
                               self.nai.password if is_auto_login else None)

    def on_logout(self):
        self.set_statusbar_text("BEFORE_LOGIN")

        self.label_loginstate.set_logged_in(False)

        self.set_disable_button(True)

        self.set_auto_login(False)

    def show_file_dialog(self, mode):
        select_dialog = QFileDialog()
        select_dialog.setFileMode(QFileDialog.ExistingFile)
        target_type = '이미지, 텍스트 파일(*.txt *.png *.webp)' if mode == 'file' else '이미지 파일(*.jpg *.png *.webp)'
        fname = select_dialog.getOpenFileName(
            self, '불러올 파일을 선택해 주세요.', '', target_type)

        if fname[0]:
            fname = fname[0]

            if mode == "file":
                if fname.endswith(".png") or fname.endswith(".webp"):
                    self.get_image_info_bysrc(fname)
                elif fname.endswith(".txt"):
                    self.get_image_info_bytxt(fname)
                else:
                    QMessageBox.information(
                        self, '경고', "png, webp, txt 파일만 가능합니다.")
                    return
            else:
                if fname.endswith(".png") or fname.endswith(".webp") or fname.endswith(".jpg"):
                    self.set_image_as_param(mode, fname)
                elif os.path.isdir(fname):
                    self.set_imagefolder_as_param(mode, fname)
                else:
                    QMessageBox.information(
                        self, '경고', "불러오기는 폴더, jpg, png, webp만 가능합니다.")
                    return

    def show_openfolder_dialog(self, mode):
        select_dialog = QFileDialog()
        select_dialog.setFileMode(QFileDialog.Directory)
        select_dialog.setOption(QFileDialog.Option.ShowDirsOnly)
        fname = select_dialog.getExistingDirectory(
            self, mode + '모드로 열 폴더를 선택해주세요.', '')

        if fname:
            if os.path.isdir(fname):
                self.set_imagefolder_as_param(mode, fname)
            else:
                QMessageBox.information(
                    self, '경고', "폴더만 선택 가능합니다.")

    def _set_image_gui(self, mode, src):
        if mode == "img2img":
            self.i2i_settings_group.set_image(src)
            self.image_options_layout.setStretch(0, 1)
        if mode == "vibe":
            self.vibe_settings_group.set_image(src)
            self.image_options_layout.setStretch(1, 1)
        self.image_options_layout.setStretch(2, 0)

    def set_image_as_param(self, mode, src):
        self.dict_img_batch_target[mode + "_foldersrc"] = ""
        target_group = self.i2i_settings_group if mode == "img2img" else self.vibe_settings_group
        target_group.set_folder_mode(False)
        self._set_image_gui(mode, src)

    def set_imagefolder_as_param(self, mode, foldersrc):
        if get_imgcount_from_foldersrc(foldersrc) == 0:
            QMessageBox.information(
                self, '경고', "이미지 파일이 없는 폴더입니다")
            return

        target_group = self.i2i_settings_group if mode == "img2img" else self.vibe_settings_group
        target_group.set_folder_mode(True)

        self.dict_img_batch_target[mode + "_foldersrc"] = foldersrc
        self.dict_img_batch_target[mode + "_index"] = -1

        self.proceed_image_batch(mode)

    def proceed_image_batch(self, mode):
        self.dict_img_batch_target[mode + "_index"] += 1
        target_group = self.i2i_settings_group if mode == "img2img" else self.vibe_settings_group

        src, is_reset = pick_imgsrc_from_foldersrc(
            foldersrc=self.dict_img_batch_target[mode + "_foldersrc"],
            index=self.dict_img_batch_target[mode + "_index"],
            sort_order=target_group.get_folder_sort_mode()
        )

        if is_reset:
            seed = random.randint(0, 9999999999)
            self.dict_ui_settings["seed"].setText(str(seed))

        self._set_image_gui(mode, src)

    def on_click_tagcheckbox(self, mode):
        box = self.sender()
        if box.isChecked():
            if not self.settings.value("selected_tagger_model", ""):
                box.setChecked(False)
                QMessageBox.information(
                    self, '경고', "먼저 옵션에서 태깅 모델을 다운/선택 해주세요.")
                return

            QMessageBox.information(
                self, '안내', "새로운 이미지를 불러올때마다 태그를 읽습니다.\n프롬프트 내에 @@" + mode + "@@를 입력해주세요.\n해당 자리에 삽입됩니다.")
            return

    # warning! Don't use this function in thread if with_dialog==True
    def predict_tag_from(self, filemode, target, with_dialog):
        result = ""

        target_model_name = self.settings.value("selected_tagger_model", '')
        if not target_model_name:
            QMessageBox.information(
                self, '경고', "먼저 옵션에서 태깅 모델을 다운/선택 해주세요.")
            return ""
        else:
            self.dtagger.options["model_name"] = target_model_name

        if filemode == "src":
            target = Image.open(target)

        if with_dialog:
            loading_dialog = FileIODialog(
                "태그하는 중...", lambda: self.dtagger.tag(target))
            if loading_dialog.exec_() == QDialog.Accepted:
                result = loading_dialog.result
                if not result:
                    list_installed_model = self.dtagger.get_installed_models()
                    if not (target_model_name in list_installed_model):
                        self.settings.setValue("selected_tagger_model", '')
        else:
            try:
                result = self.dtagger.tag(target)
            except Exception as e:
                print(e)

        return result

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

        furl = files[0]
        if furl.isLocalFile():
            fname = furl.toLocalFile()
            if fname.endswith(".png") or fname.endswith(".webp") or fname.endswith(".jpg"):
                if self.i2i_settings_group.geometry().contains(event.pos()):
                    self.set_image_as_param("img2img", fname)
                    return
                elif self.vibe_settings_group.geometry().contains(event.pos()):
                    self.set_image_as_param("vibe", fname)
                    return
                elif not fname.endswith(".jpg"):
                    self.get_image_info_bysrc(fname)
                    return
            elif fname.endswith(".txt"):
                self.get_image_info_bytxt(fname)
                return
            elif os.path.isdir(fname):
                if self.i2i_settings_group.geometry().contains(event.pos()):
                    self.set_imagefolder_as_param("img2img", fname)
                    return
                elif self.vibe_settings_group.geometry().contains(event.pos()):
                    self.set_imagefolder_as_param("vibe", fname)
                    return

            QMessageBox.information(
                self, '경고', "세팅 불러오기는 png, webp, txt 파일만 가능합니다.\ni2i와 vibe를 사용하고 싶다면 해당 칸에 떨어트려주세요.")
        else:
            self.set_statusbar_text("LOADING")
            try:
                url = furl.url()
                res = request.urlopen(url).read()
                img = Image.open(BytesIO(res))
                if img:
                    self.get_image_info_byimg(img)

            except Exception as e:
                print(e)
                self.set_statusbar_text("IDLE")
                QMessageBox.information(self, '경고', "이미지 파일 다운로드에 실패했습니다.")
                return

    def set_statusbar_text(self, status_key="", list_format=[]):
        statusbar = self.statusBar()

        if status_key:
            self.status_state = status_key
            self.status_list_format = list_format
        else:
            status_key = self.status_state
            list_format = self.status_list_format

        statusbar.showMessage(
            S.LIST_STATSUBAR_STATE[status_key].format(*list_format))

    def on_statusbar_message_changed(self, t):
        if not t:
            self.set_statusbar_text()

    def closeEvent(self, e):
        size = self.size()
        size.setWidth(
            int(size.width() / 2 if self.is_expand else size.width()))
        self.settings.setValue("size", size)
        self.settings.setValue("pos", self.pos())
        self.save_data()  # 데이터 저장
        e.accept()

    def quit_app(self):
        time.sleep(0.1)
        self.close()
        self.app.closeAllWindows()
        QCoreApplication.exit(0)


class CompletionTagLoadThread(QThread):
    on_load_completiontag_sucess = pyqtSignal(list)

    def __init__(self, parent):
        super(CompletionTagLoadThread, self).__init__(parent)
        self.parent = parent
        
        # 태그 목록을 캐시하는 클래스 변수 추가 (모든 인스턴스가 공유)
        if not hasattr(CompletionTagLoadThread, 'cached_tags'):
            CompletionTagLoadThread.cached_tags = None

    def run(self):
        # 이미 캐시된 태그가 있으면 재사용
        if CompletionTagLoadThread.cached_tags is not None:
            print("캐시된 태그 사용 (다시 로드하지 않음)")
            self.on_load_completiontag_sucess.emit(CompletionTagLoadThread.cached_tags)
            return
            
        try:
            print("----- 태그 자동 완성 로딩 시작 -----")
            # 경로 변환 - 리소스 경로 사용
            default_path = self.parent.settings.value("path_tag_completion", DEFAULT_TAGCOMPLETION_PATH)
            print(f"기본 태그 파일 경로: {default_path}")
            tag_path = resource_path(default_path)
            print(f"변환된 태그 파일 경로: {tag_path}")
            print(f"파일 존재 여부: {os.path.exists(tag_path)}")
            
            # 파일이 존재하는지 확인
            if not os.path.exists(tag_path):
                print("기본 경로에 파일이 없습니다. 대체 경로 시도...")
                # 대체 경로 시도
                alt_paths = [
                    resource_path("danbooru_tags_post_count.csv"),
                    resource_path("./danbooru_tags_post_count.csv"),
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "danbooru_tags_post_count.csv"),
                    os.path.join(os.getcwd(), "danbooru_tags_post_count.csv")
                ]
                
                for alt_path in alt_paths:
                    print(f"대체 경로 시도: {alt_path}")
                    if os.path.exists(alt_path):
                        tag_path = alt_path
                        print(f"대체 경로 발견: {tag_path}")
                        break
                    else:
                        print(f"  - 파일 없음")
            
            # 태그 파일 다운로드 URL (만약 파일이 없다면)
            download_url = "https://raw.githubusercontent.com/DCP-arca/NAI-Auto-Generator/main/danbooru_tags_post_count.csv"
            
            tag_list = []
            
            # 파일이 없으면 다운로드 시도
            if not os.path.exists(tag_path):
                print(f"태그 파일을 찾을 수 없어 다운로드를 시도합니다: {download_url}")
                try:
                    import requests
                    response = requests.get(download_url)
                    if response.status_code == 200:
                        # 다운로드 성공, 파일 저장
                        save_path = os.path.join(os.getcwd(), "danbooru_tags_post_count.csv")
                        with open(save_path, "wb") as f:
                            f.write(response.content)
                        print(f"태그 파일 다운로드 성공: {save_path}")
                        tag_path = save_path
                    else:
                        print(f"태그 파일 다운로드 실패: {response.status_code}")
                except Exception as e:
                    print(f"다운로드 중 오류 발생: {str(e)}")
            
            # CSV 파일 처리
            if os.path.exists(tag_path):
                print(f"태그 파일 로딩 중: {tag_path}")
                if tag_path.endswith('.csv'):
                    with open(tag_path, "r", encoding='utf8') as f:
                        for line in f:
                            line = line.strip()
                            if ',' in line:  # CSV 형식 확인
                                parts = line.split(',')
                                if len(parts) >= 2:
                                    tag = parts[0]
                                    count = parts[1]
                                    tag_list.append(f"{tag}[{count}]")
                            else:  # 일반 텍스트 형식
                                tag_list.append(line)
                else:
                    with open(tag_path, "r", encoding='utf8') as f:
                        tag_list = [line.strip() for line in f.readlines()]
                        
                print(f"태그 로딩 완료: {len(tag_list)}개 태그")
                
                # 첫 10개 태그 샘플 출력
            if len(tag_list) > 0:
                CompletionTagLoadThread.cached_tags = tag_list
                
                self.on_load_completiontag_sucess.emit(tag_list)
        except Exception as e:
            print(f"태그 로딩 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            self.on_load_completiontag_sucess.emit([])
            
        print("----- 태그 자동 완성 로딩 종료 -----")


class AutoGenerateThread(QThread):
    on_data_created = pyqtSignal()
    on_error = pyqtSignal(int, str)
    on_success = pyqtSignal(str)
    on_end = pyqtSignal()
    on_statusbar_change = pyqtSignal(str, list)

    def __init__(self, parent, count, delay, ignore_error):
        super(AutoGenerateThread, self).__init__(parent)
        self.count = int(count or -1)
        self.delay = float(delay or 0.01)
        self.ignore_error = ignore_error
        self.is_dead = False

    def run(self):
        parent = self.parent()

        count = self.count
        delay = float(self.delay)

        temp_preserve_data_once = False
        while count != 0:
            # 1. Generate

            # generate data
            if not temp_preserve_data_once:
                data = parent._get_data_for_generate()
                parent.nai.set_param_dict(data)
                self.on_data_created.emit()
            temp_preserve_data_once = False

            # set status bar
            if count <= -1:
                self.on_statusbar_change.emit("AUTO_GENERATING_INF", [])
            else:
                self.on_statusbar_change.emit("AUTO_GENERATING_COUNT", [
                    self.count, self.count - count + 1])

            # before generate, if setting batch
            path = parent.settings.value(
                "path_results", DEFAULT_PATH["path_results"])
            create_folder_if_not_exists(path)
            if parent.list_settings_batch_target:
                setting_path = parent.list_settings_batch_target[parent.index_settings_batch_target]
                setting_name = get_filename_only(setting_path)
                path = path + "/" + setting_name
                create_folder_if_not_exists(path)

            # generate image
            error_code, result_str = _threadfunc_generate_image(
                self, path)
            if self.is_dead:
                return
            if error_code == 0:
                self.on_success.emit(result_str)
            else:
                if self.ignore_error:
                    for t in range(int(delay), 0, -1):
                        self.on_statusbar_change.emit("AUTO_ERROR_WAIT", [t])
                        time.sleep(1)
                        if self.is_dead:
                            return

                    temp_preserve_data_once = True
                    continue
                else:
                    self.on_error.emit(error_code, result_str)
                    return

            # 2. Wait
            count -= 1
            if count != 0:
                temp_delay = delay
                for x in range(int(delay)):
                    self.on_statusbar_change.emit("AUTO_WAIT", [temp_delay])
                    time.sleep(1)
                    if self.is_dead:
                        return
                    temp_delay -= 1

        self.on_end.emit()

    def stop(self):
        self.is_dead = True
        self.quit()


def _threadfunc_generate_image(thread_self, path):
    # 1 : get image
    parent = thread_self.parent()
    nai = parent.nai
    action = NAIAction.generate
    if nai.parameters["image"]:
        action = NAIAction.img2img
    if nai.parameters['mask']:
        action = NAIAction.infill
    
    data = nai.generate_image(action)
    
    if not data:
        return 1, "서버에서 정보를 가져오는데 실패했습니다."

    # 2 : open image
    try:
        zipped = zipfile.ZipFile(io.BytesIO(data))
        image_bytes = zipped.read(zipped.infolist()[0])
        img = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        return 2, str(e) + str(data)

    # 3 : save image
    create_folder_if_not_exists(path)
    dst = ""
    if parent.dict_img_batch_target["img2img_foldersrc"] and bool(thread_self.parent().settings.value("will_savename_i2i", False)):
        filename = get_filename_only(parent.i2i_settings_group.src)
        extension = ".png"
        dst = os.path.join(path, filename + extension)
        while os.path.isfile(dst):
            filename += "_"
            dst = os.path.join(path, filename + extension)
    else:
        timename = datetime.datetime.now().strftime(
            "%y%m%d_%H%M%S%f")[:-4]
        filename = timename
        if bool(thread_self.parent().settings.value("will_savename_prompt", True)):
            filename += "_" + nai.parameters["prompt"]
        dst = create_windows_filepath(path, filename, ".png")
        if not dst:
            dst = timename
    try:
        img.save(dst)
    except Exception as e:
        return 3, str(e)

    return 0, dst


class GenerateThread(QThread):
    generate_result = pyqtSignal(int, str)

    def __init__(self, parent):
        super(GenerateThread, self).__init__(parent)

    def run(self):
        path = self.parent().settings.value(
            "path_results", DEFAULT_PATH["path_results"])
        error_code, result_str = _threadfunc_generate_image(self, path)

        self.generate_result.emit(error_code, result_str)


class TokenValidateThread(QThread):
    validation_result = pyqtSignal(int)

    def __init__(self, parent):
        super(TokenValidateThread, self).__init__(parent)

    def run(self):
        is_login_success = self.parent().nai.check_logged_in()

        self.validation_result.emit(0 if is_login_success else 1)


class AnlasThread(QThread):
    anlas_result = pyqtSignal(int)

    def __init__(self, parent):
        super(AnlasThread, self).__init__(parent)

    def run(self):
        anlas = self.parent().nai.get_anlas() or -1

        self.anlas_result.emit(anlas)


def apply_theme(self):
    # Get settings
    theme_mode = self.settings.value("theme_mode", "기본 테마 (System Default)")
    accent_color = self.settings.value("accent_color", "#2196F3")
    font_size = self.settings.value("nag_font_size", 18)
    
    # Base stylesheet
    style = f"""
    QWidget {{
        font-size: {font_size}px;
    }}
    """
    
    # Dark Theme
    if "어두운" in theme_mode:
        style += """
        QWidget {
            background-color: #2D2D2D;
            color: #FFFFFF;  /* 텍스트 색상을 흰색으로 설정 */
        }
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #404040;
            color: #FFFFFF;  /* 입력 필드의 텍스트 색상도 흰색으로 설정 */
            border: 1px solid #555555;
        }
        QComboBox {
            background-color: #404040;
            color: #FFFFFF;  /* 콤보박스 텍스트 색상 */
            border: 1px solid #555555;
        }
        QComboBox QAbstractItemView {
            background-color: #404040;
            color: #FFFFFF;  /* 콤보박스 드롭다운 텍스트 색상 */
            selection-background-color: """ + accent_color + """;
        }
        QLabel {
            color: #FFFFFF;  /* 라벨 텍스트 색상 */
        }
        QCheckBox, QRadioButton {
            color: #FFFFFF;  /* 체크박스와 라디오 버튼 텍스트 색상 */
        }
        QPushButton {
            background-color: """ + accent_color + """;
            color: white;
            border: none;
            padding: 5px;
        }
        QGroupBox {
            color: #FFFFFF;  /* 그룹박스 제목 색상 */
            border: 1px solid #555555;
        }
        QTextBrowser {
            background-color: #404040;
            color: #FFFFFF;
        }
        """
    # Light Theme
    elif "밝은" in theme_mode:
        style += """
        QWidget {
            background-color: #F5F5F5;
            color: #000000;
        }
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #FFFFFF;
            color: #000000;
            border: 1px solid #CCCCCC;
        }
        QComboBox {
            background-color: #FFFFFF;
            color: #000000;
            border: 1px solid #CCCCCC;
        }
        QPushButton {
            background-color: """ + accent_color + """;
            color: white;
            border: none;
            padding: 5px;
        }
        """
    
    # Apply the style
    self.app.setStyleSheet(style)
    
    # Special handling for progress bars etc
    if "어두운" in theme_mode:
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor("#2D2D2D"))
        dark_palette.setColor(QPalette.WindowText, QColor("#FFFFFF"))
        dark_palette.setColor(QPalette.Base, QColor("#404040"))
        dark_palette.setColor(QPalette.AlternateBase, QColor("#353535"))
        dark_palette.setColor(QPalette.ToolTipBase, QColor("#2D2D2D"))
        dark_palette.setColor(QPalette.ToolTipText, QColor("#FFFFFF"))
        dark_palette.setColor(QPalette.Text, QColor("#FFFFFF"))
        dark_palette.setColor(QPalette.Button, QColor("#353535"))
        dark_palette.setColor(QPalette.ButtonText, QColor("#FFFFFF"))
        dark_palette.setColor(QPalette.BrightText, QColor("#FF0000"))
        dark_palette.setColor(QPalette.Link, QColor(accent_color))
        dark_palette.setColor(QPalette.Highlight, QColor(accent_color))
        dark_palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        self.app.setPalette(dark_palette)
    elif "밝은" in theme_mode:
        light_palette = QPalette()
        light_palette.setColor(QPalette.Window, QColor("#F5F5F5"))
        light_palette.setColor(QPalette.WindowText, QColor("#000000"))
        light_palette.setColor(QPalette.Base, QColor("#FFFFFF"))
        light_palette.setColor(QPalette.AlternateBase, QColor("#F0F0F0"))
        light_palette.setColor(QPalette.ToolTipBase, QColor("#FFFFFF"))
        light_palette.setColor(QPalette.ToolTipText, QColor("#000000"))
        light_palette.setColor(QPalette.Text, QColor("#000000"))
        light_palette.setColor(QPalette.Button, QColor("#F0F0F0"))
        light_palette.setColor(QPalette.ButtonText, QColor("#000000"))
        light_palette.setColor(QPalette.BrightText, QColor("#000000"))
        light_palette.setColor(QPalette.Link, QColor(accent_color))
        light_palette.setColor(QPalette.Highlight, QColor(accent_color))
        light_palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        self.app.setPalette(light_palette)
    else:
        # 기본 테마일 경우 시스템 기본 팔레트 사용
        self.app.setPalette(self.palette)


def toggle_debug_mode(self):
    """디버그 모드 토글"""
    self.debug_mode = not getattr(self, 'debug_mode', False)
    
    # 로그 레벨 조정
    if self.debug_mode:
        logging.getLogger('nai_generator').setLevel(logging.DEBUG)
        QMessageBox.information(self, "디버그 모드", "디버그 모드가 활성화되었습니다. 자세한 로그가 콘솔과 로그 파일에 기록됩니다.")
    else:
        logging.getLogger('nai_generator').setLevel(logging.INFO)
        QMessageBox.information(self, "디버그 모드", "디버그 모드가 비활성화되었습니다.")
        
    # 디버그 모드 설정 저장
    self.settings.setValue("debug_mode", self.debug_mode)

if __name__ == '__main__':
    input_list = sys.argv
    app = QApplication(sys.argv)

    widget = NAIAutoGeneratorWindow(app)

    time.sleep(0.1)

    sys.exit(app.exec_())