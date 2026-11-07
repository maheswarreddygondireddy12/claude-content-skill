// Diagram kit: nodes and animated connectors on an absolute 1080x1920 canvas.
// Enough to build client↔server, flows, layers, comparisons; the Director composes them per Reel.
import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { evolvePath } from "@remotion/paths";
import { core, fontFamily } from "../brand";
import { Icon } from "./Icon";
import { enterProgress, enterStyle, type EnterKind } from "./motion";

export type NodeBoxProps = {
  x: number; y: number; w?: number; h?: number;
  label?: string; sub?: string; icon?: string; iconColor?: string;
  accent?: string; appearAt?: number; enter?: EnterKind; active?: boolean; fontKey?: string;
};

export const NodeBox: React.FC<NodeBoxProps> = ({
  x, y, w = 300, h = 220, label, sub, icon, iconColor, accent = core.glow, appearAt = 0, enter = "pop", active = false, fontKey = "spaceGrotesk",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < appearAt) return null;
  const style = enterStyle(enter, enterProgress(frame, fps, appearAt));
  return (
    <div style={{ position: "absolute", left: x - w / 2, top: y - h / 2, width: w, height: h, borderRadius: 32,
      background: `linear-gradient(160deg, ${core.steel}, ${core.navy})`, border: `3px solid ${active ? accent : core.line}`,
      boxShadow: active ? `0 0 40px ${accent}66` : "0 20px 50px rgba(0,0,0,0.45)",
      display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 12, ...style }}>
      {icon && <Icon name={icon} size={Math.min(w, h) * 0.42} color={iconColor ?? accent} />}
      {label && <div style={{ color: core.white, fontFamily: fontFamily(fontKey), fontWeight: 700, fontSize: 40, textAlign: "center" }}>{label}</div>}
      {sub && <div style={{ color: core.muted, fontFamily: fontFamily("inter"), fontSize: 28, textAlign: "center" }}>{sub}</div>}
    </div>
  );
};

export type ArrowProps = {
  from: [number, number]; to: [number, number]; curve?: number;
  color?: string; width?: number; appearAt?: number; drawFrames?: number;
  dashed?: boolean; flow?: boolean; label?: string; head?: boolean;
};

/** Connector that draws itself, optionally with travelling "packets" (flow) to show data moving. */
export const Arrow: React.FC<ArrowProps> = ({
  from, to, curve = 0, color = core.glow, width = 6, appearAt = 0, drawFrames = 14, dashed = false, flow = false, label, head = true,
}) => {
  const frame = useCurrentFrame();
  if (frame < appearAt) return null;
  const [x1, y1] = from, [x2, y2] = to;
  const mx = (x1 + x2) / 2 - (y2 - y1) * curve, my = (y1 + y2) / 2 + (x2 - x1) * curve;
  const d = `M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`;
  const p = interpolate(frame - appearAt, [0, drawFrames], [0, 1], { extrapolateRight: "clamp" });
  const ev = evolvePath(p, d);
  const angle = (Math.atan2(y2 - my, x2 - mx) * 180) / Math.PI;
  const packet = flow && p >= 1 ? ((frame - appearAt - drawFrames) % 40) / 40 : -1;
  const pt = (t: number) => [(1 - t) ** 2 * x1 + 2 * (1 - t) * t * mx + t ** 2 * x2, (1 - t) ** 2 * y1 + 2 * (1 - t) * t * my + t ** 2 * y2];
  const [px, py] = packet >= 0 ? pt(packet) : [0, 0];
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", left: 0, top: 0, overflow: "visible", pointerEvents: "none" }}>
      <path d={d} fill="none" stroke={color} strokeWidth={width} strokeLinecap="round"
        strokeDasharray={dashed ? "16 14" : ev.strokeDasharray} strokeDashoffset={dashed ? -frame * 2 : ev.strokeDashoffset}
        opacity={dashed ? p : 1} />
      {head && p >= 1 && <polygon points="0,-14 26,0 0,14" fill={color} transform={`translate(${x2},${y2}) rotate(${angle})`} />}
      {packet >= 0 && <circle cx={px} cy={py} r={12} fill={core.white} style={{ filter: `drop-shadow(0 0 10px ${color})` }} />}
      {label && p >= 1 && (
        <text x={mx} y={my - 22} fill={core.white} fontSize={32} textAnchor="middle" fontFamily={fontFamily("inter")} fontWeight={600}>{label}</text>
      )}
    </svg>
  );
};
