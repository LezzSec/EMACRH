@echo off
REM ===============================================================
REM   BUILD EMAC AVEC NUITKA (Simple - Depuis VS Code)
REM ===============================================================
REM
REM Ce script fonctionne directement depuis VS Code
REM Nuitka telecharge automatiquement MinGW (pas besoin de Visual Studio)
REM
REM ===============================================================

echo.
echo ===============================================================
echo   BUILD EMAC AVEC NUITKA (Ultra-rapide au demarrage)
echo ===============================================================
echo.

echo [1/4] Verification de Nuitka...
py -m nuitka --version >nul 2>&1
if errorlevel 1 (
    echo    Nuitka n'est pas installe, installation en cours...
    py -m pip install nuitka
    if errorlevel 1 (
        echo    ERREUR : Impossible d'installer Nuitka
        pause
        exit /b 1
    )
)
echo    OK : Nuitka est pret

echo.
echo [2/4] Nettoyage des anciens builds...
if exist "test_nuitka_build" rmdir /s /q "test_nuitka_build"
if exist "main_qt.dist" rmdir /s /q "main_qt.dist"
if exist "main_qt.build" rmdir /s /q "main_qt.build"
echo    OK : Nettoyage termine

echo.
echo [3/4] Compilation avec Nuitka (5-15 minutes)...
echo.
echo    Options utilisees :
echo      --mingw64 : Telecharge MinGW automatiquement
echo      --standalone : Exe avec toutes les dependances
echo      --enable-plugin=pyqt5 : Support PyQt5 optimise
echo      --windows-disable-console : Pas de fenetre DOS
echo      --assume-yes-for-downloads : Accepte MinGW auto
echo.
echo    La premiere compilation telecharge MinGW (~500 MB)
echo    Les compilations suivantes seront beaucoup plus rapides
echo.

py -m nuitka ^
    --mingw64 ^
    --standalone ^
    --enable-plugin=pyqt5 ^
    --windows-disable-console ^
    --assume-yes-for-downloads ^
    --show-progress ^
    --output-dir=dist_nuitka ^
    core/gui/main_qt.py

if errorlevel 1 (
    echo.
    echo ERREUR : La compilation a echoue
    echo Verifiez les messages d'erreur ci-dessus
    pause
    exit /b 1
)

echo.
echo [4/4] Organisation des fichiers...

REM Trouver le dossier cree par Nuitka
if exist "dist_nuitka\main_qt.dist" (
    REM Copier le .env
    if exist ".env" (
        copy /y ".env" "dist_nuitka\main_qt.dist\.env" >nul
        echo    - .env copie
    ) else (
        echo    - ATTENTION : .env non trouve
    )

    REM Renommer pour plus de clarte
    if exist "dist_nuitka\EMAC_Nuitka" rmdir /s /q "dist_nuitka\EMAC_Nuitka"
    move "dist_nuitka\main_qt.dist" "dist_nuitka\EMAC_Nuitka" >nul

    REM Renommer l'exe
    if exist "dist_nuitka\EMAC_Nuitka\main_qt.exe" (
        ren "dist_nuitka\EMAC_Nuitka\main_qt.exe" EMAC.exe
        echo    - Executable renomme : EMAC.exe
    )

    echo    - Dossier pret : dist_nuitka\EMAC_Nuitka
) else (
    echo    ERREUR : Dossier de sortie introuvable
    pause
    exit /b 1
)

echo.
echo ===============================================================
echo   COMPILATION TERMINEE !
echo ===============================================================
echo.
echo   Executable : dist_nuitka\EMAC_Nuitka\EMAC.exe
echo.
echo   Test local :
echo     cd dist_nuitka\EMAC_Nuitka
echo     EMAC.exe
echo.
echo   AVANTAGES DE NUITKA vs PYINSTALLER :
echo     - Demarrage : ~0.5s au lieu de 5-10s sur reseau
echo     - Taille : ~50 MB au lieu de ~100 MB
echo     - Performance : +30%% (code compile en C++)
echo.

REM Afficher la taille
if exist "dist_nuitka\EMAC_Nuitka\EMAC.exe" (
    for %%A in ("dist_nuitka\EMAC_Nuitka\EMAC.exe") do echo   Taille exe : %%~zA octets
)

echo.
pause
