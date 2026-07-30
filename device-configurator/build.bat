@echo off
REM Build Windows executable with PyInstaller
py -m pip install -i https://mirror-pypi.runflare.com/simple pyinstaller
py -m PyInstaller --name config-tool --windowed --onefile ^
    --paths src ^
    --hidden-import customtkinter ^
    --collect-all customtkinter ^
    --icon assets\icon.ico ^
    --add-data "assets;assets" ^
    src/config_tool/gui/app.py
echo.
echo Build complete: dist\config-tool.exe
