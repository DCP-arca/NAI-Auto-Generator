def prettify_naidict(nai_dict, additional_dict={}):
    d = nai_dict
    ad = additional_dict

    content = f"""프롬프트 :
{d['prompt']}

네거티브 프롬프트 :
{d['negative_prompt']}

이미지 크기 :
    가로 {d['width']}, 세로 {d['height']}

옵션 :
    scale : {d['scale']}
    sampler : {d['sampler']}
    seed : {d['seed']}
    cfg_rescale : {d['cfg_rescale']}
    uncond_scale : {d['uncond_scale']}
    sm : {d['sm']}
    sm_dyn : {d['sm_dyn']}"""

    if 'image' in d and d['image']:
        content += "\n\nI2I 모드 :\n" + (f"    target : {ad['image_src']}\n" if (
            'image_src' in ad and ad['image_src']) else '') + f"""    strength : {d['strength']}
    noise : {d['noise']}"""
        if 'image_tag' in ad and ad['image_tag']:
            content += f"""
    i2i tag :
        {ad['image_tag']}"""

    if 'reference_image' in d and d['reference_image']:
        content += "\n\n바이브 트랜스퍼 :\n" + (f"    target : {ad['reference_image_src']}\n" if (
            'reference_image_src' in ad and ad['reference_image_src']) else '') + f"""    reference_information_extracted : {d['reference_information_extracted']}
    reference_strength : {d['reference_strength']}"""
        if 'reference_image_tag' in ad and ad['reference_image_tag']:
            content += f"""
    vibe tag :
        {ad['reference_image_tag']}"""

    return content


class DEFAULT_VALUE:
    AMOUNT_WAIT_WHEN_ERROR_OCCUR = 1


DEFAULT_PATH = {
    "path_results": "results/",
    "path_wildcards": "wildcards/",
    "path_settings": "settings/",
    "path_models": "models/"
}

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


class COLOR:
    GRAY = "#7A7A7A"
    BRIGHT = "#212335"
    MIDIUM = "#1A1C2E"
    DARK = "#101224"
    BUTTON = "#F5F3C2"
    BUTTON_DSIABLED = "#999682"
    BUTTON_AUTOGENERATE = "#F5B5B5"


class S:
    LIST_STATSUBAR_STATE = {
        "BEFORE_LOGIN": "로그인이 필요합니다",
        "LOGGINGIN": "로그인 시도중...",
        "LOGINED": "로그인 성공.",
        "IDLE": "대기 중",
        "GENEARTING": "생성 요청 중...",
        "LOADING": "불러오는 중...",
        "LOAD_COMPLETE": "불러오기 완료",
        "AUTO_GENERATING_COUNT": "자동생성 중... 총 {}장 중 {}번째",
        "AUTO_GENERATING_INF": "자동생성 중...",
        "AUTO_ERROR_WAIT": "생성 중 에러가 발생. {}초 뒤 다시 시작.",
        "AUTO_WAIT": "자동생성 딜레이를 기다리는 중... {}초"
    }

    ABOUT = """
본진 : 
  아카라이브 AI그림 채널 https://arca.live/b/aiart
만든이 : 
  https://arca.live/b/aiart @DCP
크레딧 :
  https://huggingface.co/baqu2213
  https://github.com/neggles/sd-webui-stealth-pnginfo/
    """

    LABEL_PROMPT = "프롬프트(Prompt)"
    LABEL_PROMPT_HINT = "이곳에 원하는 특징을 입력하세요.\n(예 - 1girl, Tendou Aris (Blue archive), happy)"
    LABEL_NPROMPT = "네거티브 프롬프트(Undesired Content)"
    LABEL_NPROMPT_HINT = "이곳에 원하지 않는 특징을 입력하세요.\n(예 - bad quality, low quality, lowres, displeasing)"
    LABEL_AISETTING = "생성 옵션(AI Settings)"


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
