# TAKOTA – civTAK OTA Bundle Generator (Deutsch)

Erstellt `product.inf` und `product.infz` aus ATAK-Plugin-APKs und stellt diese auf deinem civTAK-Server bereit, damit Clients automatisch Over-the-Air (OTA) Plugin-Updates erhalten.

> Zuletzt getestet: Mai 2026 · TAKServer 5.x · ATAK 5.x

---

## Inhaltsverzeichnis

1. [Übersicht](#1-übersicht)
2. [Voraussetzungen](#2-voraussetzungen)
3. [Installation & Einrichtung](#3-installation--einrichtung)
   - [Windows](#option-a-windows)
   - [Linux](#option-b-linux)
   - [Optional: Standalone .exe bauen](#optional-standalone-exe-bauen-windows)
4. [Die GUI benutzen](#4-die-gui-benutzen)
5. [Was wird erzeugt](#5-was-wird-erzeugt)
6. [Upload auf den civTAK-Server](#6-upload-auf-den-civtak-server)
7. [ATAK-Clients konfigurieren](#7-atak-clients-konfigurieren)
8. [Fehlerbehebung](#8-fehlerbehebung)

---

## 1. Übersicht

TAKOTA ist ein grafisches Werkzeug, das:

- Einen Ordner mit ATAK-Plugin-`.apk`-Dateien durchsucht
- Metadaten (Paketname, Version, Icon, Beschreibung) mit dem Android-Tool `aapt` extrahiert
- Ein `product.inf`-Manifest (CSV-Format) erstellt und dieses zusammen mit den extrahierten Icons in `product.infz` (ZIP-Archiv) bündelt
- Die erzeugten Dateien können direkt auf den civTAK-Server hochgeladen werden, damit ATAK-Clients Plugins automatisch entdecken und installieren können

---

## 2. Voraussetzungen

| Voraussetzung | Details |
|---------------|---------|
| **Python 3.10+** | [python.org](https://www.python.org/downloads/) — unter Windows „Add Python to PATH" aktivieren |
| **aapt** | Android Asset Packaging Tool. Im Android-SDK enthalten. Die Setup-Skripte versuchen, es automatisch zu installieren. |
| **civTAK-Server** | Laufender TAKServer mit zugänglichem Pfad `/opt/tak/webcontent/update/` |
| **Plugin-APKs** | Plugins von [tak.gov](https://tak.gov) herunterladen |

> **tkinter** (GUI-Bibliothek) ist unter Windows im Standard-Python enthalten. Unter Linux wird ggf. das Paket `python3-tk` benötigt — das `setup.sh`-Skript kümmert sich darum automatisch.

---

## 3. Installation & Einrichtung

### Option A: Windows

1. Dieses Repository herunterladen oder klonen.
2. **PowerShell** im Repository-Ordner öffnen.
3. Das Setup-Skript ausführen:

```powershell
.\install_windows.ps1
```

Das Skript erledigt automatisch:
- Prüfung auf **Python 3** — Installation via `winget` falls nicht vorhanden
- Suche nach **aapt** in PATH, `ANDROID_HOME` und gängigen SDK-Pfaden
- Installation von aapt via `sdkmanager` oder `winget` falls nicht gefunden
- Start der TAKOTA-GUI

> Wenn das Skript durch die Execution Policy blockiert wird:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

**Manuelle aapt-Installation (falls Auto-Install fehlschlägt):**

Android Command Line Tools von [developer.android.com](https://developer.android.com/studio#command-tools) herunterladen, nach `C:\Android\cmdline-tools\latest` entpacken, dann ausführen:
```cmd
cd C:\Android\cmdline-tools\latest\bin
sdkmanager.bat "build-tools;33.0.2"
```
`aapt.exe` befindet sich danach unter `C:\Android\build-tools\33.0.2\aapt.exe`.

---

### Option B: Linux

1. Dieses Repository herunterladen oder klonen.
2. Ein Terminal im Repository-Ordner öffnen.
3. Das Setup-Skript ausführen:

```bash
bash setup.sh
```

Das Skript erledigt automatisch:
- Prüfung auf **Python 3** — Installation falls nicht vorhanden
- Prüfung auf **tkinter** (`python3-tk`) — Installation falls nicht vorhanden
- Suche nach **aapt** in PATH, `ANDROID_HOME` und gängigen SDK-Pfaden
- Automatische Installation via `apt-get` / `dnf` / `pacman` / `zypper`
- Start der TAKOTA-GUI

**Headless-/Server-Modus** (kein Display vorhanden):

```bash
TAKOTA_APK_DIR=/opt/tak/webcontent/update bash setup.sh --headless
```

**Manuelle aapt-Installation (Ubuntu/Debian):**
```bash
sudo apt-get install aapt
```

**Manuelle aapt-Installation (Fedora):**
```bash
sudo dnf install android-tools
```

---

### Optional: Standalone .exe bauen (Windows)

Um TAKOTA als einzelne ausführbare Datei bereitzustellen, die auf dem Zielrechner kein installiertes Python benötigt:

```batch
build_exe.bat
```

Dieses Skript installiert **PyInstaller** und erzeugt `dist\TAKOTA.exe`. Die `.exe` kann auf beliebige Windows-Rechner kopiert werden — Python ist dort nicht erforderlich. `aapt.exe` muss auf dem Zielrechner jedoch weiterhin vorhanden sein.

---

## 4. Die GUI benutzen

Nach dem Start (`python takota_gui.py`, `setup.sh` oder `install_windows.ps1`):

### Schritt für Schritt

**1. APK-Ordner wählen**
Auf **Browse…** neben „APK Folder" klicken und den Ordner mit den Plugin-`.apk`-Dateien auswählen.
Alle `.apk`-Dateien in diesem Ordner werden verarbeitet.

**2. aapt-Pfad**
Das Tool sucht beim Start automatisch nach `aapt`. Wenn gefunden, wird der Pfad eingetragen.
- Falls nicht gefunden: **Auto-Detect** klicken — das Tool startet eine erneute Suche inkl. Installationsversuch.
- Alternativ über **Browse…** `aapt` / `aapt.exe` manuell auswählen.

**3. Ausführen**
Auf **▶ Run** klicken. Im Log-Bereich wird der Fortschritt für jede APK angezeigt:
- Metadaten extrahiert (Paketname, Version, SDK-Anforderungen)
- Icon extrahiert und als `.png` gespeichert
- SHA-256-Prüfsumme berechnet
- Eintrag in `product.inf` geschrieben

Nach Abschluss befinden sich `product.inf` und `product.infz` im APK-Ordner.

**4. Ordner öffnen**
Mit **Open Folder** lässt sich der Ausgabe-Ordner direkt im Dateimanager öffnen.

---

## 5. Was wird erzeugt

Nach einem erfolgreichen Durchlauf enthält der APK-Ordner:

```
product.inf       ← CSV-Manifest (eine Zeile pro Plugin)
product.infz      ← ZIP-Archiv: product.inf + alle extrahierten Icons (.png)
*.apk             ← Plugin-APKs (unverändert)
*.png             ← extrahierte Plugin-Icons
```

### Format von product.inf

```
#platform, type, Paketname, Label, Version, Revision Code,
 APK-Pfad, Icon-Pfad, Beschreibung, SHA256, Min-SDK, TAK-Prereq, Größe
Android,plugin,com.example.plugin,Mein Plugin,1.2.3,42,
 my_plugin.apk,my_plugin.png,Kurzbeschreibung,...,21,,123456
```

Der TAKServer liest `product.infz` ein, um daraus den Plugin-Katalog zu erstellen, den ATAK-Clients herunterladen.

---

## 6. Upload auf den civTAK-Server

Den gesamten Inhalt des APK-Ordners in das Update-Verzeichnis des TAKServers kopieren.

### Per SCP (Linux/macOS/WSL)

```bash
scp /pfad/zum/apk/ordner/* tak@DEINE_SERVER_IP:/opt/tak/webcontent/update/
```

### Per WinSCP (Windows)

Verbindung zum Server per SFTP herstellen, nach `/opt/tak/webcontent/update/` navigieren und alle Dateien aus dem APK-Ordner hochladen.

### Berechtigungen auf dem Server setzen

Nach dem Upload per SSH auf den Server verbinden und folgende Befehle ausführen:

```bash
sudo chown -R tak:tak /opt/tak/webcontent/update
sudo chmod -R 755 /opt/tak/webcontent/update
```

### Ergebnis prüfen

Folgende URL im Browser aufrufen (Server-Adresse und Port anpassen):

```
https://DEINE_SERVER_IP:DEIN_PORT/update/product.infz
```

Eine ZIP-Datei sollte heruntergeladen werden. Erscheint stattdessen eine 404-Fehlermeldung, bitte Berechtigungen und den TAKServer-Webcontent-Pfad überprüfen.

---

## 7. ATAK-Clients konfigurieren

Jeder ATAK-Client muss einmalig auf die Update-URL des Servers zeigen. Danach erfolgen Plugin-Updates automatisch.

1. **ATAK** auf dem Android-Gerät öffnen.
2. Menü-Icon antippen → **Settings** (Einstellungen).
3. **TAK Package Management** aufrufen (je nach ATAK-Version unter „Tool Preferences").
4. **Drei-Punkte-Menü** (⋮) antippen → **Edit**.
5. **Update Server** aktivieren.
6. Die URL eingeben:
   ```
   https://DEINE_SERVER_IP:DEIN_PORT/update
   ```
7. **Update** (🔄) antippen.

ATAK lädt nun `product.infz` herunter, wertet das Manifest aus und zeigt alle verfügbaren Plugins an. Nutzer können Plugins direkt aus ATAK heraus installieren oder aktualisieren — ohne manuelles Sideloading.

> **Port:** TAKServer verwendet standardmäßig Port `8443` für HTTPS. Bei Unsicherheit die TAKServer-Konfiguration prüfen.

> **Zertifikat:** ATAK muss dem Zertifikat des TAKServers vertrauen. Falls SSL-Fehler auftreten, das CA-Zertifikat des Servers in ATAK importieren.

---

## 8. Fehlerbehebung

| Problem | Lösung |
|---------|--------|
| `aapt not found` | In der GUI auf **Auto-Detect** klicken oder manuell installieren (siehe Abschnitt 3) |
| `No APK files found` | Sicherstellen, dass der gewählte Ordner `.apk`-Dateien enthält |
| Icon fehlt bei einem Plugin | Manche APKs deklarieren kein `application-icon-160` — das Plugin funktioniert trotzdem |
| `product.infz` wird vom TAKServer nicht ausgeliefert | Dateieigentümer prüfen (`chown -R tak:tak`) und Berechtigungen setzen (`chmod -R 755`) |
| ATAK zeigt SSL-Fehler | TAKServer-CA-Zertifikat in ATAK importieren (Einstellungen → Server-Verbindungen verwalten) |
| ATAK zeigt keine Plugins | Prüfen ob die Update-URL auf `/update` endet (nicht auf `/update/product.infz`) |
| PowerShell Execution Policy Fehler | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` ausführen |
| tkinter fehlt unter Linux | `sudo apt-get install python3-tk` ausführen |

---

## Credits

Basiert auf dem originalen [takserver_ota](https://github.com/GUMMIIII/takserver_ota)-Workflow.
