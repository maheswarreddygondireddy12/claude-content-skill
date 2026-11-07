// Offline icons/illustrations. Icons are extracted per Reel into a small pack
// (`node studio/scripts/icons.mjs pack ...`) so render needs no network and no 100 MB JSON bundles.
// Names follow Iconify: "lucide:server", "logos:react", "fluent-emoji-flat:man-health-worker".
import React, { createContext, useContext, useEffect, useState } from "react";
import { continueRender, delayRender, staticFile } from "remotion";

export type IconData = { body: string; width: number; height: number };
export type IconPack = { icons: Record<string, IconData> };

const PackContext = createContext<IconPack>({ icons: {} });

/** Loads one or more icon packs (paths under public/) and makes them available to <Icon>. */
export const IconPackProvider: React.FC<{ packs: string[]; children: React.ReactNode }> = ({ packs, children }) => {
  const [pack, setPack] = useState<IconPack | null>(null);
  const [handle] = useState(() => delayRender(`Loading icon packs ${packs.join(", ")}`));
  useEffect(() => {
    Promise.all(
      packs.map((p) => fetch(staticFile(p)).then((r) => (r.ok ? (r.json() as Promise<IconPack>) : { icons: {} }))),
    )
      .then((all) => {
        setPack({ icons: Object.assign({}, ...all.map((a) => a.icons)) });
        continueRender(handle);
      })
      .catch((err) => {
        console.error(err);
        setPack({ icons: {} });
        continueRender(handle);
      });
  }, [handle, packs]);
  if (!pack) return null;
  return <PackContext.Provider value={pack}>{children}</PackContext.Provider>;
};

type Props = { name: string; size?: number; color?: string; style?: React.CSSProperties; strokeWidth?: number };

export const Icon: React.FC<Props> = ({ name, size = 96, color = "currentColor", style, strokeWidth }) => {
  const { icons } = useContext(PackContext);
  const data = icons[name];
  if (!data) {
    // Visible placeholder so a missing icon is caught in QC instead of silently vanishing.
    return (
      <div style={{ width: size, height: size, border: "4px dashed #F87171", borderRadius: 12, color: "#F87171",
        fontSize: 16, display: "flex", alignItems: "center", justifyContent: "center", textAlign: "center", ...style }}>
        missing {name}
      </div>
    );
  }
  let body = data.body.replaceAll("currentColor", color);
  if (strokeWidth) body = body.replace(/stroke-width="[\d.]+"/g, `stroke-width="${strokeWidth}"`);
  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${data.width} ${data.height}`}
      style={{ display: "block", overflow: "visible", ...style }}
      dangerouslySetInnerHTML={{ __html: body }}
    />
  );
};
