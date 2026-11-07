// Crisp, readable code for an engineering audience. Shiki tokens (VS Code-grade highlighting),
// optional typing reveal, line highlight, and "diff" marks. Highlighting runs once per code string.
import React, { useEffect, useState } from "react";
import { continueRender, delayRender, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { createHighlighterCore, type HighlighterCore, type ThemedToken } from "shiki/core";
import { createJavaScriptRegexEngine } from "shiki/engine/javascript";
import { core, fontFamily } from "../brand";
import { enterStyle, enterProgress } from "./motion";

export const CODE_LANGS = ["python", "javascript", "typescript", "java", "c", "cpp", "sql", "html", "css", "json", "bash", "jsx", "tsx", "go"] as const;
export const CODE_THEMES = ["github-dark", "one-dark-pro", "tokyo-night", "dracula", "vitesse-dark", "night-owl"] as const;
export type CodeLang = (typeof CODE_LANGS)[number];
export type CodeTheme = (typeof CODE_THEMES)[number];

let highlighterPromise: Promise<HighlighterCore> | null = null;
const getHighlighter = () => {
  highlighterPromise ??= createHighlighterCore({
    themes: [
      import("@shikijs/themes/github-dark"), import("@shikijs/themes/one-dark-pro"), import("@shikijs/themes/tokyo-night"),
      import("@shikijs/themes/dracula"), import("@shikijs/themes/vitesse-dark"), import("@shikijs/themes/night-owl"),
    ],
    langs: [
      import("@shikijs/langs/python"), import("@shikijs/langs/javascript"), import("@shikijs/langs/typescript"),
      import("@shikijs/langs/java"), import("@shikijs/langs/c"), import("@shikijs/langs/cpp"), import("@shikijs/langs/sql"),
      import("@shikijs/langs/html"), import("@shikijs/langs/css"), import("@shikijs/langs/json"), import("@shikijs/langs/bash"),
      import("@shikijs/langs/jsx"), import("@shikijs/langs/tsx"), import("@shikijs/langs/go"),
    ],
    engine: createJavaScriptRegexEngine(),
  });
  return highlighterPromise;
};

type Highlighted = { lines: ThemedToken[][]; bg: string };

const useHighlighted = (code: string, lang: CodeLang, theme: CodeTheme): Highlighted | null => {
  const [result, setResult] = useState<Highlighted | null>(null);
  const [handle] = useState(() => delayRender(`Highlighting ${lang} code`));
  useEffect(() => {
    getHighlighter()
      .then((h) => {
        const { tokens, bg } = h.codeToTokens(code, { lang, theme });
        setResult({ lines: tokens, bg: bg ?? core.night });
        continueRender(handle);
      })
      .catch((err) => { console.error(err); continueRender(handle); });
  }, [code, lang, theme, handle]);
  return result;
};

export type CodeBlockProps = {
  code: string;
  lang?: CodeLang;
  theme?: CodeTheme;
  title?: string;
  fontSize?: number;
  width?: number;
  fontKey?: string;
  /** typing reveal: characters per second, starting at `typeFrom` (frame within this component) */
  typing?: { cps: number; typeFrom?: number };
  highlightLines?: number[];           // 1-based
  highlightFrom?: number;              // frame
  added?: number[];                     // diff marks, 1-based
  removed?: number[];
  accent?: string;
  enterFrom?: number;
  showLineNumbers?: boolean;
};

export const CodeBlock: React.FC<CodeBlockProps> = ({
  code, lang = "python", theme = "one-dark-pro", title, fontSize = 40, width = 940, fontKey = "jetbrainsMono",
  typing, highlightLines = [], highlightFrom = 0, added = [], removed = [], accent = core.glow, enterFrom = 0,
  showLineNumbers = true,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const hl = useHighlighted(code, lang, theme);
  if (!hl) return null;

  const visibleChars = typing
    ? Math.max(0, Math.floor(((frame - (typing.typeFrom ?? 0)) / fps) * typing.cps))
    : Infinity;
  let budget = visibleChars;
  // line the cursor sits on while typing (the line where the visible-character budget runs out)
  let cursorLine = -1;
  if (typing && visibleChars < code.length) {
    let acc = 0;
    cursorLine = hl.lines.findIndex((line) => (acc += line.reduce((n, t) => n + t.content.length, 0) + 1) > visibleChars);
  }
  const cursorBlink = Math.floor(frame / 15) % 2 === 0;
  const hlOpacity = interpolate(frame - highlightFrom, [0, 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <div style={{ ...enterStyle("rise", enterProgress(frame, fps, enterFrom)), width, borderRadius: 28, overflow: "hidden",
      background: hl.bg, boxShadow: `0 30px 80px rgba(0,0,0,0.55), 0 0 0 2px ${core.line}` }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "18px 26px", background: "rgba(255,255,255,0.04)" }}>
        {["#FF5F57", "#FEBC2E", "#28C840"].map((c) => <div key={c} style={{ width: 18, height: 18, borderRadius: 9, background: c }} />)}
        {title && <div style={{ marginLeft: 14, color: core.muted, fontFamily: fontFamily("inter"), fontSize: 26 }}>{title}</div>}
      </div>
      <div style={{ padding: "22px 0 30px", fontFamily: fontFamily(fontKey), fontSize, lineHeight: 1.5 }}>
        {hl.lines.map((line, li) => {
          const n = li + 1;
          if (budget <= 0 && typing && li > 0) return null;
          const isHl = highlightLines.includes(n);
          const mark = added.includes(n) ? "+" : removed.includes(n) ? "−" : null;
          const rowBg = isHl ? `${accent}${Math.round(hlOpacity * 0x33).toString(16).padStart(2, "0")}`
            : mark === "+" ? "rgba(52,211,153,0.14)" : mark === "−" ? "rgba(248,113,113,0.14)" : "transparent";
          const spans: React.ReactNode[] = [];
          for (const [ti, tok] of line.entries()) {
            if (budget <= 0) break;
            const text = tok.content.slice(0, budget);
            budget -= tok.content.length;
            spans.push(<span key={ti} style={{ color: tok.color, fontStyle: tok.fontStyle === 1 ? "italic" : undefined }}>{text}</span>);
          }
          budget -= 1; // newline
          const isCursorLine = li === cursorLine && cursorBlink;
          return (
            <div key={li} style={{ display: "flex", padding: "0 30px", background: rowBg, borderLeft: `6px solid ${isHl ? accent : "transparent"}` }}>
              {showLineNumbers && <span style={{ width: fontSize * 1.6, color: "rgba(255,255,255,0.28)", flexShrink: 0 }}>{mark ?? n}</span>}
              <span style={{ whiteSpace: "pre" }}>{spans}{isCursorLine && <span style={{ color: accent }}>▍</span>}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
