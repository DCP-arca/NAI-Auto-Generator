import json

COLOR = type('COLOR', (), {
    'BUTTON_CUSTOM': '#559977',
    'BUTTON_AUTOGENERATE': '#D37493',
    'LABEL_SUCCESS': '#559977',
    'LABEL_FAILED': '#D37493',
})

# RESOLUTION_FAMILIY_MASK와 RESOLUTION_FAMILIY 업데이트
RESOLUTION_FAMILIY_MASK = [0, 0, 0, 0, -1]

RESOLUTION_FAMILIY = {
    0: ["Square (1024x1024)", "Portrait (832x1216)", "Landscape (1216x832)"],  # 기본 해상도 모음 (HD 먼저)
    1: ["Square (1472x1472)", "Portrait (1024x1536)", "Landscape (1536x1024)"],  # 더 높은 해상도
    2: ["Portrait (1088x1920)", "Landscape (1920x1088)"],  # 와이드 해상도
    3: ["Square (640x640)", "Portrait (512x768)", "Landscape (768x512)"],  # 작은 해상도
    4: []  # 커스텀을 위한 빈 항목
}

# consts.py 파일에서
DEFAULT_TAGCOMPLETION_PATH = "./danbooru_tags_post_count.csv"  # 상대 경로로 설정


def prettify_naidict(d, additional_dict=None):
    prompt = d.get('prompt', '')
    negative_prompt = d.get('negative_prompt', '')

    try:
        # 기본 정보
        result = (
            f"Description: {d.get('prompt', '')}\n"
            f"Software: NovelAI\n"
            f"Source: NovelAI Diffusion V4 (NAI Diffusion V4 Full)\n"
            f"Request Type: {'Image to Image' if d.get('image') else 'Text to Image'}\n\n"
            f"Raw Parameters\n"
            f"Prompt: {d.get('prompt', '')}\n"
            f"Undesired Content: {d.get('negative_prompt', '')}\n"
        )
        
        # 캐릭터 프롬프트가 있는 경우 추가 정보
        if 'characterPrompts' in d and d['characterPrompts']:
            result += f"\n■ 캐릭터 프롬프트\n"
            for i, char in enumerate(d['characterPrompts']):
                if isinstance(char, dict):
                    result += f"캐릭터 {i+1}: {char.get('prompt', '정보 없음')}\n"
                    if 'negative_prompt' in char and char['negative_prompt'].strip():
                        result += f"  네거티브: {char['negative_prompt']}\n"
                    if 'position' in char:
                        result += f"  위치: ({char['position'][0]:.1f}, {char['position'][1]:.1f})\n"
        
        # 기술적 정보 추가
        result += (
            f"Resolution: {d['width']}x{d['height']}\n"
            f"Seed: {d['seed']}\n"
            f"Steps: {d['steps']}\n"
            f"Sampler: {d['sampler']} (karras)\n"
            f"Prompt Guidance: {d['scale']}\n"
            f"Prompt Guidance Rescale: {d['cfg_rescale']}\n"
            f"Undesired Content Strength: {d.get('uncond_scale', 0)}\n"
        )
        
        # 추가 옵션 정보
        result += (
            f"Auto SMEA: {'On' if d.get('autoSmea', False) else 'Off'}\n"
            f"Dynamic Thresholding: {'On' if d.get('dynamic_thresholding', False) else 'Off'}\n"
            f"Quality Toggle: {'On' if d.get('quality_toggle', True) else 'Off'}\n"
            f"Anti-Artifacts: {d.get('anti_artifacts', 0.0)}\n"
            f"V4 Model Preset: {d.get('v4_model_preset', 'Artistic')}\n"
        )
    except KeyError as e:
        result = f"키를 찾을 수 없습니다: {e}"
        return result

    # 이미지/레퍼런스 이미지가 있는 경우 추가 정보
    if 'image' in d and d['image']:
        result += f"\n■ 이미지\n"
        result += f"이미지 경로: {additional_dict.get('image_src', '정보 없음') if additional_dict else '정보 없음'}\n"
        result += f"이미지 변환 강도: {d.get('strength', 0.7)}\n"
        result += f"이미지 노이즈: {d.get('noise', 0.0)}\n"
        if additional_dict and 'image_tag' in additional_dict:
            result += f"이미지 태그: {additional_dict['image_tag']}\n"

    if 'reference_image' in d and d['reference_image']:
        result += f"\n■ 참조 이미지\n"
        result += f"참조 이미지 경로: {additional_dict.get('reference_image_src', '정보 없음') if additional_dict else '정보 없음'}\n"
        result += f"참조 이미지 강도: {d.get('reference_strength', 0.6)}\n"
        result += f"참조 정보 추출: {d.get('reference_information_extracted', 1.0)}\n"
        if additional_dict and 'reference_image_tag' in additional_dict:
            result += f"참조 이미지 태그: {additional_dict['reference_image_tag']}\n"

    return result


def prettify_dict(d):
    return json.dumps(d, sort_keys=True, indent=4)


class S:
    LIST_STATSUBAR_STATE = {
        "BEFORE_LOGIN": "로그인이 필요합니다.",
        "LOGGINGIN": "로그인 중...",
        "LOGINED": "로그인 완료. 이제 생성이 가능합니다.",
        "GENEARTING": "이미지를 생성하는 중...",
        "IDLE": "대기 중",
        "LOAD_COMPLETE": "파일 로드 완료",
        "LOADING": "로드 중...",
        "AUTO_GENERATING_COUNT": "연속 생성 중 ({}/{})",
        "AUTO_GENERATING_INF": "연속 생성 중",
        "AUTO_WAIT": "다음 생성 대기 중... ({}초)",
        "AUTO_ERROR_WAIT": "에러 발생. {}초 후 재시도...",
    }

    ABOUT = """NAI Auto Generator v2.0

Made by DCP-ave

대상 API: Novel AI Image API

Notice : "본 앱은 제3자가 개발한 앱으로 노벨AI 또는 Stability AI에서 개발하거나 관리하지 않으며, 이들 회사와는 무관합니다."

="This app is a third-party app that is not developed or managed by Novel AI or Stability AI and is unaffiliated with those companies."

Github: https://github.com/DCP-arca/NAI-Auto-Generator
"""


# 기본 파라미터 수정
DEFAULT_PARAMS = {
    "prompt": "",
    "negative_prompt": "",
    "width": "1024",  # 기본값을 HD로 변경
    "height": "1024",  # 기본값을 HD로 변경
    "steps": "28",
    "sampler": "k_euler_ancestral",
    "seed": "-1",
    "scale": "5.0",    
    "cfg_rescale": "0",
    "autoSmea": "True",
    "quality_toggle": "True",
    "strength": "0.7",
    "noise": "0.0",
    "reference_information_extracted": "1.0",
    "reference_strength": "0.6",
    "v4_model_preset": "Artistic",
    "anti_artifacts": "0.0",
    "dynamic_thresholding": "False",
}

DEFAULT_PATH = {
    "path_results": "./results/",
    "path_settings": "./settings/",
    "path_wildcards": "./wildcards/",
    "path_models": "./models/",
}