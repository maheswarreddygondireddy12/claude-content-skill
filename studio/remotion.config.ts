// Render settings shared by Studio previews and CLI renders.
// Output: 1080x1920 H.264 / yuv420p, high quality so Instagram's re-encode has headroom.
import { homedir } from "node:os";
import { join } from "node:path";
import { Config } from "@remotion/cli/config";

// Staged media (VO, timing, EDL, brand SFX/logo/icons) lives outside OneDrive as a plain folder;
// pipeline/prepare_reel.py fills it. Remotion copies it into each bundle, so it must not contain links.
Config.setPublicDir(join(homedir(), ".video-editing-workflow", "studio_public"));

Config.setVideoImageFormat("jpeg");
Config.setJpegQuality(92);
Config.setConcurrency(4);
Config.setCodec("h264");
Config.setCrf(18);
Config.setPixelFormat("yuv420p");
Config.setColorSpace("bt709"); // limited-range BT.709 (yuv420p, not yuvj420p) — what Instagram expects
Config.setAudioBitrate("192k");
Config.setOverwriteOutput(true);
Config.setChromiumOpenGlRenderer("angle");
