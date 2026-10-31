@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 goto error
".venv\Scripts\python.exe" -m pip install -r requirements.txt "pyinstaller>=6,<7"
if errorlevel 1 goto error
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name "PDF-para-Markdown" --collect-all markitdown --collect-all pdfplumber --collect-all pymupdf --collect-all rapidocr --collect-all onnxruntime desktop_app.py
if errorlevel 1 goto error
echo.
echo Executavel criado em dist\PDF-para-Markdown.exe
pause
exit /b 0
:error
echo Falha ao criar o executavel.
pause
exit /b 1

