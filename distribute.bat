call D:\Dev\Workspace\Python\NAI-Auto-Generator\.venv\Scripts\activate.bat

pyinstaller --noconfirm --windowed --icon "D:/Dev/Workspace/Python/NAI-Auto-Generator/icon.ico" --name "NAI Auto Generator" --add-data "D:/Dev/Workspace/Python/NAI-Auto-Generator/no_image.png;." --add-data "D:/Dev/Workspace/Python/NAI-Auto-Generator/open_image.png;." --add-data "D:/Dev/Workspace/Python/NAI-Auto-Generator/open_folder.png;." --add-data "D:/Dev/Workspace/Python/NAI-Auto-Generator/getter.png;." --add-data "D:/Dev/Workspace/Python/NAI-Auto-Generator/tagger.png;." --distpath "D:/Dev/Workspace/Python/NAI-Auto-Generator/dist/"  "D:/Dev/Workspace/Python/NAI-Auto-Generator/gui.py"

pyinstaller --noconfirm --windowed --icon "D:/Dev/Workspace/Python/NAI-Auto-Generator/icon_getter.ico" --name "Info Getter" --add-data "D:/Dev/Workspace/Python/NAI-Auto-Generator/getter.png;." --distpath "D:/Dev/Workspace/Python/NAI-Auto-Generator/dist/"  "D:/Dev/Workspace/Python/NAI-Auto-Generator/getter_standalone.py"

pyinstaller --noconfirm --windowed --icon "D:/Dev/Workspace/Python/NAI-Auto-Generator/icon_getter.ico" --name "Tagger" --add-data "D:/Dev/Workspace/Python/NAI-Auto-Generator/tagger.png;." --distpath "D:/Dev/Workspace/Python/NAI-Auto-Generator/dist/"  "D:/Dev/Workspace/Python/NAI-Auto-Generator/tagger_standalone.py"

move /Y "D:\Dev\Workspace\Python\NAI-Auto-Generator\dist\Info Getter\*" "D:\Dev\Workspace\Python\NAI-Auto-Generator\dist\"
move /Y "D:\Dev\Workspace\Python\NAI-Auto-Generator\dist\Tagger\*" "D:\Dev\Workspace\Python\NAI-Auto-Generator\dist\"
move /Y "D:\Dev\Workspace\Python\NAI-Auto-Generator\dist\NAI Auto Generator\*" "D:\Dev\Workspace\Python\NAI-Auto-Generator\dist\"

PAUSE