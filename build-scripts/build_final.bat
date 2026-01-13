@echo off
REM ============================================================================
REM build_final.bat - Compilation EMAC version finale (RELEASE)
REM ============================================================================
REM Version optimisée sans console pour distribution
REM ============================================================================

echo.
echo ================================================================================
echo EMAC - Build FINAL (version release)
echo ================================================================================
echo.

REM Vérifier qu'on est dans le bon dossier
if not exist "EMAC.spec" (
    echo [ERREUR] Fichier EMAC.spec introuvable.
    pause
    exit /b 1
)

echo [1/5] Nettoyage des anciens builds...
if exist "build" rmdir /S /Q "build"
if exist "dist" rmdir /S /Q "dist"
echo       OK
echo.

echo [2/5] Compilation avec PyInstaller (mode release)...
echo       Configuration: console=False, strip=True, optimize=2
echo       Duree estimee: 2-3 minutes
echo.
pyinstaller EMAC.spec
if errorlevel 1 (
    echo.
    echo [ERREUR] La compilation a echoue.
    pause
    exit /b 1
)
echo       OK
echo.

echo [3/5] Verification de l'executable...
if not exist "dist\EMAC\EMAC.exe" (
    echo [ERREUR] L'executable n'a pas ete cree.
    pause
    exit /b 1
)
echo       OK
echo.

echo [4/5] Copie du fichier .env...
if exist "App\.env" (
    copy /Y "App\.env" "dist\EMAC\.env" >nul
    echo       OK
) else (
    echo [ERREUR] Fichier App\.env introuvable.
    pause
    exit /b 1
)
echo.

echo [5/5] Creation du README pour distribution...
(
echo EMAC - Application de Gestion du Personnel
echo ===========================================
echo.
echo Installation:
echo   1. Copiez tout le dossier EMAC sur votre ordinateur
echo   2. Configurez le fichier .env avec vos parametres de base de donnees
echo   3. Lancez EMAC.exe
echo.
echo Configuration requise:
echo   - Windows 10/11
echo   - MySQL 8.0 ou superieur
echo   - Connexion reseau a la base de donnees
echo.
echo Support:
echo   Consultez la documentation dans le dossier docs/
echo.
) > "dist\EMAC\README.txt"
echo       OK
echo.

echo ================================================================================
echo BUILD FINAL TERMINE AVEC SUCCES
echo ================================================================================
echo.
echo Fichier genere: dist\EMAC\EMAC.exe
echo.
echo Caracteristiques:
echo   - Mode GUI pur (pas de console)
echo   - Bytecode Python optimise
echo   - Symboles de debug supprimes
echo   - Pret pour la distribution
echo.
echo ================================================================================
echo DISTRIBUTION
echo ================================================================================
echo.
echo Pour distribuer l'application:
echo   1. Compressez le dossier dist\EMAC\ en ZIP
echo   2. Distribuez l'archive ZIP
echo   3. L'utilisateur decompresse et configure .env
echo   4. Lance EMAC.exe
echo.
echo IMPORTANT: Tous les fichiers du dossier sont requis.
echo ================================================================================
echo.

pause
