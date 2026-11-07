// Caption ENGINE. Visual style is entirely driven by the per-Reel CaptionTreatment,
// timing by timing.json. Different Reels => different treatments, same engine.
import React, { useMemo } from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { core, fontFamily, tokens, type PersonalityKey } from "../brand";
import type { CaptionTreatment, Timing, TimingWord } from "../schema";
import { enterStyle, personality } from "../primitives/motion";
import { applyCase, buildChunks, isEmphasised, type Chunk } from "./chunk";

type Props = {
  timing: Timing;
  treatment: CaptionTreatment;
  accent: string;
  personalityKey?: PersonalityKey;
  /** seconds added to the composition time (lets a clip show captions from mid-VO) */
  timeOffsetSec?: number;
  hidden?: boolean;
};

const KEYWORD_HOLD = 1.2;
const MAX_HOLD_AFTER_END = 0.9;

export const Captions: React.FC<Props> = ({ timing, treatment: t, accent, personalityKey = "crisp", timeOffsetSec = 0, hidden }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const chunks = useMemo(() => buildChunks(timing, t), [timing, t]);
  const keywords = useMemo(() => timing.words.filter((w) => isEmphasised(w, t)), [timing, t]);
  if (!t.enabled || hidden) return null;

  const now = frame / fps + timeOffsetSec + t.leadMs / 1000;
  const springKey = personality(personalityKey).spring as keyof typeof tokens.motion.springs;
  const emphasisColor = t.emphasisColor ?? accent;

  let visible: { words: TimingWord[]; start: number } | null = null;
  if (t.mode === "keyword") {
    const k = findLast(keywords, (w) => w.start <= now);
    if (k) {
      const next = keywords[keywords.indexOf(k) + 1];
      const until = Math.min(next ? next.start : Infinity, k.start + KEYWORD_HOLD);
      if (now < until) visible = { words: [k], start: k.start };
    }
  } else {
    const c = findLast(chunks, (ch) => ch.start <= now);
    if (c && now < chunkUntil(chunks, c)) visible = { words: c.words, start: c.start };
  }
  if (!visible) return null;

  const p = spring({ frame: Math.round((now - visible.start) * fps), fps, config: tokens.motion.springs[springKey] });
  const blockStyle = enterStyle(t.enter, p, 40);
  const pill = t.background === "pill";

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: (1080 - t.maxWidth) / 2,
          width: t.maxWidth,
          top: t.y,
          transform: "translateY(-50%)",
          display: "flex",
          justifyContent: t.align === "left" ? "flex-start" : t.align === "right" ? "flex-end" : "center",
        }}
      >
        <div
          style={{
            ...blockStyle,
            display: "flex",
            flexWrap: "wrap",
            justifyContent: t.align === "left" ? "flex-start" : t.align === "right" ? "flex-end" : "center",
            columnGap: t.size * 0.28,
            rowGap: t.size * 0.08,
            padding: pill ? `${t.size * 0.22}px ${t.size * 0.45}px` : 0,
            borderRadius: pill ? t.size * 0.5 : 0,
            background: pill ? t.backgroundColor : "transparent",
            fontFamily: fontFamily(t.family),
            fontWeight: t.weight,
            fontSize: t.size,
            letterSpacing: t.letterSpacing,
            lineHeight: 1.12,
            textAlign: t.align,
          }}
        >
          {visible.words.map((w) => (
            <Word key={w.i} w={w} t={t} now={now} fps={fps} emphasisColor={emphasisColor} springKey={springKey} />
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Word: React.FC<{ w: TimingWord; t: CaptionTreatment; now: number; fps: number; emphasisColor: string; springKey: keyof typeof tokens.motion.springs }> = ({
  w, t, now, fps, emphasisColor, springKey,
}) => {
  const spoken = now >= w.start;
  const active = spoken && now < w.end + 0.05;
  if (t.mode === "build" && !spoken) return null;

  const emph = isEmphasised(w, t);
  let color = t.color;
  let opacity = 1;
  if (t.mode === "karaoke") {
    if (!spoken) opacity = t.futureOpacity;
    else if (active) color = t.activeColor ?? emphasisColor;
    else color = t.pastColor ?? t.color;
  }
  if (emph && t.emphasisStyle === "color") color = emphasisColor;

  const wp = spring({ frame: Math.round((now - w.start) * fps), fps, config: tokens.motion.springs[springKey] });
  const wordEnter = spoken && t.wordEnter !== "none" ? enterStyle(t.wordEnter, wp, 18) : {};
  const scale = emph && t.emphasisStyle === "scale" ? interpolate(wp, [0, 1], [1, 1.14]) : 1;

  const style: React.CSSProperties = {
    color,
    opacity,
    display: "inline-block",
    position: "relative",
    whiteSpace: "nowrap",
    ...wordEnter,
    transform: `${wordEnter.transform ?? ""} scale(${scale})`,
  };
  if (t.background === "shadow") style.textShadow = `0 4px 18px rgba(0,0,0,0.85), 0 2px 4px rgba(0,0,0,0.9)`;
  if (t.background === "stroke") {
    style.WebkitTextStroke = `${Math.max(4, t.size * 0.09)}px ${core.ink}`;
    style.paintOrder = "stroke fill";
  }
  if (t.background === "box") {
    style.background = t.backgroundColor;
    style.padding = `0 ${t.size * 0.18}px`;
    style.borderRadius = t.size * 0.16;
  }
  if (emph && t.emphasisStyle === "glow") style.textShadow = `0 0 ${t.size * 0.35}px ${emphasisColor}, 0 0 4px ${emphasisColor}`;
  if (emph && t.emphasisStyle === "box") {
    style.background = emphasisColor;
    style.color = core.ink;
    style.padding = `0 ${t.size * 0.16}px`;
    style.borderRadius = t.size * 0.14;
  }

  return (
    <span style={style}>
      {applyCase(w.display, t)}
      {emph && t.emphasisStyle === "underline" && (
        <span
          style={{
            position: "absolute", left: 0, bottom: -t.size * 0.06, height: t.size * 0.1,
            width: `${Math.min(1, wp) * 100}%`, background: emphasisColor, borderRadius: 4,
          }}
        />
      )}
    </span>
  );
};

const chunkUntil = (chunks: Chunk[], c: Chunk) => {
  const next = chunks[c.index + 1];
  return Math.min(next ? next.start : Infinity, c.end + MAX_HOLD_AFTER_END);
};

function findLast<T>(arr: T[], pred: (x: T) => boolean): T | undefined {
  for (let k = arr.length - 1; k >= 0; k--) if (pred(arr[k])) return arr[k];
  return undefined;
}
