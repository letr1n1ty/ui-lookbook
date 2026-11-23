---
name: ui-lookbook
description: "Discover live external web design benchmarks, dissect real featured studio websites (full-page composition, typography scale, spacing rhythm, mobile adaptation), and pull MIT/open-source interactive or motion component source from curated galleries and registries (Minimal Gallery, Siteinspire, Godly, Awwwards, Curated, Navbar/Footer Gallery, Designeer, React Bits, Vue Bits, Aceternity, Magic UI, Cult UI, Animate UI). Use when creating a high-craft website or showcase, researching real industry/section visual references, or upgrading specific UI sections with proven open-source interactive primitives. Not for backend logic, routine bug fixes, form validation, or minor CSS tweaks that need no external benchmarks or new components."
---

# UI Lookbook

Bridge the gap between LLM default wireframes and real studio-grade web design by **(1) inspecting real live featured websites (not just gallery thumbnails or text links), (2) calibrating ambition to the brand's exact aesthetic mode instead of forcing one-size-fits-all effects, (3) adapting proven MIT/open-source primitives cleanly into the project's token system, and (4) verifying desktop + mobile rendering before handoff.**

Locate `<skill-dir>` (the directory containing this `SKILL.md`).

---

## 1. Classify the Surface Mode First (Never Force Effects Blindly)

Before scouting or picking components, inspect `package.json` and existing CSS/tokens, then lock down **one** of three modes:

| Mode | Target Domains | Visual & Motion Strategy |
| :--- | :--- | :--- |
| **A. Editorial & Minimal Restraint** | Architecture, spatial studios, luxury, fashion, galleries, monographs | **Zero WebGL shaders, zero kinetic tickers, zero neon/glowing borders.** Craft comes from generous negative space, asymmetric hairline grids, rich tonal photography/architectural light studies, optical serif + tabular mono contrast, and quiet `180–260ms` transitions. |
| **B. Brand Narrative & Local Upgrade** | SaaS, developer tools, fintech, partial section upgrades (Navbar/Footer/Workbench) | **Incumbent design tokens win first** on existing pages: match established palette, fonts, border weights, and voice so upgraded sections feel native, never bolted-on. Build a **genuinely functional interactive product stage** + 1–2 restrained primitives (`direction-aware-tabs`, `navbar-menu`, `SpotlightCard`, `Magnet`). |
| **C. Immersive & Experimental** | Audio/music synths, creative labs, AI art, interactive launches | Deploy tactile domain instruments (playable knobs, real-time spectrum/waveform canvas) + atmospheric WebGL/kinetic components (`Ferrofluid`, `Silk`, `Grainient`, `SplitFlapText`), strictly enforcing **Section 4 Runtime & GPU Hygiene**. |

> **Photography-First Rule for Mode A**: Architecture, interiors, luxury, and hospitality brands rely on real photographic materiality. When user photos are absent and an image generation tool (e.g. `imagegen`) is available, generate 2–4 bespoke editorial photographs (such as 4x5 architectural daylight photography) and frame them inside borderless monograph spreads or Passe-Partout mats rather than bordered gray cards. Use `<canvas>` tonal light studies only for interactive solar/section diagrams or when image generation is unavailable.

---

## 2. Deep-Scout Real Featured Websites (Look at Live Originals, Not Thumbnails)

Read [references/inspiration-galleries.md](references/inspiration-galleries.md) to pick the right source, then run `visual_scout.cjs scout` — which discovers **1–2 real external featured studio/product websites** from the gallery, visits those live sites directly, captures full `1440×960` desktop + `390×844` mobile views, and extracts computed CSS typography/spacing DNA:

```bash
# Presets: minimal | godly | curated | awwwards | httpster | navbar-megamenu | footer-typographic | onepagelove | websitevice | brutalist
node <skill-dir>/scripts/visual_scout.cjs scout minimal --deep 2 --out /tmp/ui-lookbook-scout

# Or directly scout a specific reference URL supplied by the user:
node <skill-dir>/scripts/visual_scout.cjs scout https://linear.app --out /tmp/ui-lookbook-scout

# Optional fast index queries (Siteinspire API, Designeer 913-item catalog, llms.txt):
python3 <skill-dir>/scripts/query_refs.py siteinspire --category architecture,minimal --limit 5
python3 <skill-dir>/scripts/query_refs.py llms navbar "mega"
```

1. **Call `view_image` on the captured `live-1-hero.png` / `live-1-mid.png` (and `live-2-hero.png` when present)** — study the actual live featured website's viewport proportions, whitespace ratios, image/visual framing, and typography hierarchy.
2. Formulate a brief **Reference Translation Note**: state *which* structural patterns from the live reference fit this brand (and what you are deliberately leaving out) instead of copying unrelated surface styling or defaulting to generic `[Pill Badge + Left Text + Right White Card]` SaaS wireframes.
3. **Rate-Limit & Anti-Bot Stop Gate**: If any external gallery or site returns `401`/`403`/`429` (common on `Lapa Ninja`, `Saaspo`, or repeated `Siteinspire` hits) or an anti-bot challenge, stop immediately without retrying or bypassing and switch to another preset in [references/inspiration-galleries.md](references/inspiration-galleries.md).

---

## 3. Source & Adapt Pure Open-Source Primitives (`query_refs.py`)

Only use clean, permissive open-source (MIT) component registries. Read [references/component-registries.md](references/component-registries.md) and query by mode and stack:

```bash
python3 <skill-dir>/scripts/query_refs.py recipes --stack react --mode editorial   # editorial | narrative | immersive
python3 <skill-dir>/scripts/query_refs.py recipes --stack vue --mode immersive
python3 <skill-dir>/scripts/query_refs.py registry all "tabs" --stack react
python3 <skill-dir>/scripts/query_refs.py source cultui direction-aware-tabs
```

- **Token & Coherence Discipline**: Strip upstream hardcoded demo colors (`violet-500`, `bg-black`) and bind every pulled component to the project's CSS variables / brand tokens. Combine at most 1–2 registries so motion curves and borders feel authored by a single studio.
- **Source-File Registry Invariant**: Libraries like React Bits, Vue Bits, Aceternity UI, Magic UI, Cult UI, Animate UI, and Animata distribute **copy-paste / shadcn registry source files**, not standalone npm packages (`aceternity-ui` etc.). Always pull exact upstream source via `query_refs.py source` or install via `npx shadcn@latest add @<namespace>/<item>`, then verify `motion/react` vs `framer-motion` imports and required `@keyframes` against the project.
- **Real Interactive Craft Over Fake Bars**: Never render dead static progress bars (`width: 64%`) or stick-figure clip-art. Build real interactive controls, rich tonal plates, or domain-authentic interactive workbenches.

---

## 4. Runtime Performance, GPU Hygiene & Verification Loop

1. **GPU & Animation Hygiene (Whenever Using WebGL or `requestAnimationFrame`)**:
   - Cap pixel ratio at `Math.min(window.devicePixelRatio || 1, 1.5)` (pass `dpr={1.5}` or cap in canvas setup).
   - Pause continuous loops when scrolled offscreen via `IntersectionObserver` (`paused={!inView}`) and when `document.hidden` is true (`visibilitychange`).
   - Honor `prefers-reduced-motion: reduce`: render a crisp static frame or subtle CSS fallback instead of spinning infinite loops.
2. **CJK Typography Safety**: For Traditional Chinese / Japanese animated headings (`SplitText`, `BlurText`), split by characters/lines rather than whitespace `words`, and keep `line-height >= 1.18` with unclipped mask padding.
3. **Post-Build Desktop + Mobile Self-Audit**:
   After `vite build` succeeds, run:

```bash
node <skill-dir>/scripts/visual_scout.cjs audit <project-dir> --out /tmp/ui-lookbook-audit
```

   Confirm `runtimeErrors`, `horizontalOverflow`, `clippedText`, and `brokenImages` are all empty, then **call `view_image` on `audit-desktop-hero.png`, `audit-desktop-mid.png`, and `audit-mobile.png`**. Fix any cramped mobile layout, clipped glyph, or generic wireframe box before finishing.
