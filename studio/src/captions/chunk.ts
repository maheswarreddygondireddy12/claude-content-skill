// Caption chunking from timing.json. The treatment decides the rules; the timing provides
// boundary strengths (punctuation, gaps, signposts, language switches). No fixed chunk size.
import type { CaptionTreatment, TimingWord, Timing } from "../schema";

export type Chunk = { index: number; words: TimingWord[]; start: number; end: number };

const textLen = (ws: TimingWord[]) => ws.reduce((n, w) => n + w.display.length, 0) + Math.max(0, ws.length - 1);

/** Split one phrase into the fewest near-equal chunks within the limits (no orphan last words). */
const splitBalanced = (phrase: TimingWord[], maxWords: number, maxChars: number): TimingWord[][] => {
  for (let n = Math.max(1, Math.ceil(phrase.length / maxWords)); n <= phrase.length; n++) {
    const out: TimingWord[][] = [];
    let k = 0;
    for (let g = 0; g < n; g++) {
      const size = Math.round((phrase.length - k) / (n - g));
      out.push(phrase.slice(k, k + size));
      k += size;
    }
    // a single long word may exceed maxChars on its own; that is unavoidable, so only multi-word groups count
    if (out.every((g) => g.length <= maxWords && (g.length === 1 || textLen(g) <= maxChars))) return out;
  }
  return phrase.map((w) => [w]);
};

export const buildChunks = (timing: Timing, t: CaptionTreatment): Chunk[] => {
  const { words, boundaries } = timing;
  const maxWords = t.mode === "word" ? 1 : t.maxWords;
  // 1) phrases between boundaries the treatment considers strong; 2) balanced split inside each phrase
  const phrases: TimingWord[][] = [];
  let cur: TimingWord[] = [];
  words.forEach((w, k) => {
    cur.push(w);
    const b = boundaries[k];
    if (b && b.strength >= t.breakStrength) { phrases.push(cur); cur = []; }
  });
  if (cur.length) phrases.push(cur);
  const chunks: Chunk[] = [];
  for (const p of phrases) {
    for (const g of splitBalanced(p, maxWords, t.maxChars)) {
      chunks.push({ index: chunks.length, words: g, start: g[0].start, end: g[g.length - 1].end });
    }
  }
  return chunks;
};

const EMPHASIS_MARKERS: Record<string, string> = { caps: "caps", acronym: "acronym", number: "number", question: "question", elongated: "elongated" };

export const isEmphasised = (w: TimingWord, t: CaptionTreatment): boolean => {
  if (t.emphasisWords.includes(w.i)) return true;
  return t.emphasisRules.some((rule) => {
    if (rule === "english") return w.lang === "en" && w.align.length >= 4;
    if (rule === "signpost") return w.signpost;
    if (rule === "marked") return false;
    const marker = EMPHASIS_MARKERS[rule];
    return marker ? w.markers.includes(marker) : false;
  });
};

export const applyCase = (text: string, t: CaptionTreatment) =>
  t.textCase === "upper" ? text.toUpperCase() : t.textCase === "lower" ? text.toLowerCase() : text;
