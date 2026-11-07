# Planning guide

Create an edit brief and EDL for the particular project. Adapt audience, voice, platform, pace, visual language, and accessibility choices to the user's requirements; no sample audience or style is mandatory.

## 1. Prepare

Place the script and voice-over in a private project folder such as `reels/<slug>/`, then run `python pipeline/prepare_reel.py reels/<slug>`. Read `align/<model>/qc_report.md`. Correct the script or flag mismatch/low-confidence regions before anchoring on-screen text to them. Alignment locates supplied words; it does not transcribe or verify the recording.

## 2. Write the brief

Use `director/templates/brief.example.json` as a structure example and follow the contract in `studio/src/schema.ts`. Record:

- Video type, audience, purpose, and one-sentence takeaway.
- Hook and beat ranges tied to words or timecodes.
- Assumptions, key terms, emphasis, and likely retention risks.
- Visual and audio direction with reasons grounded in the content.

## 3. Choose a visual direction

Pick palette, type, motion, background, and caption treatment based on the content and brand constraints. `brand/tokens.json` and `brand/fonts.json` are editable defaults. Verify font coverage for all languages and scripts. Keep color and typography consistent, but preserve contrast and variety between scenes.

For captions, choose from word, chunk, karaoke, build, or keyword modes. Use concise lines, emphasize selectively, and respect platform safe areas. If no timing file exists, use timecodes and mark them for review.

## 4. Plan scenes

- Make the opening immediately understandable; avoid a mandatory logo intro.
- Change the image when the idea changes. Let dense stretches breathe and hold important reveals.
- Give each scene a rationale: explain, orient, emphasize, establish, or provide an intentional pause.
- Use concrete visuals for analogies, lists, comparisons, and processes. Build lists as items are spoken when timing supports it.
- Use accurate, readable code only when it helps. Keep real product UI, claims, and testimonials grounded in user-provided evidence.
- Use transitions to support continuity, time, or emotion. Avoid gratuitous effects.
- Put the call to action on screen when one is requested.

See `director/catalog.md` for components, props, and transition values.

## 5. Audio

Use the bundled SFX index to find a cue for a meaningful action or reveal. Keep dialogue intelligible and music unobtrusive. Fewer, well-placed cues usually work better than constant effects. Confirm licence and attribution data for all external media.

## 6. Render and review

Run `python pipeline/prepare_reel.py reels/<slug> --stage-only` after updating the EDL. Render a draft using the commands in the README. Review the sequence visually and listen at normal playback speed. Check story clarity, pacing, caption readability, safe areas, continuity, audio sync, and mix. Run `pipeline/qc_video.py` for technical checks and a contact sheet. Resolve warnings where appropriate, render the final, and inspect it again.

## 7. Project-specific history

If consistency across a series matters, maintain a history file inside the user's private project folder. Do not store project history, personal content, or brand information in the public skill package.

## Hard constraints

- Do not alter or retime the voice-over without explicit user direction.
- Do not invent product interfaces, screenshots, testimonials, or factual claims.
- Keep essential content in the target platform's safe area.
- Use only assets with a known source and suitable licence.
- Report what was reviewed and what remains uncertain.
