@echo off
REM =========================================
REM Build EMAC - Version Simple
REM =========================================

setlocal

echo.
echo =========================================
echo  BUILD EMAC
echo =========================================
echo.

REM Se positionner dans le bon dossier
cd /d "%~dp0"
cd ..

echo Dossier racine: %CD%
echo.

REM Verifier Python
echo [1/7] Verification Python...
py --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python non installe
    pause
    exit /b 1
)
echo OK
echo.

REM Verifier PyInstaller
echo [2/7] Verification PyInstaller...
py -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installation PyInstaller...
    py -m pip install pyinstaller
)
echo OK
echo.

REM Verifier dependances
echo [3/7] Verification dependances...
cd App
py -c "import PyQt5, mysql.connector, reportlab, openpyxl, bcrypt, dotenv" 2>nul
if errorlevel 1 (
    echo Installation dependances...
    py -m pip install -r requirements.txt
)
cd ..
echo OK
echo.

REM Nettoyer
echo [4/7] Nettoyage...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo OK
echo.

REM Build
echo [5/7] Build PyInstaller...
echo Cela peut prendre 5-10 minutes...
echo.

pyinstaller --noconfirm --onedir --windowed ^
    --name "EMAC" ^
    --distpath "dist" ^
    --workpath "build" ^
    --add-data "App/config/.env.example;config" ^
    --hidden-import "mysql.connector" ^
    --hidden-import "PyQt5.QtPrintSupport" ^
    --hidden-import "reportlab.pdfbase.ttfonts" ^
    --hidden-import "openpyxl.cell._writer" ^
    --hidden-import "bcrypt._bcrypt" ^
    --hidden-import "dotenv" ^
    --exclude-module "pandas" ^
    --exclude-module "numpy" ^
    --exclude-module "matplotlib" ^
    --exclude-module "tkinter" ^
    "App/core/gui/main_qt.py"

if errorlevel 1 (
    echo.
    echo ERREUR lors du build
    pause
    exit /b 1
)
echo.
echo OK
echo.

REM Creer structure
echo [6/7] Creation structure...
if not exist "dist\EMAC\logs" mkdir "dist\EMAC\logs"
if not exist "dist\EMAC\exports" mkdir "dist\EMAC\exports"
if not exist "dist\EMAC\database\backups" mkdir "dist\EMAC\database\backups"
if not exist "dist\EMAC\config" mkdir "dist\EMAC\config"

REM Copier fichiers
copy /Y "App\config\.env.example" "dist\EMAC\config\.env.example" >nul 2>&1
copy /Y "App\database\schema\bddemac.sql" "dist\EMAC\database\schema.sql" >nul 2>&1

REM Creer LISEZMOI.txt
(
echo EMAC - Gestion du Personnel
echo =============================
echo.
echo Installation:
echo 1. Copier config\.env.example vers .env
echo 2. Editer .env avec vos parametres MySQL
echo 3. Lancer EMAC.exe
echo.
echo Configuration MySQL requise dans .env:
echo - EMAC_DB_HOST=votre_serveur
echo - EMAC_DB_USER=root
echo - EMAC_DB_PASSWORD=votre_mdp
echo - EMAC_DB_NAME=emac_db
) > "dist\EMAC\LISEZMOI.txt"

REM Creer script config
(
echo @echo off
echo if not exist config\.env.example ^(
echo     echo ERREUR: config\.env.example introuvable
echo     pause
echo     exit /b 1
echo ^)
echo copy config\.env.example .env
echo notepad .env
echo pause
) > "dist\EMAC\CONFIGURER.bat"

echo OK
echo.

REM Calculer taille
echo [7/7] Calcul taille...
for /f "tokens=3" %%a in ('dir /s dist\EMAC ^| find "octets"') do set SIZE=%%a
set /a SIZE_MB=%SIZE% / 1048576
echo Taille: %SIZE_MB% MB
echo.

echo =========================================
echo  BUILD TERMINE
echo =========================================
echo.
echo Executable: dist\EMAC\EMAC.exe
echo Taille: %SIZE_MB% MB
echo.
echo Pour tester:
echo   cd dist\EMAC
echo   CONFIGURER.bat
echo   EMAC.exe
echo.

pause
