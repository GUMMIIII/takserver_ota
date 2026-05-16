#!/usr/bin/env python3
"""
TAKOTA – civTAK OTA Bundle Generator
Cross-platform GUI (Windows + Linux) for generating product.inf + product.infz
"""
import os
import sys
import subprocess
import zipfile
import hashlib
import threading
import shutil
import platform
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox


# ──────────────────────────────────────────────────────────────────────────────
#  aapt detection & auto-install
# ──────────────────────────────────────────────────────────────────────────────

def _search_build_tools(bt_dir: str) -> str | None:
    """Return first aapt binary found in a build-tools directory, newest version first."""
    if not os.path.isdir(bt_dir):
        return None
    exe = "aapt.exe" if sys.platform == "win32" else "aapt"
    try:
        for ver in sorted(os.listdir(bt_dir), reverse=True):
            candidate = os.path.join(bt_dir, ver, exe)
            if os.path.isfile(candidate):
                return candidate
    except PermissionError:
        pass
    return None


def find_aapt() -> str | None:
    """Search for the aapt binary in PATH, env vars, and common SDK locations."""
    exe = "aapt.exe" if sys.platform == "win32" else "aapt"

    found = shutil.which(exe) or shutil.which("aapt")
    if found:
        return found

    for env_var in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        sdk_root = os.environ.get(env_var, "")
        if sdk_root:
            result = _search_build_tools(os.path.join(sdk_root, "build-tools"))
            if result:
                return result

    if sys.platform == "win32":
        sdk_candidates = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Android", "Sdk", "build-tools"),
            r"C:\Android\build-tools",
            os.path.join(os.environ.get("PROGRAMFILES", ""), "Android", "android-sdk", "build-tools"),
        ]
    else:
        home = os.path.expanduser("~")
        sdk_candidates = [
            os.path.join(home, "Android", "Sdk", "build-tools"),
            "/opt/android-sdk/build-tools",
            "/usr/local/android-sdk/build-tools",
        ]

    for bt in sdk_candidates:
        result = _search_build_tools(bt)
        if result:
            return result

    return None


def _run_install_cmd(args: list[str], log) -> bool:
    try:
        r = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300)
        if r.returncode == 0:
            return True
        log(f"   stderr: {r.stderr.strip()[:200]}")
    except FileNotFoundError:
        log(f"   Command not found: {args[0]}")
    except subprocess.TimeoutExpired:
        log("   Timed out.")
    except Exception as e:
        log(f"   Error: {e}")
    return False


def install_aapt(log) -> str | None:
    """Platform-aware aapt installation attempt. Returns path on success or None."""
    log("aapt not found — attempting auto-install...")

    if sys.platform == "win32":
        # Try sdkmanager if Android SDK already present
        sdkmgr = shutil.which("sdkmanager") or shutil.which("sdkmanager.bat")
        if sdkmgr:
            log(f"  Running sdkmanager build-tools;33.0.2 …")
            try:
                subprocess.run(
                    [sdkmgr, "build-tools;33.0.2"],
                    input="y\n", text=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=300,
                )
                found = find_aapt()
                if found:
                    return found
            except Exception as e:
                log(f"  sdkmanager error: {e}")

        # Try winget
        if shutil.which("winget"):
            log("  Trying winget install Google.AndroidCommandLineTools …")
            _run_install_cmd(
                ["winget", "install", "--id", "Google.AndroidCommandLineTools",
                 "-e", "--accept-source-agreements", "--accept-package-agreements"],
                log,
            )
            found = find_aapt()
            if found:
                return found

        log("❌ Could not auto-install aapt on Windows.")
        log("   Download Android Command Line Tools from developer.android.com")
        log("   then run:  sdkmanager \"build-tools;33.0.2\"")
        return None

    # Linux / macOS
    if shutil.which("apt-get"):
        log("  Running: sudo apt-get install -y aapt …")
        if _run_install_cmd(["sudo", "apt-get", "install", "-y", "aapt"], log):
            found = shutil.which("aapt")
            if found:
                return found

    if shutil.which("dnf"):
        log("  Running: sudo dnf install -y android-tools …")
        if _run_install_cmd(["sudo", "dnf", "install", "-y", "android-tools"], log):
            found = shutil.which("aapt")
            if found:
                return found

    if shutil.which("pacman"):
        log("  Running: sudo pacman -S --noconfirm android-tools …")
        if _run_install_cmd(["sudo", "pacman", "-S", "--noconfirm", "android-tools"], log):
            found = shutil.which("aapt")
            if found:
                return found

    log("❌ Could not auto-install aapt.")
    log("   Ubuntu/Debian: sudo apt-get install aapt")
    log("   Fedora:        sudo dnf install android-tools")
    log("   Arch:          sudo pacman -S android-tools")
    return None


# ──────────────────────────────────────────────────────────────────────────────
#  Core bundle generation (adapted from generate_inf_repo.py)
# ──────────────────────────────────────────────────────────────────────────────

def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_bundle(aapt_path: str, update_dir: str, log, progress) -> bool:
    """
    Build product.inf + product.infz from APK files in update_dir.
    Calls log(str) for messages and progress(0-100) for bar updates.
    Runs in a background thread — must not touch tkinter widgets directly.
    """
    try:
        if not os.path.isfile(aapt_path):
            log(f"❌ aapt not found: {aapt_path}")
            return False
        if not os.path.isdir(update_dir):
            log(f"❌ Folder not found: {update_dir}")
            return False

        os.chdir(update_dir)
        apks = sorted(f for f in os.listdir() if f.lower().endswith(".apk"))
        if not apks:
            log("❌ No APK files found in the selected folder.")
            return False

        log(f"Found {len(apks)} APK(s) — processing…")
        HEADER = (
            "#platform (Android Windows or iOS), type (app or plugin), "
            "full package name, display/label, version, revision code (integer), "
            "relative path to APK file, relative path to icon file, description, "
            "apk hash, os requirement, tak prereq (e.g. plugin-api), apk size"
        )
        with open("product.inf", "w", encoding="utf-8") as f:
            f.write(HEADER + "\n")

        total = len(apks)
        for idx, apk in enumerate(apks):
            log(f"\nProcessing [{idx + 1}/{total}]  {apk}")
            progress(int(idx / total * 90))

            lines = subprocess.run(
                [aapt_path, "dump", "badging", apk],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            ).stdout.decode("utf-8", errors="ignore").splitlines()

            pkg = ver_name = ver_code = sdk_min = label = desc = prereq = icon_path = ""

            for L in lines:
                if L.startswith("package:"):
                    for tok in L.split():
                        if tok.startswith("name="):        pkg      = tok.split("'")[1]
                        if tok.startswith("versionCode="): ver_code = tok.split("'")[1]
                        if tok.startswith("versionName="): ver_name = tok.split("'")[1]
                if L.startswith("sdkVersion:"):            sdk_min  = L.split("'")[1]
                if "application-label:" in L:              label    = L.split("'")[1]
                if "app_desc" in L and "'" in L:           desc     = L.split("'")[1].replace(",", ".")
                if "plugin-api" in L and "'" in L:         prereq   = L.split("'")[1]
                if "application-icon-160" in L:
                    icon_path = L.split("application-icon-160:")[1].strip().strip("'")

            if not label: label = os.path.splitext(apk)[0]
            if not desc:  desc  = f"No description for {label}"

            png = os.path.splitext(apk)[0] + ".png"
            if icon_path:
                try:
                    with zipfile.ZipFile(apk, "r") as z:
                        z.extract(icon_path, update_dir)
                    orig = os.path.join(update_dir, icon_path)
                    os.replace(orig, os.path.join(update_dir, png))
                    d = os.path.dirname(orig)
                    if os.path.isdir(d):
                        try:
                            os.removedirs(d)
                        except OSError:
                            pass
                    log(f"  Icon saved: {png}")
                except KeyError:
                    log("  ! Icon not found inside APK")
            else:
                log("  - No icon path in APK manifest")

            sha  = _sha256(apk)
            size = os.path.getsize(apk)
            row  = (
                f"Android,plugin,{pkg},{label},{ver_name},{ver_code},"
                f"{apk},{png},{desc},{sha},{sdk_min},{prereq},{size}"
            )
            with open("product.inf", "a", encoding="utf-8") as f:
                f.write(row + "\n")

        progress(95)
        log("\nBuilding product.infz archive…")
        with zipfile.ZipFile("product.infz", "w", zipfile.ZIP_DEFLATED) as z:
            z.write("product.inf", arcname="product.inf")
            for png in sorted(f for f in os.listdir() if f.lower().endswith(".png")):
                z.write(png, arcname=png)

        progress(100)
        log(f"\n✅ Done!  product.inf + product.infz created in:\n   {update_dir}")
        return True

    except Exception as exc:
        log(f"❌ Unexpected error: {exc}")
        return False


# ──────────────────────────────────────────────────────────────────────────────
#  GUI
# ──────────────────────────────────────────────────────────────────────────────

DARK_BG    = "#1a1a2e"
HEADER_BG  = "#16213e"
ACCENT     = "#0f3460"
BTN_BG     = "#0f3460"
BTN_FG     = "#e0e0e0"
LOG_BG     = "#0d0d1a"
LOG_FG     = "#d4d4d4"
GREEN      = "#4caf50"
RED        = "#ef5350"
CYAN       = "#4fc3f7"
YELLOW     = "#ffb300"


class TakotaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TAKOTA – civTAK OTA Bundle Generator")
        self.configure(bg=DARK_BG)
        self.minsize(760, 560)
        self.resizable(True, True)

        self.aapt_var   = tk.StringVar()
        self.folder_var = tk.StringVar()
        self._running   = False

        self._setup_styles()
        self._build_ui()
        self.after(200, self._startup_detect)

    # ── Styles ────────────────────────────────────────────────────────────────

    def _setup_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TFrame",       background=DARK_BG)
        s.configure("TLabel",       background=DARK_BG,   foreground="#c0c0c0")
        s.configure("TLabelframe",  background=DARK_BG,   foreground="#7090b0")
        s.configure("TLabelframe.Label", background=DARK_BG, foreground="#7090b0")
        s.configure("TEntry",       fieldbackground="#0d0d1a", foreground="#d4d4d4",
                    insertcolor="#ffffff")
        s.configure("TButton",      background=BTN_BG, foreground=BTN_FG, padding=5)
        s.map("TButton",
              background=[("active", "#1a4a80"), ("disabled", "#2a2a3a")],
              foreground=[("disabled", "#666")])
        s.configure("TProgressbar", troughcolor="#0d0d1a", background=CYAN,
                    lightcolor=CYAN, darkcolor=CYAN)

    # ── UI layout ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=HEADER_BG, pady=14)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="TAKOTA", bg=HEADER_BG, fg=CYAN,
                 font=("Helvetica", 20, "bold")).pack()
        tk.Label(hdr, text="civTAK OTA Bundle Generator  ·  product.inf + product.infz",
                 bg=HEADER_BG, fg="#607080",
                 font=("Helvetica", 9)).pack()

        # Config frame
        cfg = ttk.LabelFrame(self, text=" Configuration ", padding=(12, 8))
        cfg.pack(fill=tk.X, padx=16, pady=(14, 6))
        cfg.columnconfigure(1, weight=1)

        ttk.Label(cfg, text="APK Folder:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Entry(cfg, textvariable=self.folder_var).grid(
            row=0, column=1, sticky=tk.EW)
        ttk.Button(cfg, text="Browse…", command=self._browse_folder).grid(
            row=0, column=2, padx=(6, 0))

        ttk.Label(cfg, text="aapt Path:").grid(
            row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(8, 0))
        ttk.Entry(cfg, textvariable=self.aapt_var).grid(
            row=1, column=1, sticky=tk.EW, pady=(8, 0))
        aapt_btns = ttk.Frame(cfg)
        aapt_btns.grid(row=1, column=2, sticky=tk.W, pady=(8, 0), padx=(6, 0))
        ttk.Button(aapt_btns, text="Browse…", command=self._browse_aapt).pack(side=tk.LEFT)
        ttk.Button(aapt_btns, text="Auto-Detect", command=self._trigger_detect).pack(
            side=tk.LEFT, padx=(4, 0))

        # Progress
        prog_frame = ttk.Frame(self)
        prog_frame.pack(fill=tk.X, padx=16, pady=(4, 0))
        self.progress = ttk.Progressbar(prog_frame, mode="determinate", maximum=100)
        self.progress.pack(fill=tk.X)
        self.pct_label = ttk.Label(prog_frame, text="Idle")
        self.pct_label.pack(anchor=tk.W)

        # Log
        log_frame = ttk.LabelFrame(self, text=" Log ", padding=6)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=6)
        self.log = scrolledtext.ScrolledText(
            log_frame, height=14, font=("Consolas", 9),
            bg=LOG_BG, fg=LOG_FG, wrap=tk.WORD, state=tk.DISABLED,
            insertbackground="#ffffff",
        )
        self.log.pack(fill=tk.BOTH, expand=True)
        self.log.tag_config("ok",     foreground=GREEN)
        self.log.tag_config("err",    foreground=RED)
        self.log.tag_config("info",   foreground=CYAN)
        self.log.tag_config("warn",   foreground=YELLOW)
        self.log.tag_config("indent", foreground="#888888")

        # Button bar
        bar = ttk.Frame(self)
        bar.pack(fill=tk.X, padx=16, pady=(0, 10))
        self.run_btn = ttk.Button(bar, text="▶  Run", command=self._run, width=12)
        self.run_btn.pack(side=tk.LEFT)
        ttk.Button(bar, text="Clear Log", command=self._clear_log).pack(
            side=tk.LEFT, padx=(8, 0))
        ttk.Button(bar, text="Open Folder", command=self._open_folder).pack(side=tk.RIGHT)

        # Status bar
        self.status_var = tk.StringVar(
            value=f"Platform: {platform.system()} {platform.machine()}  |  Python {sys.version.split()[0]}")
        tk.Label(self, textvariable=self.status_var, anchor=tk.W,
                 bg="#0d0d1a", fg="#506070", relief=tk.FLAT,
                 font=("Consolas", 8)).pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 0))

    # ── Thread-safe helpers ────────────────────────────────────────────────────

    def _append_log(self, msg: str):
        """Append a line to the log widget with colour tagging (main thread only)."""
        self.log.config(state=tk.NORMAL)
        tag = None
        m = msg.lower()
        if "✅" in msg or "done" in m or "success" in m:
            tag = "ok"
        elif "❌" in msg or "error" in m or "not found" in m or "failed" in m:
            tag = "err"
        elif msg.startswith("  ") or msg.startswith("   "):
            tag = "indent"
        elif "warn" in m or "⚠" in msg or "could not" in m:
            tag = "warn"
        elif msg.startswith("Found") or msg.startswith("Searching") or \
                msg.startswith("Attempting") or msg.startswith("Trying") or \
                "auto-detect" in m or "auto-install" in m:
            tag = "info"

        self.log.insert(tk.END, msg + "\n", tag or "")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def _log(self, msg: str):
        """Thread-safe log call."""
        self.after(0, self._append_log, msg)

    def _set_progress(self, val: float):
        def _do():
            self.progress["value"] = val
            self.pct_label.config(text=f"{int(val)}%" if val < 100 else "Complete")
        self.after(0, _do)

    def _clear_log(self):
        self.log.config(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.config(state=tk.DISABLED)
        self.progress["value"] = 0
        self.pct_label.config(text="Idle")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _browse_folder(self):
        d = filedialog.askdirectory(title="Select folder containing APK files")
        if d:
            self.folder_var.set(d)

    def _browse_aapt(self):
        if sys.platform == "win32":
            ft = [("aapt executable", "aapt.exe"), ("All files", "*.*")]
        else:
            ft = [("aapt executable", "aapt"), ("All files", "*.*")]
        f = filedialog.askopenfilename(title="Select aapt binary", filetypes=ft)
        if f:
            self.aapt_var.set(f)

    def _startup_detect(self):
        self._log("Searching for aapt…")
        threading.Thread(target=self._detect_worker, daemon=True).start()

    def _trigger_detect(self):
        self._log("Re-scanning for aapt…")
        threading.Thread(target=self._detect_worker, daemon=True).start()

    def _detect_worker(self):
        found = find_aapt()
        if found:
            self.after(0, self.aapt_var.set, found)
            self._log(f"✅ aapt detected: {found}")
        else:
            found = install_aapt(self._log)
            if found:
                self.after(0, self.aapt_var.set, found)

    def _run(self):
        if self._running:
            return
        aapt   = self.aapt_var.get().strip()
        folder = self.folder_var.get().strip()
        if not aapt:
            messagebox.showerror("Missing", "No aapt path set.\nUse Auto-Detect or Browse to locate aapt.")
            return
        if not folder:
            messagebox.showerror("Missing", "No APK folder selected.\nClick Browse… to choose a folder.")
            return

        self._running = True
        self.run_btn.config(state=tk.DISABLED, text="Running…")
        self._clear_log()
        self._log(f"APK folder : {folder}")
        self._log(f"aapt       : {aapt}")
        self._log("─" * 60)

        def worker():
            ok = generate_bundle(aapt, folder, self._log, self._set_progress)
            def finish():
                self._running = False
                self.run_btn.config(state=tk.NORMAL, text="▶  Run")
                if ok:
                    self.status_var.set("✅ Bundle generated — ready to deploy!")
                else:
                    self.status_var.set("❌ Generation failed — see log for details")
            self.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()

    def _open_folder(self):
        folder = self.folder_var.get().strip()
        if not folder or not os.path.isdir(folder):
            return
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])


# ──────────────────────────────────────────────────────────────────────────────
#  Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main():
    app = TakotaApp()
    app.mainloop()


if __name__ == "__main__":
    main()
