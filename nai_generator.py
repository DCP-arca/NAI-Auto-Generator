from hashlib import blake2b
import argon2
from base64 import urlsafe_b64encode
import requests
import random
import zipfile
import json
import io
from enum import Enum
from PIL import Image
import base64

BASE_URL = "https://api.novelai.net"


class NAIAction(Enum):
    generate = "generate",
    img2img = "img2img"


class NAIParam(Enum):
    prompt = 1
    negative_prompt = 2
    width = 3
    height = 4
    steps = 5
    current_sampler = 6
    cfg_scale = 7
    cfg_rescale = 8
    sm = 9
    sm_dyn = 10
    sampler = 11
    seed = 12
    extra_noise_seed = 13
    scale = 14
    uncond_scale = 15,
    reference_image = 16,
    reference_information_extracted = 17,
    reference_strength = 18,
    image = 19,
    noise = 20,
    strength = 21,


TYPE_NAIPARAM_DICT = {
    NAIParam.prompt: str,
    NAIParam.negative_prompt: str,
    NAIParam.width: int,
    NAIParam.height: int,
    NAIParam.steps: int,
    NAIParam.current_sampler: str,
    NAIParam.cfg_scale: float,
    NAIParam.cfg_rescale: float,
    NAIParam.sm: bool,
    NAIParam.sm_dyn: bool,
    NAIParam.sampler: str,
    NAIParam.seed: int,
    NAIParam.extra_noise_seed: int,
    NAIParam.scale: float,
    NAIParam.uncond_scale: float,
    NAIParam.reference_image: str,
    NAIParam.reference_information_extracted: float,
    NAIParam.reference_strength: float,
    NAIParam.image: str,
    NAIParam.noise: float,
    NAIParam.strength: float
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


class NAIGenerator():
    def __init__(self):
        self.access_token = None
        self.username = None
        self.password = None
        self.parameters = {
            "prompt": "",
            "negative_prompt": "",
            "legacy": False,
            "quality_toggle": False,
            "width": 512,
            "height": 512,
            "n_samples": 1,
            "seed": random.randint(0, 9999999999),
            "extra_noise_seed": -1,
            "sampler": "k_euler_ancestral",
            "steps": 28,
            "scale": 5,
            "uncond_scale": 1.0,
            "sm": True,
            "sm_dyn": True,
            "decrisper": False,
            "controlnet_strength": 1.0,
            "add_original_image": False,
            "cfg_rescale": 0,
            "noise_schedule": "native",
            "image": None,
            "noise": 0.0,
            "strength": 0.7,
            "reference_image": None,
            "reference_information_extracted": 1.0,
            "reference_strength": 0.6
        }

    def try_login(self, username, password):
        # get_access_key
        access_key = argon_hash(username, password, 64,
                                "novelai_data_access_key")[:64]
        try:
            # try login
            response = requests.post(
                f"{BASE_URL}/user/login", json={"key": access_key})
            self.access_token = response.json()["accessToken"]

            # if success, save id/pw in
            self.username = username
            self.password = password

            return True
        except Exception as e:
            print(e)

        return False

    def set_param(self, param_key: NAIParam, param_value):
        # param_key type check
        assert(isinstance(param_key, NAIParam))
        # param_value type check
        assert(isinstance(param_value, TYPE_NAIPARAM_DICT[param_key]))

        self.parameters[param_key.name] = param_value

    def set_param_dict(self, param_dict):
        for k, v in param_dict.items():
            if k and v:
                try:
                    param_key = NAIParam[k]
                    self.set_param(param_key, v)
                except Exception as e:
                    print("NAIGenerator", "wrong param", e, k)
                    continue

    def get_anlas(self):
        try:
            response = requests.get("https://api.novelai.net/user/subscription", headers={
                "Authorization": f"Bearer {self.access_token}"})
            data_dict = json.loads(response.content)
            trainingStepsLeft = data_dict['trainingStepsLeft']
            anlas = int(trainingStepsLeft['fixedTrainingStepsLeft']) + \
                int(trainingStepsLeft['purchasedTrainingSteps'])

            return anlas
        except Exception as e:
            print(e)

        return None

    def generate_image(self, action: NAIAction):
        assert(isinstance(action, NAIAction))

        if self.parameters["extra_noise_seed"] == -1:
            self.parameters["extra_noise_seed"] = self.parameters["seed"]

        url = BASE_URL + f"/ai/generate-image"
        data = {
            "input": self.parameters["prompt"],
            "model": "nai-diffusion-3",
            "action": action.name,
            "parameters": self.parameters,
        }
        headers = {"Authorization": f"Bearer " + self.access_token}

        try:
            response = requests.post(url, json=data, headers=headers)
            return response.content
        except Exception as e:
            print(e)

        return None

    def check_logged_in(self):
        access_result = None
        try:
            access_result = requests.get("https://api.novelai.net/user/information", headers={
                                         "Authorization": f"Bearer {self.access_token}"}, timeout=5)
        except Exception as e:
            print(e)
        return (access_result is not None)

    def convert_src_to_imagedata(self, img_path, quality=100):
        img = Image.open(img_path)
        buf = io.BytesIO()
        img.save(buf, format='png', quality=100)
        return base64.b64encode(buf.getvalue()).decode("utf-8")


if __name__ == "__main__":
    username = "username"
    password = "password"

    naiG = NAIGenerator()

    is_login_success = naiG.try_login(username, password)

    if is_login_success:
        print(naiG.get_anlas())

        naiG.set_param_dict({
            "prompt": "1girl",
            "negative_prompt": "bad quality",
            "width": 512,
            "height": 512,
            "steps": 28,
            "current_sampler": "k_euler_ancestral",
            "cfg_scale": 5.0,
            "cfg_rescale": 0.0,
            "sm": True,
            "sm_dyn": True,
            # "image": get_img_base64("test.png"),
            # "strength": 0.5,
            # "noise": 0.0,
            # "reference_image": naiG.convert_src_to_imagedata("no_image.png")
        })

        img = naiG.generate_image(action=NAIAction.generate)
        # img = naiG.generate_image(action=NAIAction.img2im)

        zipped = zipfile.ZipFile(io.BytesIO(img))
        image_bytes = zipped.read(zipped.infolist()[0])
        img = Image.open(io.BytesIO(image_bytes))
        img.save("asd.png")
