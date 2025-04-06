import os
import sys

def create_folder_if_not_exists(foldersrc):
    if not os.path.exists(foldersrc):
        os.makedirs(foldersrc)


def get_imgcount_from_foldersrc(foldersrc):
    return len([file for file in os.listdir(foldersrc) if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))])


def get_filename_only(path):
    filename, _ = os.path.splitext(os.path.basename(path))
    return filename


def create_windows_filepath(base_path, filename, extension, max_length=150):
    # 파일 이름으로 사용할 수 없는 문자 제거
    cleaned_filename = filename.replace("\n", "")
    cleaned_filename = cleaned_filename.replace("\\", "")

    invalid_chars = r'<>:"/\|?*'
    cleaned_filename = ''.join(
        char for char in cleaned_filename if char not in invalid_chars)

    # 파일 이름의 최대 길이 제한 (확장자 길이 고려)
    max_filename_length = max_length - len(base_path) - len(extension) - 1
    if max_filename_length < 5:
        return None
    cleaned_filename = cleaned_filename[:max_filename_length]

    # 경로, 파일 이름, 확장자 합치기
    filepath = os.path.join(base_path, cleaned_filename + extension)

    return filepath