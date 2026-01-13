@echo off
REM ============================================================================
REM cleanup_temp.bat - Nettoyage des fichiers temporaires EMAC
REM ============================================================================
REM Supprime tous les fichiers temporaires créés par Claude et le développement
REM
REM Usage:
REM   cleanup_temp.bat
REM ============================================================================

echo.
echo ================================================================================
echo EMAC - Nettoyage des fichiers temporaires
echo ================================================================================
echo.

set count=0

REM Dossiers temporaires Claude à la racine
echo [1/4] Nettoyage des dossiers tmpclaude-* (racine)...
for /d %%d in (tmpclaude-*) do (
    if exist "%%d" (
        echo       Suppression: %%d
        rmdir /S /Q "%%d" 2>nul
        set /a count+=1
    )
)
echo       OK - %count% dossiers supprimes
echo.

set count=0

REM Dossiers temporaires Claude dans App
echo [2/4] Nettoyage des dossiers tmpclaude-* (App)...
for /d %%d in (App\tmpclaude-*) do (
    if exist "%%d" (
        echo       Suppression: %%d
        rmdir /S /Q "%%d" 2>nul
        set /a count+=1
    )
)
echo       OK - %count% dossiers supprimes
echo.

REM Fichiers cache Python
echo [3/4] Nettoyage des fichiers cache Python...
for /r %%i in (__pycache__) do (
    if exist "%%i" (
        rmdir /S /Q "%%i" 2>nul
    )
)
for /r %%i in (*.pyc) do (
    if exist "%%i" (
        del /Q "%%i" 2>nul
    )
)
echo       OK - Cache Python nettoye
echo.

REM Fichiers de build PyInstaller
echo [4/4] Nettoyage des fichiers de build...
if exist "build" (
    echo       Suppression: build\
    rmdir /S /Q "build" 2>nul
)
if exist "dist" (
    echo       Suppression: dist\
    rmdir /S /Q "dist" 2>nul
)
if exist "*.spec.pyc" (
    del /Q "*.spec.pyc" 2>nul
)
echo       OK - Fichiers de build nettoyes
echo.

echo ================================================================================
echo NETTOYAGE TERMINE
echo ================================================================================
echo.
echo Fichiers/dossiers supprimes:
echo   - tmpclaude-* (dossiers temporaires Claude)
echo   - __pycache__/ (cache Python)
echo   - *.pyc (bytecode Python compile)
echo   - build/ (fichiers de compilation PyInstaller)
echo   - dist/ (executable compile)
echo.
echo Le projet est maintenant propre et pret pour:
echo   - Un nouveau build
echo   - Un commit Git
echo   - Une archive
echo.
echo ================================================================================
echo.

pause
