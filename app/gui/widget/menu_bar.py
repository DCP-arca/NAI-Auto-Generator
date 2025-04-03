from PyQt5.QtWidgets import QAction

from gui.dialog.etc_dialog import show_file_dialog

class MenuBar:
    def __init__(self, parent):
        self.parent = parent
        self.menubar = parent.menuBar()
        self.menubar.setNativeMenuBar(False)
        self.init_menu_bar()

    def init_menu_bar(self):
        openAction = QAction('파일 열기(Open file)', self.parent)
        openAction.setShortcut('Ctrl+O')
        openAction.triggered.connect(lambda: show_file_dialog(self.parent, "file"))

        loginAction = QAction('로그인(Log in)', self.parent)
        loginAction.setShortcut('Ctrl+L')
        loginAction.triggered.connect(self.parent.show_login_dialog)

        optionAction = QAction('옵션(Option)', self.parent)
        optionAction.setShortcut('Ctrl+U')
        optionAction.triggered.connect(self.parent.show_option_dialog)

        exitAction = QAction('종료(Exit)', self.parent)
        exitAction.setShortcut('Ctrl+W')
        exitAction.triggered.connect(self.parent.quit_app)

        aboutAction = QAction('만든 이(About)', self.parent)
        aboutAction.triggered.connect(self.parent.show_about_dialog)

        getterAction = QAction('이미지 정보 확인기(Info Getter)', self.parent)
        getterAction.setShortcut('Ctrl+I')
        getterAction.triggered.connect(self.parent.on_click_getter)

        taggerAction = QAction('태그 확인기(Danbooru Tagger)', self.parent)
        taggerAction.setShortcut('Ctrl+T')
        taggerAction.triggered.connect(self.parent.on_click_tagger)

        # 파일 메뉴 생성
        file_menu = self.menubar.addMenu('&파일(Files)')
        file_menu.addAction(openAction)
        file_menu.addAction(loginAction)
        file_menu.addAction(optionAction)
        file_menu.addAction(exitAction)

        # 도구 메뉴 생성
        tool_menu = self.menubar.addMenu('&도구(Tools)')
        tool_menu.addAction(getterAction)
        tool_menu.addAction(taggerAction)

        # 기타 메뉴 생성
        etc_menu = self.menubar.addMenu('&기타(Etc)')
        etc_menu.addAction(aboutAction)
