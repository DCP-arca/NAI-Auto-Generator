from PyQt5.QtWidgets import QSlider, QLabel, QLineEdit, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator

class CustomSliderWidget(QHBoxLayout):
    def __init__(self, **option_dict):
        assert all(key in option_dict for key in [
                   "title", "min_value", "max_value", "default_value", "ui_width", "mag", "slider_text_lambda"])
        super(CustomSliderWidget, self).__init__()

        label = QLabel(option_dict["title"])
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(option_dict["min_value"])
        slider.setMaximum(option_dict["max_value"])
        slider.setValue(int(float(option_dict["default_value"])))

        edit = CustomSliderWidget.CustomLineEdit(option_dict, slider)

        if "gui_nobackground" in option_dict and option_dict["gui_nobackground"]:
            label.setStyleSheet("QLabel{background-color:#00000000}")
            slider.setStyleSheet("QSlider{background-color:#00000000}")

        self.addWidget(label)
        self.addWidget(edit)
        if "enable_percent_label" in option_dict and option_dict["enable_percent_label"]:
            self.addWidget(QLabel("%"))
        self.addWidget(slider)

        self.edit = edit

    class CustomLineEdit(QLineEdit):
        def __init__(self, option_dict, target_slider):
            super(QLineEdit, self).__init__(str(option_dict["default_value"]))
            self.min_value = option_dict["min_value"]
            self.max_value = option_dict["max_value"]
            self.mag = option_dict["mag"]
            self.target_slider = target_slider
            self.slider_text_lambda = option_dict["slider_text_lambda"]

            self.setMinimumWidth(option_dict["ui_width"])
            self.setMaximumWidth(option_dict["ui_width"])
            self.setAlignment(Qt.AlignCenter)
            self.setValidator(QIntValidator(0, 100))

            target_slider.valueChanged.connect(
                lambda value: self.setText(self.slider_text_lambda(value)))
            self.returnPressed.connect(
                self.on_enter_or_focusout)

        def on_enter_or_focusout(self):
            value = self.text()
            if not value:
                value = self.min_value
            value = max(self.min_value, min(
                self.max_value, float(value)))
            value *= self.mag
            self.setText(self.slider_text_lambda(value))
            self.target_slider.setValue(int(value))

        def focusOutEvent(self, event):
            super(CustomSliderWidget.CustomLineEdit, self).focusOutEvent(event)
            self.on_enter_or_focusout()

        def setText(self, text):
            super(CustomSliderWidget.CustomLineEdit, self).setText(text)
            self.target_slider.setValue(int(float(text) * self.mag))