import os
import time
import zipfile
import io
import random
import datetime
from PIL import Image

from PyQt5.QtCore import QThread, pyqtSignal

from core.worker.nai_generator import NAIAction

from util.common_util import strtobool
from util.file_util import create_folder_if_not_exists, get_filename_only, create_windows_filepath

from config.paths import DEFAULT_PATH


def _threadfunc_generate_image(thread_self, path):
    parent = thread_self.parent()
    nai = parent.nai
    action = NAIAction.generate
    if nai.parameters["image"]:
        action = NAIAction.img2img
    if nai.parameters['mask']:
        action = NAIAction.infill
    data = nai.generate_image(action)
    if not data:
        return 1, "서버에서 정보를 가져오는데 실패했습니다."  # 실패 메시지냐아~

    try:
        zipped = zipfile.ZipFile(io.BytesIO(data))
        image_bytes = zipped.read(zipped.infolist()[0])
        img = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        return 2, str(e) + str(data)

    create_folder_if_not_exists(path)
    dst = ""
    if parent.dict_img_batch_target["img2img_foldersrc"] and strtobool(parent.settings.value("will_savename_i2i", False)):
        filename = get_filename_only(parent.i2i_settings_group.src)
        extension = ".png"
        dst = os.path.join(path, filename + extension)
        while os.path.isfile(dst):
            filename += "_"
            dst = os.path.join(path, filename + extension)
    else:
        timename = datetime.datetime.now().strftime("%y%m%d_%H%M%S%f")[:-4]
        filename = timename
        if strtobool(parent.settings.value("will_savename_prompt", True)):
            filename += "_" + nai.parameters["prompt"]
        dst = create_windows_filepath(path, filename, ".png")
        if not dst:
            dst = timename
    try:
        img.save(dst)
    except Exception as e:
        return 3, str(e)

    return 0, dst


class GenerateThread(QThread):
    # Signals for 자동 생성 모드
    on_data_created = pyqtSignal()
    on_error = pyqtSignal(int, str)
    on_success = pyqtSignal(str)
    on_end = pyqtSignal()
    on_statusbar_change = pyqtSignal(str, list)

    # Signal for 단일 생성 모드
    generate_result = pyqtSignal(int, str)

    def __init__(self, parent, auto_mode=False, count=-1, delay=0.01, ignore_error=False):
        super(GenerateThread, self).__init__(parent)
        self.auto_mode = auto_mode
        self.count = int(count or -1)
        self.delay = float(delay or 0.01)
        self.ignore_error = ignore_error
        self.is_dead = False

    def run(self):
        parent = self.parent()
        if self.auto_mode:
            # 자동 생성 모드 (기존 AutoGenerateThread의 기능)
            count = self.count
            delay = self.delay
            temp_preserve_data_once = False
            while count != 0:
                # 1. 데이터 생성
                if not temp_preserve_data_once:
                    data = parent._get_data_for_generate()
                    parent.nai.set_param_dict(data)
                    self.on_data_created.emit()
                temp_preserve_data_once = False

                # 상태 표시줄 업데이트
                if count <= -1:
                    self.on_statusbar_change.emit("AUTO_GENERATING_INF", [])
                else:
                    self.on_statusbar_change.emit("AUTO_GENERATING_COUNT", [
                                                  self.count, self.count - count + 1])

                # 결과 저장 경로 설정 (배치 처리 고려)
                path = parent.settings.value(
                    "path_results", DEFAULT_PATH["path_results"])
                create_folder_if_not_exists(path)
                if parent.list_settings_batch_target:
                    setting_path = parent.list_settings_batch_target[parent.index_settings_batch_target]
                    setting_name = get_filename_only(setting_path)
                    path = os.path.join(path, setting_name)
                    create_folder_if_not_exists(path)

                # 이미지 생성
                error_code, result_str = _threadfunc_generate_image(self, path)
                if self.is_dead:
                    return
                if error_code == 0:
                    self.on_success.emit(result_str)
                else:
                    if self.ignore_error:
                        for t in range(int(delay), 0, -1):
                            self.on_statusbar_change.emit(
                                "AUTO_ERROR_WAIT", [t])
                            time.sleep(1+ random.uniform(0.01, 0.1))
                            if self.is_dead:
                                return
                        temp_preserve_data_once = True
                        continue
                    else:
                        self.on_error.emit(error_code, result_str)
                        return

                # 2. 대기
                count -= 1
                if count != 0:
                    temp_delay = delay
                    for _ in range(int(delay)):
                        self.on_statusbar_change.emit(
                            "AUTO_WAIT", [temp_delay])
                        time.sleep(1+ random.uniform(0.01, 0.1))
                        if self.is_dead:
                            return
                        temp_delay -= 1
            self.on_end.emit()
        else:
            # 단일 생성 모드 (기존 GenerateThread의 기능)
            path = parent.settings.value(
                "path_results", DEFAULT_PATH["path_results"])
            error_code, result_str = _threadfunc_generate_image(self, path)
            self.generate_result.emit(error_code, result_str)

    def stop(self):
        self.is_dead = True
        self.quit()
