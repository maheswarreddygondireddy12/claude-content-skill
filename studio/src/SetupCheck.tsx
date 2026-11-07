// Production readiness check: one short render that exercises every capability the engine needs.
// Not a Reel and not a template — purely an infrastructure test.
import React from "react";
import { AbsoluteFill, Sequence, type CalculateMetadataFunction } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";
import { core, fontFamily, fontKeys, accent as accentColor } from "./brand";
import { ensureFonts } from "./fonts";
import fontsJson from "../../brand/fonts.json";
import { Background, SafeZoneGuide, Wordmark } from "./primitives/Brand";
import { CodeBlock } from "./primitives/CodeBlock";
import { Arrow, NodeBox } from "./primitives/Diagram";
import { Icon, IconPackProvider } from "./primitives/Icon";
import { LottieClip, Sfx } from "./primitives/Media";
import { Checkmark, Cross, ProgressBar, Pulse, Spinner } from "./primitives/MicroAnims";
import { Counter } from "./primitives/Text";

export const SETUP_ICONS = [
  "lucide:server", "tabler:database", "mdi:api", "logos:react", "devicon:python",
  "fluent-emoji-flat:health-worker", "fluent-emoji:thermometer", "lucide:monitor", "tabler:server-2",
];
type Props = {};

export const calculateSetupMetadata: CalculateMetadataFunction<Props> = async () => ({});

// A short infrastructure composition that exercises the reusable visual components.
const LOTTIE_SQUARE = {
  v: "5.7.4", fr: 30, ip: 0, op: 60, w: 200, h: 200, ddd: 0, assets: [],
  layers: [{
    ddd: 0, ind: 1, ty: 4, nm: "square", sr: 1, ao: 0, bm: 0, ip: 0, op: 60, st: 0,
    ks: {
      o: { a: 0, k: 100 }, p: { a: 0, k: [100, 100, 0] }, a: { a: 0, k: [0, 0, 0] }, s: { a: 0, k: [100, 100, 100] },
      r: { a: 1, k: [{ t: 0, s: [0], i: { x: [0.5], y: [1] }, o: { x: [0.5], y: [0] } }, { t: 60, s: [360] }] },
    },
    shapes: [
      { ty: "rc", nm: "r", d: 1, p: { a: 0, k: [0, 0] }, s: { a: 0, k: [90, 90] }, r: { a: 0, k: 18 } },
      { ty: "fl", nm: "f", c: { a: 0, k: [0.31, 0.7, 1, 1] }, o: { a: 0, k: 100 }, r: 1 },
    ],
  }],
};

const Label: React.FC<{ children: React.ReactNode; y: number }> = ({ children, y }) => (
  <div style={{ position: "absolute", left: 80, top: y, fontFamily: fontFamily("inter"), fontSize: 26, color: core.muted, letterSpacing: 2 }}>{children}</div>
);

const PartBrandFontsIcons: React.FC = () => (
  <AbsoluteFill>
    <div style={{ position: "absolute", left: 80, top: 230, display: "flex", alignItems: "center", gap: 30 }}>
      <Wordmark size={64} />
    </div>
    <Label y={380}>FONTS</Label>
    <div style={{ position: "absolute", left: 80, top: 420, display: "flex", flexDirection: "column", gap: 2 }}>
      {fontKeys.map((k) => (
        <div key={k} style={{ fontFamily: fontFamily(k), fontSize: 34, color: core.white, fontWeight: 700, lineHeight: 1.25 }}>
          {(fontsJson.families as Record<string, { css: string }>)[k].css.replace(" Variable", "")} · Aa 0{"{}"} తెలుగు
        </div>
      ))}
    </div>
    <Label y={1000}>ICONS (offline)</Label>
    <div style={{ position: "absolute", left: 80, top: 1040, display: "flex", gap: 22 }}>
      {SETUP_ICONS.slice(0, 7).map((n) => <Icon key={n} name={n} size={96} color={core.glow} />)}
    </div>
    <Label y={1160}>MICRO-ANIMATIONS</Label>
    <div style={{ position: "absolute", left: 80, top: 1195, display: "flex", alignItems: "center", gap: 30 }}>
      <Checkmark size={110} from={10} />
      <Cross size={110} from={25} />
      <Pulse size={110} from={0}><Icon name="lucide:server" size={50} color={core.glow} /></Pulse>
      <Spinner size={90} />
      <ProgressBar width={300} from={10} frames={60} label />
    </div>
  </AbsoluteFill>
);

const PartCodeDiagram: React.FC = () => (
  <AbsoluteFill>
    <div style={{ position: "absolute", left: 70, top: 230 }}>
      <CodeBlock title="check.py" lang="python" code={'def greet(name):\n    return f"Hello, {name}!"\n\nprint(greet("editor"))'}
        typing={{ cps: 40 }} highlightLines={[2]} highlightFrom={50} fontSize={36} width={940} />
    </div>
    <NodeBox x={250} y={980} w={260} h={190} label="Client" icon="lucide:monitor" appearAt={10} />
    <NodeBox x={830} y={980} w={260} h={190} label="Server" icon="tabler:server-2" appearAt={18} active />
    <Arrow from={[390, 960]} to={[690, 960]} appearAt={26} flow label="GET /api" />
    <div style={{ position: "absolute", left: 120, top: 1140, width: 160, height: 160 }}><LottieClip data={LOTTIE_SQUARE as never} loop /></div>
    <div style={{ position: "absolute", left: 360, top: 1150 }}><Counter to={100} suffix="%" frames={50} size={110} color={accentColor("lime")} /></div>
  </AbsoluteFill>
);

export const SetupCheck: React.FC<Props> = () => {
  ensureFonts();
  return (
    <IconPackProvider packs={["brand/icons.json"]}>
      <AbsoluteFill>
        <Background variant="night" />
        <TransitionSeries>
          <TransitionSeries.Sequence durationInFrames={130}><PartBrandFontsIcons /></TransitionSeries.Sequence>
          <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={linearTiming({ durationInFrames: 12 })} />
          <TransitionSeries.Sequence durationInFrames={122}><PartCodeDiagram /></TransitionSeries.Sequence>
        </TransitionSeries>
        <Sequence from={10}><Sfx id="pop_01" gainDb={-12} /></Sequence>
        <Sequence from={124}><Sfx id="whoosh_01" gainDb={-12} /></Sequence>
        <SafeZoneGuide />
      </AbsoluteFill>
    </IconPackProvider>
  );
};
