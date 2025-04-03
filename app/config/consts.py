TITLE_NAME = "NAI Auto Generator"
TOP_NAME = "dcp_arca"
APP_NAME = "nag_gui"

MAX_COUNT_FOR_WHILELOOP = 10

DEFAULT_PARAMS = {
    "prompt": "",
    "negative_prompt": "",
    "width": 640,
    "height": 640,
    "seed": -1,
    "extra_noise_seed": -1,
    "sampler": "k_euler_ancestral",
    "steps": 28,
    "sm": True,
    "sm_dyn": True,
    "scale": 5,
    "cfg_rescale": 0,
    "uncond_scale": 1.0,
    "strength": 0.7,
    "noise": 0.0,
    "reference_information_extracted": 1.0,
    "reference_strength": 0.6,
}

DEFAULT_SETTING = {'prompt': '1girl, {aris_{{blue_archive}}}, {Character:Tendou Aris{{Blue Archive}}}, {{{chibi}}}, ?, question mark, {grab a pencil}, white eyes, white background, simple background, {looking at viewer}, oversimplified, {{icon}}, best quality, amazing quality, very aesthetic, absurdres', 'negative_prompt':
                   'nsfw, lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, bad quality, watermark, unfinished, displeasing, chromatic aberration, signature, extra digits, artistic error, username, scan, [abstract], smile, lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, bad quality, watermark, unfinished, displeasing, chromatic aberration, signature, extra digits, artistic error, username, scan, [abstract], {{{{{{closed eyes, worst quality, bad quality, buzzcut, pov, text, censored}}}}}}, {{{{bad hands}}}}, {{{bad eyes}}}, {{{undetailed eyes}}}}, text, error, extra digit, fewer digits, jpeg artifacts, signature, watermark, username, reference, {{unfinished}}, {{unclear fingertips}}, {{twist}}, {{Squiggly}}, {{Grumpy}} , {{incomplete}}, {{Imperfect Fingers}}, condom, Disorganized colors ,Cheesy, {{very displeasing}}, {{mess}}, {{Approximate}}, {{Sloppiness}}, Glazed eyes, Glasses, watermark, username, text, signature', 'width': 640, 'height': 640, 'sampler': 'k_euler_ancestral', 'steps': 28, 'seed': 177879407, 'scale': 5.0, 'cfg_rescale': 0.0, 'sm': True, 'sm_dyn': True, 'uncond_scale': 1.0}


DEFAULT_RESOLUTION = "Square (640x640)"

RESOLUTION_ITEMS = [
    "NORMAL",
    "Portrait (832x1216)",
    "Landscape (1216x832)",
    "Square (1024x1024)",
    "LARGE",
    "Portrait (1024x1536)",
    "Landscape (1536x1024)",
    "Square (1472x1472)",
    "WALLPAPER",
    "Portrait (1088x1920)",
    "Landscape (1920x1088)",
    "SMALL",
    "Portrait (512x768)",
    "Landscape (768x512)",
    "Square (640x640)",
    "CUSTOM",
    "Custom",
]
RESOLUTION_ITEMS_NOT_SELECTABLES = [0, 4, 8, 11, 15]

RESOLUTION_FAMILIY = {
    0: ["Portrait (832x1216)", "Landscape (1216x832)", "Square (1024x1024)"],
    1: ["Portrait (1024x1536)", "Landscape (1536x1024)", "Square (1472x1472)"],
    2: ["Portrait (1088x1920)", "Landscape (1920x1088)"],
    3: ["Portrait (512x768)", "Landscape (768x512)", "Square (640x640)"],
    4: []
}
RESOLUTION_FAMILIY_MASK = [
    -1,
    0,
    0,
    0,
    -1,
    1,
    1,
    1,
    -1,
    2,
    2,
    -1,
    3,
    3,
    3,
    -1,
    4
]

SAMPLER_ITEMS = ['k_euler', 'k_euler_ancestral',
                 'k_dpmpp_2s_ancestral', "k_dpmpp_2m", 
                 'k_dpmpp_sde', "k_dpmpp_2m_sde", "ddim_v3"]

DEFAULT_TAGGER_MODEL = "wd-v1-4-moat-tagger-v2"
LIST_TAGGER_MODEL = ("wd-v1-4-moat-tagger-v2",
              "wd-v1-4-convnext-tagger-v2", "wd-v1-4-convnext-tagger",
              "wd-v1-4-convnextv2-tagger-v2", "wd-v1-4-vit-tagger-v2")

