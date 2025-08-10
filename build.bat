@echo off
echo ========================================
echo    GitHub Uploader - Build Script
echo ========================================
echo.

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Building executable...
pyinstaller --onefile --windowed --name "GitHub_Uploader" github_uploader.py

echo.
echo Build completed!
echo Executable location: dist\GitHub_Uploader.exe
echo.
pause