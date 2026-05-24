# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Planned

- Tracking ideas? Open a [feature request](https://github.com/GUMMIIII/takserver_ota/issues/new?template=feature_request.yml).

---

## [0.1.2] – 2026-05-24

### Documented

- **ATAK Update-Server URL must use port `:8443`** in all three READMEs (`README.md`, `EN_README.md`, `DEU_README.md`) — both for the Vanilla-TAKServer variant and the TAKSERVER_MDM variant. Added an explicit warning explaining the reason: ATAK has its own internal trust-store containing only the TAKServer-internal `KOMMSca` CA (via `user.p12` / `truststore-tak.p12`), so it does not trust Let's Encrypt or any other public CA. Going through TAKSERVER_MDM's nginx on port 443 fails with "socket is closed" during the TLS handshake. The direct `:8443` connection presents a KOMMSca-signed cert that every ATAK client accepts.

### Notes

Documentation-only — no code changes. The TAKOTA tool itself works the same as in v0.1.1.

---

## [0.1.1] – 2026-05-24

### Documented

- **TAKSERVER_MDM-specific deployment path** added to `README.md`, `EN_README.md`, and `DEU_README.md`. Section 6 ("Upload to your civTAK Server") now has two clearly separated variants:
  - **Option A — Vanilla TAKServer:** unchanged, `/opt/tak/webcontent/update/` with `tak:tak` ownership.
  - **Option B — [TAKSERVER_MDM](https://github.com/GUMMIIII/TAKSERVER_MDM):** host path is `/opt/komms-data/tak/webcontent/update/`, no `chown` needed (container runs as root), ATAK pulls from `https://tak.DOMAIN/update`. Calls out the v0.0.15 nginx `/update/` Authelia bypass so operators understand why this works without an SSO cookie.
- README hub now shows a comparison table for both deployment variants and links straight into the TAKSERVER_MDM README section.

### Notes

Documentation-only — no code changes. Existing TAKOTA installs work the same as before.

---

## [0.1.0] – 2026-05-24

### Added

- **LICENSE** — AGPL-3.0 (symmetrical with the companion [TAKSERVER_MDM](https://github.com/GUMMIIII/TAKSERVER_MDM) repo). Until this release, no license was declared, meaning the code was effectively "all rights reserved" under default GitHub terms.
- **SECURITY.md** — private vulnerability reporting policy via GitHub Security Advisory.
- **Issue templates** — structured bug-report and feature-request forms under `.github/ISSUE_TEMPLATE/`, plus quick-links to the Security Advisory and the companion TAKSERVER_MDM repo.
- **README badges** — license, latest release, last commit, open issues, GitHub stars.
- **README "A note from the maintainer"** — sets expectations: solo-maintained hobby project, feedback welcome, response within a few days.
- **README Companion section** — references [TAKSERVER_MDM](https://github.com/GUMMIIII/TAKSERVER_MDM) for users who want the full TAKServer + MDM platform that TAKOTA plugs into.
- **`.gitignore`** — Python (`__pycache__/`, `*.pyc`), PyInstaller (`build/`, `dist/`, `*.spec`, `*.exe`), virtual environments, editor / OS junk, and TAKOTA-specific drop-in artifacts (`*.apk`, `product.inf`, `product.infz`) so accidentally-staged plugins or generated bundles cannot land in the repo.

### Notes

This is the first tagged release. The code itself is unchanged from the pre-tag state — this release marks the repository going through a public-readiness polish pass.
