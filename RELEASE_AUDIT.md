# Public-edition verification · 2026-11-06

This is an independent source export, prepared without modifying or installing over the private edition.
It starts with no inherited commits. Initial local preparation used no GitHub publication, WeChat draft upload,
mass publication or paid image request. GitHub repository and Release publication were subsequently authorized by the maintainer.

## Scope and privacy

- Website synchronization, deployment modules and their approval rules were removed from the public workflow.
- Runtime personal accounts, default contact cards, article archives, machine-specific paths and private service settings were excluded.
- The maintainer explicitly approved the public website link, one supplied homepage screenshot and three support/contact QR images for the bilingual README. These are documentation-only assets; they do not configure publication identity, credentials or upload consent. Their provenance is recorded in `assets/readme/README.md`.
- Local preview is the default. Credentials are blank templates; integrations are disabled by default.
- The publisher is included and reads only its own local credential file or a file explicitly selected by the user.
- Draft upload requires account setup, an enabled integration, article-level delivery selection and an explicit upload action.
- Account identity, approved scope and the frozen version are bound together. Ambiguous results require readback before retrying.

The local comparison of known private credential values and disallowed private identifiers found no matches in the release files.
The approved public website, GitHub handle and contact email are permitted only in named documentation files;
known credential matching has no such exemption.
Comparison was done in memory; secret values are not included here or in the public package.
The preservation audit compared 398 pre-existing private files: their SHA-256 hashes and original private Git status were unchanged.

## Dependencies, licenses and provenance

- Python runtime and development requirements are pinned with official PyPI distribution SHA-256 hashes.
- A fresh download verified those hashes for all 18 Windows runtime/development distributions.
- Optional Node tooling has an npm lockfile with package integrity hashes; installation used `npm ci --ignore-scripts`.
- The project/adaptations use AGPL-3.0-only. Six upstreams retain their own licenses and copyright notices.
- All 202 pinned original files and six compiled theme sources passed `verify_upstream.py`.
- Full licenses and the Guizang commercial-license offer remain present; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
- GitHub Actions dependencies are pinned to verified full commit hashes. CI runs offline behavior tests and source/history checks.

Dependency advisory results on 2026-11-06: pip-audit 2.10.1 checked 12 runtime packages and six development packages,
with zero known advisories. npm audit checked the optional Node dependency tree with zero reported vulnerabilities.
These are point-in-time checks, not a guarantee against future or undisclosed vulnerabilities.

## Tests and secret scanning

Tests use temporary workspaces and synthetic content. Python network access is blocked by default in tests.
The initial local run passed **48 tests**, including the optional real-browser test.
They cover local defaults, credential isolation, configuration round-tripping, safe article paths, optional contact cards,
cover contracts, rendering, version invalidation, freeze versus approval, simulated upload/account binding,
duplicate prevention, uncertain-result handling, redacted transport failures and optional image recovery.

Real local-browser previews were captured at 375 px and 390 px and visually inspected. They showed readable text,
correct image loading and no horizontal overflow. These are synthetic test previews, not production article designs.
The optional Guizang wrapper was also executed on two synthetic frames: zero failures and two advisory composition warnings.

Gitleaks 8.30.1 was installed from the official release with a pinned checksum-document hash and archive verification.
Scanning runs locally with full default rules and additional account-key rules; source is not sent to a scanning service.
A disposable synthetic credential was detected, and a force-tracked credential filename was correctly rejected.
The final public-source scan returned zero findings from both Gitleaks and the additional local rules.
The initial public export had no commits; the newly created independent public history is now included in release scans.
A separate read-only scan of the private source history returned no findings; that history is not copied into this repository or release archive.

## Packaging and limits

The source archive is built from an explicit allowlist and includes a per-file SHA-256 inventory.
Local configuration, credentials, article workspaces, caches, installed dependencies and Git metadata are excluded.
Release checks refuse missing required notices or mismatched extracted-package inventory.
An extracted copy was verified in a second clean environment installed offline from the hashed dependency downloads:
all 49 tests, environment checks, upstream checks and extracted-source secret scans passed on the final documentation update. It used no private source imports.

The Light-WeChat documentation update adds an English-first README and Chinese counterpart, original light/dark SVG logos,
the exact supplied website screenshot and personal contact QR, and checks for HTML image/source links and centered contact ordering.
The public Skill entry and archive root use `light-wechat`; internal configuration names remain compatible.
The updated complete local run passed **49 tests**, including real 375/390 px article previews.
The personal contact QR was not regenerated or resampled: decoded pixels were verified identical while ancillary metadata
and trailing bytes were removed from the public copy. The provided homepage screenshot remains byte-for-byte unchanged.
Local GitHub-style README previews were checked at 1100 px and 390 px, including a dark-mode rendering.
Both measured zero broken local images and no document-wide horizontal overflow; the middle contact code is preserved.
Remote badge images were represented by local text badges in these offline layout proofs, not tested against the badge service.
The official skills CLI discovered exactly one top-level Skill, `light-wechat`, using its local read-only listing mode.

The first hosted [public-source CI run](https://github.com/Light0305/Light-WeChat/actions/runs/42229478373) passed on both
Ubuntu and Windows on 2026-11-06, including locked dependency installation, offline behavior tests, upstream verification,
checksum-verified scanner setup and source/history scanning. The real-browser test remains an explicit local check.

Local execution was verified on Windows with Python 3.11.13 and Node.js 25.8.0. Portable discovery and CI definitions
cover other supported systems. macOS/Linux desktop execution was not verified locally; hosted CI results are reported separately on GitHub.
Live WeChat permissions, IP whitelists, account-specific API behavior and paid provider availability remain untested;
the user must configure and authorize their own services.

Automatic secret detection does not prove that no sensitive information can exist, and file integrity does not certify
the truth or rights of future article content. New assets and contributions still need human review.
