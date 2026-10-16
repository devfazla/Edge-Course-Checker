# build.ps1 - makes the Windows executable with PyInstaller.
# Run from the project folder:  pwsh -File build.ps1
# Requires: Python 3.13 on PATH.

$ErrorActionPreference = "Stop"

Write-Host ">> installing build dependencies" -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host ">> building executable (single file, windowed)" -ForegroundColor Cyan
python -m PyInstaller --clean --noconfirm EdgeCourseChecker.spec

Write-Host ""
Write-Host ">> done. The exe is at:  dist\EdgeCourseChecker.exe" -ForegroundColor Green
Write-Host "   Next: compile installer.iss with Inno Setup (ISCC.exe) to make the setup." -ForegroundColor Gray
