// Information-state primitives.
// FieldCard: what someone knows vs. doesn't know (forms, profiles, "context" panels).
// ContextSorter: a pool of items where only the relevant ones flow into a target.
import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { core, fontFamily, semantic } from "../brand";
import { Icon } from "./Icon";
import { enterProgress, enterStyle } from "./motion";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export type FieldRow = { label: string; state: "known" | "unknown"; at: number; value?: string };

export const FieldCard: React.FC<{
  title: string; icon?: string; rows: FieldRow[]; accent?: string; unknownColor?: string; alertAt?: number;
  width?: number; fontKey?: string; appearAt?: number; size?: number;
}> = ({ title, icon, rows, accent = core.glow, unknownColor = semantic.error, alertAt, width = 860, fontKey = "inter", appearAt = 0, size = 46 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < appearAt) return null;
  const alert = alertAt !== undefined && frame >= alertAt;
  const alertPulse = alert ? 0.5 + 0.5 * Math.sin(((frame - (alertAt ?? 0)) / 10) * Math.PI) : 0;
  return (
    <div style={{ width, borderRadius: 36, padding: "34px 38px", background: `linear-gradient(165deg, ${core.steel}, ${core.navy})`,
      border: `2px solid ${core.line}`, boxShadow: "0 30px 80px rgba(0,0,0,0.5)", ...enterStyle("rise", enterProgress(frame, fps, appearAt, "smooth")) }}>
      <div style={{ display: "flex", alignItems: "center", gap: 22, marginBottom: 26 }}>
        {icon && <Icon name={icon} size={size * 2} />}
        <div style={{ fontFamily: fontFamily(fontKey), fontWeight: 700, fontSize: size * 0.95, color: core.white }}>{title}</div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: size * 0.32 }}>
        {rows.filter((r) => frame >= r.at).map((r, k) => {
          const p = enterProgress(frame, fps, r.at, "snappy");
          const known = r.state === "known";
          const c = known ? semantic.success : unknownColor;
          return (
            <div key={k} style={{ display: "flex", alignItems: "center", gap: size * 0.45, padding: `${size * 0.26}px ${size * 0.4}px`, borderRadius: size * 0.4,
              background: known ? `${accent}1f` : `${unknownColor}${Math.round(0x10 + alertPulse * 0x28).toString(16).padStart(2, "0")}`,
              border: `2px ${known ? "solid" : "dashed"} ${known ? `${accent}66` : `${unknownColor}${alert ? "cc" : "66"}`}`,
              ...enterStyle("slide-left", p, 24) }}>
              <div style={{ width: size * 1.05, height: size * 1.05, borderRadius: "50%", flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center",
                background: `${c}26`, color: c, fontFamily: fontFamily("spaceGrotesk"), fontWeight: 800, fontSize: size * 0.7 }}>{known ? "✓" : "?"}</div>
              <div style={{ fontFamily: fontFamily(fontKey), fontSize: size, fontWeight: known ? 700 : 600, color: known ? core.white : `${core.white}cc` }}>{r.label}</div>
              {r.value && <div style={{ marginLeft: "auto", fontFamily: fontFamily(fontKey), fontSize: size * 0.8, color: accent }}>{r.value}</div>}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export type SortItem = { label: string; icon?: string; at: number; relevant: boolean };

/** Items appear in a grid; at `selectAt` relevant ones fly into the target, irrelevant ones are filtered out. */
export const ContextSorter: React.FC<{
  items: SortItem[]; target: { icon: string; label?: string }; selectAt: number; accent?: string; fontKey?: string;
  top?: number; targetY?: number; size?: number; rejectColor?: string; itemWidth?: number; centerX?: number;
}> = ({ items, target, selectAt, accent = core.glow, fontKey = "inter", top = 300, targetY = 1130, size = 36, rejectColor = semantic.error, itemWidth = 380, centerX = 530 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const colW = itemWidth, rowH = size * 2.7, cols = 2;
  const targetPulse = frame >= selectAt ? spring({ frame: frame - selectAt - 8, fps, config: { damping: 9, stiffness: 160 } }) : 0;
  let relevantIdx = 0;
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      {items.map((it, k) => {
        if (frame < it.at) return null;
        const col = k % cols, row = Math.floor(k / cols);
        const x0 = centerX + (col === 0 ? -colW / 2 - 10 : colW / 2 + 10), y0 = top + row * rowH;
        const appear = enterProgress(frame, fps, it.at, "snappy");
        const order = it.relevant ? relevantIdx++ : 0;
        const sel = spring({ frame: frame - selectAt - order * 3, fps, config: { damping: 22, stiffness: 120 } });
        const x = it.relevant ? interpolate(sel, [0, 1], [x0, centerX]) : x0;
        const y = it.relevant ? interpolate(sel, [0, 1], [y0, targetY]) : y0;
        const scale = it.relevant ? interpolate(sel, [0, 0.8, 1], [1, 0.55, 0.2], clamp) : 1;
        const opacity = it.relevant ? interpolate(sel, [0.75, 1], [1, 0], clamp) : interpolate(frame - selectAt, [0, 10], [1, 0.28], clamp);
        const strike = !it.relevant ? interpolate(frame - selectAt, [0, 10], [0, 1], clamp) : 0;
        return (
          <div key={k} style={{ position: "absolute", left: x, top: y, transform: `translate(-50%, -50%) scale(${scale * Math.min(1, appear * 1.05)})`,
            opacity: opacity * Math.min(1, appear * 2), width: colW, display: "flex", alignItems: "center", gap: size * 0.4,
            padding: `${size * 0.35}px ${size * 0.5}px`, borderRadius: size * 0.5,
            background: it.relevant ? core.steel : core.navy, border: `2px solid ${it.relevant ? `${accent}88` : core.line}` }}>
            {it.icon && <Icon name={it.icon} size={size * 1.2} color={it.relevant ? accent : core.muted} />}
            <div style={{ position: "relative", fontFamily: fontFamily(fontKey), fontWeight: 650, fontSize: size, color: it.relevant ? core.white : core.muted }}>
              {it.label}
              {strike > 0 && <div style={{ position: "absolute", left: 0, top: "52%", height: 4, width: `${strike * 100}%`, background: rejectColor, borderRadius: 2 }} />}
            </div>
          </div>
        );
      })}
      <div style={{ position: "absolute", left: centerX, top: targetY, transform: `translate(-50%, -50%) scale(${1 + targetPulse * 0.08})`,
        display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
        <div style={{ width: 210, height: 210, borderRadius: "50%", background: `radial-gradient(circle, ${accent}55, transparent 70%)`,
          display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Icon name={target.icon} size={150} />
        </div>
        {target.label && <div style={{ fontFamily: fontFamily(fontKey), fontWeight: 700, fontSize: 36, color: core.white }}>{target.label}</div>}
      </div>
    </div>
  );
};
