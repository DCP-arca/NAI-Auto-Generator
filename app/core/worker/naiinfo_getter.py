from PIL import Image
import json

from core.worker.stealth_pnginfo import read_info_from_image_stealth

TARGETKEY_NAIDICT_OPTION = ("steps", "height", "width",
                            "scale", "seed", "sampler", "n_samples", "sm", "sm_dyn")


def _get_infostr_from_img(img):
    exif = None
    pnginfo = None

    # exif
    if img.info:
        try:
            exif = json.dumps(img.info)
        except Exception as e:
            print("[_get_infostr_from_img]", e)

    # stealth pnginfo
    try:
        pnginfo = read_info_from_image_stealth(img)
    except Exception as e:
        print("[_get_infostr_from_img]", e)

    return exif, pnginfo


def _get_exifdict_from_infostr(info_str):
    try:
        infoDict = json.loads(info_str)
        if ('Comment' in infoDict):
            exif_dict = json.loads(infoDict['Comment'])
            return exif_dict
    except Exception as e:
        print("[_get_exifdict_from_infostr]", e)

    return None


def _get_naidict_from_exifdict(exif_dict):
    try:
        nai_dict = {}
        nai_dict["prompt"] = exif_dict["prompt"].strip()
        nai_dict["negative_prompt"] = exif_dict["uc"].strip() if "uc" in exif_dict else exif_dict["negative_prompt"].strip()
        option_dict = {}
        for key in TARGETKEY_NAIDICT_OPTION:
            if key in exif_dict.keys():
                option_dict[key] = exif_dict[key]
        nai_dict["option"] = option_dict

        etc_dict = {}
        for key in exif_dict.keys():
            if key in TARGETKEY_NAIDICT_OPTION + ("uc", "prompt"):
                continue
            etc_dict[key] = exif_dict[key]
        nai_dict["etc"] = etc_dict
        return nai_dict
    except Exception as e:
        print("[_get_naidict_from_exifdict]", e)

    return None


def get_naidict_from_file(src):
    try:
        img = Image.open(src)
        img.load()
    except Exception as e:
        print("[get_naidict_from_file]", e)
        return None, 1

    return get_naidict_from_img(img)


def get_naidict_from_txt(src):
    try:
        with open(src, "r", encoding="utf8") as f:
            info_str = f.read()
        ed = json.loads(info_str)
    except Exception as e:
        print("[get_naidict_from_txt]", e)
        return info_str or "", 1

    nd = _get_naidict_from_exifdict(ed)
    if not nd:
        return ed, 2
    else:
        return nd, 0


def get_naidict_from_img(img):
    exif, pnginfo = _get_infostr_from_img(img)
    if not exif and not pnginfo:
        return None, 1

    ed1 = _get_exifdict_from_infostr(exif)
    ed2 = _get_exifdict_from_infostr(pnginfo)
    if not ed1 and not ed2:
        return exif or pnginfo, 2

    nd1 = _get_naidict_from_exifdict(ed1)
    nd2 = _get_naidict_from_exifdict(ed2)
    if not nd1 and not nd2:
        return exif or pnginfo, 3

    if nd1:
        return nd1, 0
    elif nd2:
        return nd2, 0


if __name__ == "__main__":
    src = "settings/aris_noimage.txt"

    nd = get_naidict_from_txt(src)
    print(nd)