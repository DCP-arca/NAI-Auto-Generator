import os
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def zip_folder(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_STORED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, relative_path)


def zip_two_folders(folder1_path, folder2_path, output_zip_path):
    zip_folder(folder1_path, output_zip_path)
    with zipfile.ZipFile(output_zip_path, 'a') as zipf:
        for root, _, files in os.walk(folder2_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, folder2_path)
                zipf.write(file_path, relative_path)


if __name__ == "__main__":
    folder_dist = os.path.join(BASE_DIR, "dist")
    folder_dist_onefile = os.path.join(BASE_DIR, "dist_onefile")
    folder_for_release = os.path.join(BASE_DIR, "folder_for_release")

    output_zip_dir = os.path.join(BASE_DIR, "dist_release_zip")
    if not os.path.exists(output_zip_dir):
        os.makedirs(output_zip_dir)

    zip_two_folders(folder_dist, folder_for_release,
                    os.path.join(output_zip_dir, "NAI-Auto_Generator.zip"))
    zip_two_folders(folder_dist_onefile, folder_for_release,
                    os.path.join(output_zip_dir, "NAI-Auto_Generator-Onefile.zip"))
