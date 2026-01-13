# ============================================================================
# cleanup_temp.ps1 - Nettoyage des fichiers temporaires EMAC (PowerShell)
# ============================================================================

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "EMAC - Nettoyage des fichiers temporaires" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Dossiers temporaires Claude
Write-Host "[1/4] Nettoyage des dossiers tmpclaude-*..." -ForegroundColor Yellow
$tmpDirs = Get-ChildItem -Path . -Recurse -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'tmpclaude-*' }
if ($tmpDirs.Count -gt 0) {
    $tmpDirs | ForEach-Object {
        Write-Host "       Suppression: $($_.FullName)" -ForegroundColor Gray
        Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }
    Write-Host "       OK - $($tmpDirs.Count) dossiers supprimes" -ForegroundColor Green
} else {
    Write-Host "       OK - Aucun dossier tmpclaude trouve" -ForegroundColor Green
}
Write-Host ""

# Fichiers cache Python
Write-Host "[2/4] Nettoyage des fichiers cache Python..." -ForegroundColor Yellow
$pycacheDirs = Get-ChildItem -Path . -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue
$pycFiles = Get-ChildItem -Path . -Recurse -Filter '*.pyc' -ErrorAction SilentlyContinue
$totalPy = $pycacheDirs.Count + $pycFiles.Count
if ($totalPy -gt 0) {
    $pycacheDirs | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    $pycFiles | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "       OK - $totalPy elements de cache Python supprimes" -ForegroundColor Green
} else {
    Write-Host "       OK - Aucun cache Python trouve" -ForegroundColor Green
}
Write-Host ""

# Fichiers de build PyInstaller
Write-Host "[3/4] Nettoyage des fichiers de build PyInstaller..." -ForegroundColor Yellow
$cleaned = 0
if (Test-Path "build") {
    Write-Host "       Suppression: build\" -ForegroundColor Gray
    Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
    $cleaned++
}
if (Test-Path "dist") {
    Write-Host "       Suppression: dist\" -ForegroundColor Gray
    Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
    $cleaned++
}
$specPyc = Get-ChildItem -Path . -Filter '*.spec.pyc' -ErrorAction SilentlyContinue
if ($specPyc.Count -gt 0) {
    $specPyc | Remove-Item -Force -ErrorAction SilentlyContinue
    $cleaned += $specPyc.Count
}
Write-Host "       OK - $cleaned elements de build supprimes" -ForegroundColor Green
Write-Host ""

# Fichiers .cwd isolés
Write-Host "[4/4] Nettoyage des fichiers .cwd..." -ForegroundColor Yellow
$cwdFiles = Get-ChildItem -Path . -Recurse -Filter '*.cwd' -ErrorAction SilentlyContinue
if ($cwdFiles.Count -gt 0) {
    $cwdFiles | ForEach-Object {
        Write-Host "       Suppression: $($_.FullName)" -ForegroundColor Gray
        Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
    }
    Write-Host "       OK - $($cwdFiles.Count) fichiers .cwd supprimes" -ForegroundColor Green
} else {
    Write-Host "       OK - Aucun fichier .cwd trouve" -ForegroundColor Green
}
Write-Host ""

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "NETTOYAGE TERMINE" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Fichiers/dossiers supprimes:" -ForegroundColor White
Write-Host "  - tmpclaude-* (dossiers temporaires Claude)" -ForegroundColor Gray
Write-Host "  - __pycache__/ (cache Python)" -ForegroundColor Gray
Write-Host "  - *.pyc (bytecode Python compile)" -ForegroundColor Gray
Write-Host "  - build/ et dist/ (fichiers de compilation PyInstaller)" -ForegroundColor Gray
Write-Host "  - *.cwd (fichiers working directory)" -ForegroundColor Gray
Write-Host ""
Write-Host "Le projet est maintenant propre et pret pour:" -ForegroundColor White
Write-Host "  - Un nouveau build" -ForegroundColor Gray
Write-Host "  - Un commit Git" -ForegroundColor Gray
Write-Host "  - Une archive" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
