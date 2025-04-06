from PyQt5.QtWidgets import QWidget, QGroupBox, QFrame, QFileDialog,QLabel,QScrollArea, QVBoxLayout, QHBoxLayout, QPushButton, QDialog
from PyQt5.QtGui import QPixmap, QImage, QPainter
from PyQt5.QtCore import Qt, QSize, QRectF, QEvent

from gui.widget.custom_slider_widget import CustomSliderWidget
from gui.widget.result_image_view import ResultImageView

from gui.dialog.inpaint_dialog import InpaintDialog

from util.image_util import convert_src_to_imagedata

from config.paths import PATH_IMG_OPEN_IMAGE, PATH_IMG_IMAGE_CLEAR
from config.themes import COLOR 

PADDING_IMAGE_ITEM = 15
HEIGHT_IMAGE_ITEM = 150
MAXHEIGHT_IMAGE_ITEM = 250

VIBE_SLIDER_OPTION1 = {
    "title": "Information Extracted:",
    "min_value": 1,
    "max_value": 100,
    "edit_width": 50,
    "mag": 100
}
VIBE_SLIDER_OPTION2 = {
    "title": "Reference Strength:  ",
    "min_value": 1,
    "max_value": 100,
    "edit_width": 50,
    "mag": 100
}
I2I_SLIDER_OPTION1 = {
    "title":"Strength:",
    "min_value":1,
    "max_value":99,
    "edit_width":50,
    "mag":100
}
I2I_SLIDER_OPTION2 = {
    "title": "Noise:   ",
    "min_value": 0,
    "max_value": 99,
    "edit_width": 50,
    "mag": 100
}


class ImageFrame(QFrame):
    def __init__(self, parent=None):
        super(ImageFrame, self).__init__(parent)

        self.image = QImage()

    def set_image_by_src(self, image_path):
        self.image.load(image_path)
        self.update()

    def set_image_by_img(self, image):
        self.image = image
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
        painter.drawImage(target_rect, scaled_image)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            self.update()
            return True
        return super(ImageFrame, self).eventFilter(obj, event)

# CustomSliderWidget을 QWidget처럼 사용하기 위한 컨테이너 클래스
class CustomSliderWidgetContainer(QWidget):
    def __init__(self, **option_dict):
        super().__init__()
        layout = CustomSliderWidget(**option_dict)
        self.setLayout(layout)
        # CustomSliderWidget 내부에서 slider를 속성으로 저장했으므로 그대로 노출
        self.slider = layout.slider
        self.edit = layout.edit

class ImageItem(QWidget):
    def __init__(self, parent, is_i2i, image_path, parent_layout, settings, remove_callback, index, on_click_inpaint_button=None):
        super().__init__(parent)
        self.is_i2i = is_i2i
        self.image_path = image_path
        self.parent_layout = parent_layout
        self.settings = settings
        self.remove_callback = remove_callback
        self.index = index  # 생성 시 할당된 인덱스

        # 초기 작업
        self.setFixedHeight(HEIGHT_IMAGE_ITEM)  # 각 아이템 높이 HEIGHT_IMAGE_ITEM
        self.imagedata = convert_src_to_imagedata(image_path)

        # 전체 레이아웃 (HBox: 좌측 이미지, 우측 슬라이더 영역)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # 좌측: 이미지 프레임 (HEIGHT_IMAGE_ITEM)
        image_frame = ImageFrame()
        # image_frame.setStyleSheet("border: 1px solid gray;")
        image_frame.setFixedSize(HEIGHT_IMAGE_ITEM, HEIGHT_IMAGE_ITEM)
        image_frame.set_image_by_src(self.image_path)
        delete_button = QPushButton("X", image_frame)
        delete_button.setFixedSize(24, 24)
        delete_button.setStyleSheet("background-color: red; color: white; border-radius: 12px;")
        delete_button.move(15, 15)
        delete_button.clicked.connect(self.delete_self)
        main_layout.addWidget(image_frame)
        self.image_frame = image_frame

        # 우측: 슬라이더 영역 (VBox)
        slider_vbox = QVBoxLayout()
        slider_vbox.setSpacing(10)
        slider_vbox.setContentsMargins(0, 0, 0, 0)

        # 저장된 값 복원 (저장된 값이 없으면 기본값 50)
        mode_str = "i2i" if self.is_i2i else "vibe"
        val1 = int(self.settings.value(f"{mode_str}_slider_value_{self.index}_1", 50))
        val2 = int(self.settings.value(f"{mode_str}_slider_value_{self.index}_2", 50))

        # CustomSliderWidgetContainer로 슬라이더1 생성
        slider1_options=I2I_SLIDER_OPTION1 if self.is_i2i else VIBE_SLIDER_OPTION1
        slider1_options["default_value"] = val1
        slider1_options["slider_text_lambda"] = lambda value: "%.2f" % (value / 100)
        custom_slider1 = CustomSliderWidgetContainer(**slider1_options)
        # 슬라이더 값 변경 시 QSettings에 저장
        custom_slider1.slider.valueChanged.connect(lambda value: self.slider_value_changed(value, 1))
        slider_vbox.addWidget(custom_slider1, stretch=9)
        self.custom_slider1 = custom_slider1

        # CustomSliderWidgetContainer로 슬라이더2 생성
        slider2_options=I2I_SLIDER_OPTION2 if self.is_i2i else VIBE_SLIDER_OPTION2
        slider2_options["default_value"] = val2
        slider2_options["slider_text_lambda"] = lambda value: "%.2f" % (value / 100)
        custom_slider2 = CustomSliderWidgetContainer(**slider2_options)
        # 슬라이더 값 변경 시 QSettings에 저장
        custom_slider2.slider.valueChanged.connect(lambda value: self.slider_value_changed(value, 2))
        slider_vbox.addWidget(custom_slider2, stretch=9)
        self.custom_slider2 = custom_slider2

        main_layout.addLayout(slider_vbox)

        # i2i는 인페인트 버튼 추가
        if is_i2i:
            inpaint_button = QPushButton("인페인트")
            main_layout.addWidget(inpaint_button)
            self.inpaint_button = inpaint_button
            if on_click_inpaint_button:
                inpaint_button.clicked.connect(lambda: on_click_inpaint_button(self.image_path))

    def slider_value_changed(self, value, slider_num):
        # 슬라이더 값 변경 시 QSettings에 저장
        mode_str = "i2i" if self.is_i2i else "vibe"
        key = f"{mode_str}_slider_value_{self.index}_{slider_num}"
        self.settings.setValue(key, value)

    def change_image(self, qimage, is_mask_applied):
        if is_mask_applied:
            self.inpaint_button.setStyleSheet("""
                    background-color: """ + COLOR.BUTTON_AUTOGENERATE + """;
                    background-position: center;
                    color: white;
                """)
        else:
            self.inpaint_button.setStyleSheet("")
        self.image_frame.set_image_by_img(qimage)

    def delete_self(self):
        self.parent_layout.removeWidget(self)
        self.deleteLater()
        if self.remove_callback:
            self.remove_callback()

    def value(self):
        return [self.imagedata, self.custom_slider1.edit.text(), self.custom_slider2.edit.text()]

class ButtonsWidget(QWidget):
    def __init__(self, mode, add_callback, clear_callback=None, parent=None):
        """
        mode: "initial"이면 add.png와 folder.png 버튼,
              "normal"이면 add.png와 clear 버튼.
        """
        super().__init__(parent)
        self.mode = mode
        self.add_callback = add_callback
        self.clear_callback = clear_callback
        self.setFixedHeight(HEIGHT_IMAGE_ITEM)
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        def create_open_button(img_src, func=None):
            open_button = ResultImageView(
                img_src)
            open_button.setStyleSheet("""
                background-color: """ + COLOR.BRIGHT + """;
                background-position: center
            """)
            open_button.setFixedSize(QSize(80, 80))
            if func:
                open_button.clicked.connect(func)
            return open_button

        # add 버튼 (add.png 아이콘)
        layout.addStretch(1)
        self.add_button = create_open_button(PATH_IMG_OPEN_IMAGE, self.add_callback)
        layout.addWidget(self.add_button)
        if mode == "initial":
            pass
        elif mode == "normal":
            layout.addStretch(1)
            # clear 버튼 (Clear 텍스트)
            self.clear_button = create_open_button(PATH_IMG_IMAGE_CLEAR, self.clear_callback)
            layout.addWidget(self.clear_button)
        layout.addStretch(1)

class ImageLayout(QWidget):
    def __init__(self, parent, title, is_i2i):
        super().__init__(parent)

        self.mask = None

        self.settings = parent.settings
        self.is_i2i = is_i2i

        main_layout = QVBoxLayout(self)
        groupbox = QGroupBox(title)
        main_layout.addWidget(groupbox)
        grouplayout = QVBoxLayout(groupbox)

        main_layout.setContentsMargins(0,0,0,0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        grouplayout.addWidget(self.scroll_area)
        
        self.container = QWidget()
        self.scroll_layout = QVBoxLayout(self.container)
        self.scroll_layout.setSpacing(PADDING_IMAGE_ITEM)
        self.container.setLayout(self.scroll_layout)
        self.scroll_area.setWidget(self.container)

        # 처음엔 아무 아이템도 없으므로 초기 모드 버튼 위젯 추가 (높이 HEIGHT_IMAGE_ITEM)
        self.buttons_widget = self.create_buttons_widget("initial")
        self.scroll_layout.addWidget(self.buttons_widget)
        self.update_container_height()

    def create_buttons_widget(self, mode):
        """mode에 따라 ButtonsWidget 생성"""
        if mode == "initial":
            return ButtonsWidget(mode, add_callback=self.on_click_add_item)
        else:
            return ButtonsWidget(mode, add_callback=self.on_click_add_item, clear_callback=self.clear_all_items)

    def on_click_add_item(self):
        """파일 다이얼로그를 통해 이미지 선택 후, ImageItem 추가 (버튼 위젯 교체)"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.webp)")
        if file_dialog.exec_():
            image_path = file_dialog.selectedFiles()[0]

            self._add_item(image_path)

    def _add_item(self, image_path):
        # 마지막 위젯(버튼 위젯)이 있으면 제거
        last_index = self.scroll_layout.count() - 1
        last_widget = self.scroll_layout.itemAt(last_index).widget()
        if isinstance(last_widget, ButtonsWidget):
            self.scroll_layout.removeWidget(last_widget)
            last_widget.deleteLater()
        # 새 ImageItem 생성 시 현재 count()를 인덱스로 사용
        new_item = ImageItem(self, self.is_i2i, image_path, self.scroll_layout, 
                             settings=self.settings,
                             remove_callback=self.on_click_remove_button,
                             index=self.scroll_layout.count(),
                             on_click_inpaint_button=self.on_click_inpaint_button)
        self.scroll_layout.addWidget(new_item)
        # 새 버튼 위젯 (normal 모드: add와 clear 버튼) 추가
        if not self.is_i2i:
            new_buttons = self.create_buttons_widget("normal")
            self.scroll_layout.addWidget(new_buttons)
        self.update_container_height()

    def update_container_height(self):
        # """컨테이너 높이 계산 (최대 700)
        #    계산: height = PADDING_IMAGE_ITEM (top padding) + (count * HEIGHT_IMAGE_ITEM) + ((count+1)*PADDING_IMAGE_ITEM)
        #    예) 0개: PADDING_IMAGE_ITEM, 1개: PADDING_IMAGE_ITEM+HEIGHT_IMAGE_ITEM+PADDING_IMAGE_ITEM, 2개: PADDING_IMAGE_ITEM+HEIGHT_IMAGE_ITEM+PADDING_IMAGE_ITEM+HEIGHT_IMAGE_ITEM+PADDING_IMAGE_ITEM, ... 최대 700
        # """
        # calc_height = PADDING_IMAGE_ITEM + count * HEIGHT_IMAGE_ITEM + (count + 1) * PADDING_IMAGE_ITEM
        count = self.scroll_layout.count()
        self.scroll_area.setFixedHeight(180 if count <= 1 else MAXHEIGHT_IMAGE_ITEM)

    def on_click_remove_button(self):
        if self.is_i2i:
            self.mask = None
            self.buttons_widget = self.create_buttons_widget("initial")
            self.scroll_layout.addWidget(self.buttons_widget)
        self.update_container_height()

    def clear_all_items(self):
        """Clear 버튼 클릭 시 모든 아이템과 버튼 위젯 제거, QSettings 초기화"""
        while self.scroll_layout.count() > 0:
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        # 초기 상태: 초기 모드 버튼 위젯 추가
        init_buttons = self.create_buttons_widget("initial")
        self.scroll_layout.addWidget(init_buttons)
        self.update_container_height()

    def on_click_inpaint_button(self, src):
        if self.is_i2i:
            last_widget = self.scroll_layout.itemAt(0).widget()
            if isinstance(last_widget, ImageItem):
                img = QImage(src)
                mask = self.mask if self.mask else None

                d = InpaintDialog(img, mask)
                if d.exec_() == QDialog.Accepted:
                    is_mask_applied = d.mask_only != None

                    last_widget.change_image(d.mask_add, is_mask_applied)
                    self.mask = d.mask_only

    # i2i는 [img, slider1, slider2, mask_only]
    # vibe는 [[img, slider1, slider2]]
    def get_nai_param(self):
        result = []
        if self.is_i2i:
            last_widget = self.scroll_layout.itemAt(0).widget()
            if isinstance(last_widget, ImageItem):
                result = last_widget.value()

                if self.mask:
                    result.append(self.mask)
        else:
            for i in range(self.scroll_layout.count()):
                item = self.scroll_layout.itemAt(i)
                widget = item.widget()
                if isinstance(widget, ImageItem):
                    values = widget.value()
                    if values[0]:
                        result.append(values)
        return result
        
def init_image_options_layout(self):
    image_options_layout = QVBoxLayout()

    # I2I Settings Group
    i2i_settings_group = ImageLayout(self, title="I2I Settings", is_i2i=True)
    image_options_layout.addWidget(i2i_settings_group )

    vibe_settings_group = ImageLayout(self, title="Vibe Settings", is_i2i=False)
    image_options_layout.addWidget(vibe_settings_group )

    image_options_layout.addStretch()

    # Assign
    self.i2i_settings_group = i2i_settings_group
    self.vibe_settings_group = vibe_settings_group
    # self.dict_ui_settings["strength"] = i2i_settings_group.slider_1.edit
    # self.dict_ui_settings["noise"] = i2i_settings_group.slider_2.edit
    # self.dict_ui_settings["reference_information_extracted"] = vibe_settings_group.slider_1.edit
    # self.dict_ui_settings["reference_strength"] = vibe_settings_group.slider_2.edit

    return image_options_layout
