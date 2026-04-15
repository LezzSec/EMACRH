@echo off
REM ============================================================================
REM build_release.bat - Compilation EMAC version release
REM ============================================================================
REM Usage: double-clic ou lancer depuis build-scripts\
REM Output: dist\EMAC\EMAC.exe (sans console)
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ================================================================================
echo  EMAC - Build Release
echo ================================================================================
echo.

REM Se positionner a la racine du projet (dossier parent de build-scripts\)
cd /d "%~dp0"
cd ..
set "ROOT=%CD%"
set "SPEC_FILE=build-scripts\specs\EMAC_base.spec"

echo Racine projet : %ROOT%
echo Spec          : %SPEC_FILE%
echo.

REM -----------------------------------------------------------------------
REM [1/6] Verifications prealables
REM -----------------------------------------------------------------------
echo [1/6] Verifications...

if not exist "%SPEC_FILE%" (
    echo [ERREUR] Fichier spec introuvable : %SPEC_FILE%
    pause
    exit /b 1
)
echo       OK - Spec trouve

py --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python introuvable. Verifiez votre installation.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('py --version 2^>^&1') do echo       OK - %%i

py -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo       PyInstaller absent - Installation en cours...
    py -m pip install pyinstaller
    if errorlevel 1 (
        echo [ERREUR] Impossible d'installer PyInstaller.
        pause
        exit /b 1
    )
)
for /f "tokens=*" %%i in ('py -m PyInstaller --version 2^>^&1') do echo       OK - PyInstaller %%i

echo       OK - Verifications terminees
echo.

REM -----------------------------------------------------------------------
REM [2/5] Verification des credentials DB
REM -----------------------------------------------------------------------
echo [2/5] Verification des credentials DB...

if exist "App\.env" (
    echo       OK - App\.env trouve, sera embarque dans le build
    echo            ^(tous les postes fonctionneront sans configuration manuelle^)
) else (
    echo [AVERTISSEMENT] App\.env absent.
    echo                 Les credentials DB ne seront PAS embarques dans l'exe.
    echo                 Les utilisateurs devront lancer setup_machine.bat sur chaque poste.
    echo.
    choice /C CN /M "Continuer quand meme"
    if errorlevel 2 (
        echo Build annule. Creez App\.env avec EMAC_DB_PASSWORD=votre_mot_de_passe
        pause
        exit /b 1
    )
)
echo.

REM -----------------------------------------------------------------------
REM [3/5] Nettoyage
REM -----------------------------------------------------------------------
echo [3/5] Nettoyage des anciens builds...
if exist "build"  rmdir /S /Q "build"
if exist "dist"   rmdir /S /Q "dist"
echo       OK
echo.

REM -----------------------------------------------------------------------
REM [3/5] Compilation PyInstaller
REM -----------------------------------------------------------------------
echo [3/5] Compilation PyInstaller (mode release, sans console)...
echo       Duree estimee : 3-5 minutes
echo.

py -m PyInstaller --noconfirm "%SPEC_FILE%"

if errorlevel 1 (
    echo.
    echo [ERREUR] La compilation a echoue.
    if exist "build\EMAC\warn-EMAC.txt" (
        echo Consultez build\EMAC\warn-EMAC.txt pour les details.
    )
    pause
    exit /b 1
)
echo.
echo       OK - Compilation terminee
echo.

REM -----------------------------------------------------------------------
REM [4/5] Verification de l'executable
REM -----------------------------------------------------------------------
echo [4/5] Verification de l'executable...
if not exist "dist\EMAC\EMAC.exe" (
    echo [ERREUR] dist\EMAC\EMAC.exe introuvable apres compilation.
    pause
    exit /b 1
)
for %%A in ("dist\EMAC\EMAC.exe") do (
    set /a EXE_MB=%%~zA / 1048576
    echo       OK - EMAC.exe trouve ^(!EXE_MB! MB^)
)
echo.

REM -----------------------------------------------------------------------
REM [5/5] Finalisation du dossier de distribution
REM -----------------------------------------------------------------------
echo [5/5] Finalisation...

if not exist "dist\EMAC\logs" mkdir "dist\EMAC\logs"
echo       OK - Dossier logs\ cree

REM Masquer le .env embarque dans _internal\
if exist "dist\EMAC\_internal\.env" (
    attrib +h "dist\EMAC\_internal\.env"
    echo       OK - .env masque ^(invisible sans "afficher les fichiers caches"^)
)

REM Copier setup_machine.bat dans le dossier de distribution
if exist "build-scripts\setup_machine.bat" (
    copy /Y "build-scripts\setup_machine.bat" "dist\EMAC\setup_machine.bat" >nul
    echo       OK - setup_machine.bat copie ^(a lancer une fois sur chaque poste^)
)
echo.

REM -----------------------------------------------------------------------
REM Resume final
REM -----------------------------------------------------------------------
echo Calcul de la taille totale...
set TOTAL_SIZE=0
for /r "dist\EMAC" %%F in (*) do set /a TOTAL_SIZE+=%%~zF
set /a SIZE_MB=%TOTAL_SIZE% / 1048576
for /f %%A in ('dir /s /b "dist\EMAC\*.*" 2^>nul ^| find /c /v ""') do set FILE_COUNT=%%A
echo       Taille : %SIZE_MB% MB  (%FILE_COUNT% fichiers)
echo.

echo ================================================================================
echo  BUILD RELEASE TERMINE AVEC SUCCES
echo ================================================================================
echo.
echo  Executable   : dist\EMAC\EMAC.exe
echo  Setup poste  : dist\EMAC\setup_machine.bat
echo  Logs         : dist\EMAC\logs\
echo.
echo  DEPLOIEMENT :
if exist "App\.env" (
    echo    Si App\.env etait present : copier dist\EMAC\ sur chaque poste et lancer EMAC.exe.
    echo    Aucune configuration supplementaire requise.
) else (
    echo    App\.env absent - sur chaque poste : copier dist\EMAC\, lancer setup_machine.bat, puis EMAC.exe.
)
echo.
echo ================================================================================
echo.

set /p "launch=Lancer l'application maintenant ? (O/N) : "
if /i "%launch%"=="O" (
    echo Lancement de EMAC...
    start "" "dist\EMAC\EMAC.exe"
)

pause
