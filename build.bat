call .venv\Scripts\activate.bat

pyinstaller --workpath "build/_pyinstaller_build" --onefile --noconfirm --windowed --icon "assets/icon.ico" --name "NAI Auto Generator" --add-data "assets/no_image.png;assets" --add-data "assets/open_image.png;assets" --add-data "assets/image_clear.png;assets" --add-data "assets/getter.png;assets" --add-data "assets/tagger.png;assets" --distpath "build/dist_onefile/"  "app/main_window.py"

pyinstaller --workpath "build/_pyinstaller_build" --noconfirm --windowed --icon "assets/icon.ico" --name "NAI Auto Generator" --add-data "assets/no_image.png;assets" --add-data "assets/open_image.png;assets" --add-data "assets/image_clear.png;assets" --add-data "assets/getter.png;assets" --add-data "assets/tagger.png;assets" --distpath "build/dist/"  "app/main_window.py"

pyinstaller --workpath "build/_pyinstaller_build" --noconfirm --windowed --icon "assets/icon_getter.ico" --name "Info Getter" --add-data "assets/getter.png;assets" --distpath "build/dist/"  "app/getter_window.py"

pyinstaller --workpath "build/_pyinstaller_build" --noconfirm --windowed --icon "assets/icon_tagger.ico" --name "Tagger" --add-data "assets/tagger.png;assets" --distpath "build/dist/"  "app/tagger_window.py"

xcopy "build\dist\Info Getter\" "build\dist\" /s /e /y
xcopy "build\dist\Tagger\" "build\dist\" /s /e /y
xcopy "build\dist\NAI Auto Generator\" "build\dist\" /s /e /y

xcopy "assets\danbooru_tags_post_count.csv" "build\dist\" /Y /Q /R
xcopy "assets\danbooru_tags_post_count.csv" "build\dist_onefile\" /Y /Q /R

rd /s /q "build\dist\Info Getter"
rd /s /q "build\dist\Tagger"
rd /s /q "build\dist\NAI Auto Generator"

python build\installer_zipper.py

PAUSE