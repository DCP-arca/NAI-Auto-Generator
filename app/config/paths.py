import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

PATH_IMG_NO_IMAGE = os.path.join(ASSETS_DIR , "no_image.png")
PATH_IMG_OPEN_IMAGE = os.path.join(ASSETS_DIR , "open_image.png")
PATH_IMG_OPEN_FOLDER = os.path.join(ASSETS_DIR , "open_folder.png")
PATH_IMG_TAGGER = os.path.join(ASSETS_DIR , "tagger.png")
PATH_IMG_GETTER = os.path.join(ASSETS_DIR , "getter.png")
PATH_IMG_ICON = os.path.join(ASSETS_DIR , "icon.png")
PATH_IMG_ICON_GETTER = os.path.join(ASSETS_DIR , "icon_getter.png")
PATH_IMG_ICON_TAGGER = os.path.join(ASSETS_DIR , "icon_tagger.png")
PATH_CSV_TAG_COMPLETION = os.path.join(ASSETS_DIR , "danbooru_tags_post_count.csv")

DEFAULT_PATH = {
    "path_results": "results/",
    "path_wildcards": "wildcards/",
    "path_settings": "settings/",
    "path_models": "models/"
}