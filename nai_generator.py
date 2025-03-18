from hashlib import blake2b
import argon2
from base64 import urlsafe_b64encode
import requests
import random
import json
import io
import zipfile
import logging
from enum import Enum
from PIL import Image
import base64

BASE_URL_DEPRE = "https://api.novelai.net"
BASE_URL = "https://image.novelai.net"


class NAIAction(Enum):
    generate = "generate",
    img2img = "img2img",
    infill = "infill"


class NAIParam(Enum):
    # 기본 파라미터
    prompt = 1
    negative_prompt = 2
    width = 3
    height = 4
    steps = 5
    cfg_rescale = 8
    sampler = 11
    seed = 12
    extra_noise_seed = 13
    scale = 14
    uncond_scale = 15
    reference_image = 16
    reference_information_extracted = 17
    reference_strength = 18
    image = 19
    noise = 20
    strength = 21
    mask = 22
    
    # V4 전용 파라미터
    autoSmea = 23
    v4_model_preset = 24
    anti_artifacts = 25
    add_original_image = 26
    params_version = 27
    legacy = 28
    prefer_brownian = 29
    ucPreset = 30
    dynamic_thresholding = 31
    quality_toggle = 32
    characterPrompts = 33


TYPE_NAIPARAM_DICT = {
    NAIParam.prompt: str,
    NAIParam.negative_prompt: str,
    NAIParam.width: int,
    NAIParam.height: int,
    NAIParam.steps: int,
    NAIParam.cfg_rescale: float,
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
    NAIParam.strength: float,
    NAIParam.mask: str,
    
    # V4 파라미터 타입
    NAIParam.autoSmea: bool,
    NAIParam.v4_model_preset: str,
    NAIParam.anti_artifacts: float,
    NAIParam.add_original_image: bool,
    NAIParam.params_version: int,
    NAIParam.legacy: bool,
    NAIParam.prefer_brownian: bool,
    NAIParam.ucPreset: int,
    NAIParam.dynamic_thresholding: bool,
    NAIParam.quality_toggle: bool,
    NAIParam.characterPrompts: list
}

def setup_logger():
    logger = logging.getLogger('nai_generator')
    logger.setLevel(logging.DEBUG)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    
    # 파일 핸들러
    file_handler = logging.FileHandler('nai_api_log.txt')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(file_format)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger

logger = setup_logger()


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

def logout(self):
    """사용자 로그아웃 처리: 접근 토큰 및 로그인 정보를 초기화합니다."""
    self.access_token = None
    self.username = None
    self.password = None
    return True


class NAIGenerator():
    def __init__(self):
        self.access_token = None
        self.username = None
        self.password = None
        self.parameters = {
            # 기본 입력
            "prompt": "",
            "negative_prompt": "",
            
            # 이미지 설정
            "width": 1024,  # 832에서 1024로 변경
            "height": 1024, # 1216에서 1024로 변경
            "n_samples": 1,
            
            # 시드 설정
            "seed": random.randint(0, 2**32-1),
            "extra_noise_seed": -1,
            
            # 샘플링 옵션
            "sampler": "k_euler_ancestral",
            "steps": 28,
            "scale": 5.0,  # CFG 값
            "uncond_scale": 1.0,
            
            # V4 품질 관련
            "autoSmea": True,  # 스마팅 효과 활성화
            "cfg_rescale": 0,  # CFG 리스케일 (0 = 비활성화)
            "quality_toggle": True,  # 품질 향상 토글
            "dynamic_thresholding": False,  # 동적 임계처리
            
            # V4 모델 프리셋 및 기타 설정
            "v4_model_preset": "Artistic",  # Normal, Artistic, Anime 중 선택
            "anti_artifacts": 0.0,  # 아티팩트 제거 강도
            
            # V4 시스템 설정
            "params_version": 3,
            "add_original_image": True,
            "legacy": False,
            "prefer_brownian": True,
            "ucPreset": 0,
            
            # 이미지 변환 설정 (img2img, inpainting)
            "image": None,
            "mask": None,
            "noise": 0.0,
            "strength": 0.7,
            
            # 참조 이미지 설정 (reference)
            "reference_image": None,
            "reference_strength": 0.6,
            "reference_information_extracted": 1.0,
            
            # 캐릭터 프롬프트
            "characterPrompts": [],
            
            # 기타 설정
            "noise_schedule": "karras",
        }

    def try_login(self, username, password):
        # get_access_key
        access_key = argon_hash(username, password, 64,
                                "novelai_data_access_key")[:64]
        try:
            # try login
            response = requests.post(
                f"{BASE_URL_DEPRE}/user/login", json={"key": access_key})
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
        if param_value is not None:
            assert(isinstance(param_value, TYPE_NAIPARAM_DICT[param_key]))

        self.parameters[param_key.name] = param_value

    def set_param_dict(self, param_dict):
        # V4 API에서만 사용하는 특별한 파라미터들
        special_params = ["legacy_v3_extend", "noise_schedule", "params_version", 
                          "characterPrompts", "v4_prompt", "v4_negative_prompt",
                          "use_character_coords"]  # use_character_coords 추가
        
        for k, v in param_dict.items():
            if k:
                if k in special_params:
                    # 특별 파라미터는 직접 설정 (use_character_coords는 별도 처리)
                    if k != "use_character_coords":  # use_character_coords는 내부에서만 사용
                        self.parameters[k] = v
                    continue
                    
                try:
                    param_key = NAIParam[k]
                    self.set_param(param_key, v)
                except Exception as e:
                    print("NAIGenerator", "wrong param", e, k)
                    continue

    def get_anlas(self):
        try:
            response = requests.get(BASE_URL_DEPRE + "/user/subscription", headers={
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
        
        # 요청 추적을 위한 ID 생성
        import uuid
        request_id = str(uuid.uuid4())[:8]
        logger.info(f"이미지 생성 요청 시작 [ID: {request_id}] - {action.name}")

        # 모델 선택 (V4 모델만 지원)
        model = "nai-diffusion-4-full" if action != NAIAction.infill else "nai-diffusion-4-full-inpainting"
        
        # 시드 설정
        if self.parameters["extra_noise_seed"] == -1:
            self.parameters["extra_noise_seed"] = self.parameters["seed"]

        # V4 구조에 맞게 파라미터 변환
        self._prepare_v4_parameters()

        url = BASE_URL + f"/ai/generate-image"
        data = {
            "input": self.parameters["prompt"],
            "model": model,
            "action": action.name,
            "parameters": self.parameters,
        }
        headers = {"Authorization": f"Bearer {self.access_token}"}

        # API 요청 파라미터 로깅 (민감 정보 제외)
        debug_data = data.copy()
        if "Authorization" in headers:
            debug_headers = headers.copy()
            debug_headers["Authorization"] = "Bearer [REDACTED]"
        
        # 중요 파라미터 로깅
        log_params = {
            "action": action.name,
            "model": model,
            "width": self.parameters.get("width"),
            "height": self.parameters.get("height"),
            "steps": self.parameters.get("steps"),
            "sampler": self.parameters.get("sampler"),
            "has_image": "image" in self.parameters and self.parameters["image"] is not None,
            "has_mask": "mask" in self.parameters and self.parameters["mask"] is not None,
            "has_reference": "reference_image" in self.parameters and self.parameters["reference_image"] is not None,
            "character_count": len(self.parameters.get("characterPrompts", [])),
        }
        
        logger.debug(f"요청 파라미터 [ID: {request_id}]: {log_params}")
        
        # 재시도 메커니즘 구현
        max_retries = 3
        retry_delay = 2  # 초 단위
        
        for retry in range(max_retries):
            try:
                logger.info(f"API 요청 시도 [ID: {request_id}] - 시도 {retry+1}/{max_retries}")
                response = requests.post(url, json=data, headers=headers, timeout=60)
                
                # 상태 코드 확인
                if response.status_code == 200 or response.status_code == 201:
                    logger.info(f"API 요청 성공 [ID: {request_id}] - 상태 코드: {response.status_code}")
                    return response.content
                else:
                    # 오류 응답 분석
                    error_info = f"상태 코드: {response.status_code}"
                    try:
                        error_json = response.json()
                        error_info += f", 메시지: {error_json.get('message', '알 수 없음')}"
                    except:
                        error_info += f", 응답: {response.text[:200]}"
                    
                    logger.error(f"API 오류 응답 [ID: {request_id}] - {error_info}")
                    
                    # 특정 오류에 따른 처리
                    if response.status_code == 401:
                        return None, "인증 오류: 로그인이 필요합니다."
                    elif response.status_code == 402:
                        return None, "결제 필요: Anlas가 부족합니다."
                    elif response.status_code == 429:
                        return None, "요청 제한: 너무 많은 요청을 보냈습니다. 잠시 후 다시 시도하세요."
                    elif response.status_code >= 500:
                        # 서버 오류는 재시도
                        if retry < max_retries - 1:
                            logger.info(f"서버 오류로 인한 재시도 [ID: {request_id}] - {retry_delay}초 후 다시 시도")
                            import time
                            time.sleep(retry_delay)
                            retry_delay *= 2  # 지수 백오프
                            continue
                    
                    return None, f"API 오류: {error_info}"
                    
            except requests.exceptions.Timeout:
                logger.error(f"API 요청 타임아웃 [ID: {request_id}] - 시도 {retry+1}/{max_retries}")
                if retry < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 지수 백오프
                    continue
                return None, "API 요청 타임아웃: 서버 응답이 너무 느립니다."
                
            except Exception as e:
                logger.error(f"API 요청 예외 [ID: {request_id}]: {str(e)}", exc_info=True)
                return None, f"API 요청 오류: {str(e)}"

        return None, "최대 재시도 횟수 초과: 서버에 연결할 수 없습니다."
    
    def _prepare_v4_parameters(self):
        """V4 API에 필요한 파라미터 구조로 변환"""
        # 내부 파라미터 처리 - use_character_coords 값 저장 후 제거
        use_coords = False
        if "use_character_coords" in self.parameters:
            use_coords = self.parameters["use_character_coords"]
            del self.parameters["use_character_coords"]  # API 요청에서 제거
        
        # V4 프롬프트 형식 설정
        self.parameters["v4_prompt"] = {
            "caption": {
                "base_caption": self.parameters["prompt"],
                "char_captions": []
            },
            "use_coords": use_coords,  # 저장해둔 값 사용
            "use_order": True
        }
        
        # V4 네거티브 프롬프트 형식 설정
        self.parameters["v4_negative_prompt"] = {
            "caption": {
                "base_caption": self.parameters["negative_prompt"],
                "char_captions": []
            },
            "legacy_uc": False
        }
        
        # 캐릭터 프롬프트 처리
        if self.parameters.get("characterPrompts") and len(self.parameters["characterPrompts"]) > 0:
            char_prompts = self.parameters["characterPrompts"]
            
            for i, char in enumerate(char_prompts):
                # 캐릭터 프롬프트 구조 설정
                if isinstance(char, dict) and "prompt" in char:
                    char_caption = {
                        "char_caption": char["prompt"],
                        "centers": [{"x": 0.5, "y": 0.5}]  # 기본 중앙 위치 설정
                    }
                    
                    # 위치 정보가 있으면 덮어쓰기
                    if use_coords and "position" in char and char["position"]:
                        char_caption["centers"] = [{
                            "x": char["position"][0],
                            "y": char["position"][1]
                        }]
                    
                    # 캐릭터 프롬프트 추가
                    self.parameters["v4_prompt"]["caption"]["char_captions"].append(char_caption)
                    
                    # 캐릭터 네거티브 프롬프트 (있을 경우)
                    neg_caption = {
                        "char_caption": char.get("negative_prompt", ""),
                        "centers": char_caption["centers"]
                    }
                    self.parameters["v4_negative_prompt"]["caption"]["char_captions"].append(neg_caption)

    def check_logged_in(self):
        access_result = None
        try:
            access_result = requests.get(BASE_URL_DEPRE + "/user/information", headers={
                                         "Authorization": f"Bearer {self.access_token}"}, timeout=5)
        except Exception as e:
            print(e)
        return (access_result is not None)

    def convert_src_to_imagedata(self, img_path, quality=100):
        try:
            img = Image.open(img_path)
            buf = io.BytesIO()
            img.save(buf, format='png', quality=100)
            return base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception as e:
            return ""


if __name__ == "__main__":
    import configparser
    config = configparser.ConfigParser()
    config.read('testsetting.ini')
    username = config['USER']['username']
    password = config['USER']['password']

    print(username, password)

    naiG = NAIGenerator()

    is_login_success = naiG.try_login(username, password)
    print(is_login_success)
    print(naiG.check_logged_in())

    if is_login_success:
        # print(naiG.get_anlas())

        naiG.parameters = {
            "prompt": "1girl",
            "negative_prompt": "bad quality",
            "legacy": False,
            "width": 832,
            "height": 1216,
            "n_samples": 1,
            "seed": random.randint(0, 2**32-1),
            "extra_noise_seed": -1,
            "sampler": "k_euler_ancestral",
            "steps": 28,
            "scale": 5,
            "uncond_scale": 1.0,
            "autoSmea": True,
            "cfg_rescale": 0,
            "noise_schedule": "karras",
            "quality_toggle": True,
            "anti_artifacts": 0.0,
            "v4_model_preset": "Artistic",
        }

        img = naiG.generate_image(action=NAIAction.generate)
        # img = naiG.generate_image(action=NAIAction.img2img)

        print(img)
        zipped = zipfile.ZipFile(io.BytesIO(img))
        image_bytes = zipped.read(zipped.infolist()[0])
        img = Image.open(io.BytesIO(image_bytes))
        img.save(r"testresult.png")