@echo off
REM Script de build automatique pour EMAC
REM Construit l'executable et copie les fichiers necessaires

echo ============================================================================
echo Build EMAC - Mode ONEDIR (dossier rapide)
echo ============================================================================
echo.

REM Verifier que le fichier .env existe
if not exist ".env" (
    echo [ERREUR] Fichier .env introuvable!
    echo Veuillez creer le fichier .env avec la configuration de la base de donnees
    pause
    exit /b 1
)

echo [1/3] Nettoyage des anciens builds...
if exist "dist\EMAC" rmdir /s /q "dist\EMAC"
if exist "build\EMAC" rmdir /s /q "build\EMAC"

echo [2/3] Construction de l'executable...
pyinstaller EMAC.spec --clean -y

if %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] La construction a echoue!
    pause
    exit /b 1
)

echo [3/3] Copie du fichier .env...
copy /y ".env" "dist\EMAC\.env" >nul

if %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Impossible de copier le fichier .env!
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo [SUCCES] Build termine!
echo ============================================================================
echo.
echo Executable disponible dans: dist\EMAC\EMAC.exe
echo.
echo Pour distribuer:
echo  1. Zippez tout le dossier dist\EMAC\
echo  2. Distribuez le ZIP aux utilisateurs
echo  3. Les utilisateurs decompressent et lancent EMAC.exe
echo.

pause
