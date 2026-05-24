# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Planned

- Tracking ideas? Open a [feature request](https://github.com/GUMMIIII/takserver_ota/issues/new?template=feature_request.yml).

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
