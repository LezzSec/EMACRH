@echo off
REM ========================================
REM Script de test du déploiement EMAC
REM À exécuter avant le déploiement en production
REM ========================================

setlocal enabledelayedexpansion

cls
echo.
echo ================================================
echo   TEST DE DEPLOIEMENT EMAC
echo ================================================
echo.
echo   Ce script va verifier que tous les fichiers
echo   necessaires sont presents avant le deploiement
echo.
timeout /t 2 /nobreak >nul

REM Variables de configuration
set "TEST_PASSED=0"
set "TEST_FAILED=0"

REM ========================================
REM TEST 1 : Vérifier que l'exe existe
REM ========================================
echo [TEST 1/7] Verification de l'executable compile...

if exist "..\App\dist\EMAC\EMAC.exe" (
    echo    [OK] EMAC.exe trouve dans App\dist\EMAC\
    set /a TEST_PASSED+=1
) else (
    echo    [ERREUR] EMAC.exe introuvable
    echo             Veuillez compiler avec : pyinstaller EMAC_optimized.spec
    set /a TEST_FAILED+=1
)
echo.
timeout /t 1 /nobreak >nul

REM ========================================
REM TEST 2 : Vérifier que .env existe
REM ========================================
echo [TEST 2/7] Verification du fichier .env...

if exist "..\App\dist\EMAC\.env" (
    echo    [OK] .env present dans dist\EMAC\
    set /a TEST_PASSED+=1

    REM Vérifier le contenu
    findstr /C:"EMAC_DB_PASSWORD" "..\App\dist\EMAC\.env" >nul 2>&1
    if !errorlevel! EQU 0 (
        echo         EMAC_DB_PASSWORD configure
    ) else (
        echo    [ATTENTION] EMAC_DB_PASSWORD non trouve dans .env
    )
) else (
    echo    [ERREUR] .env introuvable
    echo             L'application ne pourra pas se connecter a la base de donnees
    set /a TEST_FAILED+=1
)
echo.
timeout /t 1 /nobreak >nul

REM ========================================
REM TEST 3 : Vérifier la structure du dossier
REM ========================================
echo [TEST 3/7] Verification de la structure du dossier...

if exist "..\App\dist\EMAC\_internal" (
    echo    [OK] Dossier _internal present
    set /a TEST_PASSED+=1
) else (
    echo    [ERREUR] Dossier _internal manquant
    echo             Structure PyInstaller incorrecte
    set /a TEST_FAILED+=1
)
echo.
timeout /t 1 /nobreak >nul

REM ========================================
REM TEST 4 : Vérifier que le lanceur existe
REM ========================================
echo [TEST 4/7] Verification du lanceur reseau...

if exist "Lancer_EMAC.bat" (
    echo    [OK] Lancer_EMAC.bat trouve
    set /a TEST_PASSED+=1

    REM Vérifier que SOURCE_RESEAU est configuré (pas la valeur par défaut)
    findstr /C:"SERVEUR\\Partage\\EMAC" "Lancer_EMAC.bat" >nul 2>&1
    if !errorlevel! EQU 0 (
        echo    [ATTENTION] SOURCE_RESEAU non configure (valeur par defaut)
        echo                Modifiez la ligne 10 de Lancer_EMAC.bat avant deploiement
    ) else (
        echo         SOURCE_RESEAU configure avec un chemin personnalise
    )
) else (
    echo    [ERREUR] Lancer_EMAC.bat introuvable
    set /a TEST_FAILED+=1
)
echo.
timeout /t 1 /nobreak >nul

REM ========================================
REM TEST 5 : Tester la compilation (mode one-folder)
REM ========================================
echo [TEST 5/7] Verification du mode de compilation...

REM Vérifier qu'il n'y a pas de fichier .pkg dans _internal (one-file)
dir /b "..\App\dist\EMAC\_internal\*.pkg" >nul 2>&1
if errorlevel 1 (
    echo    [OK] Compilation en mode one-folder (correct)
    set /a TEST_PASSED+=1
) else (
    echo    [ATTENTION] Fichiers .pkg detectes (mode one-file?)
    echo                Le mode one-folder est recommande pour le reseau
)
echo.
timeout /t 1 /nobreak >nul

REM ========================================
REM TEST 6 : Vérifier la taille de l'exe
REM ========================================
echo [TEST 6/7] Verification de la taille de l'application...

for %%A in ("..\App\dist\EMAC\EMAC.exe") do set "EXE_SIZE=%%~zA"
set /a "EXE_SIZE_MB=!EXE_SIZE! / 1048576"

if !EXE_SIZE_MB! LSS 5 (
    echo    [OK] Taille de l'exe : !EXE_SIZE_MB! Mo (normal pour one-folder)
    set /a TEST_PASSED+=1
) else (
    echo    [ATTENTION] Taille de l'exe : !EXE_SIZE_MB! Mo (elevee)
    echo                Verifiez que vous utilisez bien le mode one-folder
)

REM Taille totale du dossier
echo         Calcul de la taille totale...
for /f "tokens=3" %%a in ('dir /s "..\App\dist\EMAC" 2^>nul ^| findstr "octets"') do set "TOTAL_SIZE=%%a"
if defined TOTAL_SIZE (
    set "TOTAL_SIZE=!TOTAL_SIZE: =!"
    set "TOTAL_SIZE=!TOTAL_SIZE:,=!"
    if not "!TOTAL_SIZE!"=="" (
        set /a "TOTAL_SIZE_MB=!TOTAL_SIZE! / 1048576" 2>nul
        if !TOTAL_SIZE_MB! GTR 0 (
            echo         Taille totale : !TOTAL_SIZE_MB! Mo
        ) else (
            echo         Taille totale : calcul impossible
        )
    )
) else (
    echo         Taille totale : calcul impossible
)
echo.
timeout /t 1 /nobreak >nul

REM ========================================
REM TEST 7 : Vérifier que la doc existe
REM ========================================
echo [TEST 7/7] Verification de la documentation...

set "DOC_COUNT=0"
if exist "README_DEPLOIEMENT.md" set /a DOC_COUNT+=1
if exist "GUIDE_UTILISATEUR.md" set /a DOC_COUNT+=1

if !DOC_COUNT! EQU 2 (
    echo    [OK] Documentation complete (2/2 fichiers)
    set /a TEST_PASSED+=1
) else (
    echo    [ATTENTION] Documentation incomplete (!DOC_COUNT!/2 fichiers)
)
echo.
timeout /t 1 /nobreak >nul

REM ========================================
REM RÉSUMÉ DES TESTS
REM ========================================
echo.
echo ================================================
echo   RESUME DES TESTS
echo ================================================
echo.
echo   Tests reussis : !TEST_PASSED!/7
echo   Tests echoues : !TEST_FAILED!/7
echo.

if !TEST_FAILED! EQU 0 (
    echo   [SUCCES] TOUS LES TESTS SONT PASSES
    echo.
    echo   Vous pouvez proceder au deploiement :
    echo   1. Configurez SOURCE_RESEAU dans Lancer_EMAC.bat
    echo   2. Copiez dist\EMAC sur le partage reseau
    echo   3. Distribuez Lancer_EMAC.bat aux utilisateurs
    echo.
) else (
    echo   [ECHEC] !TEST_FAILED! TEST(S) ECHOUE(S)
    echo.
    echo   Veuillez corriger les erreurs avant le deploiement.
    echo.
)

echo ================================================
echo.
echo Appuyez sur une touche pour fermer...
pause >nul
exit /b !TEST_FAILED!
