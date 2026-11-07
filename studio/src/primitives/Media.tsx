// Audio & media wrappers: SFX by id, VO, Lottie, images/stock. Paths are under studio/public/.
import React, { useEffect, useState } from "react";
import { Audio, Img, continueRender, delayRender, staticFile } from "remotion";
import { Lottie, type LottieAnimationData } from "@remotion/lottie";

/** SFX from the brand palette (brand/sfx/<id>.wav, staged to public/brand/sfx). */
export const Sfx: React.FC<{ id: string; gainDb?: number }> = ({ id, gainDb = -16 }) => (
  <Audio src={staticFile(`brand/sfx/${id}.wav`)} volume={Math.pow(10, gainDb / 20)} />
);

/** Lottie from a licence-registered JSON file (library/lottie → public), or inline animation data. */
export const LottieClip: React.FC<{ src?: string; data?: LottieAnimationData; loop?: boolean; playbackRate?: number; style?: React.CSSProperties }> = ({
  src, data, loop = false, playbackRate = 1, style,
}) => {
  const [anim, setAnim] = useState<LottieAnimationData | null>(data ?? null);
  const [handle] = useState(() => (data ? null : delayRender(`Loading Lottie ${src}`)));
  useEffect(() => {
    if (data || !src || handle === null) return;
    fetch(staticFile(src)).then((r) => r.json()).then((json) => { setAnim(json); continueRender(handle); })
      .catch((err) => { console.error(err); continueRender(handle); });
  }, [src, data, handle]);
  if (!anim) return null;
  return <Lottie animationData={anim} loop={loop} playbackRate={playbackRate} style={style} />;
};

/** Image beat (stock or creator asset) with optional slow Ken Burns push. */
export const ImageBeat: React.FC<{ src: string; fit?: "cover" | "contain"; radius?: number; style?: React.CSSProperties }> = ({
  src, fit = "cover", radius = 0, style,
}) => <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: fit, borderRadius: radius, ...style }} />;
