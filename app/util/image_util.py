import os
import random
import io
import base64

from PIL import Image

from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QBuffer


def convert_qimage_to_imagedata(qimage):
    try:
        buf = QBuffer()
        buf.open(QBuffer.ReadWrite)
        qimage.save(buf, "PNG")
        pil_im = Image.open(io.BytesIO(buf.data()))

        buf = io.BytesIO()
        pil_im.save(buf, format='png', quality=100)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception:
        return ""


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


def pil2pixmap(im):
    if im.mode == "RGB":
        r, g, b = im.split()
        im = Image.merge("RGB", (b, g, r))
    elif im.mode == "RGBA":
        r, g, b, a = im.split()
        im = Image.merge("RGBA", (b, g, r, a))
    elif im.mode == "L":
        im = im.convert("RGBA")
    # Bild in RGBA konvertieren, falls nicht bereits passiert
    im2 = im.convert("RGBA")
    data = im2.tobytes("raw", "RGBA")
    qim = QImage(
        data, im.size[0], im.size[1], QImage.Format_ARGB32)
    pixmap = QPixmap.fromImage(qim)
    return pixmap
