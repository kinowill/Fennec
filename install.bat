@echo off
setlocal enabledelayedexpansion
title Fennec - Installation

echo.
echo   ==============================
echo     Fennec - Installation
echo   ==============================
echo.

set "SRC=%~dp0"
REM Retirer le trailing backslash pour eviter les problemes de guillemets
if "%SRC:~-1%"=="\" set "SRC=%SRC:~0,-1%"
set "DEST=%LocalAppData%\Fennec"
set "VENV=%DEST%\.venv"
set "DESKTOP=%USERPROFILE%\Desktop"

REM --- [1/6] Verification Python ---
echo   [1/6] Verification de Python...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   [ERREUR] Python introuvable.
    echo   Installe Python 3.10+ depuis https://python.org
    echo   Coche "Add Python to PATH" pendant l'installation.
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PYVER=%%v"
echo   [OK] Python %PYVER% detecte.

REM --- [2/6] Creation du dossier ---
echo   [2/6] Creation du dossier d'installation...
if not exist "%DEST%" mkdir "%DEST%"
if %errorlevel% neq 0 (
    echo   [ERREUR] Impossible de creer %DEST%
    pause
    exit /b 1
)
echo   [OK] %DEST%

REM --- [3/6] Copie des fichiers ---
echo   [3/6] Copie des fichiers...
copy /y "%SRC%\src\fennec.py" "%DEST%\" > nul
copy /y "%SRC%\src\launcher.py" "%DEST%\" > nul
copy /y "%SRC%\src\fennec.bat" "%DEST%\" > nul
copy /y "%SRC%\src\requirements.txt" "%DEST%\" > nul
copy /y "%SRC%\FENNEC_LOGO.webp" "%DEST%\" > nul
copy /y "%SRC%\uninstall.bat" "%DEST%\" > nul
echo   [OK] 6 fichiers copies.

REM --- [4/6] Environnement virtuel + dependances ---
echo   [4/6] Creation de l'environnement virtuel...
if not exist "%VENV%\Scripts\python.exe" (
    python -m venv "%VENV%"
    if %errorlevel% neq 0 (
        echo   [ERREUR] Impossible de creer le venv.
        pause
        exit /b 1
    )
)
set "VPYTHON=%VENV%\Scripts\python.exe"
echo          Installation des dependances...
"%VPYTHON%" -m pip install --upgrade pip --quiet > nul 2>&1
"%VPYTHON%" -m pip install -r "%DEST%\requirements.txt" --quiet > nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERREUR] Impossible d'installer les dependances.
    pause
    exit /b 1
)
"%VPYTHON%" -m pip install Pillow --quiet > nul 2>&1
echo   [OK] Dependances installees.

REM --- [5/6] Creation de l'icone ---
echo   [5/6] Creation de l'icone...
"%VPYTHON%" -c "from PIL import Image; img = Image.open(r'%DEST%\FENNEC_LOGO.webp').convert('RGBA'); img.save(r'%DEST%\fennec.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])" > nul 2>&1
if %errorlevel% neq 0 (
    echo   [ATTENTION] Conversion du logo echouee, raccourci sans icone.
) else (
    echo   [OK] fennec.ico cree.
)

REM --- [6/6] Raccourci bureau ---
echo   [6/6] Creation du raccourci bureau...
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\Fennec.lnk'); $s.TargetPath = '%DEST%\fennec.bat'; $s.WorkingDirectory = '%USERPROFILE%'; $s.IconLocation = '%DEST%\fennec.ico,0'; $s.Description = 'Fennec - Shell IA Windows'; $s.Save()" > nul 2>&1
if %errorlevel% neq 0 (
    echo   [ATTENTION] Impossible de creer le raccourci.
) else (
    echo   [OK] Raccourci Fennec cree sur le bureau.
)

echo.
echo   ======================================
echo     Fennec installe avec succes !
echo   ======================================
echo.
echo   Dossier  : %DEST%
echo   Raccourci: %DESKTOP%\Fennec.lnk
echo.
echo   Lance Fennec depuis le raccourci sur ton bureau.
echo   Launch Fennec from the shortcut on your desktop.
echo.

REM --- Proposer de supprimer le dossier source ---
echo   ------------------------------------------------
echo   Ce dossier n'est plus necessaire.
echo   Fennec est installe dans %DEST%.
echo   Pour mettre a jour, il faudra re-cloner le projet.
echo.
echo   This folder is no longer needed.
echo   Fennec is installed in %DEST%.
echo   To update, you will need to re-clone the project.
echo   ------------------------------------------------
echo.
set /p CLEANUP="  Supprimer ce dossier source ? / Delete this source folder? (o/y/N) : "
if /i "%CLEANUP%"=="o" goto do_cleanup
if /i "%CLEANUP%"=="y" goto do_cleanup
if /i "%CLEANUP%"=="oui" goto do_cleanup
if /i "%CLEANUP%"=="yes" goto do_cleanup
echo.
echo   OK, dossier conserve. / OK, folder kept.
echo.
pause
exit /b 0

:do_cleanup
echo.
echo   [OK] Le dossier sera supprime automatiquement.
echo   [OK] Folder will be deleted automatically.
echo.
REM Lancer PowerShell en process separe : attend 3s puis supprime le dossier source.
start "" /min powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep 3; Remove-Item -LiteralPath '%SRC%' -Recurse -Force"
exit
