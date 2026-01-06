@echo off
REM ===============================================================
REM   BUILD EMAC AVEC NUITKA (Version ultra-rapide)
REM ===============================================================
REM
REM Nuitka compile Python en C++ pour un exe natif ultra-rapide
REM Demarrage: ~0.5s au lieu de 5-10s avec PyInstaller
REM
REM PREREQUIS:
REM   pip install nuitka
REM   Visual Studio Build Tools OU MinGW-w64
REM
REM ===============================================================

echo.
echo ===============================================================
echo   BUILD EMAC AVEC NUITKA (Compilation native C++)
echo ===============================================================
echo.

REM Verifier que Nuitka est installe
python -m nuitka --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERREUR : Nuitka n'est pas installe
    echo.
    echo Installation :
    echo   pip install nuitka
    echo.
    echo Puis installez un compilateur C++ :
    echo   - Visual Studio Build Tools : https://visualstudio.microsoft.com/downloads/
    echo   - OU MinGW-w64 : https://www.mingw-w64.org/
    echo.
    pause
    exit /b 1
)

echo [1/4] Nettoyage des anciens builds...
if exist "core.gui.main_qt.dist" rmdir /s /q "core.gui.main_qt.dist"
if exist "core.gui.main_qt.build" rmdir /s /q "core.gui.main_qt.build"
if exist "main_qt.exe" del /q "main_qt.exe"

echo.
echo [2/4] Compilation avec Nuitka (peut prendre 5-15 min)...
echo.
echo Options utilisees :
echo   - standalone : Exe autonome avec toutes les dependances
echo   - enable-plugin=pyqt5 : Support PyQt5 optimise
echo   - windows-disable-console : Pas de console DOS
echo   - show-progress : Afficher la progression
echo.

python -m nuitka ^
    --standalone ^
    --enable-plugin=pyqt5 ^
    --windows-disable-console ^
    --assume-yes-for-downloads ^
    --show-progress ^
    --output-dir=dist_nuitka ^
    core/gui/main_qt.py

if errorlevel 1 (
    echo.
    echo ERREUR : La compilation Nuitka a echoue
    pause
    exit /b 1
)

echo.
echo [3/4] Organisation des fichiers...

REM Nuitka cree un dossier main_qt.dist
if exist "dist_nuitka\main_qt.dist" (
    REM Copier le .env
    if exist ".env" (
        copy /y ".env" "dist_nuitka\main_qt.dist\.env" >nul
        echo    - .env copie
    )

    REM Renommer le dossier pour plus de clarte
    if exist "dist_nuitka\EMAC_Nuitka" rmdir /s /q "dist_nuitka\EMAC_Nuitka"
    move "dist_nuitka\main_qt.dist" "dist_nuitka\EMAC_Nuitka" >nul

    REM Renommer l'exe
    if exist "dist_nuitka\EMAC_Nuitka\main_qt.exe" (
        move "dist_nuitka\EMAC_Nuitka\main_qt.exe" "dist_nuitka\EMAC_Nuitka\EMAC.exe" >nul
    )

    echo    - Dossier renomme en EMAC_Nuitka
    echo    - Executable renomme en EMAC.exe
)

echo.
echo [4/4] Build termine !

echo.
echo ===============================================================
echo   EXECUTABLE CREE : dist_nuitka\EMAC_Nuitka\EMAC.exe
echo ===============================================================
echo.
echo AVANTAGES DE NUITKA :
echo   - Demarrage ultra-rapide (~0.5s au lieu de 5-10s)
echo   - Code compile en C++ natif
echo   - Taille reduite (~50-70 MB)
echo   - Moins de faux positifs antivirus
echo.
echo COMPARAISON :
dir dist\EMAC\EMAC.exe 2>nul | find "EMAC.exe"
dir dist_nuitka\EMAC_Nuitka\EMAC.exe 2>nul | find "EMAC.exe"
echo.
echo Testez : dist_nuitka\EMAC_Nuitka\EMAC.exe
echo.
pause
