@echo off
REM ============================================================================
REM build_debug.bat - Compilation EMAC avec mode debug
REM ============================================================================
REM Ce script compile l'application avec console=True pour diagnostiquer les crashs
REM
REM Usage:
REM   build_debug.bat
REM
REM Output:
REM   dist/EMAC/EMAC.exe (avec console de debug)
REM ============================================================================

echo.
echo ================================================================================
echo EMAC - Build Debug (avec console)
echo ================================================================================
echo.

REM Vérifier qu'on est dans le bon dossier
if not exist "EMAC.spec" (
    echo [ERREUR] Fichier EMAC.spec introuvable.
    echo Vous devez executer ce script depuis le dossier racine du projet.
    pause
    exit /b 1
)

REM Vérifier que PyInstaller est installé
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [ERREUR] PyInstaller n'est pas installe.
    echo.
    echo Installation de PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERREUR] Impossible d'installer PyInstaller.
        pause
        exit /b 1
    )
)

echo [1/5] Nettoyage des anciens builds...
if exist "build" rmdir /S /Q "build"
if exist "dist" rmdir /S /Q "dist"
echo       OK - Dossiers build et dist supprimes
echo.

echo [2/5] Compilation avec PyInstaller (mode debug)...
echo       Fichier: EMAC.spec
echo       Mode: one-folder, console=True
echo       Duree estimee: 2-3 minutes
echo.
pyinstaller EMAC.spec
if errorlevel 1 (
    echo.
    echo [ERREUR] La compilation a echoue.
    echo Verifiez les erreurs ci-dessus.
    pause
    exit /b 1
)
echo       OK - Compilation terminee
echo.

echo [3/5] Verification de l'executable...
if not exist "dist\EMAC\EMAC.exe" (
    echo [ERREUR] L'executable n'a pas ete cree.
    echo Verifiez les erreurs de compilation.
    pause
    exit /b 1
)
echo       OK - EMAC.exe trouve
echo.

echo [4/5] Copie du fichier .env (configuration DB)...
if exist "App\.env" (
    copy /Y "App\.env" "dist\EMAC\.env" >nul
    echo       OK - .env copie
) else (
    echo [AVERTISSEMENT] Fichier App\.env introuvable.
    echo                 L'application ne pourra pas se connecter a la base de donnees.
    echo                 Copiez manuellement App\.env vers dist\EMAC\.env
)
echo.

echo [5/5] Creation d'un lanceur avec pause...
(
echo @echo off
echo cd /d "%%~dp0"
echo echo Lancement de EMAC en mode debug...
echo echo.
echo EMAC.exe
echo echo.
echo echo Application fermee. Appuyez sur une touche pour quitter.
echo pause ^>nul
) > "dist\EMAC\EMAC_debug.bat"
echo       OK - EMAC_debug.bat cree
echo.

echo ================================================================================
echo BUILD TERMINE AVEC SUCCES
echo ================================================================================
echo.
echo Fichiers generes:
echo   - dist\EMAC\EMAC.exe           (executable avec console)
echo   - dist\EMAC\.env               (configuration DB)
echo   - dist\EMAC\EMAC_debug.bat     (lanceur avec pause)
echo.
echo IMPORTANT - Mode Debug Active:
echo   - Une console Windows s'affichera au lancement
echo   - Les erreurs seront visibles dans la console
echo   - Si l'application crash, la console restera ouverte
echo.
echo ================================================================================
echo PROCHAINES ETAPES
echo ================================================================================
echo.
echo 1. Tester l'application:
echo    cd dist\EMAC
echo    EMAC_debug.bat
echo.
echo 2. Si l'application fonctionne:
echo    - Modifier EMAC.spec: console=False, strip=True
echo    - Relancer: build_release.bat
echo.
echo 3. Si l'application crash:
echo    - Relevez l'erreur exacte dans la console
echo    - Consultez FIX_CRASH_EXE.md
echo.
echo ================================================================================
echo.

pause
