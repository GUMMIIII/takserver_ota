#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  TAKOTA – civTAK OTA Bundle Generator
#  Linux Setup & Launcher
#  Usage: bash setup.sh [--headless]
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HEADLESS=false
[[ "${1:-}" == "--headless" ]] && HEADLESS=true

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "${GREEN}  ✔  $*${NC}"; }
warn() { echo -e "${YELLOW}  ⚠  $*${NC}"; }
err()  { echo -e "${RED}  ✗  $*${NC}"; }
info() { echo -e "${CYAN}  →  $*${NC}"; }
step() { echo -e "\n${BOLD}$*${NC}"; }

# ── Header ───────────────────────────────────────────────────────────────────
print_header() {
    clear
    echo -e "${BLUE}${BOLD}"
    echo "  ╔══════════════════════════════════════════════════════════╗"
    echo "  ║       TAKOTA — civTAK OTA Bundle Generator              ║"
    echo "  ║            Linux Setup & Launcher  v1.0                 ║"
    echo "  ╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# ── Package manager detection ─────────────────────────────────────────────────
detect_pm() {
    for pm in apt-get dnf pacman zypper; do
        command -v "$pm" &>/dev/null && { echo "$pm"; return 0; }
    done
    echo "none"
}

install_pkg() {
    local pkg="$1"
    local pm
    pm=$(detect_pm)
    info "Installing $pkg via $pm …"
    case "$pm" in
        apt-get) sudo apt-get install -y "$pkg" >/dev/null 2>&1 ;;
        dnf)     sudo dnf install -y "$pkg" >/dev/null 2>&1 ;;
        pacman)  sudo pacman -S --noconfirm "$pkg" >/dev/null 2>&1 ;;
        zypper)  sudo zypper install -y "$pkg" >/dev/null 2>&1 ;;
        *)       err "No supported package manager found. Install $pkg manually."; return 1 ;;
    esac
}

# ── [1/4] Python 3 ───────────────────────────────────────────────────────────
check_python() {
    step "[1/4] Checking Python 3 …"
    if command -v python3 &>/dev/null; then
        ok "$(python3 --version)"
    else
        warn "Python 3 not found — installing …"
        install_pkg python3
        ok "$(python3 --version) installed"
    fi
}

# ── [2/4] tkinter ────────────────────────────────────────────────────────────
check_tkinter() {
    step "[2/4] Checking tkinter (GUI library) …"
    if python3 -c "import tkinter" 2>/dev/null; then
        ok "tkinter available"
        return
    fi
    warn "tkinter missing — installing …"
    local pm
    pm=$(detect_pm)
    case "$pm" in
        apt-get) install_pkg python3-tk ;;
        dnf)     install_pkg python3-tkinter ;;
        pacman)  install_pkg tk ;;
        zypper)  install_pkg python3-tk ;;
        *)       err "Cannot auto-install tkinter. Run: sudo apt-get install python3-tk"; exit 1 ;;
    esac
    if python3 -c "import tkinter" 2>/dev/null; then
        ok "tkinter installed"
    else
        err "tkinter still not importable. Please install manually."; exit 1
    fi
}

# ── [3/4] aapt ───────────────────────────────────────────────────────────────
find_aapt_bin() {
    # PATH
    command -v aapt &>/dev/null && { command -v aapt; return 0; }

    # Android SDK env vars
    for env_val in "${ANDROID_HOME:-}" "${ANDROID_SDK_ROOT:-}"; do
        if [[ -d "$env_val/build-tools" ]]; then
            local latest
            latest=$(ls -1 "$env_val/build-tools" 2>/dev/null | sort -rV | head -1)
            [[ -f "$env_val/build-tools/$latest/aapt" ]] && \
                { echo "$env_val/build-tools/$latest/aapt"; return 0; }
        fi
    done

    # Common SDK locations
    local sdk_roots=("$HOME/Android/Sdk" "/opt/android-sdk" "/usr/local/android-sdk")
    for sdk in "${sdk_roots[@]}"; do
        if [[ -d "$sdk/build-tools" ]]; then
            local latest
            latest=$(ls -1 "$sdk/build-tools" 2>/dev/null | sort -rV | head -1)
            [[ -f "$sdk/build-tools/$latest/aapt" ]] && \
                { echo "$sdk/build-tools/$latest/aapt"; return 0; }
        fi
    done
    return 1
}

check_aapt() {
    step "[3/4] Checking aapt (Android Asset Packaging Tool) …"
    AAPT_PATH=""
    if AAPT_PATH=$(find_aapt_bin); then
        ok "aapt found: $AAPT_PATH"
        export TAKOTA_AAPT="$AAPT_PATH"
        return
    fi

    warn "aapt not found — attempting auto-install …"
    local pm
    pm=$(detect_pm)

    case "$pm" in
        apt-get)
            install_pkg aapt
            if AAPT_PATH=$(command -v aapt 2>/dev/null); then
                ok "aapt installed: $AAPT_PATH"
                export TAKOTA_AAPT="$AAPT_PATH"
                return
            fi
            ;;
        dnf)
            install_pkg android-tools
            if AAPT_PATH=$(command -v aapt 2>/dev/null); then
                ok "aapt installed: $AAPT_PATH"
                export TAKOTA_AAPT="$AAPT_PATH"
                return
            fi
            ;;
        pacman)
            install_pkg android-tools
            if AAPT_PATH=$(command -v aapt 2>/dev/null); then
                ok "aapt installed: $AAPT_PATH"
                export TAKOTA_AAPT="$AAPT_PATH"
                return
            fi
            ;;
    esac

    warn "Could not auto-install aapt. You can set the path manually in the GUI."
    warn "  Ubuntu/Debian: sudo apt-get install aapt"
    warn "  Fedora:        sudo dnf install android-tools"
    warn "  Or install Android SDK build-tools and set ANDROID_HOME"
}

# ── [4/4] Launch ─────────────────────────────────────────────────────────────
launch() {
    step "[4/4] Launching TAKOTA …"

    if $HEADLESS; then
        # Headless / CLI mode — run the core generation script directly
        info "Headless mode: running CLI (no GUI)"
        if [[ -z "${TAKOTA_APK_DIR:-}" ]]; then
            echo ""
            echo -e "${YELLOW}Set TAKOTA_APK_DIR to your APK folder, e.g.:${NC}"
            echo "  TAKOTA_APK_DIR=/opt/tak/webcontent/update bash setup.sh --headless"
            exit 1
        fi
        python3 "$SCRIPT_DIR/takota_gui.py" --headless \
            --aapt "${TAKOTA_AAPT:-aapt}" \
            --dir  "$TAKOTA_APK_DIR"
        return
    fi

    # Need DISPLAY for GUI
    if [[ -z "${DISPLAY:-}" ]] && [[ -z "${WAYLAND_DISPLAY:-}" ]]; then
        err "No display detected (DISPLAY / WAYLAND_DISPLAY not set)."
        warn "For headless servers, run:  bash setup.sh --headless"
        exit 1
    fi

    ok "Starting GUI …"
    python3 "$SCRIPT_DIR/takota_gui.py"
}

# ── Interactive folder selector (whiptail/dialog) ────────────────────────────
select_folder_interactive() {
    if command -v whiptail &>/dev/null; then
        whiptail --title "TAKOTA" --inputbox \
            "Enter path to your APK folder:" 10 60 \
            "${HOME}/ATAK/update" 3>&1 1>&2 2>&3 || true
    elif command -v dialog &>/dev/null; then
        dialog --title "TAKOTA" --inputbox \
            "Enter path to your APK folder:" 10 60 \
            "${HOME}/ATAK/update" 3>&1 1>&2 2>&3 || true
    fi
}

# ── Main ─────────────────────────────────────────────────────────────────────
main() {
    print_header
    echo -e "${BOLD}  Checking dependencies…${NC}\n"

    check_python
    check_tkinter
    check_aapt

    echo ""
    echo -e "${GREEN}${BOLD}  ✔  All checks complete — launching TAKOTA!${NC}"
    echo ""

    launch
}

main "$@"
