// Shared motion vocabulary. Primitives call these instead of inventing their own easing,
// so a Reel's chosen "personality" changes the feel everywhere at once.
import type { CSSProperties } from "react";
import { interpolate, spring } from "remotion";
import { tokens, type PersonalityKey, type SpringKey } from "../brand";

export type EnterKind = "none" | "fade" | "pop" | "rise" | "slide" | "slide-left" | "slide-right" | "blur" | "zoom" | "drop";

export const springConfig = (key: SpringKey) => tokens.motion.springs[key];

export const personality = (key: PersonalityKey) => tokens.motion.personalities[key];

/** 0 → 1 progress of an entrance that starts at `startFrame`. */
export const enterProgress = (frame: number, fps: number, startFrame: number, springKey: SpringKey = "snappy") =>
  spring({ frame: frame - startFrame, fps, config: springConfig(springKey) });

/** Style for an element entering with progress p (0..1). */
export const enterStyle = (kind: EnterKind, p: number, distance = 60): CSSProperties => {
  const o = Math.min(1, Math.max(0, p));
  switch (kind) {
    case "none": return {};
    case "fade": return { opacity: o };
    case "pop": return { opacity: o, transform: `scale(${interpolate(p, [0, 1], [0.6, 1])})` };
    case "rise": return { opacity: o, transform: `translateY(${interpolate(p, [0, 1], [distance, 0])}px)` };
    case "drop": return { opacity: o, transform: `translateY(${interpolate(p, [0, 1], [-distance, 0])}px)` };
    case "slide":
    case "slide-left": return { opacity: o, transform: `translateX(${interpolate(p, [0, 1], [distance * 2, 0])}px)` };
    case "slide-right": return { opacity: o, transform: `translateX(${interpolate(p, [0, 1], [-distance * 2, 0])}px)` };
    case "blur": return { opacity: o, filter: `blur(${interpolate(p, [0, 1], [18, 0])}px)` };
    case "zoom": return { opacity: o, transform: `scale(${interpolate(p, [0, 1], [1.25, 1])})` };
  }
};

/** Convenience: entrance style for an element appearing at startFrame. */
export const useEnter = (
  frame: number, fps: number, startFrame: number, kind: EnterKind = "rise", springKey: SpringKey = "snappy",
): CSSProperties => enterStyle(kind, enterProgress(frame, fps, startFrame, springKey));

/** Gentle continuous float for idle elements (keeps static frames alive without distraction). */
export const idleFloat = (frame: number, amplitude = 6, periodFrames = 90) =>
  Math.sin((frame / periodFrames) * Math.PI * 2) * amplitude;

/** Slow camera push used on static scenes (1.0 → 1+amount over the scene). */
export const cameraPush = (frame: number, durationFrames: number, amount = 0.06) =>
  interpolate(frame, [0, Math.max(1, durationFrames)], [1, 1 + amount], { extrapolateRight: "clamp" });
