# InfZ-Model OTA Bundle Generator for civTAK

This repository provides a Python script and step-by-step instructions to generate an **InfZ-format** OTA update bundle from ATAK plugin APKs. The resulting files can be directly deployed to a civTAK server under `/opt/tak/webcontent/update`.

## Contents

* `generate_inf_repo.py` – Python script to create `product.inf` (CSV) and `product.infz` (ZIP of CSV + icons), and extract icons from APKs
* **README.md** – this guide in English

---

## Prerequisites

* A **Windows** or **Linux** (x86\_64) machine with Administrator/Root access
* **Python 3** installed (`python3` on Linux, Windows installer with "Add Python to PATH")
* **Java JDK 11+** (Adoptium Temurin) with `JAVA_HOME` environment variable set
* **Android SDK Command-Line Tools** + **Build-Tools 33.0.2** (`aapt` utility)
* A working civTAK server serving `/opt/tak/webcontent/update`

---

## 1. Install Android Build Tools (`aapt`)

### Option A: Windows

1. Download **Command-line Tools (Windows ZIP)** from:
   [https://developer.android.com/studio#command-tools](https://developer.android.com/studio#command-tools)
2. Unzip to `C:\Android\cmdline-tools\latest\`
3. Open **cmd.exe** and run:

   ```bat
   cd C:\Android\cmdline-tools\latest\bin
   sdkmanager.bat "build-tools;33.0.2"
   ```
4. Verify `aapt.exe` is present:

   ```text
   C:\Android\build-tools\33.0.2\aapt.exe
   ```

### Option B: Linux (Debian/Ubuntu)

```bash
sudo apt update
dpkg --add-architecture i386            # if needed for 32-bit libs
sudo apt install aapt                   # older aapt versions
# Or use Android SDK:
export ANDROID_SDK_ROOT="$HOME/Android/Sdk"
export PATH="$ANDROID_SDK_ROOT/build-tools/33.0.2:$PATH"
```

---

## 2. Prepare Project Folder

On your local machine (or Linux server):

```bash
mkdir -p C:/ATAK/update       # Windows
# or on Linux:
# mkdir -p ~/ATAK/update
cd C:/ATAK/update
```

Copy **all** plugin `.apk` files from tak.gov into this directory.

---

## 3. Python Script: `generate_inf_repo.py`

Create file `generate_inf_repo.py` in the update folder with this content:

```python
import os, subprocess, zipfile, hashlib

# —— Configuration ——
AAPT = r"C:/Android/build-tools/33.0.2/aapt.exe"  # Adjust path if needed
UPDATE_DIR = os.path.dirname(os.path.abspath(__file__))

# Compute SHA256 digest
def sha256sum(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# Verify prerequisites
if not os.path.isfile(AAPT):
    raise FileNotFoundError(f"aapt tool not found at: {AAPT}")
if not os.path.isdir(UPDATE_DIR):
    raise NotADirectoryError(f"Update directory not found: {UPDATE_DIR}")

os.chdir(UPDATE_DIR)

# Write CSV header
HEADER = (
    "#platform (Android Windows or iOS), type (app or plugin), "
    "full package name, display/label, version, revision code (integer), "
    "relative path to APK file, relative path to icon file, description, "
    "apk hash, os requirement, tak prereq (e.g. plugin-api), apk size"
)
with open("product.inf", "w", encoding="utf-8") as outfile:
    outfile.write(HEADER + "\n")

# Process each APK
for apk in sorted(f for f in os.listdir() if f.lower().endswith(".apk")):
    print(f"Processing {apk}...")
    # Extract metadata
    lines = subprocess.run(
        [AAPT, "dump", "badging", apk],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    ).stdout.decode("utf-8", errors="ignore").splitlines()

    pkg = ver_name = ver_code = sdk_min = label = desc = prereq = ""
    icon_path = ""
    for line in lines:
        if line.startswith("package:"):
            parts = line.split()
            for p in parts:
                if p.startswith("name="):
                    pkg = p.split("'")[1]
                if p.startswith("versionCode="):
                    ver_code = p.split("'")[1]
                if p.startswith("versionName="):
                    ver_name = p.split("'")[1]
        if line.startswith("sdkVersion:"):
            sdk_min = line.split("'")[1]
        if "application-label:" in line:
            label = line.split("'")[1]
        if "app_desc" in line:
            desc = line.split("'")[1].replace(",", ".")
        if "plugin-api" in line:
            prereq = line.split("'")[1]
        if "application-icon-160" in line:
            icon_path = line.split("application-icon-160:")[1].strip().strip("'")

    if not label:
        label = os.path.splitext(apk)[0]
    if not desc:
        desc = f"No description for {label}"

    # Extract icon if available
    png = os.path.splitext(apk)[0] + ".png"
    if icon_path:
        try:
            with zipfile.ZipFile(apk, 'r') as z:
                z.extract(icon_path, UPDATE_DIR)
            orig = os.path.join(UPDATE_DIR, icon_path)
            os.replace(orig, os.path.join(UPDATE_DIR, png))
            # Cleanup empty dirs
            d = os.path.dirname(orig)
            if os.path.isdir(d):
                os.removedirs(d)
            print(f"  Icon: {png}")
        except KeyError:
            print("  ! Icon not found in APK")
    else:
        print("  - No icon")

    # Compute hash and size
    sha = sha256sum(apk)
    size = os.path.getsize(apk)

    # Append CSV line
    line = (
        f"Android,plugin,{pkg},{label},{ver_name},{ver_code},"
        f"{apk},{png},{desc},{sha},{sdk_min},{prereq},{size}"
    )
    with open("product.inf", "a", encoding="utf-8") as f:
        f.write(line + "\n")

# Bundle CSV + PNGs into product.infz
with zipfile.ZipFile("product.infz", "w", zipfile.ZIP_DEFLATED) as z:
    z.write("product.inf", arcname="product.inf")
    for png in sorted(f for f in os.listdir() if f.lower().endswith(".png")):
        z.write(png, arcname=png)

print("✅ Created product.inf and product.infz successfully.")
```

---

## 4. Run the Script

```bash
cd C:/ATAK/update    # Windows path
the python command may be `python` or `python3`
python generate_inf_repo.py
```

On Linux:

```bash
cd /opt/tak/webcontent/update
python3 generate_inf_repo.py
```

After execution, the folder will contain:

```
product.inf       # CSV metadata
product.infz      # ZIP archive of CSV + icons
*.apk             # plugin APKs
*.png             # extracted icons
```

---

## 5. Upload to civTAK Server

Use **WinSCP** (or `scp` on Linux) to upload the entire contents of the update folder to the server:

```bash
scp C:/ATAK/update/* tak@IP:/opt/tak/webcontent/update/
# then on the server:
sudo chown -R tak:tak /opt/tak/webcontent/update
sudo chmod -R 755 /opt/tak/webcontent/update
```

---

## 6. Configure ATAK Client

1. Open ATAK → **Settings** → **TAK Package Management**
2. Tap the three dots → **Edit** → Enable **Update Server**
3. Enter URL:

   ```
   https://IP:PORT/update
   ```
4. Tap 🔄 **Update**

Your ATAK client will now fetch the `product.infz` (metadata + icons) and list plugins ready for install or update. 🎉

---

## Additional Linux Usage

The same script runs on any x86\_64 Linux with Python 3 and `aapt` available:

```bash
# install prerequisites on Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip aapt

cd /opt/tak/webcontent/update
python3 generate_inf_repo.py
```

Ensure correct file ownership and permissions:

```bash
sudo chown -R tak:tak /opt/tak/webcontent/update
sudo chmod -R 755 /opt/tak/webcontent/update
```

Your civTAK OTA server works the same way under Linux or Windows.
