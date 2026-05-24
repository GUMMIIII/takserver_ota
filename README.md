# TAKOTA – civTAK OTA Bundle Generator

[![License: AGPL v3](https://img.shields.io/github/license/GUMMIIII/takserver_ota?color=blue)](LICENSE)
[![Latest Release](https://img.shields.io/github/v/release/GUMMIIII/takserver_ota?label=release)](https://github.com/GUMMIIII/takserver_ota/releases)
[![Last Commit](https://img.shields.io/github/last-commit/GUMMIIII/takserver_ota)](https://github.com/GUMMIIII/takserver_ota/commits/main)
[![Issues](https://img.shields.io/github/issues/GUMMIIII/takserver_ota)](https://github.com/GUMMIIII/takserver_ota/issues)
[![Stars](https://img.shields.io/github/stars/GUMMIIII/takserver_ota?style=social)](https://github.com/GUMMIIII/takserver_ota/stargazers)

Automatically generate `product.inf` + `product.infz` from ATAK plugin APKs and serve them via your civTAK server for over-the-air (OTA) distribution to connected ATAK clients.

> Last tested: May 2026 · TAKServer 5.x · ATAK 5.x

---

## A note from the maintainer

Hey — this is a hobby tool I built to automate plugin packaging for my own civTAK deployment and decided to publish in case it helps others running similar setups. It works for me, but I'm one person: expect bugs, rough edges, and undocumented assumptions baked into the code.

If you run into problems or have ideas, please open an [issue](https://github.com/GUMMIIII/takserver_ota/issues) — I read all of them and I'm genuinely happy to get feedback, both bug reports and suggestions.

I'll try to respond within a few days. Bigger changes (new features, refactors) might take longer depending on how much free-time work they need, but they're not off the table.

---

## Documentation

| Language | Link |
|----------|------|
| English  | [EN_README.md](EN_README.md) |
| Deutsch  | [DEU_README.md](DEU_README.md) |

---

## Quick Start

**Windows**
```powershell
.\install_windows.ps1
```

**Linux**
```bash
bash setup.sh
```

**Direct (Python 3 required)**
```bash
python takota_gui.py
```

---

## Companion: Full TAKServer + MDM Platform

If you're looking for a complete self-hosted TAKServer deployment with OpenVPN, Matrix, Mumble, Nextcloud, Headwind MDM, and SSO baked in — check the companion repo **[GUMMIIII/TAKSERVER_MDM](https://github.com/GUMMIIII/TAKSERVER_MDM)**.

TAKOTA plugs straight into the TAKServer set up there. The path differs slightly because TAKSERVER_MDM bind-mounts `/opt/tak/` from the host:

| Setup | Drop generated files into | ATAK pulls from |
|---|---|---|
| Vanilla TAKServer | `/opt/tak/webcontent/update/` | `https://SERVER:8443/update` |
| TAKSERVER_MDM | `/opt/komms-data/tak/webcontent/update/` | `https://tak.DOMAIN/update` |

TAKSERVER_MDM (v0.0.15+) ships an nginx bypass for `/update/` so ATAK can fetch the manifest without an SSO session. See the [TAKSERVER_MDM README](https://github.com/GUMMIIII/TAKSERVER_MDM#companion-atak-ota-updates) for details.

---

## License

[AGPL-3.0](LICENSE)
