@echo off
title Fennec
chcp 65001 > nul 2>&1

set "SCRIPT=%~dp0fennec.py"
set "VENV=%~dp0.venv\Scripts\python.exe"
set "OLLAMA_KEEP_ALIVE=30m"

:: Choix Python : venv si present, sinon python systeme
set "PY=python"
if exist "%VENV%" set "PY=%VENV%"

:: Verification Python
"%PY%" --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python introuvable.
    echo Installe Python depuis https://python.org
    pause
    exit /b 1
)

:: Verification fennec.py
if not exist "%SCRIPT%" (
    echo [ERREUR] fennec.py introuvable.
    echo Mets fennec.bat et fennec.py dans le meme dossier.
    pause
    exit /b 1
)

:: Dependances principales
"%PY%" -c "import rich, prompt_toolkit" > nul 2>&1
if %errorlevel% neq 0 (
    echo Installation des dependances...
    "%PY%" -m pip install rich prompt_toolkit --quiet
    if %errorlevel% neq 0 (
        echo [ERREUR] Impossible d'installer les dependances.
        pause
        exit /b 1
    )
)

:: Dependances optionnelles
"%PY%" -c "import pdfplumber" > nul 2>&1
if %errorlevel% neq 0 (
    echo Installation pdfplumber...
    "%PY%" -m pip install pdfplumber --quiet
)

"%PY%" -c "import docx" > nul 2>&1
if %errorlevel% neq 0 (
    echo Installation python-docx...
    "%PY%" -m pip install python-docx --quiet
)

:: Verification Ollama installe
where ollama > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Ollama n'est pas installe.
    echo Telecharge-le sur https://ollama.com
    pause
    exit /b 1
)

:: Demarrage Ollama si necessaire
curl -s --max-time 2 http://localhost:11434 > nul 2>&1
if %errorlevel% equ 0 goto check_model

echo Demarrage Ollama...
start "" /min ollama serve
set /a tries=0

:wait_loop
timeout /t 2 /nobreak > nul
curl -s --max-time 2 http://localhost:11434 > nul 2>&1
if %errorlevel% equ 0 goto check_model
set /a tries+=1
if %tries% lss 7 goto wait_loop
echo [ERREUR] Ollama ne repond pas apres 14 secondes.
pause
exit /b 1

:: Verification modele
:check_model
ollama list 2>nul | findstr /i "qwen2.5" > nul 2>&1
if %errorlevel% equ 0 goto launch

echo Telechargement du modele qwen2.5:7b...
ollama pull qwen2.5:7b
if %errorlevel% neq 0 (
    echo [ERREUR] Impossible de telecharger le modele.
    pause
    exit /b 1
)

:launch
"%PY%" "%SCRIPT%"
if %errorlevel% neq 0 (
    echo.
    echo [ERREUR] Fennec s'est arrete avec le code %errorlevel%
    pause
)