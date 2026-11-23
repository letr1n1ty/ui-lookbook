#!/usr/bin/env python3
"""Deterministic, cached lookup helper for vibe-ui-refs.

Queries S-tier component registries (catalog + full component source code) and
A-tier inspiration endpoints (llms.txt, Designeer Markdown, Siteinspire API)
using Python standard library only, with 1-hour local disk caching and strict
non-retry stop gates on HTTP 429 / anti-bot responses.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CACHE_DIR = Path(tempfile.gettempdir()) / "vibe-ui-refs-cache"
CACHE_TTL_SECONDS = 3600
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) VibeUIRefs/1.0"

REGISTRIES = {
    "magicui": {
        "namespace": "@magicui",
        "stack": "react",
        "catalog_url": "https://magicui.design/r/registry.json",
        "item_url": "https://magicui.design/r/{name}.json",
        "homepage": "https://magicui.design",
    },
    "aceternity": {
        "namespace": "@aceternity",
        "stack": "react",
        "catalog_url": "https://ui.aceternity.com/api/components",
        "item_url": "https://ui.aceternity.com/registry/{name}.json",
        "homepage": "https://ui.aceternity.com",
    },
    "reactbits": {
        "namespace": "@react-bits",
        "stack": "react",
        "catalog_url": "https://reactbits.dev/r/registry.json",
        "item_url": "https://reactbits.dev/r/{name}.json",
        "homepage": "https://reactbits.dev",
    },
    "vuebits": {
        "namespace": "@vue-bits",
        "stack": "vue",
        "catalog_url": "https://vue-bits.dev/r/registry.json",
        "item_url": "https://vue-bits.dev/r/{name}.json",
        "homepage": "https://vue-bits.dev",
    },
    "animateui": {
        "namespace": "@animate-ui",
        "stack": "react",
        "catalog_url": "https://animate-ui.com/r/registry.json",
        "item_url": "https://animate-ui.com/r/{name}.json",
        "homepage": "https://animate-ui.com",
    },
    "cultui": {
        "namespace": "@cult-ui",
        "stack": "react",
        "catalog_url": "https://www.cult-ui.com/r/registry.json",
        "item_url": "https://www.cult-ui.com/r/{name}.json",
        "homepage": "https://cult-ui.com",
    },
    "animata": {
        "namespace": "animata",
        "stack": "react",
        "catalog_url": "https://animata.design/llms.txt",
        "item_url": "https://animata.design/r/{name}.json",
        "homepage": "https://animata.design",
    },
}

LLMS_SITES = {
    "awwwards": "https://www.awwwards.com/llms.txt",
    "onepagelove": "https://onepagelove.com/llms.txt",
    "landbook": "https://land-book.com/llms.txt",
    "navbar": "https://www.navbar.gallery/llms.txt",
    "footer": "https://www.footer.design/llms.txt",
    "siteinspire": "https://www.siteinspire.com/llms.txt",
    "animata": "https://animata.design/llms.txt",
    "designeer": "https://designeer.xyz/llms.txt",
}


class FetchStoppedError(RuntimeError):
    def __init__(self, status: int | str, url: str, reason: str):
        super().__init__(f"[{status}] {url} -> {reason}")
        self.status = status
        self.url = url
        self.reason = reason


def fetch_cached(url: str, accept: str = "*/*", timeout: int = 8) -> str:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(f"{url}|{accept}".encode("utf-8")).hexdigest()[:24]
    cache_file = CACHE_DIR / f"{key}.cache"
    if cache_file.exists():
        age = time.time() - cache_file.stat().st_mtime
        if age < CACHE_TTL_SECONDS:
            return cache_file.read_text(encoding="utf-8")

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            cache_file.write_text(body, encoding="utf-8")
            return body
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403, 429):
            raise FetchStoppedError(
                exc.code,
                url,
                "Rate-limited or gated. Stop gate active: do NOT retry or bypass; use documented fallback.",
            ) from exc
        raise FetchStoppedError(exc.code, url, str(exc.reason)) from exc
    except Exception as exc:
        raise FetchStoppedError(type(exc).__name__, url, str(exc)) from exc


def parse_registry_items(lib: str) -> list[dict]:
    cfg = REGISTRIES[lib]
    raw = fetch_cached(cfg["catalog_url"])
    if lib == "animata":
        items = []
        for line in raw.splitlines():
            if "animata.design/docs/" in line or line.lstrip().startswith("- ["):
                items.append(
                    {
                        "lib": lib,
                        "name": line.strip(),
                        "title": "",
                        "description": "",
                        "deps": [],
                        "install": "See animata.design/r/{category}/{component}.json",
                    }
                )
        return items

    data = json.loads(raw)
    raw_items = data.get("items") or (data.get("components", []) + data.get("blocks", []))
    out = []
    for it in raw_items:
        name = it.get("name", "")
        if not name or name == "index":
            continue
        ns = cfg["namespace"]
        install_cmd = it.get("installCommand") or f"npx shadcn@latest add {ns}/{name}"
        out.append(
            {
                "lib": lib,
                "name": name,
                "title": it.get("title", ""),
                "description": (it.get("description") or "").strip(),
                "deps": it.get("dependencies") or [],
                "install": install_cmd,
            }
        )
    return out


def cmd_registry(args: argparse.Namespace) -> int:
    target = args.library.lower()
    query_terms = [t.lower() for t in (args.query or "").split() if t.strip()]
    if target == "all":
        libs = [k for k, v in REGISTRIES.items() if v["stack"] == args.stack and k != "animata"]
    elif target in REGISTRIES:
        libs = [target]
    else:
        print(f"Unknown library {target!r}. Valid: all, {', '.join(REGISTRIES)}", file=sys.stderr)
        return 1

    matches = []
    errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(libs)) as pool:
        fut_map = {pool.submit(parse_registry_items, lib): lib for lib in libs}
        for fut in concurrent.futures.as_completed(fut_map):
            lib = fut_map[fut]
            try:
                for item in fut.result():
                    hay = f"{item['name']} {item['title']} {item['description']}".lower()
                    if all(term in hay for term in query_terms):
                        score = sum(3 if term in item["name"].lower() else 1 for term in query_terms)
                        matches.append((score, item))
            except FetchStoppedError as exc:
                errors.append(str(exc))

    matches.sort(key=lambda pair: (-pair[0], pair[1]["lib"], pair[1]["name"]))
    shown = matches[: args.limit]
    print(f"Found {len(matches)} matching items across [{', '.join(libs)}] (showing {len(shown)}):")
    for _, it in shown:
        deps = f" | deps: {', '.join(it['deps'])}" if it["deps"] else ""
        desc = f" — {it['description'][:110]}" if it["description"] else ""
        print(f"- [{it['lib']}] {it['name']}{desc}{deps}")
        if it["lib"] != "animata":
            print(f"    source: python3 {Path(__file__).resolve()} source {it['lib']} {it['name']}")
            print(f"    cli:    {it['install']}")
    for err in errors:
        print(f"Note: {err}", file=sys.stderr)
    return 0


def cmd_source(args: argparse.Namespace) -> int:
    lib = args.library.lower()
    if lib not in REGISTRIES:
        print(f"Unknown library {lib!r}. Valid: {', '.join(REGISTRIES)}", file=sys.stderr)
        return 1
    url = REGISTRIES[lib]["item_url"].format(name=args.item)
    try:
        raw = fetch_cached(url, accept="application/json")
    except FetchStoppedError as exc:
        print(f"Error fetching component source: {exc}", file=sys.stderr)
        print(f"Tip: run `registry {lib} <keyword>` to check exact item name/variant.", file=sys.stderr)
        return 1

    data = json.loads(raw)
    print(f"# Component: [{lib}] {data.get('name', args.item)}")
    if data.get("description"):
        print(f"Description: {data['description']}")
    print(f"Dependencies: {json.dumps(data.get('dependencies') or [])}")
    if data.get("registryDependencies"):
        print(f"Registry Dependencies: {json.dumps(data.get('registryDependencies'))}")
    if data.get("cssVars"):
        print(f"CSS Vars / Keyframes: {json.dumps(data.get('cssVars'), indent=2)}")
    if data.get("tailwind"):
        print(f"Tailwind Config Additions: {json.dumps(data.get('tailwind'), indent=2)}")
    if data.get("css"):
        print(f"Custom CSS Additions: {json.dumps(data.get('css'), indent=2)}")

    files = data.get("files") or []
    for idx, fobj in enumerate(files, 1):
        fpath = fobj.get("target") or fobj.get("path") or f"file_{idx}"
        content = fobj.get("content", "")
        print(f"\n--- FILE {idx}/{len(files)}: {fpath} ---")
        if args.max_lines and len(content.splitlines()) > args.max_lines:
            lines = content.splitlines()[: args.max_lines]
            print("\n".join(lines))
            print(f"\n... [truncated at {args.max_lines} lines; pass --max-lines 0 for full file] ...")
        else:
            print(content)
    return 0


def cmd_llms(args: argparse.Namespace) -> int:
    site = args.site.lower()
    if site not in LLMS_SITES:
        print(f"Unknown site {site!r}. Valid: {', '.join(LLMS_SITES)}", file=sys.stderr)
        return 1
    try:
        raw = fetch_cached(LLMS_SITES[site], accept="text/plain, text/markdown")
    except FetchStoppedError as exc:
        print(f"Stop gate: {exc}", file=sys.stderr)
        return 1

    lines = raw.splitlines()
    if args.query:
        terms = [t.lower() for t in args.query.split() if t.strip()]
        matched = []
        for i, line in enumerate(lines):
            window = " ".join(lines[max(0, i - 1) : min(len(lines), i + 2)]).lower()
            if all(t in window for t in terms):
                matched.append(line)
        lines = matched

    shown = lines[: args.limit]
    print(f"# [{site}] llms.txt ({len(shown)}/{len(lines)} lines shown):")
    for line in shown:
        print(line)
    return 0


def cmd_designeer(args: argparse.Namespace) -> int:
    page = args.page.strip("/") or "catalog"
    url = "https://designeer.xyz/api/md/_catalog" if page == "catalog" else f"https://designeer.xyz/{page}.md"
    try:
        raw = fetch_cached(url, accept="text/markdown, text/plain")
    except FetchStoppedError as exc:
        print(f"Stop gate: {exc}", file=sys.stderr)
        return 1

    lines = raw.splitlines()
    if args.query:
        terms = [t.lower() for t in args.query.split() if t.strip()]
        lines = [ln for ln in lines if all(t in ln.lower() for t in terms)]
    shown = lines[: args.limit]
    print(f"# [designeer:{page}] ({len(shown)}/{len(lines)} lines shown):")
    for ln in shown:
        print(ln)
    return 0


def cmd_siteinspire(args: argparse.Namespace) -> int:
    if args.category:
        cats = ",".join(s.strip() for s in args.category.split(",") if s.strip())
        url = f"https://www.siteinspire.com/api/websites/explore?categories={urllib.parse.quote(cats)}&scope=recent"
    else:
        url = f"https://www.siteinspire.com/api/websites?limit={args.limit}&offset=0"
    try:
        raw = fetch_cached(url, accept="application/json")
    except FetchStoppedError as exc:
        print(f"Notice: {exc}")
        print("Fallback: Querying Siteinspire llms.txt taxonomy instead:")
        try:
            si_llms = fetch_cached(LLMS_SITES["siteinspire"], accept="text/plain")
            for ln in si_llms.splitlines()[:25]:
                print("  " + ln)
        except FetchStoppedError:
            pass
        return 0

    data = json.loads(raw)
    websites = (data.get("websites") or data.get("items") or [])[: args.limit]
    total = (data.get("metadata") or {}).get("totalCount", len(websites))
    print(f"# [siteinspire] category={args.category or 'all'} (total={total}, showing={len(websites)}):")
    for w in websites:
        title = w.get("title") or w.get("name") or w.get("slug") or "Untitled"
        live_url = w.get("finalRedirectUrl") or w.get("url") or ""
        cats = w.get("categoriesTsv") or ""
        print(f"- {title}: {live_url}  [tags: {cats}]")
    return 0


HIGH_IMPACT_RECIPES = {
    "react": {
        "editorial": [
            ("reactbits", "FadeContent-TS-TW", "Restrained scroll/blur entrance without visual noise — ideal for minimal/architecture"),
            ("reactbits", "SplitText-TS-TW", "Optical staggered line/character reveal (use chars mode + line-height >= 1.18 for CJK)"),
            ("aceternity", "navbar-menu", "Clean motion layoutId Mega Menu transitions — strip rounded dark defaults to match hairline grid"),
            ("cultui", "texture-card", "Subtle multi-layered paper/editorial framing"),
        ],
        "narrative": [
            ("cultui", "direction-aware-tabs", "Smooth directional layoutId workbench tabs (use ResizeObserver instead of react-use-measure)"),
            ("magicui", "magic-card", "Subtle pointer-tracked radial light card — recolor to brand accent"),
            ("magicui", "number-ticker", "Spring-damped tabular-nums metric counter"),
            ("aceternity", "container-scroll-animation", "3D perspective product stage linked to scroll"),
            ("aceternity", "sticky-scroll-reveal", "Synchronized narrative + visual stage"),
            ("reactbits", "Magnet-TS-TW", "Tactile magnetic pull for primary CTA"),
        ],
        "immersive": [
            ("reactbits", "Silk-TS-TW", "Zero-dep WebGL silk shader — cap dpr<=1.5 & pause offscreen via IntersectionObserver"),
            ("reactbits", "Grainient-TS-TW", "Zero-dep WebGL film-grain gradient field — cap dpr<=1.5 & pause offscreen"),
            ("reactbits", "SplitFlapText-TS-TW", "Mechanical split-flap display for telemetry/counters"),
            ("reactbits", "TiltedCard-TS-TW", "3D spring perspective card with specular glare"),
            ("reactbits", "Noise-TS-TW", "Subtle film grain canvas — cap frame rate / pause offscreen"),
        ],
    },
    "vue": {
        "editorial": [
            ("vuebits", "FadeContent", "Quiet editorial fade/blur reveal"),
            ("vuebits", "SplitText", "GSAP character reveal (use chars mode + leading-[1.2] for CJK)"),
            ("vuebits", "AccordionGallery", "Horizontal architectural/editorial expanding plates"),
        ],
        "narrative": [
            ("vuebits", "SpotlightCard", "Damped cursor spotlight + proximity neighbor border glow"),
            ("vuebits", "Magnet", "Tactile magnetic button wrapper"),
            ("vuebits", "CountUp", "Clean numeric counter"),
        ],
        "immersive": [
            ("vuebits", "Ferrofluid", "Zero-dep WebGL magnetic liquid ferrofluid (built-in dpr & paused props — wire IntersectionObserver!)"),
            ("vuebits", "Silk", "Zero-dep WebGL flowing silk shader (pass dpr<=1.5 & pause offscreen)"),
            ("vuebits", "SplitFlapText", "Mechanical split-flap display for hardware/synth presets & readouts"),
            ("vuebits", "SpotlightCard", "Damped cursor spotlight + proximity neighbor border glow"),
            ("vuebits", "Magnet", "Magnetic pull for tactile hardware triggers"),
        ],
    },
}


def cmd_recipes(args: argparse.Namespace) -> int:
    stack = args.stack.lower()
    groups = HIGH_IMPACT_RECIPES.get(stack, {})
    selected = {args.mode: groups[args.mode]} if args.mode != "all" and args.mode in groups else groups
    print(f"# Calibrated Open-Source Component Recipes (stack={stack}, mode={args.mode})")
    for cat, entries in selected.items():
        print(f"\n## MODE: {cat.upper()}")
        for lib, name, note in entries:
            print(f"- [{lib}] {name} — {note}")
            print(f"    fetch: python3 {Path(__file__).resolve()} source {lib} {name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="vibe-ui-refs lookup utility")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_rec = sub.add_parser("recipes", help="List curated high-visual-impact WebGL shaders, kinetic type & 3D stages")
    p_rec.add_argument("--stack", choices=["react", "vue"], default="react")
    p_rec.add_argument("--mode", choices=["all", "editorial", "narrative", "immersive"], default="all")
    p_rec.set_defaults(func=cmd_recipes)

    p_reg = sub.add_parser("registry", help="Search component registries")
    p_reg.add_argument("library", help="all | magicui | aceternity | reactbits | vuebits | animateui | cultui | animata")
    p_reg.add_argument("query", nargs="?", default="", help="Keyword filter")
    p_reg.add_argument("--stack", choices=["react", "vue"], default="react")
    p_reg.add_argument("--limit", type=int, default=12)
    p_reg.set_defaults(func=cmd_registry)

    p_src = sub.add_parser("source", help="Fetch exact upstream component source from a registry")
    p_src.add_argument("library", help="magicui | aceternity | reactbits | vuebits | animateui | cultui | animata")
    p_src.add_argument("item", help="Exact component item name (e.g. number-ticker, spotlight, SplitText)")
    p_src.add_argument("--max-lines", type=int, default=220, help="0 for unlimited")
    p_src.set_defaults(func=cmd_source)

    p_llms = sub.add_parser("llms", help="Search structured llms.txt from curated galleries")
    p_llms.add_argument("site", help=", ".join(LLMS_SITES))
    p_llms.add_argument("query", nargs="?", default="", help="Optional filter words")
    p_llms.add_argument("--limit", type=int, default=35)
    p_llms.set_defaults(func=cmd_llms)

    p_des = sub.add_parser("designeer", help="Query Designeer clean Markdown catalogue")
    p_des.add_argument("--page", default="catalog", help="catalog (all 913 entries) | index | inspiration | resources | tools | portfolios")
    p_des.add_argument("query", nargs="?", default="", help="Optional filter words")
    p_des.add_argument("--limit", type=int, default=30)
    p_des.set_defaults(func=cmd_designeer)

    p_si = sub.add_parser("siteinspire", help="Query Siteinspire public REST API (with 429 auto-fallback)")
    p_si.add_argument("--category", default="", help="e.g. architecture, minimal, typography, black-and-white")
    p_si.add_argument("--limit", type=int, default=6)
    p_si.set_defaults(func=cmd_siteinspire)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
