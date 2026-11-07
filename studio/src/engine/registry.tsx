// EDL component registry. Scenes in edl.json name one of these components.
// Scene props may use any "<name>Word" key (e.g. atWord, appearAtWord, typeFromWord): the engine
// converts it to "<name>" in frames relative to the scene start, so everything stays voice-locked.
// "Composite" lets the Director freely arrange primitives without new code for each Reel.
import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { core, fontFamily } from "../brand";
import { Arrow, NodeBox } from "../primitives/Diagram";
import { CodeBlock } from "../primitives/CodeBlock";
import { BrowserFrame, ChatThread, PhoneFrame } from "../primitives/Mockups";
import { BuildList, Counter, KeywordCard } from "../primitives/Text";
import { Checkmark, Cross, HighlightSweep, ProgressBar, Pulse, Spinner } from "../primitives/MicroAnims";
import { Icon } from "../primitives/Icon";
import { ImageBeat, LottieClip } from "../primitives/Media";
import { ContextSorter, FieldCard } from "../primitives/Cards";
import { Wordmark } from "../primitives/Brand";
import { enterProgress, enterStyle, idleFloat, type EnterKind } from "../primitives/motion";

export type SceneCtx = { accent: string; accent2?: string; fonts: { display: string; body: string; code: string; keys: Record<string, string> }; durationInFrames: number };
type SceneComponent = React.FC<{ props: Record<string, any>; ctx: SceneCtx }>;

const Center: React.FC<{ children: React.ReactNode; y?: number }> = ({ children, y = 880 }) => (
  <AbsoluteFill>
    <div style={{ position: "absolute", left: 0, right: 0, top: y, transform: "translateY(-50%)", display: "flex", justifyContent: "center" }}>{children}</div>
  </AbsoluteFill>
);

const Title: React.FC<{ text?: string; ctx: SceneCtx; y?: number; size?: number; appearAt?: number }> = ({ text, ctx, y = 330, size = 72, appearAt = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!text || frame < appearAt) return null;
  return (
    <div style={{ position: "absolute", left: 80, right: 80, top: y, textAlign: "center", fontFamily: ctx.fonts.display, fontWeight: 800,
      fontSize: size, color: core.white, lineHeight: 1.1, ...enterStyle("rise", enterProgress(frame, fps, appearAt)) }}>{text}</div>
  );
};

/** Plain styled text element for Composite. Optional marker highlight, glow, box (chip/block) and animated strike-through. */
const TextEl: React.FC<{
  text: string; size?: number; color?: string; fontKey?: string; weight?: number; appearAt?: number; enter?: EnterKind;
  highlight?: string; width?: number; align?: "left" | "center" | "right"; glow?: string; strikeAt?: number; strikeColor?: string;
  box?: { background?: string; border?: string; padding?: string; radius?: number }; letterSpacing?: number; lineHeight?: number;
}> = ({
  text, size = 56, color = core.white, fontKey = "inter", weight = 700, appearAt = 0, enter = "rise", highlight, width, align = "center",
  glow, strikeAt, strikeColor = "#F87171", box, letterSpacing, lineHeight = 1.15,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < appearAt) return null;
  const body = highlight ? <HighlightSweep color={highlight} from={appearAt + 4}>{text}</HighlightSweep> : text;
  const strike = strikeAt !== undefined ? Math.min(1, Math.max(0, (frame - strikeAt) / 8)) : 0;
  return (
    <div style={{ fontFamily: fontFamily(fontKey), fontSize: size, color, fontWeight: weight, width, textAlign: align, lineHeight, letterSpacing,
      textShadow: glow ? `0 0 ${size * 0.5}px ${glow}, 0 0 ${size * 0.12}px ${glow}` : undefined,
      background: box?.background, border: box?.border, padding: box ? (box.padding ?? `${size * 0.25}px ${size * 0.5}px`) : undefined,
      borderRadius: box ? (box.radius ?? size * 0.45) : undefined, whiteSpace: width ? undefined : "nowrap",
      ...enterStyle(enter, enterProgress(frame, fps, appearAt)) }}>
      <span style={{ position: "relative", opacity: 1 - strike * 0.45 }}>
        {body}
        {strike > 0 && <span style={{ position: "absolute", left: "-3%", top: "54%", height: Math.max(4, size * 0.09), width: `${strike * 106}%`,
          background: strikeColor, borderRadius: 4 }} />}
      </span>
    </div>
  );
};

/** Icon with optional label, entrance and idle float, for analogy compositions. */
const IconEl: React.FC<{ name: string; size?: number; color?: string; label?: string; appearAt?: number; enter?: EnterKind; float?: boolean; labelColor?: string }> = ({
  name, size = 200, color, label, appearAt = 0, enter = "pop", float = true, labelColor = core.white,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < appearAt) return null;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 14, ...enterStyle(enter, enterProgress(frame, fps, appearAt)),
      translate: float ? `0 ${idleFloat(frame + size)}px` : undefined }}>
      <Icon name={name} size={size} color={color} />
      {label && <div style={{ fontFamily: fontFamily("inter"), fontWeight: 700, fontSize: Math.max(30, size * 0.2), color: labelColor }}>{label}</div>}
    </div>
  );
};

// Primitives available inside Composite. Each element: { type, x, y, anchor?, props }
const ELEMENTS: Record<string, React.FC<any>> = {
  NodeBox, Arrow, CodeBlock, ChatThread, PhoneFrame, BrowserFrame, BuildList, Counter, KeywordCard,
  Checkmark, Cross, Pulse, Spinner, ProgressBar, Wordmark, Text: TextEl, Icon: IconEl, Image: ImageBeat, Lottie: LottieClip,
  FieldCard, ContextSorter,
};
export const elementTypes = Object.keys(ELEMENTS);

type Element = { type: string; x?: number; y?: number; anchor?: "center" | "topleft"; w?: number; h?: number; props?: Record<string, any> };

const Composite: SceneComponent = ({ props, ctx }) => (
  <AbsoluteFill>
    <Title text={props.title} ctx={ctx} y={props.titleY} />
    {(props.elements as Element[] ?? []).map((el, k) => {
      const Comp = ELEMENTS[el.type];
      if (!Comp) return <div key={k} style={{ color: "#F87171", fontSize: 30 }}>Unknown element {el.type}</div>;
      // Diagram primitives position themselves on the full canvas.
      if (el.type === "NodeBox" || el.type === "Arrow" || el.type === "ContextSorter") return <Comp key={k} accent={ctx.accent} color={ctx.accent} {...el.props} />;
      const centered = (el.anchor ?? "center") === "center";
      return (
        <div key={k} style={{ position: "absolute", left: el.x ?? 540, top: el.y ?? 960, width: el.w, height: el.h,
          transform: centered ? "translate(-50%, -50%)" : undefined }}>
          <Comp accent={ctx.accent} {...el.props} />
        </div>
      );
    })}
  </AbsoluteFill>
);

export const REGISTRY: Record<string, SceneComponent> = {
  /** Captions carry the beat; background only. Use when a visual would not add clarity. */
  CaptionFocus: () => null,
  KeywordCard: ({ props, ctx }) => <Center y={props.y}><KeywordCard accent={ctx.accent} fontKey={ctx.fonts.keys.display} {...(props as any)} /></Center>,
  BuildList: ({ props, ctx }) => (
    <AbsoluteFill><Title text={props.title} ctx={ctx} /><Center y={props.y ?? 900}><BuildList accent={ctx.accent} fontKey={ctx.fonts.keys.body} {...(props as any)} /></Center></AbsoluteFill>
  ),
  Code: ({ props, ctx }) => (
    <AbsoluteFill><Title text={props.heading} ctx={ctx} /><Center y={props.y ?? 900}><CodeBlock accent={ctx.accent} fontKey={ctx.fonts.keys.code} {...(props as any)} /></Center></AbsoluteFill>
  ),
  Chat: ({ props, ctx }) => <Center y={props.y ?? 860}><ChatThread accent={ctx.accent} fontKey={ctx.fonts.keys.body} {...(props as any)} /></Center>,
  Phone: ({ props }) => <Center y={props.y ?? 900}><PhoneFrame {...(props as any)} /></Center>,
  Browser: ({ props }) => <Center y={props.y ?? 880}><BrowserFrame {...(props as any)} /></Center>,
  Counter: ({ props, ctx }) => (
    <Center y={props.y}><div style={{ textAlign: "center" }}><Counter color={ctx.accent} fontKey={ctx.fonts.keys.display} {...(props as any)} />
      {props.label && <div style={{ fontFamily: ctx.fonts.body, fontSize: 48, color: core.white }}>{props.label}</div>}</div></Center>
  ),
  Image: ({ props }) => (
    <AbsoluteFill style={{ padding: props.inset ?? 0 }}><ImageBeat {...(props as any)} /></AbsoluteFill>
  ),
  Lottie: ({ props }) => <Center y={props.y}><div style={{ width: props.size ?? 600, height: props.size ?? 600 }}><LottieClip {...(props as any)} /></div></Center>,
  Composite,
};

export const sceneTypes = Object.keys(REGISTRY);
