from hashlib import blake2b
import argon2
from base64 import urlsafe_b64encode
import requests
import json
import io
import zipfile
from PIL import Image

BASE_URL_MAIN = "https://api.novelai.net"
BASE_URL_IMAGE = "https://image.novelai.net/ai/generate-image"


MODEL_NAME_DICT = {
    "NAI Diffusion Anime V3": "nai-diffusion-3",
    "NAI Diffusion V4 Full": "nai-diffusion-4-full",
    "NAI Diffusion V4 Curated": "nai-diffusion-4-curated-preview"
}

MODEL_NAME_INPANT_DIC = {
    "nai-diffusion-3": "nai-diffusion-3-inpainting",
    "nai-diffusion-4-curated-preview": "nai-diffusion-4-curated-inpainting",
    "nai-diffusion-4-full": "nai-diffusion-4-full-inpainting"
}

SAMPLER_ITEMS_V3 = ['k_euler', 'k_euler_ancestral', 'k_dpmpp_2s_ancestral', "k_dpmpp_2m_sde", 
				 "k_dpmpp_2m", 'k_dpmpp_sde', "ddim_v3"]

SAMPLER_ITEMS_V4 = ['k_euler_ancestral', 'k_dpmpp_2s_ancestral', "k_dpmpp_2m_sde",
                 'k_euler', "k_dpmpp_2m",'k_dpmpp_sde']

# 이 dict에 있는 값만 설정 가능.
TARGET_PARAMETERS = {
    "model": "k_euler_ancestral",
    "prompt": "1girl",
    "negative_prompt": "worst quality",
    "width": 640,
    "height": 640,
    "noise_schedule": "karras",
    "sampler": "k_euler_ancestral",
    "steps": 25,
    "seed": 9999999999,
    "scale": 6,
    "cfg_rescale": 0.3,
    "sm": True,
    "sm_dyn": True,
    "variety_plus": True,
    "image": "",  # i2i image
    "mask": "",  # inpant mask
    "strength": 0.7,  # i2i 세팅값1
    "noise": 0.0,  # i2i 세팅값2
    "reference_image_multiple": [],  # 바이브 이미지
    "reference_information_extracted_multiple": [0],  # 바이브 세팅값1
    "reference_strength_multiple": [0],  # 바이스 세팅값2
    "legacy_uc": False,
    "use_coords": False,
    "characterPrompts": []  # DEFAULT_PARAMETER_CHARPROMPTS를 생성해서 넣어야함.
}


DEFAULT_PARAMETER_CHARPROMPTS = {
    "prompt": "girl, ",
    "uc": "lowres, aliasing, ",
    "center": {
        "x": 0.5,
        "y": 0.5
    },
    "enabled": True
}


DEFAULT_PARAMETER_CHARCAPTIONS = {
    "char_caption": "boy, ",
    "centers": [
        {
            "x": 0.1,
            "y": 0.5
        }
    ]
}


V3_PARAMETERS = {
    "params_version": 3,
    "width": 1024,
    "height": 1024,
    "scale": 6,
    "sampler": "k_euler_ancestral",
    "steps": 28,
    "n_samples": 1,
    "ucPreset": 0,
    "qualityToggle": True,
    "sm": False,
    "sm_dyn": False,
    "dynamic_thresholding": False,
    "controlnet_strength": 1,
    "legacy": False,
    "add_original_image": False,
    "cfg_rescale": 0,
    "noise_schedule": "karras",
    "legacy_v3_extend": False,
    "skip_cfg_above_sigma": None,
    "use_coords": False,
    "seed": 9999999999,
    "extra_noise_seed":9999999999,
    "characterPrompts": [],
    "prompt": "1girl",
    "negative_prompt": "nsfw, lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, bad quality, watermark, unfinished, displeasing, chromatic aberration, signature, extra digits, artistic error, username, scan, [abstract], 3d, blender, pixel art, realistic, blurry, lowres, error, film grain, scan artifacts, worst quality, bad quality, jpeg artifacts, very displeasing, chromatic aberration, multiple views, logo, too many watermarks, white blank page, blank page, {{{worst quality, bad quality}}}, normal quality, very displeasing, censored, displeasing, gundam, furry, simple background, logo, sign, glitch, sketch, simple coloring",
    "reference_image_multiple": [],
    "reference_information_extracted_multiple": [],
    "reference_strength_multiple": [],
    "deliberate_euler_ancestral_bug": False,
    "prefer_brownian": True
}

V4_PARAMETERS = {
    "params_version": 3,
    "width": 832,
    "height": 1216,
    "scale": 4.8,
    "sampler": "k_euler_ancestral",
    "steps": 28,
    "n_samples": 1,
    "ucPreset": 2,
    "qualityToggle": False,
    "autoSmea": True,
    "dynamic_thresholding": False,
    "controlnet_strength": 1,
    "legacy": False,
    "add_original_image": True,
    "cfg_rescale": 0.3,
    "noise_schedule": "karras",
    "legacy_v3_extend": False,
    "skip_cfg_above_sigma": None,
    "use_coords": True,
    "v4_prompt": {
        "caption": {
            "base_caption": "1girl",
            "char_captions": [],
        },
        "use_coords": True,
        "use_order": True
    },
    "v4_negative_prompt": {
        "caption": {
            "base_caption": "3d, blender, pixel art, realistic, blurry, lowres, error, film grain, scan artifacts, worst quality, bad quality, jpeg artifacts, very displeasing, chromatic aberration, multiple views, logo, too many watermarks, white blank page, blank page, {{{worst quality, bad quality}}}, normal quality, very displeasing, censored, displeasing, gundam, furry, simple background, logo, sign, glitch, sketch, simple coloring",
            "char_captions": []
        },
        "legacy_uc": False
    },
    "legacy_uc": False,
    "seed": 9999999999,
    "extra_noise_seed":9999999999,
    "characterPrompts": [],
    "negative_prompt": "3d, blender, pixel art, realistic, blurry, lowres, error, film grain, scan artifacts, worst quality, bad quality, jpeg artifacts, very displeasing, chromatic aberration, multiple views, logo, too many watermarks, white blank page, blank page, {{{worst quality, bad quality}}}, normal quality, very displeasing, censored, displeasing, gundam, furry, simple background, logo, sign, glitch, sketch, simple coloring",
    "reference_image_multiple": [],
    "reference_information_extracted_multiple": [],
    "reference_strength_multiple": [],
    "deliberate_euler_ancestral_bug": False,
    "prefer_brownian": True
}


def argon_hash(email: str, password: str, size: int, domain: str) -> str:
    pre_salt = f"{password[:6]}{email}{domain}"
    # salt
    blake = blake2b(digest_size=16)
    blake.update(pre_salt.encode())
    salt = blake.digest()
    raw = argon2.low_level.hash_secret_raw(
        password.encode(),
        salt,
        2,
        int(2000000 / 1024),
        1,
        size,
        argon2.low_level.Type.ID,
    )
    hashed = urlsafe_b64encode(raw).decode()
    return hashed


def _complete_v4_parameters(parameters):
    # prompt
    parameters["v4_prompt"]["caption"]["base_caption"] = parameters["prompt"]

    # prompt -> use_coords
    parameters["v4_prompt"]["use_coords"] = parameters["use_coords"]

    # negative prompt
    parameters["v4_negative_prompt"]["caption"]["base_caption"] = parameters["negative_prompt"]

    # negative prompt -> legacy_uc
    parameters["v4_negative_prompt"]["legacy_uc"] = parameters["legacy_uc"]

    # both -> char_captions
    for target in ["v4_prompt", "v4_negative_prompt"]:
        for char_dict in parameters["characterPrompts"]:
            new_char_dict = DEFAULT_PARAMETER_CHARCAPTIONS.copy()
            new_char_dict["char_captions"] = char_dict["prompt"] if target == "v4_prompt" else char_dict["uc"]
            new_char_dict["centers"][0]["x"] = char_dict["center"]["x"]
            new_char_dict["centers"][0]["y"] = char_dict["center"]["x"]

            parent = parameters[target]["caption"]["char_captions"]
            parent.append(new_char_dict)

    # 바이브도 제거함
    parameters["reference_image_multiple"] = []
    parameters["reference_information_extracted_multiple"]= []
    parameters["reference_strength_multiple"]= []

    # 다음이 포함되어있으면 작동이 안됨.
    del parameters["sm"]
    del parameters["sm_dyn"]
    del parameters["variety_plus"]

def is_now_model_v4(model_key):
    if model_key == "NAI Diffusion V4 Full" or model_key == "NAI Diffusion V4 Curated" or model_key == "nai-diffusion-4-full" or model_key == "nai-diffusion-4-curated-preview":
        return True
    else:
        return False

class NAIGenerator():
    def __init__(self):
        self.access_token = None
        self.username = None
        self.password = None
        self.parameters = {}

    def set_param_dict(self, param_dict):
        allowedKeyList = TARGET_PARAMETERS.keys()
        for key in param_dict.keys():
            assert key in allowedKeyList, "[NAIGenerator.set_param_dict] 허용되지않은 키가 있습니다. " + key

        self.parameters = param_dict

    def try_login(self, username, password):
        # get_access_key
        access_key = argon_hash(username, password, 64,
                                "novelai_data_access_key")[:64]
        try:
            # try login
            response = requests.post(
                f"{BASE_URL_MAIN}/user/login", json={"key": access_key})
            self.access_token = response.json()["accessToken"]

            # if success, save id/pw in
            self.username = username
            self.password = password

            return True
        except Exception as e:
            print(e)

        return False

    def get_anlas(self):
        try:
            response = requests.get(BASE_URL_MAIN + "/user/subscription", headers={
                "Authorization": f"Bearer {self.access_token}"})
            data_dict = json.loads(response.content)
            trainingStepsLeft = data_dict['trainingStepsLeft']
            anlas = int(trainingStepsLeft['fixedTrainingStepsLeft']) + \
                int(trainingStepsLeft['purchasedTrainingSteps'])

            return anlas
        except Exception as e:
            print(e)

        return None

    def generate_image(self):
        parameters = {}

        # model
        model = self.parameters["model"]
        if model in MODEL_NAME_DICT:
            model = MODEL_NAME_DICT[model]
        isV4 = is_now_model_v4(model)

        # action
        action = "generate"
        if "image" in self.parameters and self.parameters['image']:
            action = "img2img"
        if 'mask' in self.parameters and self.parameters['mask']:
            action = "infill"
            model = MODEL_NAME_INPANT_DIC[model]

        # parameter 생성
        if isV4:
            parameters = V4_PARAMETERS.copy()
        else:
            parameters = V3_PARAMETERS.copy()
        parameters.update(self.parameters)

        # extraseed 통일
        parameters["extra_noise_seed"] = parameters["seed"]

        # smea 버그 수정
        if "image" in parameters or parameters['sampler'] == 'ddim_v3':
            parameters['sm'] = False
            parameters['sm_dyn'] = False

        # v4는 추가 수정함.
        if isV4:
            _complete_v4_parameters(parameters)

        try:
            response = requests.post(url=BASE_URL_IMAGE,
                                     json={
                                        "input": parameters["prompt"],
                                        "model": model,
                                        "action": action,
                                        "parameters": parameters
                                    },
                                     headers={
                                         "Authorization": f"Bearer " + self.access_token}
                                     )
            return response.content
        except Exception as e:
            print("[generate_image]", e)

        return None

    def check_logged_in(self):
        access_result = None
        try:
            access_result = requests.get(BASE_URL_MAIN + "/user/information", headers={
                                         "Authorization": f"Bearer {self.access_token}"}, timeout=5)
        except Exception as e:
            print(e)
        return (access_result is not None)
