@echo off
setlocal
title Fennec - Desinstallation

set "DEST=%LocalAppData%\Fennec"
set "DATADIR=%LocalAppData%\Fennec"
set "SHORTCUT=%USERPROFILE%\Desktop\Fennec.lnk"

echo.
echo   ==============================
echo     Fennec - Desinstallation
echo   ==============================
echo.
echo   Dossier  : %DEST%
echo   Donnees  : %DATADIR%
echo   Raccourci: %SHORTCUT%
echo.

set /p CONFIRM="  Confirmer la desinstallation ? (o/N) : "
if /i not "%CONFIRM%"=="o" (
    echo.
    echo   Desinstallation annulee.
    echo.
    pause
    exit /b 0
)

echo.

REM Suppression raccourci
if exist "%SHORTCUT%" (
    del "%SHORTCUT%"
    echo   [OK] Raccourci bureau supprime.
) else (
    echo   [--] Raccourci non trouve.
)

REM Suppression dossier
if exist "%DEST%" (
    rmdir /s /q "%DEST%"
    if exist "%DEST%" (
        echo.
        echo   [ERREUR] Impossible de supprimer %DEST%
        echo   Ferme Fennec et reessaye.
        echo.
        pause
        exit /b 1
    )
    echo   [OK] Dossier supprime.
) else (
    echo   [--] Dossier non trouve.
)

echo.
echo   Fennec a ete desinstalle.
echo.
pause
