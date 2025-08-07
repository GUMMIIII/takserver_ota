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
