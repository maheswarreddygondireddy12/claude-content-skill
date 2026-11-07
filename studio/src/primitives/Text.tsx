// Typographic building blocks: keyword cards, build-up lists, counters.
import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { core, fontFamily } from "../brand";
import { Icon } from "./Icon";
import { enterProgress, enterStyle, type EnterKind } from "./motion";

export const KeywordCard: React.FC<{
  text: string; sub?: string; accent?: string; fontKey?: string; size?: number; enter?: EnterKind; appearAt?: number; icon?: string;
}> = ({ text, sub, accent = core.glow, fontKey = "spaceGrotesk", size = 120, enter = "pop", appearAt = 0, icon }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < appearAt) return null;
  const p = enterProgress(frame, fps, appearAt);
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 24, ...enterStyle(enter, p) }}>
      {icon && <Icon name={icon} size={size * 1.3} color={accent} />}
      <div style={{ fontFamily: fontFamily(fontKey), fontWeight: 800, fontSize: size, color: core.white, textAlign: "center", lineHeight: 1.05,
        textShadow: `0 0 50px ${accent}55` }}>{text}</div>
      {sub && <div style={{ fontFamily: fontFamily("inter"), fontSize: size * 0.36, color: accent, fontWeight: 600, textAlign: "center" }}>{sub}</div>}
    </div>
  );
};

export type ListItem = { text: string; icon?: string; at: number; state?: "neutral" | "good" | "bad" };

/** Items appear on their `at` frame (usually the word that names them). */
export const BuildList: React.FC<{ items: ListItem[]; accent?: string; fontKey?: string; size?: number; width?: number; enter?: EnterKind }> = ({
  items, accent = core.glow, fontKey = "inter", size = 54, width = 860, enter = "slide-left",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div style={{ width, display: "flex", flexDirection: "column", gap: size * 0.45 }}>
      {items.map((it, k) => {
        if (frame < it.at) return null;
        const c = it.state === "good" ? "#34D399" : it.state === "bad" ? "#F87171" : accent;
        return (
          <div key={k} style={{ display: "flex", alignItems: "center", gap: size * 0.45, padding: `${size * 0.32}px ${size * 0.5}px`,
            borderRadius: size * 0.4, background: core.navy, border: `2px solid ${core.line}`, ...enterStyle(enter, enterProgress(frame, fps, it.at), 30) }}>
            {it.icon ? <Icon name={it.icon} size={size * 1.1} color={c} /> :
              <div style={{ width: size * 0.32, height: size * 0.32, borderRadius: "50%", background: c, flexShrink: 0 }} />}
            <div style={{ fontFamily: fontFamily(fontKey), fontSize: size, fontWeight: 650, color: core.white }}>{it.text}</div>
          </div>
        );
      })}
    </div>
  );
};

export const Counter: React.FC<{
  from?: number; to: number; startFrame?: number; frames?: number; prefix?: string; suffix?: string; decimals?: number;
  fontKey?: string; size?: number; color?: string;
}> = ({ from = 0, to, startFrame = 0, frames = 40, prefix = "", suffix = "", decimals = 0, fontKey = "spaceGrotesk", size = 160, color = core.white }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - startFrame, fps, durationInFrames: frames, config: { damping: 200 } });
  const value = interpolate(p, [0, 1], [from, to]);
  return (
    <div style={{ fontFamily: fontFamily(fontKey), fontWeight: 800, fontSize: size, color, fontVariantNumeric: "tabular-nums" }}>
      {prefix}{value.toFixed(decimals)}{suffix}
    </div>
  );
};
