# InfZ-Modell OTA-Bundle Generator für civTAK

Dieses Repository enthält ein Python-Skript und eine Anleitung, um aus ATAK-Plugin-APKs ein OTA-Update-Bundle im InfZ-Format zu erstellen. Das Ergebnis lässt sich direkt auf einem civTAK-Server unter `/opt/tak/webcontent/update` bereitstellen.

## Inhalt

* `generate_inf_repo.py` – Python-Skript zur automatischen Erzeugung von `product.inf` und `product.infz` sowie Extraktion der Icons
* **Anleitung** in diesem README zur Einrichtung auf Windows

---

## Voraussetzungen

* Windows 10/11 mit Administrator-Rechten
* Python 3 (mit „Add Python to PATH“)
* Java JDK 11+ (Adoptium Temurin) und gesetzte Umgebungsvariable `JAVA_HOME`
* Android SDK Command-Line Tools + Build-Tools 33.0.2 (`aapt.exe`)
* Ordner für dein Bundle: `C:\ATAK\update`

---

## 1. Android Build-Tools & aapt.exe installieren

1. Lade das **Command-Line Tools (Windows ZIP)** von [Android Developer](https://developer.android.com/studio#command-tools) herunter.
2. Entpacke nach `C:\Android\cmdline-tools\latest\`.
3. Öffne eine Eingabeaufforderung und führe aus:

   ```bat
   cd C:\Android\cmdline-tools\latest\bin
   sdkmanager.bat "build-tools;33.0.2"
   ```
4. Prüfe, ob `aapt.exe` jetzt existiert:

   ```text
   C:\Android\build-tools\33.0.2\aapt.exe
   ```

---

## 2. Projektordner einrichten

```bat
mkdir C:\ATAK\update
cd C:\ATAK\update
```

Kopiere alle `.apk`-Dateien von tak.gov in diesen Ordner.

---

## 3. Skript `generate_inf_repo.py`

Lege in `C:\ATAK\update\generate_inf_repo.py` folgenden Code ab:

```python
import os, subprocess, zipfile, hashlib

# —— Konfiguration ——
AAPT = r"C:\Android\build-tools\33.0.2\aapt.exe"
UPDATE_DIR = r"C:\ATAK\update"

# SHA256-Hash-Funktion
def sha256sum(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# 1) Validierung
if not os.path.isfile(AAPT):
    raise FileNotFoundError(f"aapt.exe nicht gefunden: {AAPT}")
if not os.path.isdir(UPDATE_DIR):
    raise NotADirectoryError(f"Update-Dir nicht gefunden: {UPDATE_DIR}")

os.chdir(UPDATE_DIR)

# 2) product.inf (CSV-Header)
HEADER = (
    "#platform (Android Windows or iOS), type (app or plugin), "
    "full package name, display/label, version, revision code (integer), "
    "relative path to APK file, relative path to icon file, description, "
    "apk hash, os requirement, tak prereq (e.g. plugin-api), apk size"
)
with open("product.inf", "w", encoding="utf-8") as f:
    f.write(HEADER + "\n")

# 3) Jede APK verarbeiten
for apk in sorted([f for f in os.listdir() if f.lower().endswith(".apk")]):
    print(f"Verarbeite {apk}…")
    out = subprocess.run(
        [AAPT, "dump", "badging", apk],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    ).stdout.decode("utf-8", errors="ignore").splitlines()

    pkg = ver_name = ver_code = sdk_min = label = desc = prereq = ""
    icon_path = ""
    for L in out:
        if L.startswith("package:"):
            parts = L.split()
            for p in parts:
                if p.startswith("name="):
                    pkg = p.split("'")[1]
                if p.startswith("versionName="):
                    ver_name = p.split("'")[1]
                if p.startswith("versionCode="):
                    ver_code = p.split("'")[1]
        if L.startswith("sdkVersion:"):
            sdk_min = L.split("'")[1]
        if "application-label:" in L:
            label = L.split("'")[1]
        if "app_desc" in L:
            desc = L.split("'")[1].replace(",", ".")
        if "plugin-api" in L:
            prereq = L.split("'")[1]
        if "application-icon-160" in L:
            icon_path = L.split("application-icon-160:")[1].strip().strip("'")

    if not label:
        label = os.path.splitext(apk)[0]
    if not desc:
        desc = f"No description for {label}"

    png = os.path.splitext(apk)[0] + ".png"
    if icon_path:
        try:
            with zipfile.ZipFile(apk, 'r') as z:
                z.extract(icon_path, UPDATE_DIR)
            orig = os.path.join(UPDATE_DIR, icon_path)
            os.replace(orig, os.path.join(UPDATE_DIR, png))
            d = os.path.dirname(orig)
            if os.path.isdir(d):
                os.removedirs(d)
            print(f"  Icon: {png}")
        except KeyError:
            print("  ! Icon nicht im APK gefunden")
    else:
        print("  – kein Icon")

    h = sha256sum(apk)
    size = os.path.getsize(apk)

    line = (
        f"Android,plugin,{pkg},{label},{ver_name},{ver_code},"
        f"{apk},{png},{desc},{h},{sdk_min},{prereq},{size}"
    )
    with open("product.inf", "a", encoding="utf-8") as f:
        f.write(line + "\n")

# 4) product.infz erzeugen
with zipfile.ZipFile("product.infz", "w", zipfile.ZIP_DEFLATED) as z:
    z.write("product.inf", arcname="product.inf")
    for png in sorted([f for f in os.listdir() if f.lower().endswith(".png")]):
        z.write(png, arcname=png)

print("✅ product.inf und product.infz erstellt.")
```

---

## 4. Skript ausführen

```bat
cd C:\ATAK\update
python generate_inf_repo.py
```

## 5. Upload auf TAK-Server

1. Mit **WinSCP** zu `tak@IP` verbinden
2. Ziel: `/opt/tak/webcontent/update` → gesamten Inhalt hochladen
3. Auf dem Server:

   ```bash
   sudo chown -R tak:tak /opt/tak/webcontent/update
   sudo chmod -R 755 /opt/tak/webcontent/update
   ```

## 6. ATAK-Client konfigurieren

1. ATAK → **Settings** → **TAK Package Management**
2. Drei Punkte → **Edit** → **Update Server** aktivieren
3. URL: `https://IP:PORT/update`
4. Auf 🔄 **Update** tippen

Jetzt bezieht dein ATAK-Client das Bundle im InfZ-Modell mit Icon-Anzeige! 🎉

---

## Zusätzliche Linux-Nutzung

Das Python-Skript funktioniert auch **direkt auf Linux-Servern**, sofern folgende Voraussetzungen erfüllt sind:

1. **Python 3** installiert (z. B. `sudo apt install python3`)
2. **aapt** verfügbar – entweder aus dem Android SDK oder als Paket:

   ```bash
   # Option A: über Android SDK (im Home-Verzeichnis)
   export ANDROID_SDK_ROOT="$HOME/Android/Sdk"
   export PATH="$ANDROID_SDK_ROOT/build-tools/33.0.2:$PATH"

   # Option B: apt (Debian/Ubuntu, evtl. älter)
   sudo apt update
   sudo apt install aapt
   ```
3. Der **Update-Ordner** auf dem Server, z. B. `/opt/tak/webcontent/update`, enthält bereits alle `.apk`-Dateien.

### Ausführen auf Linux

```bash
cd /opt/tak/webcontent/update
# Optional: Umgebungsvariablen setzen
export AAPT_PATH="$HOME/Android/Sdk/build-tools/33.0.2/aapt"
# Skript starten
python3 generate_inf_repo.py
```

→ Am Ende liegen im Verzeichnis:

```
product.inf
product.infz
*.png
*.apk
```

Anschließend musst du nur noch auf dem TAK-Server sicherstellen, dass der Owner und die Rechte stimmen:

```bash
sudo chown -R tak:tak /opt/tak/webcontent/update
sudo chmod -R 755 /opt/tak/webcontent/update
```

Danach funktioniert dein OTA-Update-Server unter Linux genauso wie unter Windows.
