# Video Editing Workflow Skill

A reusable skill and reference implementation for planning and producing short-form videos. The project combines an AI-assisted, word-timed edit planning workflow with a Python audio alignment and QC pipeline and a Remotion renderer. It is designed to be adapted to each creator and project.

## What it can do

- Prepare a project brief and scene-by-scene edit decision list (EDL).
- Align a known script to voice-over audio, with confidence indicators and mismatch reports.
- Design word-timed captions, scene transitions, motion graphics, diagrams, code cards, and generic device mockups.
- Search and download stock images through Openverse, with licence sidecars and attribution tracking. Optional Pexels and Pixabay search require user-supplied API keys.
- Render vertical video with Remotion and create a contact sheet.
- Check dimensions, frame rate, codec, audio presence, duration, black frames, freeze warnings, and loudness; optionally normalize audio.

The included renderer is a short-form, data-driven composition system, not a replacement for Premiere, Resolve, Final Cut, or another nonlinear editor for arbitrary multi-track footage, advanced compositing, or manual grading. Color choices and grading guidance are provided; the implementation does not perform shot-matched color grading.

## Project layout

```text
video-editing-skill/
├── SKILL.md
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── director/                 # Planning guide, component catalogue, JSON examples
├── brand/                    # Generic palette/type/motion tokens and bundled SFX
├── library/                  # Generic SFX index; user asset register is created as needed
├── pipeline/                 # Alignment, staging, media search, asset tracking, QC
├── studio/                   # Remotion renderer and motion/caption components
├── references/                # Workflow, cinematic, color, audio, export guidance
├── examples/                  # Generic brief and EDL examples
└── scripts/                   # Public package checks
```

## Requirements

- Python 3.10 or later; install project dependencies with `python -m pip install -r pipeline/requirements.txt`.
- Node.js 20 or later and npm for rendering; run `npm install` from `studio/`.
- FFmpeg and FFprobe for audio loading, rendering support, contact sheets, and media QC.
- PyTorch, Transformers, and a compatible Hugging Face acoustic model for forced alignment. The first alignment may download model weights. A GPU is optional; CPU inference is supported but slower.
- A compatible OS and Chromium environment for Remotion rendering.

Some components work independently: planning documents and EDL examples need no runtime; video QC requires FFmpeg/FFprobe; alignment requires Python dependencies and model access; Remotion rendering requires Node/npm dependencies.

## Install and start

1. Clone or download this repository.
2. Read [SKILL.md](SKILL.md), then [director/planning-guide.md](director/planning-guide.md) and [director/catalog.md](director/catalog.md).
3. Install Python requirements and run `npm install` in `studio/`.
4. Create a private project folder such as `reels/my-project/`. Add `script.txt` and a voice-over file (`.wav`, `.mp3`, `.m4a`, or `.flac`). Optional footage, screenshots, music, and graphics belong in that project's `assets/` folder.
5. Run alignment and staging from the repository root:

   ```powershell
   python pipeline/prepare_reel.py reels/my-project
   ```

6. Draft `brief.json` and `edl.json` from the generic examples. Run staging again after editing the EDL:

   ```powershell
   python pipeline/prepare_reel.py reels/my-project --stage-only
   ```

7. Preview or render from `studio/` (replace the output path as needed):

   ```powershell
   npm run studio
   npx remotion render src/index.ts Reel ../reels/my-project/out/draft.mp4 --props='{"slug":"my-project"}' --scale=0.5
   npx remotion render src/index.ts Reel ../reels/my-project/out/final.mp4 --props='{"slug":"my-project"}'
   ```

8. Review the draft and inspect technical QC. A contact sheet helps visual review; the automated script does not judge story or aesthetics:

   ```powershell
   python ../pipeline/qc_video.py ../reels/my-project/out/final.mp4 --sheet ../reels/my-project/out/contact-sheet.jpg
   ```

See the planning guide for the brief-to-EDL process, scene anchoring, captions, audio, and review. Treat all sample word indices and content as illustrative only. The cleanup and verification notes are in [references/cleanup-report.md](references/cleanup-report.md).

## Optional stock providers

Openverse search does not require an API key. Optional Pexels/Pixabay keys should be provided through environment variables (`PEXELS_API_KEY`, `PIXABAY_API_KEY`) or a local, untracked `.env`. Never commit credentials. Review each asset's licence and attribution before publishing.

## Model and media licensing

The English wav2vec2 alignment model is listed as Apache-2.0. The multilingual MMS aligner is listed as CC-BY-NC-4.0 and is not suitable for commercial use under those terms. Check upstream model terms before use. Bundled sound effects include CC0 Kenney clips and locally synthesized clips; each bundled effect is indexed with its source/licence in `library/sfx_index.json` and `library/assets.json`. User-provided assets and stock downloads remain subject to their own licences.

## Privacy and repository hygiene

Keep source footage, voice-over, user-specific briefs/EDLs, exports, model weights, caches, local `.env`, and private brand assets outside version control. The generic project examples contain no source creator footage. `reels/` and `reports/` are intentionally not included in this public package.

## Quality checks

```powershell
python scripts/check_public_package.py
python -m pytest pipeline/tests
```

The package checker scans tracked project files for common personal path/brand markers and forbidden media/output extensions. It is a useful guard, not a guarantee that every possible personal detail or secret has been detected. Review results and asset licences before publishing.

## Limitations

- Alignment is not speech recognition. It locates supplied words in audio and needs human review, especially with code-switching, names, accents, noisy audio, or unscripted speech.
- The default renderer is configured for 1080×1920, 30 fps, H.264. Verify current platform delivery requirements for each release.
- Technical QC cannot assess narrative clarity, color continuity, taste, accessibility, rights, or whether captions are factually correct.
- The project does not ship personal video, voice-over, logo, thumbnails, or finished exports.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Changes should remain generic, document supported behavior, and avoid embedding personal media, secrets, or creator-specific assumptions.
