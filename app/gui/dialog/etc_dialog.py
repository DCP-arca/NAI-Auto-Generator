import os
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from config.paths import DEFAULT_PATH

def show_prompt_dialog(self, title, prompt, nprompt):
    QMessageBox.about(self, title,
                      "프롬프트:\n" +
                      prompt +
                      "\n\n" +
                      "네거티브 프롬프트:\n" +
                      nprompt)

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

def show_setting_dialog(self):
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
                self, '경고', "세팅을 불러오는데 실패했습니다.\n\n")
