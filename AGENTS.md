# Light-WeChat public edition

This directory is an independent, self-contained skill. Never import credentials,
brand images, article workspaces, deployment settings or approval records from
another checkout or the developer's local environment.

The maintainer explicitly authorized the public website link, supplied homepage
screenshot and support/contact QR images under assets/readme/ for README display.
Keep those documentation assets separate from runtime publication settings and
generated articles; never infer account access or upload consent from them.

- Preserve pinned upstream files under vendor/ byte for byte. Keep their licenses.
- Local preview is the default. Enabling a configured account is not consent to upload.
- Only a specific authorized draft upload may use --confirm-upload; never test against live accounts.
- Keep secrets in ignored local files and out of CLI arguments, logs and reports.
- Use the included backend and local configuration; do not reintroduce absolute personal paths.
- Run the meaningful offline tests, upstream verification and release checks after changes.
- Inspect real 375/390 px rendering when a change affects layout.
