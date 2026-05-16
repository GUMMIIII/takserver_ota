#Requires -Version 5.1
<#
.SYNOPSIS
    TAKOTA – civTAK OTA Bundle Generator — Windows Setup & Launcher
.DESCRIPTION
    Checks and installs Python 3 and aapt, then launches the GUI.
    Run from PowerShell as: .\install_windows.ps1
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# ── Helpers ───────────────────────────────────────────────────────────────────
function Write-Header {
    Clear-Host
    $c = "Cyan"
    Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor $c
    Write-Host "  ║       TAKOTA — civTAK OTA Bundle Generator              ║" -ForegroundColor $c
    Write-Host "  ║          Windows Setup & Launcher  v1.0                 ║" -ForegroundColor $c
    Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor $c
    Write-Host ""
}

function OK   { param($m) Write-Host "  ✔  $m" -ForegroundColor Green }
function WARN { param($m) Write-Host "  ⚠  $m" -ForegroundColor Yellow }
function ERR  { param($m) Write-Host "  ✗  $m" -ForegroundColor Red }
function INFO { param($m) Write-Host "  →  $m" -ForegroundColor Cyan }
function STEP { param($m) Write-Host "`n$m" -ForegroundColor White }

function Test-Command($cmd) {
    return [bool](Get-Command $cmd -ErrorAction SilentlyContinue)
}

# ── Find aapt ─────────────────────────────────────────────────────────────────
function Find-Aapt {
    # 1. PATH
    $found = Get-Command "aapt.exe" -ErrorAction SilentlyContinue
    if ($found) { return $found.Source }

    # 2. Environment variables
    foreach ($ev in @("ANDROID_HOME", "ANDROID_SDK_ROOT")) {
        $sdkRoot = [System.Environment]::GetEnvironmentVariable($ev, "User")
        if (-not $sdkRoot) {
            $sdkRoot = [System.Environment]::GetEnvironmentVariable($ev, "Machine")
        }
        if ($sdkRoot -and (Test-Path "$sdkRoot\build-tools")) {
            $vers = Get-ChildItem "$sdkRoot\build-tools" -ErrorAction SilentlyContinue |
                    Sort-Object Name -Descending
            foreach ($v in $vers) {
                $c = Join-Path $v.FullName "aapt.exe"
                if (Test-Path $c) { return $c }
            }
        }
    }

    # 3. Common paths
    $roots = @(
        "$env:LOCALAPPDATA\Android\Sdk\build-tools",
        "C:\Android\build-tools",
        "$env:PROGRAMFILES\Android\android-sdk\build-tools"
    )
    foreach ($bt in $roots) {
        if (Test-Path $bt) {
            $vers = Get-ChildItem $bt -ErrorAction SilentlyContinue |
                    Sort-Object Name -Descending
            foreach ($v in $vers) {
                $c = Join-Path $v.FullName "aapt.exe"
                if (Test-Path $c) { return $c }
            }
        }
    }
    return $null
}

# ── [1/3] Python ─────────────────────────────────────────────────────────────
function Check-Python {
    STEP "[1/3] Checking Python 3 …"

    $pythonCmd = $null
    foreach ($cmd in @("python", "python3", "py")) {
        try {
            $v = & $cmd --version 2>&1
            if ($v -match "Python 3") {
                $pythonCmd = $cmd
                OK "$v found  ($((Get-Command $cmd -ErrorAction SilentlyContinue).Source))"
                break
            }
        } catch {}
    }

    if (-not $pythonCmd) {
        WARN "Python 3 not found — attempting install via winget …"
        if (Test-Command "winget") {
            try {
                winget install --id Python.Python.3.12 -e `
                    --accept-source-agreements --accept-package-agreements
                # Refresh PATH for this session
                $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                            [System.Environment]::GetEnvironmentVariable("PATH", "User")
                $pythonCmd = "python"
                OK "Python installed. PATH refreshed."
            } catch {
                ERR "winget install failed: $_"
            }
        }

        if (-not $pythonCmd) {
            ERR "Python 3 could not be installed automatically."
            INFO "Download from: https://www.python.org/downloads/"
            INFO "Enable 'Add Python to PATH' during install, then re-run this script."
            Read-Host "`nPress Enter to exit"
            exit 1
        }
    }

    return $pythonCmd
}

# ── [2/3] aapt ───────────────────────────────────────────────────────────────
function Check-Aapt {
    STEP "[2/3] Checking aapt (Android Asset Packaging Tool) …"

    $aapt = Find-Aapt
    if ($aapt) {
        OK "aapt found: $aapt"
        return $aapt
    }

    WARN "aapt not found — scanning for sdkmanager …"
    $sdkmgr = Get-Command "sdkmanager.bat" -ErrorAction SilentlyContinue
    if (-not $sdkmgr) {
        $sdkmgr = Get-Command "sdkmanager" -ErrorAction SilentlyContinue
    }

    if ($sdkmgr) {
        INFO "Running: sdkmanager `"build-tools;33.0.2`" …"
        try {
            "y" | & $sdkmgr.Source "build-tools;33.0.2" 2>&1 | Out-Null
            $aapt = Find-Aapt
            if ($aapt) {
                OK "aapt installed via sdkmanager: $aapt"
                return $aapt
            }
        } catch {
            WARN "sdkmanager call failed: $_"
        }
    }

    if (Test-Command "winget") {
        INFO "Trying winget install Google.AndroidCommandLineTools …"
        try {
            winget install --id Google.AndroidCommandLineTools -e `
                --accept-source-agreements --accept-package-agreements 2>&1 | Out-Null
            $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" +
                        [System.Environment]::GetEnvironmentVariable("PATH","User")
            $aapt = Find-Aapt
            if ($aapt) {
                OK "aapt found after winget install: $aapt"
                return $aapt
            }
        } catch {
            WARN "winget failed: $_"
        }
    }

    WARN "Could not auto-install aapt."
    INFO "Download Android Command Line Tools from:"
    INFO "  https://developer.android.com/studio#command-tools"
    INFO "Extract to C:\Android\cmdline-tools\latest, then run:"
    INFO "  sdkmanager.bat `"build-tools;33.0.2`""
    INFO ""
    INFO "You can also set the aapt path manually inside the GUI."
    return $null
}

# ── [3/3] Launch ─────────────────────────────────────────────────────────────
function Launch-GUI($pythonCmd) {
    STEP "[3/3] Launching TAKOTA GUI …"
    $guiScript = Join-Path $ScriptDir "takota_gui.py"
    if (-not (Test-Path $guiScript)) {
        ERR "takota_gui.py not found in $ScriptDir"
        Read-Host "Press Enter to exit"
        exit 1
    }
    OK "Starting …"
    & $pythonCmd $guiScript
}

# ── Main ──────────────────────────────────────────────────────────────────────
Write-Header
Write-Host "  Checking dependencies …" -ForegroundColor White

$python = Check-Python
$null   = Check-Aapt          # GUI handles aapt detection internally too

Write-Host ""
Write-Host "  ✔  Setup complete — launching TAKOTA!" -ForegroundColor Green
Write-Host ""

Launch-GUI $python
