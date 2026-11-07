// Contracts between the Director (writes brief.json / edl.json) and the renderer.
// The EDL describes WHAT to show and WHEN (anchored to word indices from timing.json);
// it never encodes a fixed template. Every Reel brings its own look + caption treatment.
import { z } from "zod";

// ---------- timing.json (produced by pipeline/prepare_reel.py) ----------
export type TimingWord = {
  i: number;
  raw: string;
  display: string;
  align: string;
  start: number;
  end: number;
  conf: number;
  lang: "en" | "te" | "num" | "other";
  markers: string[];
  punct_after: string;
  sentence: number;
  phrase: number;
  signpost: boolean;
  flags: string[];
  dur_z: number;
  rms_db: number;
  chars?: [number, number][];
};
export type TimingBoundary = { after: number; gap_ms: number; strength: number; sentence_break: boolean; signpost_next: boolean; lang_switch: boolean; punct: string };
export type TimingGroup = { i: number; word_start: number; word_end: number; start: number; end: number; text: string };
export type Timing = {
  schema_version: number;
  meta: { slug: string; duration_s: number; [k: string]: unknown };
  words: TimingWord[];
  boundaries: TimingBoundary[];
  sentences: TimingGroup[];
  phrases: TimingGroup[];
  rate: { values: [number, number][] };
};

// ---------- caption treatment (chosen per Reel) ----------
export const emphasisRuleSchema = z.enum(["english", "caps", "acronym", "number", "signpost", "question", "marked", "elongated"]);

export const captionTreatmentSchema = z.object({
  enabled: z.boolean().default(true),
  family: z.string().describe("font key from brand/fonts.json"),
  weight: z.number().int().min(100).max(900).default(800),
  size: z.number().min(40).max(140),
  letterSpacing: z.number().default(0),
  textCase: z.enum(["as-is", "upper", "lower"]).default("as-is"),
  y: z.number().min(0).max(1920).describe("vertical centre of the caption block, px"),
  align: z.enum(["left", "center", "right"]).default("center"),
  maxWidth: z.number().default(860),
  mode: z.enum(["word", "chunk", "karaoke", "build", "keyword"]),
  maxWords: z.number().int().min(1).max(10).default(4),
  maxChars: z.number().int().min(4).max(60).default(24),
  breakStrength: z.number().min(0).max(1).default(0.5),
  color: z.string().default("#F5F8FF"),
  pastColor: z.string().optional(),
  futureOpacity: z.number().min(0).max(1).default(0.45),
  activeColor: z.string().optional(),
  emphasisColor: z.string().optional().describe("defaults to the Reel accent"),
  emphasisRules: z.array(emphasisRuleSchema).default([]),
  emphasisWords: z.array(z.number().int()).default([]).describe("word indices the Director wants emphasised"),
  emphasisStyle: z.enum(["color", "scale", "underline", "box", "glow"]).default("color"),
  background: z.enum(["none", "shadow", "stroke", "pill", "box"]).default("shadow"),
  backgroundColor: z.string().default("rgba(5,7,12,0.78)"),
  enter: z.enum(["none", "fade", "pop", "rise", "slide", "blur"]).default("pop"),
  wordEnter: z.enum(["none", "fade", "pop", "rise"]).default("none"),
  hideInScenes: z.array(z.string()).default([]).describe("scene ids during which captions are hidden"),
  leadMs: z.number().default(0).describe("show words slightly early (negative = late)"),
});
export type CaptionTreatment = z.infer<typeof captionTreatmentSchema>;

// ---------- EDL ----------
export const transitionSchema = z.object({
  type: z.enum(["cut", "fade", "slide-up", "slide-left", "slide-right", "wipe", "zoom", "blur", "glitch"]).default("cut"),
  frames: z.number().int().min(0).max(30).default(8),
});

export const sceneSchema = z.object({
  id: z.string(),
  beat: z.string().optional().describe("brief beat id this scene serves"),
  wordStart: z.number().int().min(0),
  wordEnd: z.number().int().min(0).describe("inclusive; scene lasts until the next scene starts unless holdMs is set"),
  startOffsetMs: z.number().default(0),
  holdMs: z.number().optional(),
  component: z.string().describe("key in engine/registry.tsx"),
  props: z.record(z.string(), z.any()).default({}),
  transitionIn: transitionSchema.default({ type: "cut", frames: 0 }),
  layer: z.enum(["main", "overlay"]).default("main"),
  rationale: z.string().min(1).describe("why this visual helps clarity/retention here"),
});
export type Scene = z.infer<typeof sceneSchema>;

export const sfxCueSchema = z.object({
  sfx: z.string().describe("id from library/sfx_index.json"),
  atWord: z.number().int().optional(),
  atSec: z.number().optional(),
  offsetMs: z.number().default(0),
  gainDb: z.number().default(-16),
  reason: z.string().optional(),
});

export const lookSchema = z.object({
  accent: z.string(),
  accent2: z.string().optional(),
  pairing: z.string(),
  personality: z.enum(["crisp", "calm", "playful", "cinematic"]),
  background: z.enum(["night", "grid", "spotlight", "noise", "solid"]).default("night"),
  watermark: z.enum(["none", "wordmark", "logo"]).default("wordmark"),
});

export const edlSchema = z.object({
  slug: z.string(),
  version: z.number().int().default(1),
  look: lookSchema,
  captions: captionTreatmentSchema,
  scenes: z.array(sceneSchema),
  sfx: z.array(sfxCueSchema).default([]),
  music: z.object({ file: z.string(), gainDb: z.number().default(-24), duck: z.boolean().default(true) }).optional(),
  iconPack: z.string().optional().describe("path under public/, default reels/<slug>/icons.json"),
  tailSec: z.number().default(0.8),
});
export type Edl = z.infer<typeof edlSchema>;
export type Look = z.infer<typeof lookSchema>;

// ---------- brief (Director's understanding; not used for rendering) ----------
export const briefSchema = z.object({
  slug: z.string(),
  reelType: z.string(),
  coreTakeaway: z.string(),
  audienceAssumption: z.string(),
  hook: z.object({ wordStart: z.number().int(), wordEnd: z.number().int(), why: z.string() }),
  beats: z.array(z.object({
    id: z.string(), intent: z.string(), wordStart: z.number().int(), wordEnd: z.number().int(), summary: z.string(),
  })),
  keyTerms: z.array(z.string()),
  emphasisWords: z.array(z.number().int()),
  retentionRisks: z.array(z.string()),
  lookRationale: z.string(),
});
export type Brief = z.infer<typeof briefSchema>;
