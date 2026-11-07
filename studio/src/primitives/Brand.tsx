// Backgrounds, wordmark, logo watermark and the safe-zone debug overlay.
import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { noise2D } from "@remotion/noise";
import { core, fontFamily, safe } from "../brand";

export type BackgroundVariant = "night" | "grid" | "spotlight" | "noise" | "solid";

/** Subtle animated backgrounds; motion is slow so it never competes with content. */
export const Background: React.FC<{ variant?: BackgroundVariant; accent?: string }> = ({ variant = "night", accent = core.glow }) => {
  const frame = useCurrentFrame();
  const drift = noise2D("bg", frame / 240, 0) * 60;
  if (variant === "solid") return <AbsoluteFill style={{ background: core.ink }} />;
  return (
    <AbsoluteFill style={{ background: `linear-gradient(180deg, ${core.ink} 0%, ${core.night} 55%, ${core.navy} 100%)` }}>
      {(variant === "night" || variant === "spotlight") && (
        <div style={{ position: "absolute", left: 540 - 700 + drift, top: variant === "spotlight" ? 300 : 900, width: 1400, height: 1400,
          borderRadius: "50%", background: `radial-gradient(circle, ${accent}2e 0%, transparent 62%)` }} />
      )}
      {variant === "grid" && (
        <AbsoluteFill style={{ backgroundImage: `linear-gradient(${core.line}55 2px, transparent 2px), linear-gradient(90deg, ${core.line}55 2px, transparent 2px)`,
          backgroundSize: "90px 90px", backgroundPosition: `0 ${frame * 0.4}px`,
          maskImage: "radial-gradient(circle at 50% 45%, black 20%, transparent 75%)" }} />
      )}
      {variant === "noise" && Array.from({ length: 26 }).map((_, k) => {
        const x = 540 + noise2D("x" + k, frame / 300, k) * 600, y = 960 + noise2D("y" + k, frame / 300, k) * 1000;
        return <div key={k} style={{ position: "absolute", left: x, top: y, width: 6, height: 6, borderRadius: 3, background: accent, opacity: 0.35 }} />;
      })}
    </AbsoluteFill>
  );
};

/** Generic typographic mark, optional </> glyph. Scales to any size. */
export const Wordmark: React.FC<{ size?: number; glyph?: boolean; fontKey?: string; accent?: string }> = ({
  size = 90, glyph = true, fontKey = "spaceGrotesk", accent = core.glow,
}) => (
  <div style={{ display: "flex", alignItems: "center", gap: size * 0.3, fontFamily: fontFamily(fontKey), fontWeight: 700, fontSize: size, lineHeight: 1 }}>
    {glyph && (
      <div style={{ fontFamily: fontFamily("jetbrainsMono"), fontSize: size * 0.62, color: accent, border: `${Math.max(2, size * 0.04)}px solid ${accent}`,
        borderRadius: size * 0.18, padding: `${size * 0.06}px ${size * 0.14}px`, boxShadow: `0 0 ${size * 0.3}px ${accent}55` }}>{"</>"}</div>
    )}
    <span style={{ color: core.white }}>Video</span>
    <span style={{ color: accent, marginLeft: -size * 0.28 }}>Studio</span>
  </div>
);

/** Small corner watermark (generic wordmark or optional project logo). */
export const Watermark: React.FC<{ kind: "none" | "wordmark" | "logo"; opacity?: number }> = ({ kind, opacity = 0.75 }) => {
  if (kind === "none") return null;
  return (
    <div style={{ position: "absolute", left: safe.side, top: safe.top - 120, opacity }}>
      {kind === "logo"
        ? <Wordmark size={34} />
        : <Wordmark size={34} />}
    </div>
  );
};

/** Debug overlay showing vertical short-form UI zones; never enabled in final renders. */
export const SafeZoneGuide: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: safe.top, background: "rgba(248,113,113,0.18)" }} />
    <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: safe.bottomUi, background: "rgba(248,113,113,0.18)" }} />
    <div style={{ position: "absolute", right: 0, top: safe.top, bottom: safe.bottomUi, width: safe.rightRail, background: "rgba(251,191,36,0.15)" }} />
    <div style={{ position: "absolute", left: safe.content.x, top: safe.content.y, width: safe.content.width, height: safe.content.height,
      border: "3px dashed rgba(52,211,153,0.8)" }} />
  </AbsoluteFill>
);
