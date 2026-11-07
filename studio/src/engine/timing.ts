// Word-time helpers. All scene/SFX/caption timing is derived from timing.json, never hand-typed seconds.
import type { Timing, TimingWord } from "../schema";

export const secToFrame = (sec: number, fps: number) => Math.round(sec * fps);

export const wordStartFrame = (timing: Timing, i: number, fps: number, offsetMs = 0) =>
  secToFrame(timing.words[clampIndex(timing, i)].start + offsetMs / 1000, fps);

export const wordEndFrame = (timing: Timing, i: number, fps: number) =>
  secToFrame(timing.words[clampIndex(timing, i)].end, fps);

export const clampIndex = (timing: Timing, i: number) => Math.max(0, Math.min(timing.words.length - 1, i));

/** Index of the word being spoken at time t (last word whose start <= t). */
export const activeWordIndex = (words: TimingWord[], t: number): number => {
  let lo = 0, hi = words.length - 1, ans = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (words[mid].start <= t) { ans = mid; lo = mid + 1; } else hi = mid - 1;
  }
  return ans;
};

export const totalFrames = (timing: Timing, fps: number, tailSec: number) =>
  Math.ceil((timing.meta.duration_s + tailSec) * fps);

export const fetchJson = async <T,>(url: string): Promise<T> => {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to load ${url}: ${res.status}`);
  return (await res.json()) as T;
};
