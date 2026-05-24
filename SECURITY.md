# Security Policy

## Reporting a Vulnerability

If you find a security issue in TAKOTA, **please do not open a public GitHub issue**. Instead, report it privately so it can be fixed before details become public.

### Preferred: GitHub Security Advisory

Use the **[private vulnerability reporting form](https://github.com/GUMMIIII/takserver_ota/security/advisories/new)** on this repository. This routes directly to the maintainer and lets us track the fix without exposing the issue.

### Alternative

If GitHub advisories are not an option for you, open a regular issue titled `Security: please contact me` (without any technical detail) and I'll reach out so we can move the conversation to a private channel.

## What to include in a report

- Affected component (e.g. `takota_gui.py`, `install_windows.ps1`, `setup.sh`, `build_exe.bat`)
- Affected version / commit hash
- Steps to reproduce — or a minimal proof-of-concept
- Impact: what an attacker could do with this (e.g. code execution on the host running TAKOTA, malicious APK content reaching ATAK clients via a tampered `product.infz`)
- Suggested fix, if you have one

## What to expect

This is a solo-maintained hobby project. I aim to:

- Acknowledge your report within a few days
- Assess and triage within a week
- Ship a fix as soon as I reasonably can — critical issues take priority over feature work

I'll credit you in the changelog and release notes unless you ask me not to. Once the fix is released, the vulnerability details can be made public.

## Scope

This policy covers the code in this repository — the TAKOTA GUI, setup scripts, and the Windows installer. Vulnerabilities in upstream components (Python, tkinter, aapt / Android SDK, TAKServer itself) should be reported to those projects directly.

## Out of scope

- Self-inflicted misconfigurations (running TAKOTA on a machine where untrusted users can drop APKs into the input folder, etc.)
- Issues that require an attacker to already have local execution on the machine running TAKOTA
- Generic Python supply-chain concerns covered by Dependabot
