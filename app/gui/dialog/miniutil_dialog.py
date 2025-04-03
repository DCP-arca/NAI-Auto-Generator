import os
import sys
from io import BytesIO
from PIL import Image
from urllib import request

from PyQt5.QtWidgets import QApplication, QTextEdit, QFrame, QFileDialog, QLabel, QVBoxLayout, QDialog, QMessageBox
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QRectF, QSize, pyqtSignal

from core.worker.danbooru_tagger import DanbooruTagger

from core.worker.naiinfo_getter import get_naidict_from_file, get_naidict_from_txt, get_naidict_from_img

from util.image_util import pil2pixmap
from util.file_util import resource_path
from util.tagger_util import predict_tag_from
from util.string_util import prettify_naidict

from config.paths import DEFAULT_PATH, PATH_IMG_TAGGER, PATH_IMG_GETTER

class BackgroundFrame(QFrame):
    clicked = pyqtSignal()

    def __init__(self, parent, opacity):
        super(BackgroundFrame, self).__init__(parent)
        self.image = QImage()
        self.opacity = opacity

    def set_background_image_by_src(self, image_path):
        self.image.load(image_path)
        self.update()

    def set_background_image_by_img(self, image):
        self.image = pil2pixmap(image).toImage()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        scaled_image = self.image.scaled(
            self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        target_rect = QRectF(
            (self.width() - scaled_image.width()) / 2,
            (self.height() - scaled_image.height()) / 2,
            scaled_image.width(),
            scaled_image.height())
        painter.setOpacity(self.opacity)
        painter.drawImage(target_rect, scaled_image)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            self.update()
            return True
        return super(BackgroundFrame, self).eventFilter(obj, event)

    def mousePressEvent(self, ev):
        self.clicked.emit()


class DoubleClickableTextEdit(QTextEdit):
    doubleclicked = pyqtSignal()

    def mouseDoubleClickEvent(self, ev):
        self.doubleclicked.emit()


class MiniUtilDialog(QDialog):
    def __init__(self, parent, mode):
        super(MiniUtilDialog, self).__init__(parent)
        self.mode = mode
        self.setAcceptDrops(True)
        self.setWindowTitle("태그 확인기" if self.mode ==
                            "tagger" else "이미지 정보 확인기")

        # 레이아웃 설정
        layout = QVBoxLayout()
        frame = BackgroundFrame(self, opacity=0.3)
        frame.set_background_image_by_src(resource_path(
            PATH_IMG_TAGGER if self.mode == "tagger" else PATH_IMG_GETTER))
        self.frame = frame
        self.parent().installEventFilter(frame)
        frame.setFixedSize(QSize(512, 512))
        frame.setStyleSheet("""QLabel{
            font-size:30px;
            }
            QTextEdit{
            font-size:20px;
            background-color:#00000000;
            }""")

        inner_layout = QVBoxLayout()
        label1 = QLabel("Double Click Me")
        label1.setAlignment(Qt.AlignCenter)
        inner_layout.addWidget(label1)
        label_content = DoubleClickableTextEdit("")
        label_content.setReadOnly(True)
        label_content.setAcceptRichText(False)
        label_content.setFrameStyle(QFrame.NoFrame)
        label_content.setAlignment(Qt.AlignCenter)
        inner_layout.addWidget(label_content, stretch=999)
        label2 = QLabel("Or Drag-Drop Here")
        label2.setAlignment(Qt.AlignCenter)
        inner_layout.addWidget(label2)
        frame.setLayout(inner_layout)

        label_content.doubleclicked.connect(self.show_file_minidialog)

        self.label_content = label_content
        self.label1 = label1
        self.label2 = label2

        layout.addWidget(frame)
        self.setLayout(layout)

    def set_content(self, src, nai_dict):
        if isinstance(src, str) and os.path.isfile(src):
            self.frame.set_background_image_by_src(src)
        else:
            self.frame.set_background_image_by_img(src)
        self.frame.opacity = 0.1
        self.label1.setVisible(False)
        self.label2.setVisible(False)
        self.label_content.setEnabled(True)
        self.label_content.setText(nai_dict)

    def execute(self, filemode, target):
        if self.mode == "getter":
            if filemode == "src":
                nai_dict, error_code = get_naidict_from_file(
                    target)
            elif filemode == "img":
                nai_dict, error_code = get_naidict_from_img(
                    target)
            elif filemode == "txt":
                nai_dict, error_code = get_naidict_from_txt(
                    target)

            if nai_dict and error_code == 0:
                target_dict = {
                    "prompt": nai_dict["prompt"],
                    "negative_prompt": nai_dict["negative_prompt"]
                }
                target_dict.update(nai_dict["option"])
                target_dict.update(nai_dict["etc"])

                if 'reference_strength' in target_dict:
                    rs_float = 0.0
                    try:
                        rs_float = float(target_dict['reference_strength'])
                    except Exception as e:
                        pass
                    if rs_float > 0:
                        target_dict["reference_image"] = "True"
                if "request_type" in target_dict and target_dict["request_type"] == "Img2ImgRequest":
                    target_dict["image"] = "True"

                self.set_content(target, prettify_naidict(target_dict))

                return
        elif self.mode == "tagger":
            window = self.parent()
            result = predict_tag_from(window, filemode, target, True)

            if result:
                self.set_content(target, result)
                return
        QMessageBox.information(
            self, '경고', "불러오는 중에 오류가 발생했습니다.")

    def show_file_minidialog(self):
        select_dialog = QFileDialog()
        select_dialog.setFileMode(QFileDialog.ExistingFile)
        fname, _ = select_dialog.getOpenFileName(
            self, '불러올 파일을 선택해 주세요.', '',
            '이미지 파일(*.png *.webp)' if self.mode == "tagger" else
            '이미지, 텍스트 파일(*.txt *.png *.webp)')

        if fname:
            if self.mode == "tagger":
                if fname.endswith(".png") or fname.endswith(".webp"):
                    self.execute("src", fname)
                else:
                    QMessageBox.information(
                        self, '경고', "png, webp, txt 파일만 가능합니다.")
                    return
            else:
                if fname.endswith(".png") or fname.endswith(".webp"):
                    self.execute("src", fname)
                elif fname.endswith(".txt"):
                    self.execute("txt", fname)
                    QMessageBox.information(
                        self, '경고', "png, webp 또는 폴더만 가능합니다.")
                    return

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
            if fname.endswith(".png") or fname.endswith(".webp"):
                self.execute("src", fname)
                return
            elif fname.endswith(".txt"):
                if self.mode == "getter":
                    self.execute("txt", fname)
                    return
            elif fname.endswith('.jpg') and self.mode == 'tagger':
                self.execute("src", fname)
                return

            if self.mode == "getter":
                QMessageBox.information(
                    self, '경고', "세팅 불러오기는 png, webp, txt 파일만 가능합니다.")
            else:
                QMessageBox.information(
                    self, '경고', "태그 불러오기는 jpg, png, webp 파일만 가능합니다.")
        else:
            try:
                url = furl.url()
                res = request.urlopen(url).read()
                img = Image.open(BytesIO(res))
                if img:
                    self.execute("img", img)

            except Exception as e:
                print(e)
                QMessageBox.information(self, '경고', "이미지 파일 다운로드에 실패했습니다.")
                return


if __name__ == '__main__':
    app = QApplication(sys.argv)
    from PyQt5.QtWidgets import QMainWindow
    from PyQt5.QtCore import QSettings
    qw = QMainWindow()
    qw.move(200, 200)
    TOP_NAME = "dcp_arca"
    APP_NAME = "nag_gui"
    qw.settings = QSettings(TOP_NAME, APP_NAME)
    qw.dtagger = DanbooruTagger(qw.settings.value(
        "path_models", os.path.abspath(DEFAULT_PATH["path_models"])))
    loading_dialog = MiniUtilDialog(qw, "getter")
    if loading_dialog.exec_() == QDialog.Accepted:
        print(len(loading_dialog.result))
