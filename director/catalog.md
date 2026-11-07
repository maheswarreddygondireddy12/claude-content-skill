# Component catalogue (engine v1)

Scenes in `edl.json` name a **scene component**. Any prop ending in `Word` (`atWord`, `appearAtWord`, `typeFromWord`, `highlightFromWord`, `startFrameWord`, `fromWord`) is converted to frames relative to the scene start, so animations stay locked to the voice. Code lives in `studio/src/engine/registry.tsx` and `studio/src/primitives/`.

## Scene components
| Component | Use when | Avoid when | Key props |
|---|---|---|---|
| `CaptionFocus` | No visual would add clarity; the captions carry the beat | Overused: more than about 3 in a row feels empty | — |
| `KeywordCard` | Naming or defining a key term; the reveal moment | The term is already on screen | `text`, `sub`, `icon`, `size`, `enter`, `appearAtWord`, `y` |
| `BuildList` | Lists, steps, features, "what you need" | Only 1–2 items | `title`, `items[{text, icon, atWord, state: neutral/good/bad}]`, `size`, `y` |
| `Code` | Showing real code, a syntax or output | The code is longer than about 8 lines; abstract ideas | `heading`, `code`, `lang`, `theme`, `title`, `typing{cps, typeFromWord}`, `highlightLines`, `highlightFromWord`, `added`, `removed`, `fontSize` |
| `Chat` | Prompting, AI conversations, Q&A framing | Real product claims | `messages[{from: user/ai, text, atWord}]`, `assistantName` |
| `Phone` | User-provided app or website screenshots, mobile flows | No real asset exists (never fake one) | `screenshot` or `video` (paths under public `reels/<slug>/assets/...`), `width`, `scrollPx` |
| `Browser` | Website or dashboard screenshots | Same as above | `url`, `screenshot` |
| `Counter` | Numbers that matter (days, %, users) | Decorative numbers | `to`, `from`, `suffix`, `prefix`, `label`, `startFrameWord` |
| `Image` | Stock or user-provided image where realism helps | An icon scene would explain better | `src`, `fit`, `inset` |
| `Lottie` | A licensed Lottie (`library/lottie`) adds meaning | Purely decorative loops | `src` (`brand/lottie/<file>.json`), `loop`, `size` |
| `Composite` | **Everything else**: analogies, client↔server, flows, comparisons, before/after, custom layouts | — | `title`, `titleY`, `elements[]` (below) |

## Composite elements
`{ "type": "...", "x": 540, "y": 960, "anchor": "center" | "topleft", "props": {...} }`. NodeBox and Arrow use absolute canvas coordinates in their own props.

| Element | Purpose | Key props |
|---|---|---|
| `Icon` | Icon or illustration with label, entrance and idle float | `name` (`set:name`), `size`, `color`, `label`, `appearAtWord`, `enter`, `float` |
| `Text` | Free text; `highlight` adds a marker sweep | `text`, `size`, `fontKey`, `color`, `weight`, `appearAtWord`, `enter`, `highlight`, `width`, `align` |
| `NodeBox` | Diagram node (client, server, DB, layer) | `x`, `y`, `w`, `h`, `label`, `sub`, `icon`, `active`, `appearAtWord`, `enter` |
| `Arrow` | Connector that draws itself; `flow` sends packets | `from[x,y]`, `to[x,y]`, `curve`, `label`, `dashed`, `flow`, `appearAtWord`, `color` |
| `KeywordCard`, `BuildList`, `CodeBlock`, `ChatThread`, `PhoneFrame`, `BrowserFrame`, `Counter` | Same as the scene versions, freely positioned | as above |
| `Checkmark`, `Cross` | Right/wrong, solved/problem | `size`, `fromWord` |
| `Pulse` | Draw attention to an element | `size`, `fromWord`, `color` |
| `Spinner`, `ProgressBar` | Loading, waiting, progress or streaks | `fromWord`, `frames`, `to`, `label` |
| `Wordmark` | Brand mark (end card or CTA) | `size`, `glyph` |
| `Image`, `Lottie` | As above | — |

## Shared options
- **Enter kinds:** `none`, `fade`, `pop`, `rise`, `drop`, `slide-left`, `slide-right`, `blur`, `zoom`.
- **Scene `transitionIn.type`:** `cut`, `fade`, `slide-up`, `slide-left`, `slide-right`, `wipe`, `zoom`, `blur`, `glitch` (`frames` 0–30).
- **Scene `layer`:** `main` (sequential, lasts until the next main scene) or `overlay` (on top, lasts until `wordEnd` + `holdMs`).
- **Code languages:** python, javascript, typescript, java, c, cpp, sql, html, css, json, bash, jsx, tsx, go.
- **Code themes:** github-dark, one-dark-pro, tokyo-night, dracula, vitesse-dark, night-owl.

## Caption treatment (`edl.captions`)
| Setting | Options |
|---|---|
| `mode` | `word` (one at a time), `chunk` (phrase appears whole), `karaoke` (phrase with the active word lit), `build` (words appear as spoken), `keyword` (only emphasised words) |
| `family` | Any key in `brand/fonts.json`. Also set `weight`, `size` (40–140), `textCase`, `letterSpacing`. |
| `y`, `align`, `maxWidth` | Placement. Keep `y` ≤ about 1500. |
| `maxWords`, `maxChars`, `breakStrength` | Chunking. Breaks come from `timing.json` boundaries (punctuation, signposts, language switches, gaps). |
| `emphasisRules` | `english`, `caps`, `acronym`, `number`, `signpost`, `question`, `elongated` |
| `emphasisWords` | Explicit word indices to emphasise |
| `emphasisStyle` | `color`, `scale`, `underline`, `box`, `glow` |
| `background` | `none`, `shadow`, `stroke`, `pill`, `box` |
| `enter`, `wordEnter` | Animation of the phrase and of individual words |
| `hideInScenes` | Scene ids where captions step aside |

## Assets and tools
- **Icons:** `node studio/scripts/icons.mjs search <query>` lists matches. Sets: lucide, tabler, mdi (UI), logos and devicon (tech logos), fluent-emoji-flat and fluent-emoji (illustrations for analogies). Icons in an EDL are packed automatically on staging.
- **SFX:** see `library/sfx_index.json`. The roles are:
  - UI: click, tick, select, toggle, pop, open, close
  - feedback: confirm, error, question, bong, ding, powerup
  - transitions: whoosh, riser, rise_short, fall_short, zap, glitch
  - hits: impact_soft, impact_punch, impact_metal, impact_bell, sub_hit
  - other: scratch, tone, typing
- **Stock:** `python pipeline/stock.py search "<query>"` (Openverse, no key), then `download openverse <id> --reel <slug>`.
- **Licences:** run `python pipeline/assets.py --verify`.
