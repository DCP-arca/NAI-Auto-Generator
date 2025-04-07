import os
import sys


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path).replace("\\", "/")


PATH_IMG_NO_IMAGE = resource_path("assets/no_image.png")
PATH_IMG_OPEN_IMAGE = resource_path("assets/open_image.png")
PATH_IMG_OPEN_FOLDER = resource_path("assets/open_folder.png")
PATH_IMG_IMAGE_CLEAR = resource_path("assets/image_clear.png")
PATH_IMG_TAGGER = resource_path("assets/tagger.png")
PATH_IMG_GETTER = resource_path("assets/getter.png")
PATH_IMG_ICON = resource_path("assets/icon.png")
PATH_IMG_ICON_GETTER = resource_path("assets/icon_getter.png")
PATH_IMG_ICON_TAGGER = resource_path("assets/icon_tagger.png")
PATH_CSV_TAG_COMPLETION = resource_path("assets/danbooru_tags_post_count.csv")

DEFAULT_PATH = {
    "path_results": "results/",
    "path_wildcards": "wildcards/",
    "path_settings": "settings/",
    "path_models": "models/"
}
