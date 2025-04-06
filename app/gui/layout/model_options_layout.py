from PyQt5.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QHBoxLayout, QComboBox

from core.worker.nai_generator import MODEL_NAME_DICT


def init_model_options_layout(self):
    layout = QVBoxLayout()

    model_options_group = QGroupBox("Image Settings")
    layout.addWidget(model_options_group)

    model_options_layout = QHBoxLayout()
    model_options_group.setLayout(model_options_layout)

    model_options_layout.addWidget(QLabel("모델: "))
    
    model_combo = QComboBox()
    model_combo.addItems(MODEL_NAME_DICT.keys())
    model_combo.currentTextChanged.connect(self.on_model_changed)
    model_options_layout.addWidget(model_combo, stretch=2)
    
    self.dict_ui_settings["model"] = model_combo
    
    return layout