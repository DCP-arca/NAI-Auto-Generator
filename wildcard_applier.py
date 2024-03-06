import os
import random
from enum import Enum

MAX_TRY_AMOUNT = 99


class WildcardApplier():
    def __init__(self, src_wildcards_folder):
        self.src_wildcards_folder = src_wildcards_folder
        self._wildcards_dict = {}

    def set_src(self, src):
        self.src_wildcards_folder = src

    def load_wildcards(self):
        self._wildcards_dict.clear()

        for dirpath, dname_list, fname_list in os.walk(self.src_wildcards_folder):
            path = ""  # path for wildcards
            path = dirpath.replace(self.src_wildcards_folder, "")
            path = path.replace("\\", "/") + "/"
            path = path[1:]

            for filename in fname_list:
                if filename.endswith(".txt"):
                    src = os.path.join(dirpath, filename)
                    with open(src, "r", encoding="utf8") as f:
                        lines = f.readlines()
                        if lines:
                            onlyname = os.path.splitext(
                                os.path.basename(filename))[0]
                            key = path + onlyname
                            self._wildcards_dict[key.lower()] = lines

    def _apply_wildcard_once(self, target_str, except_list=[]):
        result = target_str

        applied_wildcard_list = []
        prev_point = 0
        while "__" in result:
            p_left = result.find("__", prev_point)
            if p_left == -1:
                break

            p_right = result.find("__", p_left + 1)
            if p_right == -1:
                print("Warning : A single __ exists")
                break

            str_left = result[0:p_left]
            str_center = result[p_left + 2:p_right].lower()
            str_right = result[p_right + 2:len(result)]

            if str_center in self._wildcards_dict and not (str_center in except_list):
                wc_list = self._wildcards_dict[str_center]
                str_center = wc_list[random.randrange(0, len(wc_list))].strip()

                applied_wildcard_list.append(str_center)
            else:
                print("Warning : Unknown wildcard", str_center)
                str_center = "__" + str_center + "__"

            result_left = str_left + str_center
            prev_point = len(result_left) + 1

            result = result_left + str_right

        return result, applied_wildcard_list

    def apply_wildcards(self, target_str):
        self.load_wildcards()

        result = target_str

        index = 0
        except_list = []
        while True:
            result, applied_wildcard_list = self._apply_wildcard_once(
                result, except_list)

            except_list.extend(applied_wildcard_list)
            if len(applied_wildcard_list) == 0:
                break

            index += 1
            if index > MAX_TRY_AMOUNT:
                print("Warning : Too much recursion")
                break

        return result


if __name__ == "__main__":
    wa = WildcardApplier("wildcards")

    # result = wa.apply_wildcards("")

    # print(result)
