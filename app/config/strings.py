class STRING:
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