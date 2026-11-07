// Data-driven Reel: timing.json + edl.json (both under public/reels/<slug>/) -> video.
// The engine has no opinion about look or sequence; it only executes the Director's EDL.
import React, { useMemo } from "react";
import { AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame, type CalculateMetadataFunction } from "remotion";
import { z } from "zod";
import { FPS, accent as accentColor, pairing } from "../brand";
import { ensureFonts } from "../fonts";
import { Captions } from "../captions/Captions";
import { edlSchema, type Edl, type Scene, type Timing } from "../schema";
import { Background, SafeZoneGuide, Watermark } from "../primitives/Brand";
import { IconPackProvider } from "../primitives/Icon";
import { Sfx } from "../primitives/Media";
import { enterStyle, type EnterKind } from "../primitives/motion";
import { REGISTRY, type SceneCtx } from "./registry";
import { fetchJson, totalFrames, wordEndFrame, wordStartFrame } from "./timing";

export const reelPropsSchema = z.object({
  slug: z.string(),
  showSafeZones: z.boolean().default(false),
});
type ReelProps = z.infer<typeof reelPropsSchema> & { timing?: Timing; edl?: Edl; voFile?: string };

export const calculateReelMetadata: CalculateMetadataFunction<ReelProps> = async ({ props }) => {
  const base = `reels/${props.slug}`;
  const [timing, rawEdl, manifest] = await Promise.all([
    fetchJson<Timing>(staticFile(`${base}/timing.json`)),
    fetchJson<unknown>(staticFile(`${base}/edl.json`)),
    fetchJson<{ vo: string }>(staticFile(`${base}/manifest.json`)),
  ]);
  const edl = edlSchema.parse(rawEdl);
  return { durationInFrames: totalFrames(timing, FPS, edl.tailSec), props: { ...props, timing, edl, voFile: manifest.vo } };
};

type Placed = { scene: Scene; from: number; duration: number };

const placeScenes = (edl: Edl, timing: Timing, total: number): Placed[] => {
  const main = edl.scenes.filter((s) => s.layer === "main").sort((a, b) => a.wordStart - b.wordStart);
  const placed: Placed[] = [];
  const startOf = (s: Scene) => (s.wordStart === 0 && s.startOffsetMs <= 0 ? 0 : wordStartFrame(timing, s.wordStart, FPS, s.startOffsetMs));
  main.forEach((s, k) => {
    const from = startOf(s);
    const next = main[k + 1];
    const end = s.holdMs !== undefined ? wordEndFrame(timing, s.wordEnd, FPS) + Math.round((s.holdMs / 1000) * FPS)
      : next ? startOf(next) : total;
    placed.push({ scene: s, from, duration: Math.max(1, end - from) });
  });
  for (const s of edl.scenes.filter((x) => x.layer === "overlay")) {
    const from = startOf(s);
    const end = wordEndFrame(timing, s.wordEnd, FPS) + Math.round(((s.holdMs ?? 300) / 1000) * FPS);
    placed.push({ scene: s, from, duration: Math.max(1, end - from) });
  }
  return placed;
};

/** Converts every "<name>Word" numeric prop into "<name>" frames relative to the scene start. */
const resolveWordProps = (value: any, timing: Timing, sceneFrom: number): any => {
  if (Array.isArray(value)) return value.map((v) => resolveWordProps(v, timing, sceneFrom));
  if (value && typeof value === "object") {
    const out: Record<string, any> = {};
    for (const [k, v] of Object.entries(value)) {
      if (k.endsWith("Word") && typeof v === "number" && k.length > 4) {
        out[k.slice(0, -4)] = Math.max(0, wordStartFrame(timing, v, FPS) - sceneFrom);
      } else out[k] = resolveWordProps(v, timing, sceneFrom);
    }
    return out;
  }
  return value;
};

const TRANSITION_KIND: Record<string, EnterKind> = {
  fade: "fade", "slide-up": "rise", "slide-left": "slide-left", "slide-right": "slide-right", zoom: "zoom", blur: "blur", wipe: "fade", glitch: "fade",
};

const SceneFrame: React.FC<{ placed: Placed; ctx: SceneCtx; timing: Timing }> = ({ placed, ctx, timing }) => {
  const { scene } = placed;
  const Comp = REGISTRY[scene.component];
  const props = useMemo(() => resolveWordProps(scene.props, timing, placed.from), [scene.props, timing, placed.from]);
  return (
    <TransitionIn type={scene.transitionIn.type} frames={scene.transitionIn.frames}>
      {Comp ? <Comp props={props} ctx={{ ...ctx, durationInFrames: placed.duration }} />
        : <AbsoluteFill style={{ color: "#F87171", fontSize: 40, padding: 80 }}>Unknown scene component “{scene.component}”</AbsoluteFill>}
    </TransitionIn>
  );
};

const TransitionIn: React.FC<{ type: string; frames: number; children: React.ReactNode }> = ({ type, frames, children }) => {
  const frame = useCurrentFrame();
  if (type === "cut" || frames <= 0) return <AbsoluteFill>{children}</AbsoluteFill>;
  const p = interpolate(frame, [0, frames], [0, 1], { extrapolateRight: "clamp" });
  if (type === "wipe") return <AbsoluteFill style={{ clipPath: `inset(0 ${100 - p * 100}% 0 0)` }}>{children}</AbsoluteFill>;
  if (type === "glitch") {
    const jitter = p < 1 ? Math.sin(frame * 9) * 18 * (1 - p) : 0;
    return <AbsoluteFill style={{ transform: `translateX(${jitter}px)`, filter: p < 1 ? `hue-rotate(${(1 - p) * 90}deg)` : undefined }}>{children}</AbsoluteFill>;
  }
  return <AbsoluteFill style={enterStyle(TRANSITION_KIND[type] ?? "fade", p, 80)}>{children}</AbsoluteFill>;
};


export const ReelComposition: React.FC<ReelProps> = ({ slug, timing, edl, voFile, showSafeZones }) => {
  ensureFonts();
  if (!timing || !edl || !voFile) return null;
  const total = totalFrames(timing, FPS, edl.tailSec);
  const fonts = pairing(edl.look.pairing);
  const accent = accentColor(edl.look.accent);
  const ctx: SceneCtx = { accent, accent2: edl.look.accent2 ? accentColor(edl.look.accent2) : undefined, fonts, durationInFrames: total };
  const placed = placeScenes(edl, timing, total);
  const hiddenRanges = placed.filter((p) => edl.captions.hideInScenes.includes(p.scene.id)).map((p) => [p.from, p.from + p.duration]);

  return (
    <IconPackProvider packs={[edl.iconPack ?? `reels/${slug}/icons.json`, "brand/icons.json"]}>
      <AbsoluteFill>
        <Background variant={edl.look.background} accent={accent} />
        {placed.map((p) => (
          <Sequence key={p.scene.id} from={p.from} durationInFrames={p.duration} name={`${p.scene.id} · ${p.scene.component}`}>
            <SceneFrame placed={p} ctx={ctx} timing={timing} />
          </Sequence>
        ))}
        <Watermark kind={edl.look.watermark} />
        <CaptionLayer timing={timing} edl={edl} accent={accent} hiddenRanges={hiddenRanges} />
        <Audio src={staticFile(`reels/${slug}/${voFile}`)} />
        {edl.music && <Audio src={staticFile(edl.music.file)} volume={Math.pow(10, edl.music.gainDb / 20)} loop />}
        {edl.sfx.map((cue, k) => {
          const at = cue.atWord !== undefined ? wordStartFrame(timing, cue.atWord, FPS, cue.offsetMs)
            : Math.round(((cue.atSec ?? 0) + cue.offsetMs / 1000) * FPS);
          return <Sequence key={`sfx${k}`} from={Math.max(0, at)} durationInFrames={FPS * 4} name={`sfx ${cue.sfx}`}><Sfx id={cue.sfx} gainDb={cue.gainDb} /></Sequence>;
        })}
        {showSafeZones && <SafeZoneGuide />}
      </AbsoluteFill>
    </IconPackProvider>
  );
};

const CaptionLayer: React.FC<{ timing: Timing; edl: Edl; accent: string; hiddenRanges: number[][] }> = ({ timing, edl, accent, hiddenRanges }) => {
  const frame = useCurrentFrame();
  const hidden = hiddenRanges.some(([a, b]) => frame >= a && frame < b);
  return <Captions timing={timing} treatment={edl.captions} accent={accent} personalityKey={edl.look.personality} hidden={hidden} />;
};
