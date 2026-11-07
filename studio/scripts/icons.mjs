#!/usr/bin/env node
// Offline icon/illustration tool for the Director.
//
//   node studio/scripts/icons.mjs search <query> [--sets lucide,tabler,...] [--limit 40]
//   node studio/scripts/icons.mjs pack <out.json> <set:name> [<set:name> ...]
//   node studio/scripts/icons.mjs pack-edl <edl.json> <out.json>     (collects every "set:name" string in the EDL)
//   node studio/scripts/icons.mjs sets                                (sets + licences + counts)
//
// Packs contain only the icons a Reel uses, so rendering never loads the large set JSONs.
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { getIconData } from "@iconify/utils";

const here = dirname(fileURLToPath(import.meta.url));
const nm = join(here, "..", "node_modules", "@iconify-json");
export const SETS = ["lucide", "tabler", "mdi", "logos", "devicon", "fluent-emoji-flat", "fluent-emoji"];
const cache = new Map();

const loadSet = (set) => {
  if (!SETS.includes(set)) throw new Error(`Unknown icon set "${set}". Allowed: ${SETS.join(", ")}`);
  if (!cache.has(set)) cache.set(set, JSON.parse(readFileSync(join(nm, set, "icons.json"), "utf8")));
  return cache.get(set);
};
const info = (set) => JSON.parse(readFileSync(join(nm, set, "info.json"), "utf8"));

export const resolveIcon = (full) => {
  const [set, name] = full.split(":");
  const data = getIconData(loadSet(set), name);
  if (!data) throw new Error(`Icon not found: ${full}`);
  const json = loadSet(set);
  return { body: data.body, width: data.width ?? json.width ?? 16, height: data.height ?? json.height ?? 16 };
};

const search = (query, sets, limit) => {
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  const out = [];
  for (const set of sets) {
    const json = loadSet(set);
    const names = [...Object.keys(json.icons), ...Object.keys(json.aliases ?? {})];
    for (const n of names) if (terms.every((t) => n.includes(t))) out.push(`${set}:${n}`);
  }
  out.sort((a, b) => a.length - b.length);
  return out.slice(0, limit);
};

const writePack = (out, names) => {
  const icons = {};
  const missing = [];
  for (const n of [...new Set(names)]) {
    try { icons[n] = resolveIcon(n); } catch { missing.push(n); }
  }
  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, JSON.stringify({ icons }));
  console.log(`wrote ${Object.keys(icons).length} icons -> ${out}`);
  if (missing.length) { console.error(`MISSING: ${missing.join(", ")}`); process.exitCode = 1; }
};

const ICON_RE = new RegExp(`^(${SETS.join("|")}):[a-z0-9-]+$`);
const collect = (node, acc) => {
  if (typeof node === "string") { if (ICON_RE.test(node)) acc.push(node); }
  else if (Array.isArray(node)) node.forEach((x) => collect(x, acc));
  else if (node && typeof node === "object") Object.values(node).forEach((x) => collect(x, acc));
  return acc;
};

const [cmd, ...args] = process.argv.slice(2);
const flag = (name, def) => { const k = args.indexOf(`--${name}`); return k >= 0 ? args.splice(k, 2)[1] : def; };
if (cmd === "search") {
  const sets = flag("sets", SETS.join(",")).split(",");
  const limit = Number(flag("limit", 40));
  console.log(search(args.join(" "), sets, limit).join("\n") || "(no matches)");
} else if (cmd === "pack") {
  writePack(args[0], args.slice(1));
} else if (cmd === "pack-edl") {
  writePack(args[1], collect(JSON.parse(readFileSync(args[0], "utf8")), []));
} else if (cmd === "sets") {
  for (const s of SETS) { const i = info(s); console.log(`${s.padEnd(18)} ${String(i.total).padStart(6)}  ${i.license.spdx}  ${i.name}`); }
} else {
  console.log("usage: icons.mjs search <query> | pack <out.json> <set:name>... | pack-edl <edl.json> <out.json> | sets");
}
