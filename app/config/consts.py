TITLE_NAME = "NAI Auto Generator"
TOP_NAME = "dcp_arca"
APP_NAME = "nag_gui"

MAX_COUNT_FOR_WHILELOOP = 10

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

DEFAULT_TAGGER_MODEL = "wd-v1-4-moat-tagger-v2"
LIST_TAGGER_MODEL = ("wd-v1-4-moat-tagger-v2",
              "wd-v1-4-convnext-tagger-v2", "wd-v1-4-convnext-tagger",
              "wd-v1-4-convnextv2-tagger-v2", "wd-v1-4-vit-tagger-v2")

