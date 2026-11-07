// Code-native micro-animations (no Lottie dependency): small, on-brand, frame-accurate.
// All take `from` = frame (within the current Sequence) at which the animation starts.
import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { evolvePath } from "@remotion/paths";
import { core, semantic } from "../brand";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const useDraw = (from: number, frames: number) => {
  const frame = useCurrentFrame();
  return interpolate(frame - from, [0, frames], [0, 1], clamp);
};

export const Checkmark: React.FC<{ size?: number; color?: string; from?: number; ring?: boolean }> = ({
  size = 160, color = semantic.success, from = 0, ring = true,
}) => {
  const p = useDraw(from, 16);
  const tick = "M 30 52 L 45 67 L 72 36";
  const circle = "M 50 6 A 44 44 0 1 1 49.99 6";
  const { strokeDasharray: d1, strokeDashoffset: o1 } = evolvePath(Math.min(1, p * 1.6), circle);
  const { strokeDasharray: d2, strokeDashoffset: o2 } = evolvePath(Math.max(0, p * 1.6 - 0.6), tick);
  return (
    <svg width={size} height={size} viewBox="0 0 100 100">
      {ring && <path d={circle} fill="none" stroke={color} strokeWidth={6} strokeDasharray={d1} strokeDashoffset={o1} strokeLinecap="round" />}
      <path d={tick} fill="none" stroke={color} strokeWidth={9} strokeDasharray={d2} strokeDashoffset={o2} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
};

export const Cross: React.FC<{ size?: number; color?: string; from?: number }> = ({ size = 160, color = semantic.error, from = 0 }) => {
  const p = useDraw(from, 14);
  const a = evolvePath(Math.min(1, p * 2), "M 28 28 L 72 72");
  const b = evolvePath(Math.max(0, p * 2 - 1), "M 72 28 L 28 72");
  return (
    <svg width={size} height={size} viewBox="0 0 100 100">
      <path d="M 28 28 L 72 72" stroke={color} strokeWidth={10} strokeLinecap="round" strokeDasharray={a.strokeDasharray} strokeDashoffset={a.strokeDashoffset} />
      <path d="M 72 28 L 28 72" stroke={color} strokeWidth={10} strokeLinecap="round" strokeDasharray={b.strokeDasharray} strokeDashoffset={b.strokeDashoffset} />
    </svg>
  );
};

export const Pulse: React.FC<{ size?: number; color?: string; from?: number; periodFrames?: number; children?: React.ReactNode }> = ({
  size = 140, color = core.glow, from = 0, periodFrames = 36, children,
}) => {
  const frame = useCurrentFrame();
  const t = Math.max(0, frame - from);
  const rings = [0, 0.5].map((phase) => ((t / periodFrames + phase) % 1));
  return (
    <div style={{ position: "relative", width: size, height: size, display: "flex", alignItems: "center", justifyContent: "center" }}>
      {frame >= from && rings.map((r, k) => (
        <div key={k} style={{ position: "absolute", inset: 0, borderRadius: "50%", border: `4px solid ${color}`,
          transform: `scale(${0.6 + r * 0.9})`, opacity: 1 - r }} />
      ))}
      {children}
    </div>
  );
};

export const Spinner: React.FC<{ size?: number; color?: string }> = ({ size = 90, color = core.glow }) => {
  const frame = useCurrentFrame();
  return (
    <svg width={size} height={size} viewBox="0 0 50 50" style={{ transform: `rotate(${frame * 12}deg)` }}>
      <circle cx="25" cy="25" r="20" fill="none" stroke={core.line} strokeWidth="5" />
      <circle cx="25" cy="25" r="20" fill="none" stroke={color} strokeWidth="5" strokeDasharray="40 126" strokeLinecap="round" />
    </svg>
  );
};

export const ProgressBar: React.FC<{ width?: number; height?: number; color?: string; from?: number; frames?: number; to?: number; label?: boolean }> = ({
  width = 700, height = 28, color = core.glow, from = 0, frames = 45, to = 1, label = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - from, fps, durationInFrames: frames, config: { damping: 200 } }) * to;
  return (
    <div style={{ width, height, borderRadius: height, background: core.line, overflow: "hidden", position: "relative" }}>
      <div style={{ width: `${p * 100}%`, height: "100%", borderRadius: height, background: color, boxShadow: `0 0 24px ${color}` }} />
      {label && <div style={{ position: "absolute", right: 12, top: 0, lineHeight: `${height}px`, fontSize: height * 0.7, color: core.white }}>{Math.round(p * 100)}%</div>}
    </div>
  );
};

export const TypingCursor: React.FC<{ height?: number; color?: string }> = ({ height = 60, color = core.glow }) => {
  const frame = useCurrentFrame();
  return <span style={{ display: "inline-block", width: height * 0.12, height, background: color, opacity: Math.floor(frame / 15) % 2 ? 0 : 1, verticalAlign: "middle" }} />;
};

/** Marker-style highlight that sweeps behind text. */
export const HighlightSweep: React.FC<{ color?: string; from?: number; frames?: number; children: React.ReactNode }> = ({
  color = core.glow, from = 0, frames = 10, children,
}) => {
  const p = useDraw(from, frames);
  return (
    <span style={{ position: "relative", display: "inline-block", padding: "0 0.15em" }}>
      <span style={{ position: "absolute", left: 0, bottom: "0.08em", height: "0.42em", width: `${p * 100}%`, background: color, opacity: 0.55, borderRadius: 6 }} />
      <span style={{ position: "relative" }}>{children}</span>
    </span>
  );
};

export const Ripple: React.FC<{ x: number; y: number; color?: string; from?: number }> = ({ x, y, color = core.white, from = 0 }) => {
  const p = useDraw(from, 18);
  if (p <= 0 || p >= 1) return null;
  return <div style={{ position: "absolute", left: x - 60, top: y - 60, width: 120, height: 120, borderRadius: "50%",
    border: `5px solid ${color}`, transform: `scale(${0.2 + p})`, opacity: 1 - p }} />;
};
