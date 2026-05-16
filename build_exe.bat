@echo off
:: ─────────────────────────────────────────────────────────────────────────────
::  TAKOTA – Build standalone Windows .exe via PyInstaller
::  Run this once to create dist\TAKOTA.exe
:: ─────────────────────────────────────────────────────────────────────────────

title TAKOTA – Build EXE
color 0B

echo.
echo   TAKOTA -- Build Windows .exe
echo   ============================================
echo.

:: Locate Python
set PY=
for %%C in (python python3 py) do (
    if "!PY!"=="" (
        where %%C >nul 2>&1 && set PY=%%C
    )
)
setlocal EnableDelayedExpansion
for %%C in (python python3 py) do (
    if "!PY!"=="" (
        where %%C >nul 2>&1 && set PY=%%C
    )
)

if "!PY!"=="" (
    echo   [ERROR] Python not found. Run install_windows.ps1 first.
    pause
    exit /b 1
)
echo   [OK] Python found: !PY!

:: Install / upgrade PyInstaller
echo.
echo   Installing PyInstaller ...
!PY! -m pip install --quiet --upgrade pyinstaller
if errorlevel 1 (
    echo   [ERROR] pip install failed.
    pause
    exit /b 1
)
echo   [OK] PyInstaller ready

:: Build
echo.
echo   Building TAKOTA.exe ...
!PY! -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "TAKOTA" ^
    --add-data "." ^
    takota_gui.py

echo.
if exist "dist\TAKOTA.exe" (
    echo   [SUCCESS] Built: dist\TAKOTA.exe
    echo.
    echo   You can now distribute dist\TAKOTA.exe — no Python needed on target machine.
    echo   Note: aapt.exe must still be present on the target system.
) else (
    echo   [FAILED] dist\TAKOTA.exe not found. Check errors above.
)

pause
