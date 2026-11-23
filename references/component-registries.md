# Component & Motion Registries (Sites #14–#24)

Use this reference when adding polished visual effects, interactive primitives, micro-interactions, or animated blocks.

## 1. Tier-S Registries (Machine-Readable Source & CLI Ready)

All 7 libraries below expose real component source code via JSON registries or `llms.txt`. Query them through `scripts/query_refs.py` before writing custom animation code.

| # | Library | Query Key | shadcn Namespace | Stack | Best-In-Class Use Cases | Typical Dependencies |
| :- | :--- | :--- | :--- | :--- | :--- | :--- |
| 15 | **React Bits** | `reactbits` | `@react-bits` | React (JS/TS x CSS/TW) | Text reveals (`SplitText`, `BlurText`), WebGL/Canvas backgrounds (`Aurora`, `Silk`), cursor/magnetic micro-interactions. Variant suffixes: `-JS-CSS`, `-JS-TW`, `-TS-CSS`, `-TS-TW`. | `gsap` or `motion` / `ogl` (varies per item) |
| 16 | **Vue Bits** | `vuebits` | `@vue-bits` | Vue 3 (JS/TS + TW) | **Primary choice for Vue 3 projects.** Vue-native SFCs (`.vue`) for split text, magnetic buttons, spotlight cards, accordion galleries, and shader backgrounds. Never paste React JSX into Vue when `@vue-bits` has the native `.vue` SFC. | `gsap` / `ogl` (varies per item) |
| 18 | **Magic UI** | `magicui` | `@magicui` | React + Tailwind | High-restraint SaaS landing polish: `number-ticker`, `marquee`, `bento-grid`, `magic-card` (cursor spotlight), `animated-beam`, `border-beam`, `shimmer-button`. | `motion` (`motion/react`), `clsx`, `tailwind-merge` |
| 19 | **Aceternity UI** | `aceternity` | `@aceternity` | React / Next.js + Tailwind | High-drama hero atmospheres: `spotlight`, `background-beams`, `aurora-background`, `card-spotlight`, `3d-card`, `sticky-scroll-reveal`, `lamp`. **Always recolor default dark-violet demo styles to match project brand.** | `motion` / `framer-motion` |
| 20 | **Animate UI** | `animateui` | `@animate-ui` | React + Radix / Base UI | Stateful UI transitions: animated `tabs` (sliding active indicator), `accordion`, `dialog`, `popover`, `tooltip`, `switch`, and subtle interactive backgrounds. Best when standard primitives feel stiff. | `motion`, Radix / Base UI |
| 21 | **Cult UI** | `cultui` | `@cult-ui` | React + shadcn | Expandable cards, floating docks, `text-animate`, `direction-aware-tabs`, dynamic island / expandable drawers built cleanly on shadcn conventions. | `motion`, `lucide-react` |
| 23 | **Animata** | `animata` | URL registry | React + Tailwind v4 | ~130 lightweight animated cards, tickers, progress widgets, typewriter text, and bento tiles (`https://animata.design/r/{category}/{component}.json`). Check `llms animata <keyword>` first. | Tailwind v4 utilities / `framer-motion` |

### Fast Lookup Recipes

```bash
# 1. List mode-calibrated MIT component recipes (editorial | narrative | immersive | all)
python3 <skill-dir>/scripts/query_refs.py recipes --stack react --mode editorial
python3 <skill-dir>/scripts/query_refs.py recipes --stack react --mode narrative
python3 <skill-dir>/scripts/query_refs.py recipes --stack vue --mode immersive

# 2. Pull zero-extra-dependency WebGL GLSL Shaders (imports ONLY 'react' or 'vue'!)
python3 <skill-dir>/scripts/query_refs.py source reactbits Silk-TS-TW
python3 <skill-dir>/scripts/query_refs.py source reactbits Grainient-TS-TW
python3 <skill-dir>/scripts/query_refs.py source reactbits Threads-TS-TW
python3 <skill-dir>/scripts/query_refs.py source reactbits Noise-TS-TW
python3 <skill-dir>/scripts/query_refs.py source vuebits Ferrofluid
python3 <skill-dir>/scripts/query_refs.py source vuebits Silk
python3 <skill-dir>/scripts/query_refs.py source vuebits CRTWarp

# 3. Pull kinetic typography, 3D stages & tactile controls
python3 <skill-dir>/scripts/query_refs.py source reactbits SplitFlapText-TS-TW
python3 <skill-dir>/scripts/query_refs.py source reactbits ScrollVelocity-TS-TW
python3 <skill-dir>/scripts/query_refs.py source reactbits TiltedCard-TS-TW
python3 <skill-dir>/scripts/query_refs.py source reactbits Magnet-TS-TW
python3 <skill-dir>/scripts/query_refs.py source aceternity container-scroll-animation
python3 <skill-dir>/scripts/query_refs.py source cultui direction-aware-tabs
python3 <skill-dir>/scripts/query_refs.py source magicui number-ticker
python3 <skill-dir>/scripts/query_refs.py source vuebits SplitFlapText
python3 <skill-dir>/scripts/query_refs.py source vuebits SpotlightCard
```

### Mode C Note: Zero-Dep WebGL Shaders (Use Selectively for Immersive Brands)

For **Mode C (Immersive & Experimental)** surfaces (audio synths, creative labs, interactive launches), components like `Silk`, `Grainient`, `Aurora`, `LightRays`, `Threads`, `Ferrofluid`, `LiquidChrome`, `CRTWarp`, and `Noise` compile self-contained WebGL fragment shaders directly inside React/Vue without requiring `three` or `ogl`. Always pass custom brand hexes (`color`, `color1`/`color2`/`color3`, `colorStops`), cap `dpr <= 1.5`, and pause offscreen via `IntersectionObserver`. Do **not** inject these into Mode A minimal/architectural brands.

## 2. Open-Source Policy & Reference-Only Sites (#14, #17, #22, #24)

Pull source code **exclusively** from permissive open-source (MIT) registries (`@react-bits`, `@vue-bits`, `@aceternity`, `@magicui`, `@cult-ui`, `@animate-ui`, `Animata`, and MIT-licensed **#14 Codrops** tutorial repos / **#22 Uiverse** snippets). Exclude non-permissive or paid-locked sources (**#24 Hover.css** and **#17 OriginKit** Pro items) from code retrieval; write micro-hovers directly with clean Tailwind utilities.

## 3. Integration & Performance Checklist

1. **Check CSS keyframes**: `Magic UI` (`marquee`, `border-beam`, `shimmer`) and `Aceternity` (`spotlight`, `aurora`) define custom `@keyframes` in `cssVars` / `tailwind` / `css` metadata returned by `query_refs.py source`. Copy those `@keyframes` into the project's global CSS so animations actually run!
2. **Check `cn()` helper**: Most shadcn-style components import `cn` from `@/lib/utils`. Either ensure `lib/utils.ts` exists or inline a lightweight `cn(...classes)` helper.
3. **GPU & Offscreen Pause Hygiene**: For continuous WebGL or canvas components (`Ferrofluid`, `Silk`, `Grainient`, `Noise`), cap `dpr` at `1.5`, wire `IntersectionObserver` + `document.visibilityState` to pause `requestAnimationFrame` when offscreen, and provide a static frame when `prefers-reduced-motion: reduce` matches.
4. **CJK (`zh-Hant` / `ja`) Text Reveal Safety**: When adapting `SplitText`, `BlurText`, or `text-animate` for Traditional Chinese headlines, split by characters/lines rather than English whitespace `words`, and preserve at least `leading-[1.18]` with unclipped inner padding so CJK strokes are never sliced by overflow masks.
