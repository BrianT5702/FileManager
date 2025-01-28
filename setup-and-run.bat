@echo off
echo Installing required packages...
pip install firebase-admin
pip install tkinterdnd2
pip install Pillow

echo.
echo Running FileHaven...
cd FileManager
python run.py
pause