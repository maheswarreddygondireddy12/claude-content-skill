// Typed access to the brand vocabulary in /brand. Studio code never hardcodes brand values.
import tokensJson from "../../brand/tokens.json";
import fontsJson from "../../brand/fonts.json";

export const tokens = tokensJson;
export type AccentKey = Exclude<keyof typeof tokensJson.color.accents, "_about">;
export type PairingKey = Exclude<keyof typeof fontsJson.pairings, "_about">;
export type FontKey = keyof typeof fontsJson.families;
export type SpringKey = keyof typeof tokensJson.motion.springs;
export type PersonalityKey = keyof typeof tokensJson.motion.personalities;

export const core = tokensJson.color.core;
export const semantic = tokensJson.color.semantic;
export const safe = tokensJson.safeZone;
export const { width: WIDTH, height: HEIGHT, fps: FPS } = tokensJson.canvas;

export const accent = (key: string): string =>
  (tokensJson.color.accents as Record<string, string>)[key] ?? (key.startsWith("#") ? key : core.glow);

export const fontFamily = (key: string): string => {
  const fam = (fontsJson.families as Record<string, { css: string }>)[key];
  if (!fam) throw new Error(`Unknown font key "${key}". See brand/fonts.json`);
  return `'${fam.css}', 'Noto Sans Telugu Variable', system-ui, sans-serif`;
};

export const pairing = (key: string) => {
  const p = (fontsJson.pairings as unknown as Record<string, Record<string, string>>)[key];
  if (!p || key === "_about") throw new Error(`Unknown pairing "${key}". See brand/fonts.json`);
  return {
    display: fontFamily(p.display),
    body: fontFamily(p.body),
    caption: fontFamily(p.caption),
    code: fontFamily(p.code),
    telugu: fontFamily(p.telugu),
    keys: p,
  };
};

export const fontKeys = Object.keys(fontsJson.families) as FontKey[];
export const pairingKeys = Object.keys(fontsJson.pairings).filter((k) => k !== "_about") as PairingKey[];
export const accentKeys = Object.keys(tokensJson.color.accents).filter((k) => k !== "_about") as AccentKey[];
