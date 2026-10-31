@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo Criando ambiente virtual...
    py -3 -m venv .venv
    if errorlevel 1 goto error
)
".venv\Scripts\python.exe" -c "import markitdown" >nul 2>&1
if errorlevel 1 (
    echo Instalando Microsoft MarkItDown...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto error
)
start "PDF para Markdown" ".venv\Scripts\pythonw.exe" desktop_app.py
exit /b 0
:error
echo Nao foi possivel iniciar. Verifique o Python 3.10 a 3.14 e sua conexao com a internet.
pause
exit /b 1

