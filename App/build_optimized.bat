@echo off
REM ✅ Script de compilation optimisé pour EMAC
REM Génère un exécutable rapide (one-folder)

echo.
echo ================================================
echo   COMPILATION EMAC - VERSION OPTIMISEE
echo ================================================
echo.

REM Nettoyer les anciens builds
echo [1/4] Nettoyage des anciens builds...
if exist build rmdir /s /q build
if exist dist\EMAC rmdir /s /q dist\EMAC

REM Compiler avec PyInstaller
echo.
echo [2/4] Compilation avec PyInstaller (mode one-folder)...
pyinstaller EMAC_optimized.spec --clean --noconfirm

REM Vérifier le résultat
if not exist dist\EMAC\EMAC.exe (
    echo.
    echo ❌ ERREUR : La compilation a echoue
    pause
    exit /b 1
)

REM ✅ Copier le .env à côté de l'exe (IMPORTANT)
if exist ".env" (
    copy /y ".env" "dist\EMAC\.env" >nul
) else if exist "config\.env" (
    copy /y "config\.env" "dist\EMAC\.env" >nul
) else (
    echo.
    echo ⚠️ ATTENTION : aucun .env trouvé (ni .env, ni config\.env)
    echo    L'exe peut planter si EMAC_DB_PASSWORD n'est pas défini.
)

REM ✅ Vérifier que le .env est bien présent (optionnel mais conseillé)
if not exist "dist\EMAC\.env" (
    echo.
    echo ⚠️ WARNING : .env non copié dans dist\EMAC\
)

echo.
echo [3/4] Copie des ressources additionnelles...
REM Copier les fichiers nécessaires si besoin
REM xcopy /s /i database dist\EMAC\database

echo.
echo [4/4] Optimisation terminee !
echo.
echo ================================================
echo   ✅ EXECUTABLE CREE : dist\EMAC\EMAC.exe
echo ================================================
echo.
echo Taille du dossier :
dir dist\EMAC /s | find "octets"
echo.
echo Lancez dist\EMAC\EMAC.exe pour tester
echo.
pause
