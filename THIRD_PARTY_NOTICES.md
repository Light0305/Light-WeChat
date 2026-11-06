# Third-party notices

This distribution preserves pinned upstream originals. Their notices and licenses continue to apply.
Project code and adaptations use AGPL-3.0-only; MIT originals retain MIT. No upstream authors endorse this project.

## Vendored source and design assets

| Component | Original repository | Pinned commit | Files | License / full text |
| --- | --- | --- | ---: | --- |
| aihot | https://github.com/KKKKhazix/AIHOT | `b3998dc6fc138eb9659f33f55eb38c1c716f0d57` | 35 | MIT; [LICENSE](vendor/aihot/LICENSE) |
| wewrite | https://github.com/imraywang/wewrite | `220db1dcf141d92c03ddb704628a774ecd2b79f7` | 37 | MIT; [LICENSE](vendor/wewrite/LICENSE) |
| gzh-design | https://github.com/isjiamu/gzh-design-skill | `750a50dffdc4abb5e853b98136dad13a57e64ce3` | 21 | AGPL-3.0-or-later; [LICENSE](vendor/gzh-design/LICENSE) |
| guizang | https://github.com/op7418/guizang-social-card-skill | `cf4b810fac1c73fb65a2bb31d8c9278d82cbc4c5` | 34 | AGPL-3.0 (version 3 used for this distribution); [LICENSE](vendor/guizang/LICENSE) |
| baoyu | https://github.com/JimLiu/baoyu-skills | `1567581c26ec29f4216c6e6835415bf30343b0e3` | 73 | MIT; [LICENSE](vendor/baoyu/LICENSE) |
| humanizer | https://github.com/blader/humanizer | `8c307f367c91bd974002f10f2be2965d642c13df` | 2 | MIT; [LICENSE](vendor/humanizer/LICENSE) |

The file-level SHA-256 inventory is [vendor/manifest.json](vendor/manifest.json).
Run `python scripts/verify_upstream.py` to verify 202 originals and six compiled theme sources.

Guizang also supplies [COMMERCIAL_LICENSING.md](vendor/guizang/COMMERCIAL_LICENSING.md), preserved verbatim.
This project uses the included AGPL license, does not claim a separate commercial license, and does not alter that offer.
An ISC value in upstream package metadata does not replace its included LICENSE; this distribution follows the included AGPL text.

Nine binary background assets are pinned Guizang originals, not developer contact cards or article images.
External photos, screenshots, fonts and generated article assets must have their own usage basis; upstream examples do not grant rights to unrelated material.

## Adaptations outside vendor

- `tools/wechat-publisher/wechat_publisher/gzh_components.json`: compiled HTML fences from gzh-design themes; each theme records its original source and hash.
- `tools/wechat-publisher/wechat_publisher/gzh_layout.py`: modified renderer/assembly based on those theme components and the editorial adaptation.
- `scripts/cover_pair.py`: fills Guizang Swiss/Editorial template seeds with user content.
- `scripts/validate_cover_deck.mjs`: portable wrapper around Guizang R1–R9 validation. Its runtime copy is temporary; the original is unchanged.
- `scripts/upstream_modules.py` and editorial/research adapters invoke pinned WeWrite, AIHOT and gzh-design validators/prompts.

These adaptations are supplied with editable source under AGPL-3.0-only. See NOTICE for the public-edition change summary.

## Installed Python dependencies

Dependencies are downloaded separately from PyPI, not bundled in the source archive.
The table records upstream package metadata for the exact locked versions; installed distributions contain their own full license texts.
Runtime and development locks include official distribution SHA-256 hashes.

| Package | Locked version | Upstream license metadata |
| --- | --- | --- |
| Markdown | 3.11.3 | BSD-3-Clause |
| Pillow | 13.0.0 | MIT-CMU |
| python-dotenv | 1.2.4 | BSD-3-Clause |
| requests | 2.34.2 | Apache-2.0 |
| beautifulsoup4 | 4.15.0 | MIT License |
| PyYAML | 6.0.3 | MIT |
| certifi | 2026.10.23 | MPL-2.0 |
| charset-normalizer | 3.5.2 | MIT |
| idna | 3.20 | BSD-3-Clause |
| urllib3 | 2.8.0 | MIT |
| soupsieve | 4.0.1 | MIT |
| typing_extensions | 4.16.0 | PSF-2.0 |
| pytest | 9.2.0 | MIT |
| colorama | 0.4.6 | License :: OSI Approved :: BSD License |
| iniconfig | 2.3.1 | MIT |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pluggy | 1.7.0 | MIT |
| pygments | 2.21.0 | BSD-2-Clause |

## Optional Node tooling and external runtime

| Component | Locked version | License | Distribution |
| --- | --- | --- | --- |
| playwright / playwright-core | 1.60.0 | Apache-2.0 | Optional `npm ci --ignore-scripts`; not bundled |
| fsevents | 2.3.2 | MIT | Optional macOS transitive package; not bundled |
| Gitleaks | 8.30.1 | MIT | Separate checksum-verified download from its official release; not bundled |

Python, Node.js and the chosen browser are separately installed runtimes. Browser binaries and their notices are not bundled.
WeChat API access, model services and other third-party services remain subject to their own account terms and permissions.

No private account credentials, website deployment modules or article archives form part of this distribution.

## Public README display assets

The maintainer authorized one public website screenshot and three support/contact QR images for this project's documentation. Their sources and usage boundaries are recorded in [assets/readme/README.md](assets/readme/README.md). These display assets are separate from the vendored software, publication configuration and generated article content. Original Light-WeChat SVG logos are project-authored; no official WeChat logo is incorporated into that wordmark.
