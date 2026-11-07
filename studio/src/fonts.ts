// Loads every approved font family (brand/fonts.json) and blocks rendering until they are ready,
// so no frame is ever captured with a fallback font.
import { continueRender, delayRender } from "remotion";

import "@fontsource-variable/inter";
import "@fontsource/poppins/400.css";
import "@fontsource/poppins/500.css";
import "@fontsource/poppins/600.css";
import "@fontsource/poppins/700.css";
import "@fontsource/poppins/800.css";
import "@fontsource/poppins/900.css";
import "@fontsource-variable/space-grotesk";
import "@fontsource-variable/montserrat";
import "@fontsource/anton";
import "@fontsource/bebas-neue";
import "@fontsource-variable/jetbrains-mono";
import "@fontsource-variable/fira-code";
import "@fontsource-variable/noto-sans-telugu";
import "@fontsource-variable/baloo-tammudu-2";

import fontsJson from "../../brand/fonts.json";

const SAMPLE = "Aa తె 0{";

let started = false;
export const ensureFonts = () => {
  if (started || typeof document === "undefined") return;
  started = true;
  const handle = delayRender("Loading brand fonts");
  const families = Object.values(fontsJson.families).map((f) => f.css);
  Promise.all(
    families.flatMap((css) => [
      document.fonts.load(`400 40px '${css}'`, SAMPLE),
      document.fonts.load(`800 40px '${css}'`, SAMPLE),
    ]),
  )
    .then(() => document.fonts.ready)
    .then(() => continueRender(handle))
    .catch((err) => {
      console.error("Font loading failed", err);
      continueRender(handle);
    });
};
