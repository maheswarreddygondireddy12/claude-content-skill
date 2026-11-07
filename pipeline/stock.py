"""Stock media search + download with licence tracking.

Sources
  openverse  keyless, CC-licensed images (CC0 / PDM / CC-BY / CC-BY-SA), commercial-use filter on
  pexels     needs PEXELS_API_KEY in .env (free account)  — photos + videos, Pexels licence
  pixabay    needs PIXABAY_API_KEY in .env (free account) — images, Pixabay licence

    python pipeline/stock.py search "doctor illustration" [--source openverse] [--limit 12]
    python pipeline/stock.py download openverse <id> [--reel <slug>]   -> library/stock/ or reels/<slug>/assets/stock/
    python pipeline/stock.py --test

    Every download gets a licence sidecar (<file>.licence.json) and an entry in library/assets.json.
Attribution-required licences (CC-BY*) carry the attribution text the Reel caption must include.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from assets import ROOT, load, register, save

STOCK_DIR = ROOT / "library" / "stock"
UA = "VideoEditingWorkflow/1.0 (local production tool)"
OPENVERSE_LICENCES = {"cc0": "CC0-1.0", "pdm": "PDM-1.0", "by": "CC-BY-{v}", "by-sa": "CC-BY-SA-{v}"}


def _env(key: str) -> str | None:
    if os.environ.get(key):
        return os.environ[key]
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip()
    return None


def _get(url: str, headers: dict | None = None) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def _licence_openverse(item: dict) -> str:
    lic = (item.get("license") or "").lower()
    tmpl = OPENVERSE_LICENCES.get(lic)
    if not tmpl:
        return f"UNSUPPORTED:{lic}"
    v = item.get("license_version") or "4.0"
    return tmpl.format(v=v if "." in v else f"{v}.0")


def search(query: str, source: str = "openverse", limit: int = 12) -> list[dict]:
    if source == "openverse":
        q = urllib.parse.urlencode({"q": query, "license": "cc0,pdm,by,by-sa", "license_type": "commercial,modification",
                                    "page_size": limit, "mature": "false"})
        data = json.loads(_get(f"https://api.openverse.org/v1/images/?{q}"))
        return [{"source": "openverse", "id": it["id"], "title": it.get("title"), "url": it["url"],
                 "licence": _licence_openverse(it), "attribution": it.get("attribution"),
                 "page": it.get("foreign_landing_url"), "creator": it.get("creator"),
                 "size": f"{it.get('width')}x{it.get('height')}", "filetype": it.get("filetype")} for it in data["results"]]
    if source == "pexels":
        key = _env("PEXELS_API_KEY") or sys.exit("PEXELS_API_KEY not set (.env)")
        data = json.loads(_get(f"https://api.pexels.com/v1/search?{urllib.parse.urlencode({'query': query, 'per_page': limit})}",
                               {"Authorization": key}))
        return [{"source": "pexels", "id": str(p["id"]), "title": p.get("alt"), "url": p["src"]["large2x"], "licence": "Pexels",
                 "attribution": f"Photo by {p['photographer']} on Pexels", "page": p["url"], "creator": p["photographer"],
                 "size": f"{p['width']}x{p['height']}", "filetype": "jpg"} for p in data["photos"]]
    if source == "pixabay":
        key = _env("PIXABAY_API_KEY") or sys.exit("PIXABAY_API_KEY not set (.env)")
        data = json.loads(_get(f"https://pixabay.com/api/?{urllib.parse.urlencode({'key': key, 'q': query, 'per_page': max(3, limit)})}"))
        return [{"source": "pixabay", "id": str(h["id"]), "title": h.get("tags"), "url": h["largeImageURL"], "licence": "Pixabay",
                 "attribution": f"Image by {h['user']} from Pixabay", "page": h["pageURL"], "creator": h["user"],
                 "size": f"{h['imageWidth']}x{h['imageHeight']}", "filetype": "jpg"} for h in data["hits"]]
    raise SystemExit(f"unknown source {source}")


def download(item: dict, reel: str | None = None) -> Path:
    if item["licence"].startswith("UNSUPPORTED"):
        raise SystemExit(f"refusing {item['id']}: licence {item['licence']}")
    ext = (item.get("filetype") or Path(urllib.parse.urlparse(item["url"]).path).suffix.lstrip(".") or "jpg").lower()
    base = (ROOT / "reels" / reel / "assets" / "stock") if reel else STOCK_DIR
    base.mkdir(parents=True, exist_ok=True)
    out = base / f"{item['source']}_{item['id']}.{ext}"
    out.write_bytes(_get(item["url"]))
    (out.parent / (out.name + ".licence.json")).write_text(json.dumps(item, indent=1, ensure_ascii=False), encoding="utf-8")
    entry = {"id": f"stock:{item['source']}:{item['id']}", "kind": "stock", "path": out.relative_to(ROOT).as_posix(),
             "licence": item["licence"], "source": item.get("page") or item["source"], "url": item["url"],
             "creator": item.get("creator")}
    if item.get("attribution") and item["licence"].startswith("CC-BY"):
        entry["attribution"] = item["attribution"]
    register([entry])
    return out


def by_id(source: str, item_id: str) -> dict:
    if source != "openverse":
        raise SystemExit("download by id is supported for openverse; for pexels/pixabay pass the search index")
    it = json.loads(_get(f"https://api.openverse.org/v1/images/{item_id}/"))
    return {"source": "openverse", "id": it["id"], "title": it.get("title"), "url": it["url"], "licence": _licence_openverse(it),
            "attribution": it.get("attribution"), "page": it.get("foreign_landing_url"), "creator": it.get("creator"),
            "filetype": it.get("filetype")}


def self_test() -> None:
    results = search("laptop", "openverse", 10)
    cc0 = next((r for r in results if r["licence"] in ("CC0-1.0", "PDM-1.0")), None)
    if not cc0:
        raise SystemExit("FAIL: no CC0/PDM result from Openverse")
    path = download(cc0)
    sidecar = path.parent / (path.name + ".licence.json")
    assert path.stat().st_size > 1000 and sidecar.exists(), "download or sidecar missing"
    print(f"OK: openverse search ({len(results)} results), downloaded {path.name} ({path.stat().st_size // 1024} KB, {cc0['licence']})")
    path.unlink()
    sidecar.unlink()
    reg = load()
    reg["assets"].pop(f"stock:openverse:{cc0['id']}", None)
    save(reg)
    print("OK: test file and register entry removed")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", nargs="?", choices=["search", "download"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--source", default="openverse", choices=["openverse", "pexels", "pixabay"])
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--reel")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        return self_test()
    if a.cmd == "search":
        for k, r in enumerate(search(" ".join(a.args), a.source, a.limit)):
            print(f"[{k}] {r['source']}:{r['id']}  {r['licence']:12} {r['size']:>10}  {(r['title'] or '')[:60]}")
    elif a.cmd == "download":
        source, item_id = a.args[0], a.args[1]
        print(download(by_id(source, item_id), a.reel))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
