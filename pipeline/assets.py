"""Asset & licence register (library/assets.json).

Every file or package used in a Reel must have an entry: source, licence, whether attribution is
needed. `--verify` fails if anything under brand/ or library/ is unregistered or has no licence.

    python pipeline/assets.py --verify
    python pipeline/assets.py --list [--kind sfx]
    python pipeline/assets.py --scan-npm      (refresh npm package licences from studio/node_modules)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "library" / "assets.json"
TRACKED_DIRS = ["brand/sfx", "library/stock", "library/lottie"]
IGNORED_SUFFIXES = {".json", ".md", ".txt"}

# Licences we accept for production use, and whether they require on-screen/caption attribution.
LICENCES = {
    "CC0-1.0": False, "MIT": False, "Apache-2.0": False, "ISC": False, "BSD-2-Clause": False,
    "BSD-3-Clause": False, "OFL-1.1": False, "Remotion": False, "Pexels": False, "Pixabay": False,
    "CC-BY-4.0": True, "CC-BY-3.0": True, "CC-BY-2.0": True, "CC-BY-SA-4.0": True, "CC-BY-SA-3.0": True,
    "Owned": False, "Generated": False, "BlueOak-1.0.0": False, "0BSD": False, "Unlicense": False,
    "Python-2.0": False, "CC-BY-SA-2.0": True, "PDM-1.0": False,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load() -> dict:
    if REGISTER.exists():
        return json.loads(REGISTER.read_text(encoding="utf-8"))
    return {"_about": "Licence register for assets and packages used by this project.", "assets": {}}


def save(reg: dict) -> None:
    REGISTER.parent.mkdir(parents=True, exist_ok=True)
    reg["assets"] = dict(sorted(reg["assets"].items()))
    REGISTER.write_text(json.dumps(reg, indent=1, ensure_ascii=False), encoding="utf-8")


def register(entries: list[dict]) -> None:
    """Add/replace entries keyed by 'id'. Required: id, kind, licence, source. Optional: path, url, attribution, notes."""
    reg = load()
    for e in entries:
        missing = {"id", "kind", "licence", "source"} - set(e)
        if missing:
            raise ValueError(f"asset entry {e.get('id')} missing {missing}")
        e = dict(e)
        e.setdefault("attribution_required", LICENCES.get(e["licence"], True))
        e.setdefault("added", date.today().isoformat())
        if e.get("path"):
            p = ROOT / e["path"]
            if p.is_file():
                e["sha256"] = sha256(p)
        reg["assets"][e["id"]] = e
    save(reg)


def scan_npm() -> int:
    nm = ROOT / "studio" / "node_modules"
    pkg = json.loads((ROOT / "studio" / "package.json").read_text(encoding="utf-8"))
    entries = []
    for name in list(pkg.get("dependencies", {})) + list(pkg.get("devDependencies", {})):
        meta_path = nm / name / "package.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        lic = meta.get("license") or (meta.get("licenses") or [{}])[0].get("type") or "UNKNOWN"
        if isinstance(lic, dict):
            lic = lic.get("type", "UNKNOWN")
        if name == "remotion" or name.startswith("@remotion/"):
            lic = "Remotion"  # Remotion licence: free for individuals / companies up to 3 people
        if name.startswith("@iconify-json/"):
            info = meta.get("iconSetInfo") or {}
            icon_info = json.loads((nm / name / "info.json").read_text(encoding="utf-8")) if (nm / name / "info.json").exists() else {}
            lic = (icon_info.get("license") or info.get("license") or {}).get("spdx", lic)
        entries.append({"id": f"npm:{name}", "kind": "npm", "licence": lic, "source": "npm",
                        "version": meta.get("version"), "url": f"https://www.npmjs.com/package/{name}"})
    register(entries)
    return len(entries)


def verify() -> list[str]:
    reg = load()["assets"]
    problems = []
    known_paths = {e.get("path") for e in reg.values() if e.get("path")}
    for d in TRACKED_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() not in IGNORED_SUFFIXES:
                rel = p.relative_to(ROOT).as_posix()
                if rel not in known_paths:
                    problems.append(f"unregistered file: {rel}")
    for key, e in reg.items():
        if e["licence"] not in LICENCES:
            problems.append(f"{key}: licence '{e['licence']}' not on the accepted list")
        if e.get("path") and not (ROOT / e["path"]).exists():
            problems.append(f"{key}: file missing: {e['path']}")
        if e.get("attribution_required") and not e.get("attribution"):
            problems.append(f"{key}: attribution required but no attribution text")
    return problems


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--scan-npm", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--kind")
    args = ap.parse_args()
    if args.scan_npm:
        print(f"registered {scan_npm()} npm packages")
    if args.list:
        for k, e in load()["assets"].items():
            if not args.kind or e["kind"] == args.kind:
                print(f"{k:60} {e['licence']:14} {'ATTRIB' if e.get('attribution_required') else ''}")
    if args.verify:
        if not REGISTER.exists():
            print("No asset register exists yet. Add media or dependencies before verifying.")
            return
        problems = verify()
        n = len(load()["assets"])
        if problems:
            print(f"FAIL: {len(problems)} problem(s) in {n} assets")
            for p in problems:
                print("  -", p)
            sys.exit(1)
        print(f"OK: {n} assets registered, all licensed")


if __name__ == "__main__":
    main()
