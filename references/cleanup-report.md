# Public package cleanup and QA report

Date: 2026-11-07

## Removed creator-specific and local files

- `brand/logo/profile_pic.jpg` — personal profile image.
- `library/assets.json` — original project-specific register containing creator identity and history; replaced with a clean register for 78 generic bundled sound effects.
- `library/history.json` — per-video history and look-selection records.
- `reels/` and `reports/` — private project/output locations. The inventory contained no tracked media files in these directories at conversion time.
- `.pytest_cache/` — local test cache (removal was attempted; the host denied access to this pre-existing cache directory).
- `brand/icons.txt` — project-specific icon preload list; the setup check now packs its small generic icon set and project EDL icons are packed as needed.
- Original promotional brief example and reel EDL — replaced with synthetic examples.
- Python alignment package — renamed to `pipeline/aligner/` for a neutral public module name.
- Custom dependency installer and machine-specific `node_modules` junction setup — removed. Standard npm install is documented for independent setup; a local lockfile can be generated during installation.

The source inventory found no personal video, voice-over, thumbnail, or rendered video/audio files to include in the public package. The profile image was the only personal image found and was removed.

## Preserved capabilities

- English/Romanized Telugu-English script tokenization and word-level forced alignment with confidence/QC reporting.
- Brief-to-EDL scene planning and word-anchored captions, transitions, motion graphics, diagrams, code cards, and generic device frames.
- Remotion vertical renderer, icon packing, SFX staging, and optional Lottie support.
- Openverse/Pexels/Pixabay stock search/download workflow with sidecar licence records.
- Technical video QC, contact sheets, freeze/black-frame checks, and audio loudness mastering.
- Asset registration and verification utilities for user-added assets.

## Checks performed

- Parsed the retained JSON configuration and examples with Node/PowerShell JSON parsers.
- Ran `npm run typecheck --prefix studio`: passed with no TypeScript diagnostics.
- Searched the public project for the original creator/channel name, product name, username, private Windows path, and private project slug: no hits after cleanup, excluding the checker’s constructed marker strings and inaccessible dependency junction.
- Inspected the retained project file inventory; bundled media is limited to generic WAV sound effects.
- Verified the README’s paths against the new structure by inspection.

## Checks not run / limitations

- Python tests and `scripts/check_public_package.py` were not run: no Python interpreter is installed in this environment (`py -0p` reports no installed Python).
- Full renderer build/render was not run. The existing `studio/node_modules` junction targets a user-local directory outside the workspace; the TypeScript check could run, but direct dependency inventory was unavailable. A clean user should run `npm install` in `studio/`.
- The workspace denied access to the pre-existing `.pytest_cache`; `.gitignore` excludes it from future public commits.
- SFX source details originate from the existing project’s CC0 Kenney selection and locally synthesized clips. Verify upstream source/licence provenance for each clip before redistribution or commercial use.
- Automated QC cannot judge story quality, aesthetic continuity, caption correctness, accessibility, or rights.
