# Inspiration Galleries & Section References (Sites #00–#13, #25–#26)

Use this guide when shaping page narrative, industry aesthetic, typography/grid direction, or specific structural sections (Navbar, Mega Menu, Footer, Pricing).

## 1. Decision Routing by Design Problem

Combine **Live Visual Scouting (`visual_scout.cjs scout <preset>` + `view_image`)** so your eyes anchor on real award-winning composition, plus **Fast Index Lookup (`query_refs.py`)** for exact taxonomy links:

| Design Need | Live Visual Scout Preset (`visual_scout.cjs scout ...`) | Fast Structured Index (`query_refs.py`) & Notes |
| :--- | :--- | :--- |
| **Motion-Rich SaaS, Tech Product, Dual Desktop/Mobile Craft** | `scout godly` (**#08 Godly**) or `scout curated` (**#11 Curated**) | Also check `llms landbook` (**#07 Land-book**). Note how Godly sites use dark/light contrast stages and interactive product theater instead of static cards. |
| **Award-Winning Agency / Experimental Art Direction** | `scout awwwards` (**#00 Awwwards**) or `scout httpster` (**#09 Httpster**) | Also check **#02 CSS Design Awards** & **#26 Designeer** (`designeer "ascii"` / `"button"`). |
| **Navbar, Sticky Header, Mega Menu, Drawer** | `scout navbar-megamenu` or `scout navbar-minimal` (**#12 Navbar Gallery**) | Run `llms navbar mega` for category links. Study real photographic/architectural preview cards inside Mega Menus. |
| **Footer Layout (Monumental Wordmark, Dark Studio, Grid)** | `scout footer-typographic` or `scout footer-dark` (**#13 Footer Design**) | Run `llms footer typographic`. Contrast a dark architectural footer chapter against a light main body for dramatic closure! |
| **Editorial Typography, Architecture, Minimal Restraint** | `scout minimal` (**#06 Minimal Gallery**) | Query **#05 Siteinspire** (`siteinspire --category architecture,minimal`). Use atmospheric tonal plates/photography/canvases, never stick-figure clip-art! |
| **Single-Page Narrative & SaaS Pricing** | `scout onepagelove` (**#03 One Page Love**) or `scout curated` | Query `llms landbook pricing` + `designeer pricing`. (**#01 Lapa Ninja** & **#10 Saaspo** are behind 403/429 gates — never scrape or retry them!) |
| **Real-World Industry Verticals / Brutalist** | `scout websitevice` (**#04 Websitevice**) or `scout brutalist` (**#25 Brutalist**) | Match industry materiality (warm timber/stone for architecture, precision oscilloscope/knobs for audio, ledger foil/slate for fintech). |

## 2. Fast CLI Commands (`scripts/query_refs.py`)

```bash
# Navbar & Footer taxonomies and category URLs
python3 <skill-dir>/scripts/query_refs.py llms navbar "mega"
python3 <skill-dir>/scripts/query_refs.py llms footer "typographic"

# Curated studio & editorial websites via Siteinspire REST API (cached; auto-fallbacks on 429)
python3 <skill-dir>/scripts/query_refs.py siteinspire --category architecture --limit 6
python3 <skill-dir>/scripts/query_refs.py siteinspire --category minimal --limit 6

# Designeer Markdown catalogue (default `catalog` searches all 913 listings & finds)
python3 <skill-dir>/scripts/query_refs.py designeer "button"
python3 <skill-dir>/scripts/query_refs.py designeer --page resources

# Landing page & SaaS pricing taxonomies
python3 <skill-dir>/scripts/query_refs.py llms landbook "pricing"
python3 <skill-dir>/scripts/query_refs.py llms onepagelove "product"
python3 <skill-dir>/scripts/query_refs.py llms awwwards
```

## 3. How to Turn Reference Findings into Real UI Code

Merely citing a gallery URL does not improve UI quality. After retrieving reference entries (or taking 1–2 targeted screenshots), synthesize a **4-Point Structural Spec** before writing code:

1. **Hero archetype**: Read `dna.heroArchetype` and `dna.heroMediaCoverage` from the scout output. `full-bleed-immersive` (coverage ≥ 0.7) means the reference lets one image own the first screen; `dark-precision-stage` means a dark canvas where the product UI is the hero image; `editorial-composition` means type and grid lead. Match the archetype's scale, not its colors.
2. **Tonal chapters**: List the 3–5 chapters of the page and the luminance of each (for example: dark photo hero → light index → dark interactive chapter → light statements → dark footer). Two adjacent chapters should rarely share the same surface.
3. **Type scale and label budget**: Record the reference's H1 size/weight/tracking from `dna.h1`, then set a label budget: eyebrows, badges and bordered boxes only where they carry information.
4. **Signature interaction**: One domain-authentic centrepiece (a solar section you can scrub, a real diff with a counterexample, a playable instrument) rather than motion on every element.
