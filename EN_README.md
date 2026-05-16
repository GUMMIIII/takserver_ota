# TAKOTA – civTAK OTA Bundle Generator (English)

Generate `product.inf` and `product.infz` from ATAK plugin APKs and deploy them to your civTAK server so clients receive automatic over-the-air (OTA) plugin updates.

> Last tested: May 2026 · TAKServer 5.x · ATAK 5.x

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Installation & Setup](#3-installation--setup)
   - [Windows](#option-a-windows)
   - [Linux](#option-b-linux)
   - [Optional: Build a standalone .exe](#optional-build-a-standalone-exe-windows)
4. [Using the GUI](#4-using-the-gui)
5. [What gets generated](#5-what-gets-generated)
6. [Upload to your civTAK Server](#6-upload-to-your-civtak-server)
7. [Configure ATAK Clients](#7-configure-atak-clients)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Overview

TAKOTA is a graphical tool that:

- Scans a folder of ATAK plugin `.apk` files
- Extracts metadata (package name, version, icon, description) using the Android `aapt` tool
- Writes a `product.inf` manifest (CSV format) and bundles it with the extracted icons into `product.infz` (ZIP archive)
- The resulting files are placed directly on your civTAK server so ATAK clients can discover and install plugins automatically

---

## 2. Prerequisites

| Requirement | Details |
|-------------|---------|
| **Python 3.10+** | [python.org](https://www.python.org/downloads/) — enable "Add Python to PATH" on Windows |
| **aapt** | Android Asset Packaging Tool. Included in Android SDK build-tools. The setup scripts attempt to install this automatically. |
| **civTAK Server** | Running TAKServer with `/opt/tak/webcontent/update/` accessible |
| **Plugin APKs** | Download your plugins from [tak.gov](https://tak.gov) |

> **tkinter** (GUI library) ships with standard Python on Windows. On Linux it may need a separate package (`python3-tk`). The `setup.sh` script handles this automatically.

---

## 3. Installation & Setup

### Option A: Windows

1. Download or clone this repository.
2. Open **PowerShell** in the repository folder.
3. Run the setup script:

```powershell
.\install_windows.ps1
```

The script will:
- Check for **Python 3** — install via `winget` if missing
- Search for **aapt** in PATH, `ANDROID_HOME`, and common SDK locations
- Attempt to install aapt via `sdkmanager` or `winget` if not found
- Launch the TAKOTA GUI

> If the script is blocked by execution policy, run:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

**Manual aapt install (if auto-install fails):**

Download the Android Command Line Tools from [developer.android.com](https://developer.android.com/studio#command-tools), extract to `C:\Android\cmdline-tools\latest`, then run:
```cmd
cd C:\Android\cmdline-tools\latest\bin
sdkmanager.bat "build-tools;33.0.2"
```
`aapt.exe` will be at `C:\Android\build-tools\33.0.2\aapt.exe`.

---

### Option B: Linux

1. Download or clone this repository.
2. Open a terminal in the repository folder.
3. Run the setup script:

```bash
bash setup.sh
```

The script will:
- Check for **Python 3** — install if missing
- Check for **tkinter** (`python3-tk`) — install if missing
- Search for **aapt** in PATH, `ANDROID_HOME`, and common SDK locations
- Install aapt automatically via `apt-get` / `dnf` / `pacman` / `zypper`
- Launch the TAKOTA GUI

**Headless / server mode** (no display available):

```bash
TAKOTA_APK_DIR=/opt/tak/webcontent/update bash setup.sh --headless
```

**Manual aapt install (Ubuntu/Debian):**
```bash
sudo apt-get install aapt
```

**Manual aapt install (Fedora):**
```bash
sudo dnf install android-tools
```

---

### Optional: Build a standalone .exe (Windows)

If you want to distribute TAKOTA as a single executable that requires no Python installation on the target machine:

```batch
build_exe.bat
```

This installs **PyInstaller** and builds `dist\TAKOTA.exe`. Copy the `.exe` to any Windows machine — Python is not required. Note that `aapt.exe` must still be present on the target system.

---

## 4. Using the GUI

After launching (`python takota_gui.py`, `setup.sh`, or `install_windows.ps1`):

![TAKOTA GUI layout]

### Step-by-step

**1. APK Folder**
Click **Browse…** next to "APK Folder" and select the directory containing your plugin `.apk` files.
All `.apk` files in that folder will be processed.

**2. aapt Path**
The tool searches for `aapt` automatically on startup. If found, the path is filled in.
- If not found, click **Auto-Detect** to trigger another search + install attempt.
- Or click **Browse…** to select `aapt` / `aapt.exe` manually.

**3. Run**
Click **▶ Run**. The log area shows progress for each APK:
- Metadata extracted (package name, version, SDK requirements)
- Icon extracted and saved as `.png`
- SHA-256 hash calculated
- Entry written to `product.inf`

When finished, `product.inf` and `product.infz` appear in the APK folder.

**4. Open Folder**
Click **Open Folder** to open the output directory in your file manager.

---

## 5. What gets generated

After a successful run, your APK folder contains:

```
product.inf       ← CSV manifest (one line per plugin)
product.infz      ← ZIP archive: product.inf + all extracted icons (.png)
*.apk             ← your plugin APKs (unchanged)
*.png             ← extracted plugin icons
```

### product.inf format

```
#platform, type, package name, label, version, revision code,
 apk path, icon path, description, sha256, min sdk, tak prereq, size
Android,plugin,com.example.plugin,My Plugin,1.2.3,42,
 my_plugin.apk,my_plugin.png,Short description,...,21,,123456
```

The TAKServer reads `product.infz` to build the plugin catalogue that ATAK clients download.

---

## 6. Upload to your civTAK Server

Copy the entire contents of your APK folder to the TAKServer update directory.

### Using SCP (Linux/macOS/WSL)

```bash
scp /path/to/apk/folder/* tak@YOUR_SERVER_IP:/opt/tak/webcontent/update/
```

### Using WinSCP (Windows)

Connect to your server via SFTP, navigate to `/opt/tak/webcontent/update/`, and upload all files from your APK folder.

### Fix permissions on the server

After uploading, SSH into your server and run:

```bash
sudo chown -R tak:tak /opt/tak/webcontent/update
sudo chmod -R 755 /opt/tak/webcontent/update
```

### Verify

Open the following URL in a browser (replace with your server's address and port):

```
https://YOUR_SERVER_IP:YOUR_PORT/update/product.infz
```

You should receive a ZIP file download. If you get a 404, check file permissions and the TAKServer webcontent path.

---

## 7. Configure ATAK Clients

Each ATAK client needs to be pointed at your server's update URL once. After that, plugin updates happen automatically.

1. Open **ATAK** on the Android device.
2. Tap the menu icon → **Settings**.
3. Go to **TAK Package Management** (sometimes under "Tool Preferences" depending on ATAK version).
4. Tap the **three-dot menu** (⋮) → **Edit**.
5. Enable **Update Server**.
6. Enter the URL:
   ```
   https://YOUR_SERVER_IP:YOUR_PORT/update
   ```
7. Tap **Update** (🔄).

ATAK will download `product.infz`, parse the manifest, and display all available plugins. Users can then install or update plugins directly from within ATAK without side-loading.

> **Port:** TAKServer typically uses port `8443` for HTTPS. Check your TAKServer configuration if unsure.

> **Certificate:** ATAK must trust your TAKServer's certificate. Import your server's CA certificate into ATAK if you see SSL errors.

---

## 8. Troubleshooting

| Problem | Solution |
|---------|----------|
| `aapt not found` | Click **Auto-Detect** in the GUI, or install manually (see Section 3) |
| `No APK files found` | Make sure the selected folder contains `.apk` files |
| Icon missing for a plugin | Some APKs don't declare an `application-icon-160` — the plugin still works without an icon |
| `product.infz` not served by TAKServer | Check file ownership (`chown -R tak:tak`) and permissions (`chmod -R 755`) |
| ATAK shows SSL error | Import your TAKServer CA certificate into ATAK (Settings → Manage Server Connections) |
| ATAK shows no plugins | Verify the update URL ends in `/update` (not `/update/product.infz`) |
| PowerShell execution policy error | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| tkinter missing on Linux | Run `sudo apt-get install python3-tk` |

---

## Credits

Built on top of the original [takserver_ota](https://github.com/GUMMIIII/takserver_ota) workflow.
