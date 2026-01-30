@echo off
REM ============================================================================
REM EMAC - Lancement DEBUG avec console visible
REM ============================================================================
setlocal

REM Se placer dans le dossier du .bat
cd /d %~dp0

echo =====================================================
echo EMAC - MODE DEBUG (console active)
echo =====================================================
echo.

REM Activer le faulthandler Python (crash natifs, segfault, etc.)
set PYTHONFAULTHANDLER=1

REM Optionnel : forcer l'encodage UTF-8
set PYTHONUTF8=1

REM Lancer l'application
python -X faulthandler -m core.gui.main_qt

echo.
echo =====================================================
echo L'application s'est fermee.
echo Si une erreur est apparue, elle est affichee au-dessus.
echo =====================================================
echo.

pause
endlocal
