---
name: video-editing-workflow
description: Plan and produce polished short-form videos with a reusable word-timed editing workflow, scene planning, captions, motion graphics, audio, rendering, and quality checks. Use when a user asks to plan, edit, caption, grade, mix, render, or optimize a video, especially a vertical short made from a script and voice-over.
---

# Video Editing Workflow

Use this skill to turn a user's goals and media into a clear, reviewable edit plan and, when the included tools and dependencies are available, a rendered vertical video. Adapt to the user’s platform, audience, source material, experience, and preferred style. Do not impose a fixed brand, audience, language, pace, or visual treatment.

## Start with the project

1. Identify the deliverable: platform, aspect ratio, duration, audience, purpose, and whether the user wants planning, a timeline/EDL, or a rendered file.
2. Ask only for details that materially affect the edit. If the project files are not available, request the script, voice-over, footage/images, logos or product captures, music/SFX, captions/transcript, and any reference/look preferences that apply. Accept partial materials and explain what can be done with them.
3. Confirm which assets may be used and any licensing, privacy, accessibility, language, or brand constraints. Never fabricate product interfaces, testimonials, footage, or claims.
4. Offer a concise workflow suited to the project, then proceed in reviewable stages: brief, scene plan, draft, review, final export. Explain assumptions and invite corrections at natural review points.

## Workflow

### 1. Brief and prepare

- Summarize the message, audience, tone, platform, runtime, and call to action.
- For scripted voice-over, keep the supplied recording as the timing source. Do not retime or alter it unless explicitly requested.
- Put a project in `reels/<project-slug>/` with `script.txt`, one voice-over file, and optional `assets/`, `brief.json`, and `edl.json`. Keep personal media in the user's project; do not add it to this public skill repository.
- Run alignment and read its QC report. Treat mismatch regions and low-confidence words as uncertain; avoid anchoring text or visual reveals to them until corrected.

### 2. Plan the edit

- Create a brief and scene-by-scene EDL using `director/templates/brief.example.json` and `director/templates/edl.example.json` as format examples. Consult `director/planning-guide.md` and `director/catalog.md` for detailed choices and supported scene components.
- Anchor scenes, captions, lists, and animation reveals to word indices when timing data exists; otherwise use timecodes and mark estimates.
- Give every visual a purpose: explain, establish, emphasize, orient, or create a deliberate emotional beat. Use footage, screenshots, typography, diagrams, or simple graphic scenes according to the material.
- Choose a hook, pacing, transitions, color treatment, typography, captions, music, and sound effects for the specific project. Use restraint and preserve dialogue intelligibility.
- Keep essential text inside platform-safe areas. Provide readable captions, meaningful line breaks, sufficient contrast, and an appropriate language/script font.

### 3. Build and render

- Use the Python pipeline for script/audio alignment, asset tracking, staging and video QC. Use the Remotion project for data-driven scenes, captions, transitions, motion graphics, and rendering.
- See `README.md` for installation, supported inputs, dependency requirements, and commands. If tools are unavailable, deliver explicit editor-agnostic steps or a timeline/EDL instead of claiming a render was made.
- Use only user-provided, generated, or properly licensed assets. Record downloaded stock asset sources and attribution requirements. Do not commit private project assets, downloaded media, rendered outputs, model weights, caches, credentials, or `.env` files.

### 4. Review and deliver

- Review a draft visually as a viewer: hook clarity, narrative flow, scene relevance, pacing, caption readability, safe zones, visual continuity, color consistency, transitions, and whether the CTA matches the brief.
- Check audio synchronization, voice intelligibility, music/SFX balance, clipping/peaks, and export loudness. Review the contact sheet and QC report; QC scripts cannot assess story quality.
- Verify the export's dimensions, frame rate, codec, audio stream, duration, black frames, freeze warnings, and loudness where tooling allows. State any unperformed checks.
- Deliver the render or edit instructions plus a short summary of choices, assumptions, known issues, and export details.

## Supported project capabilities

The included implementation supports word-level forced alignment for English and Romanized Telugu-English workflows, alignment confidence/QC, word-timed captions, data-driven scene planning, transitions, motion graphics, icon/diagram/code/device mockup scenes, SFX selection, stock search/download with licence tracking, Remotion rendering, contact sheets, technical video checks, and audio loudness mastering. See the README for exact scope and limitations. It does not replace a nonlinear editor for arbitrary multi-track footage editing, advanced compositing, or manual color-science work.

## Error handling and limits

- If files are missing, formats are unsupported, alignment is unreliable, or required dependencies are absent, report the specific issue and offer the next useful path (provide a transcript, use manual timecodes, install a dependency, or produce an editor-ready plan).
- Forced alignment estimates where known script words occur; it does not transcribe speech or guarantee correctness. Human review is required, especially for code-switching, names, noisy audio, and unscripted speech.
- The bundled alignment models have different language and licence constraints. Check the model's current terms before commercial use; the multilingual MMS option is non-commercial under its listed licence.
- Platform specifications change. Confirm current export requirements when strict platform compliance matters; the bundled default renderer is a 1080×1920, 30 fps H.264 workflow.
- Stock availability and licensing depend on the source and individual asset. Preserve sidecar licence data and provide required attribution.
- Never claim a render, asset verification, visual review, or test succeeded unless it was actually performed.
