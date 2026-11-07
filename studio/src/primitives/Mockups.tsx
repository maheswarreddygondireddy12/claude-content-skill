// Generic, UNBRANDED device/app frames. Real product UI must come from the project owner's
// screenshots/recordings and is placed inside these frames, never re-drawn as if real.
import React from "react";
import { Img, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { core, fontFamily } from "../brand";
import { enterProgress, enterStyle } from "./motion";

export const PhoneFrame: React.FC<{ width?: number; screenshot?: string; video?: string; children?: React.ReactNode; scrollPx?: number }> = ({
  width = 560, screenshot, video, children, scrollPx = 0,
}) => {
  const h = width * 2.05;
  return (
    <div style={{ width, height: h, borderRadius: width * 0.13, background: "#0b0d12", padding: width * 0.035,
      boxShadow: `0 40px 100px rgba(0,0,0,0.6), 0 0 0 3px ${core.line}` }}>
      <div style={{ width: "100%", height: "100%", borderRadius: width * 0.1, overflow: "hidden", position: "relative", background: core.night }}>
        {screenshot && <Img src={staticFile(screenshot)} style={{ width: "100%", transform: `translateY(${-scrollPx}px)` }} />}
        {video && <OffthreadVideo src={staticFile(video)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />}
        {children}
        <div style={{ position: "absolute", top: width * 0.025, left: "50%", transform: "translateX(-50%)", width: width * 0.3,
          height: width * 0.07, borderRadius: width, background: "#000" }} />
      </div>
    </div>
  );
};

export const BrowserFrame: React.FC<{ width?: number; height?: number; url?: string; screenshot?: string; children?: React.ReactNode }> = ({
  width = 940, height = 640, url = "", screenshot, children,
}) => (
  <div style={{ width, height, borderRadius: 24, overflow: "hidden", background: core.night, boxShadow: `0 30px 80px rgba(0,0,0,0.55), 0 0 0 2px ${core.line}` }}>
    <div style={{ height: 64, display: "flex", alignItems: "center", gap: 12, padding: "0 22px", background: core.steel }}>
      {["#FF5F57", "#FEBC2E", "#28C840"].map((c) => <div key={c} style={{ width: 16, height: 16, borderRadius: 8, background: c }} />)}
      <div style={{ marginLeft: 16, flex: 1, height: 38, borderRadius: 19, background: core.navy, color: core.muted,
        fontFamily: fontFamily("inter"), fontSize: 24, display: "flex", alignItems: "center", padding: "0 18px" }}>{url}</div>
    </div>
    <div style={{ position: "relative", height: height - 64 }}>
      {screenshot && <Img src={staticFile(screenshot)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "top" }} />}
      {children}
    </div>
  </div>
);

export type ChatMessage = { from: "user" | "ai"; text: string; at: number };

/** Generic AI-chat thread (not ChatGPT-branded). Messages appear at their `at` frame. */
export const ChatThread: React.FC<{ messages: ChatMessage[]; width?: number; accent?: string; assistantName?: string; fontKey?: string; fontSize?: number }> = ({
  messages, width = 900, accent = core.glow, assistantName = "AI", fontKey = "inter", fontSize = 38,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div style={{ width, display: "flex", flexDirection: "column", gap: 26 }}>
      {messages.filter((m) => frame >= m.at).map((m, k) => {
        const user = m.from === "user";
        return (
          <div key={k} style={{ alignSelf: user ? "flex-end" : "flex-start", maxWidth: width * 0.82,
            ...enterStyle(user ? "slide-left" : "rise", enterProgress(frame, fps, m.at), 24) }}>
            {!user && <div style={{ color: accent, fontFamily: fontFamily(fontKey), fontSize: fontSize * 0.68, fontWeight: 700, marginBottom: 6 }}>{assistantName}</div>}
            <div style={{ padding: "22px 30px", borderRadius: 30, borderBottomRightRadius: user ? 8 : 30, borderBottomLeftRadius: user ? 30 : 8,
              background: user ? accent : core.steel, color: user ? core.ink : core.white,
              fontFamily: fontFamily(fontKey), fontSize, lineHeight: 1.35, fontWeight: 500 }}>{m.text}</div>
          </div>
        );
      })}
    </div>
  );
};
