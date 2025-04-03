from PyQt5.QtWidgets import QGroupBox, QLabel, QLineEdit, QCheckBox, QVBoxLayout, QHBoxLayout, QComboBox

from gui.widget.custom_slider_widget import CustomSliderWidget

from config.consts import SAMPLER_ITEMS

def init_parameter_options_layout(self):
    layout = QVBoxLayout()

    # AI Settings Group
    ai_settings_group = QGroupBox("AI Settings")
    layout.addWidget(ai_settings_group)

    ai_settings_layout = QVBoxLayout()
    ai_settings_group.setLayout(ai_settings_layout)

    # Steps Slider
    steps_layout = CustomSliderWidget(
        title="Steps: ",
        min_value=1,
        max_value=50,
        default_value=28,
        ui_width=35,
        mag=1,
        slider_text_lambda=lambda value: "%d" % value
    )
    ai_settings_layout.addLayout(steps_layout, stretch=1)

    lower_layout = QHBoxLayout()
    ai_settings_layout.addLayout(lower_layout, stretch=1)

    lower_slider_layout = QVBoxLayout()
    lower_checkbox_layout = QVBoxLayout()
    lower_layout.addLayout(lower_slider_layout, stretch=2)
    lower_layout.addLayout(lower_checkbox_layout, stretch=1)

    # Seed and Sampler
    seed_layout = QVBoxLayout()
    seed_label_layout = QHBoxLayout()
    seed_label_layout.addWidget(QLabel("시드(Seed)"))
    seed_label_layout.addStretch(1)
    seed_layout.addLayout(seed_label_layout)
    seed_input = QLineEdit()
    seed_input.setPlaceholderText("여기에 시드 입력")
    seed_layout.addWidget(seed_input)
    sampler_layout = QVBoxLayout()
    sampler_layout.addWidget(QLabel("샘플러(Sampler)"))
    sampler_combo = QComboBox()
    sampler_combo.addItems(SAMPLER_ITEMS)
    self.dict_ui_settings["sampler"] = sampler_combo
    sampler_layout.addWidget(sampler_combo)
    lower_slider_layout.addLayout(seed_layout)
    lower_slider_layout.addLayout(sampler_layout)

    # SMEA Checkbox
    seed_opt_layout = QHBoxLayout()
    seed_opt_layout.setContentsMargins(10, 25, 0, 0)
    seed_fix_checkbox = QCheckBox("고정")
    seed_opt_layout.addWidget(seed_fix_checkbox)
    variety_plus_checkbox = QCheckBox("variety+")
    seed_opt_layout.addWidget(variety_plus_checkbox)
    checkbox_layout = QHBoxLayout()
    checkbox_layout.setContentsMargins(10, 30, 0, 0)
    smea_checkbox = QCheckBox("SMEA")
    dyn_checkbox = QCheckBox("+DYN")
    checkbox_layout.addWidget(smea_checkbox, stretch=1)
    checkbox_layout.addWidget(dyn_checkbox, stretch=1)
    lower_checkbox_layout.addLayout(seed_opt_layout)
    lower_checkbox_layout.addLayout(checkbox_layout)

    ########

    # Advanced Settings
    advanced_settings_group = QGroupBox("Advanced Settings")
    advanced_settings_layout = QVBoxLayout()

    # Prompt Guidance Slider

    prompt_guidance_layout = CustomSliderWidget(
        title="Prompt Guidance(CFG):",
        min_value=0,
        max_value=100,
        default_value=5.0,
        ui_width=40,
        mag=10,
        slider_text_lambda=lambda value: "%.1f" % (value / 10)
    )
    advanced_settings_layout.addLayout(prompt_guidance_layout)

    # Prompt Guidance Rescale
    prompt_rescale_layout = CustomSliderWidget(
        title="Prompt Guidance Rescale: ",
        min_value=0,
        max_value=100,
        default_value="0.00",
        ui_width=50,
        mag=100,
        slider_text_lambda=lambda value: "%.2f" % (value / 100)
    )
    advanced_settings_layout.addLayout(prompt_rescale_layout)

    # Undesired Content Strength
    undesired_content_layout = CustomSliderWidget(
        title="Undesired Content Strength:",
        min_value=0,
        max_value=100,
        default_value=100,
        ui_width=40,
        mag=1,
        slider_text_lambda=lambda value: "%d" % value,
        enable_percent_label=True
    )
    advanced_settings_layout.addLayout(undesired_content_layout)

    advanced_settings_group.setLayout(advanced_settings_layout)
    layout.addWidget(advanced_settings_group)

    self.dict_ui_settings["sampler"] = sampler_combo
    self.dict_ui_settings["steps"] = steps_layout.edit
    self.dict_ui_settings["seed"] = seed_input
    self.dict_ui_settings["seed_fix_checkbox"] = seed_fix_checkbox
    self.dict_ui_settings["scale"] = prompt_guidance_layout.edit
    self.dict_ui_settings["cfg_rescale"] = prompt_rescale_layout.edit
    self.dict_ui_settings["variety_plus"] = variety_plus_checkbox
    self.dict_ui_settings["sm"] = smea_checkbox
    self.dict_ui_settings["sm_dyn"] = dyn_checkbox
    self.dict_ui_settings["uncond_scale"] = undesired_content_layout.edit

    return layout