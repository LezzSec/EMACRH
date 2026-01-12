@echo off
cd /d "%~dp0\App"
echo ============================================================
echo LANCEMENT DE L'APPLICATION AVEC CONSOLE DE DEBUG
echo ============================================================
echo.

python -m core.gui.main_qt

echo.
echo ============================================================
echo Application fermee
echo ============================================================
pause
