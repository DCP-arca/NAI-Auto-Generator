import os
import io
import base64
import onnxruntime as ort
import csv
from PIL import Image
import numpy as np
import requests
import shutil

DEFAULT_MODEL = "wd-v1-4-moat-tagger-v2"
LIST_MODEL = ("wd-v1-4-moat-tagger-v2",
              "wd-v1-4-convnext-tagger-v2", "wd-v1-4-convnext-tagger",
              "wd-v1-4-convnextv2-tagger-v2", "wd-v1-4-vit-tagger-v2")


def download_file(url, dst):
    try:
        with requests.get(url, stream=True) as response:
            if response.status_code == 200:
                with open(dst, 'wb') as f:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, f)
                return True
            else:
                print(
                    f"Failed to download file from {url}. Status code: {response.status_code}")
                return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def create_folder_if_not_exists(foldersrc):
    if not os.path.exists(foldersrc):
        os.makedirs(foldersrc)


def convert_src_to_imagedata(img_path, quality=100):
    img = Image.open(img_path)
    buf = io.BytesIO()
    img.save(buf, format='png', quality=100)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


class DanbooruTagger():
    def __init__(self, models_dir):
        self.models_dir = models_dir
        self.options = {
            "model_name": DEFAULT_MODEL,
            "threshold": 0.35,
            "character_threshold": 0.85,
            "replace_underscore": True,
            "trailing_comma": False,
            "exclude_tags": ""
        }

    def get_installed_models(self):
        create_folder_if_not_exists(self.models_dir)
        return list(filter(lambda x: x.endswith(".onnx"), os.listdir(self.models_dir)))

    def tag(self, image):
        model_name = self.options['model_name']
        threshold = self.options['threshold']
        character_threshold = self.options['character_threshold']
        replace_underscore = self.options['replace_underscore']
        trailing_comma = self.options['trailing_comma']
        exclude_tags = self.options['exclude_tags']

        if model_name.endswith(".onnx"):
            model_name = model_name[0:-5]
        installed = self.get_installed_models()
        if not any(model_name + ".onnx" in s for s in installed):
            print("model not installed")
            return

        name = os.path.join(self.models_dir, model_name + ".onnx")
        model = ort.InferenceSession(
            name, providers=ort.get_available_providers())

        input = model.get_inputs()[0]
        height = input.shape[1]

        # Reduce to max size and pad with white
        ratio = float(height) / max(image.size)
        new_size = tuple([int(x * ratio) for x in image.size])
        image = image.resize(new_size, Image.LANCZOS)
        square = Image.new("RGB", (height, height), (255, 255, 255))
        square.paste(
            image, ((height - new_size[0]) // 2, (height - new_size[1]) // 2))

        image = np.array(square).astype(np.float32)
        image = image[:, :, ::-1]  # RGB -> BGR
        image = np.expand_dims(image, 0)

        # Read all tags from csv and locate start of each category
        tags = []
        general_index = None
        character_index = None
        with open(os.path.join(self.models_dir, model_name + ".csv")) as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if general_index is None and row[2] == "0":
                    general_index = reader.line_num - 2
                elif character_index is None and row[2] == "4":
                    character_index = reader.line_num - 2
                if replace_underscore:
                    tags.append(row[1].replace("_", " "))
                else:
                    tags.append(row[1])

        label_name = model.get_outputs()[0].name
        probs = model.run([label_name], {input.name: image})[0]

        result = list(zip(tags, probs[0]))

        # rating = max(result[:general_index], key=lambda x: x[1])
        general = [item for item in result[general_index:character_index]
                   if item[1] > threshold]
        character = [item for item in result[character_index:]
                     if item[1] > character_threshold]

        all = character + general
        remove = [s.strip() for s in exclude_tags.lower().split(",")]
        all = [tag for tag in all if tag[0] not in remove]

        res = ("" if trailing_comma else ", ").join((item[0].replace(
            "(", "\\(").replace(")", "\\)") + (", " if trailing_comma else "") for item in all))

        return res

    def download_model(self, model):
        installed = self.get_installed_models()
        if any(model + ".onnx" in s for s in installed):
            print("model already installed")
            return True

        url = f"https://huggingface.co/SmilingWolf/{model}/resolve/main/"
        is_success = download_file(
            f"{url}model.onnx",
            os.path.join(self.models_dir, f"{model}.onnx"))
        is_success = is_success and download_file(
            f"{url}selected_tags.csv",
            os.path.join(self.models_dir, f"{model}.csv"))

        return is_success


if __name__ == '__main__':
    dt = DanbooruTagger(r'D:\Dev\Workspace\Python\NAI-Auto-Generator\models')

    is_success = dt.download_model("wd-v1-4-moat-tagger-v2")

    print(is_success)

    result = dt.tag(Image.open("no_image.png"))

    print(result)
