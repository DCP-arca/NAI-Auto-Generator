call D:\Dev\Workspace\Python\NAI-Auto-Generator\.venv\Scripts\activate.bat

pyinstaller --onefile --noconfirm --windowed --icon "D:/Dev/Workspace/Python/NAI-Auto-Generator/icon.ico" --name "NAI Auto Generator" --add-data "D:/Dev/Workspace/Python/NAI-Auto-Generator/no_image.png;." --add-data "D:/Dev/Workspace/Python/NAI-Auto-Generator/open_image.png;." --add-data "D:/Dev/Workspace/Python/NAI-Auto-Generator/open_folder.png;." --add-data "D:/Dev/Workspace/Python/NAI-Auto-Generator/getter.png;." --add-data "D:/Dev/Workspace/Python/NAI-Auto-Generator/tagger.png;." --distpath "D:/Dev/Workspace/Python/NAI-Auto-Generator/dist_onefile/"  "D:/Dev/Workspace/Python/NAI-Auto-Generator/gui.py"

pyinstaller --noconfirm --windowed --icon "D:/Dev/Workspace/Python/NAI-Auto-Generator/icon.ico" --name "NAI Auto Generator" --add-data "D:/Dev/Workspace/Python/NAI-Auto-Generator/no_image.png;." --add-data "D:/Dev/Workspace/Python/NAI-Auto-Generator/open_image.png;." --add-data "D:/Dev/Workspace/Python/NAI-Auto-Generator/open_folder.png;." --add-data "D:/Dev/Workspace/Python/NAI-Auto-Generator/getter.png;." --add-data "D:/Dev/Workspace/Python/NAI-Auto-Generator/tagger.png;." --distpath "D:/Dev/Workspace/Python/NAI-Auto-Generator/dist/"  "D:/Dev/Workspace/Python/NAI-Auto-Generator/gui.py"

pyinstaller --noconfirm --windowed --icon "D:/Dev/Workspace/Python/NAI-Auto-Generator/icon_getter.ico" --name "Info Getter" --add-data "D:/Dev/Workspace/Python/NAI-Auto-Generator/getter.png;." --distpath "D:/Dev/Workspace/Python/NAI-Auto-Generator/dist/"  "D:/Dev/Workspace/Python/NAI-Auto-Generator/getter_standalone.py"

pyinstaller --noconfirm --windowed --icon "D:/Dev/Workspace/Python/NAI-Auto-Generator/icon_tagger.ico" --name "Tagger" --add-data "D:/Dev/Workspace/Python/NAI-Auto-Generator/tagger.png;." --distpath "D:/Dev/Workspace/Python/NAI-Auto-Generator/dist/"  "D:/Dev/Workspace/Python/NAI-Auto-Generator/tagger_standalone.py"

xcopy "D:\Dev\Workspace\Python\NAI-Auto-Generator\dist\Info Getter\" "D:\Dev\Workspace\Python\NAI-Auto-Generator\dist\" /s /e /y
xcopy "D:\Dev\Workspace\Python\NAI-Auto-Generator\dist\Tagger\" "D:\Dev\Workspace\Python\NAI-Auto-Generator\dist\" /s /e /y
xcopy "D:\Dev\Workspace\Python\NAI-Auto-Generator\dist\NAI Auto Generator\" "D:\Dev\Workspace\Python\NAI-Auto-Generator\dist\" /s /e /y

xcopy "D:\Dev\Workspace\Python\NAI-Auto-Generator\danbooru_tags_post_count.csv" "D:\Dev\Workspace\Python\NAI-Auto-Generator\dist\" /Y /Q /R
xcopy "D:\Dev\Workspace\Python\NAI-Auto-Generator\danbooru_tags_post_count.csv" "D:\Dev\Workspace\Python\NAI-Auto-Generator\dist_onefile\" /Y /Q /R

rd /s /q "D:\Dev\Workspace\Python\NAI-Auto-Generator\dist\Info Getter"
rd /s /q "D:\Dev\Workspace\Python\NAI-Auto-Generator\dist\Tagger"
rd /s /q "D:\Dev\Workspace\Python\NAI-Auto-Generator\dist\NAI Auto Generator"

python installer_zipper.py

PAUSE