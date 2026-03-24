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
REM [2/6] Chiffrement du .env pour distribution multi-machines
REM -----------------------------------------------------------------------
echo [2/6] Chiffrement des credentials DB...

if exist "App\.env" (
    py -c "import sys; sys.path.insert(0, 'App'); from core.utils.config_crypter import encrypt_env_file_dist; encrypt_env_file_dist('App/.env', 'App/.env.encrypted')"
    if errorlevel 1 (
        echo [ERREUR] Echec du chiffrement de App\.env
        pause
        exit /b 1
    )
    echo       OK - App\.env.encrypted genere ^(cle embarquee, fonctionne sur toutes les machines^)
) else (
    echo [AVERTISSEMENT] App\.env introuvable - les credentials DB ne seront pas embarques.
    echo                 Creez App\.env avec EMAC_DB_PASSWORD=votre_mot_de_passe
    echo                 puis relancez le build.
    if not exist "App\.env.encrypted" (
        echo [ERREUR] Ni App\.env ni App\.env.encrypted present - build annule.
        pause
        exit /b 1
    )
    echo       INFO - App\.env.encrypted existant conserve.
)
echo.

REM -----------------------------------------------------------------------
REM [3/7] Nettoyage
REM -----------------------------------------------------------------------
echo [3/7] Nettoyage des anciens builds...
if exist "build"  rmdir /S /Q "build"
if exist "dist"   rmdir /S /Q "dist"
echo       OK
echo.

REM -----------------------------------------------------------------------
REM [4/7] Compilation PyInstaller
REM -----------------------------------------------------------------------
echo [4/7] Compilation PyInstaller (mode release, sans console)...
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
REM [5/7] Verification de l'executable
REM -----------------------------------------------------------------------
echo [5/7] Verification de l'executable...
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
REM [6/7] Copie des fichiers de configuration
REM -----------------------------------------------------------------------
echo [6/7] Copie des fichiers de configuration...

REM Le .env.encrypted est inclus automatiquement par le spec PyInstaller (etape 2).
REM Il est chiffre avec la cle embarquee et fonctionne sur toutes les machines cibles.
REM Le .env en clair n'est JAMAIS copie dans le build (securite).
if exist "App\.env.encrypted" (
    echo       OK - .env.encrypted embarque ^(chiffre, fonctionne sur toutes les machines^)
) else (
    echo [AVERTISSEMENT] .env.encrypted absent - les credentials ne seront pas embarques
)

if not exist "dist\EMAC\logs" mkdir "dist\EMAC\logs"
echo       OK - Dossier logs\ cree
echo.

REM -----------------------------------------------------------------------
REM [7/7] Resume final
REM -----------------------------------------------------------------------
echo [7/7] Calcul de la taille totale...
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
echo  Configuration: dist\EMAC\.env
echo  Logs         : dist\EMAC\logs\
echo  Exports      : dist\EMAC\exports\
echo.
echo  Pour distribuer : copiez tout le dossier dist\EMAC\
echo                    (ne pas distribuer uniquement EMAC.exe)
echo.
echo ================================================================================
echo.

set /p "launch=Lancer l'application maintenant ? (O/N) : "
if /i "%launch%"=="O" (
    echo Lancement de EMAC...
    start "" "dist\EMAC\EMAC.exe"
)

pause
