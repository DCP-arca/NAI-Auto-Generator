import random
import json
from collections import OrderedDict

from config.consts import MAX_COUNT_FOR_WHILELOOP

def pickedit_lessthan_str(original_str):
    try_count = 0

    edited_str = original_str
    while try_count < MAX_COUNT_FOR_WHILELOOP:
        try_count += 1

        before_edit_str = edited_str
        pos_prev = 0
        while True:
            pos_r = edited_str.find(">", pos_prev + 1)
            if pos_r == -1:
                break

            pos_l = edited_str.rfind("<", pos_prev, pos_r)
            if pos_l != -1:
                left = edited_str[0:pos_l]
                center = edited_str[pos_l + 1:pos_r]
                right = edited_str[pos_r + 1:len(edited_str)]

                center_splited = center.split("|")
                center_picked = center_splited[random.randrange(
                    0, len(center_splited))]

                result_left = left + center_picked
                pos_prev = len(result_left)
                edited_str = result_left + right
            else:
                pos_prev = pos_r

        if before_edit_str == edited_str:
            break

    return edited_str


def apply_wc_and_lessthan(wcapplier, prompt):
    for x in range(MAX_COUNT_FOR_WHILELOOP):
        before_prompt = prompt
        prompt = pickedit_lessthan_str(prompt) # lessthan pick
        try:
            prompt = wcapplier.apply_wildcards(prompt)
        except Exception:
            pass

        if before_prompt == prompt:
            break
        
    return prompt


def inject_imagetag(original_str, tagname, additional_str):
    result_str = original_str[:]

    tag_str_left = "@@" + tagname
    left_pos = original_str.find(tag_str_left)
    if left_pos != -1:
        right_pos = original_str.find("@@", left_pos + 1)
        except_tag_list = [x.strip() for x in original_str[left_pos +
                                                           len(tag_str_left) + 1:right_pos].split(",")]
        original_tag_list = [x.strip() for x in additional_str.split(',')]
        target_tag_list = [
            x for x in original_tag_list if x not in except_tag_list]

        result_str = original_str[0:left_pos] + ", ".join(target_tag_list) + \
            original_str[right_pos + 2:len(original_str)]

    return result_str


def prettify_naidict(nai_dict):
    desired_order = [
        "prompt",
        "negative_prompt",
        "width",
        "height",
        "scale",
        "steps",
        "sampler",
        "cfg_scale",
        "uncond_scale",
        "sm",
        "sm_dyn",
        "seed",
        "strength",
        "noise",
        "reference_information_extracted",
        "reference_strength",
        "v4_prompt",
        "v4_negative_prompt"
    ]

    ban_keys = [
        "image"
        "reference_image"
    ]
    
    # 먼저 순서대로 정렬할 딕셔너리 만들기
    ordered_dict = OrderedDict()
    for key in desired_order:
        if key in nai_dict:
            ordered_dict[key] = nai_dict[key]
    
    # 남은 키들도 자동으로 추가해주기
    for key in nai_dict:
        if key not in ordered_dict and key not in ban_keys:
            ordered_dict[key] = nai_dict[key]

    content = json.dumps(ordered_dict, indent=4)
    content = content.replace("\\n", "\n")
    return content