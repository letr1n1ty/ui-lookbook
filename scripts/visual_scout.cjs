#!/usr/bin/env node
/**
 * visual_scout.cjs — Live Visual Reference Capture & Post-Build Visual Audit
 *
 * Commands:
 *   node visual_scout.cjs scout <preset-or-url> [--out <dir>]
 *   node visual_scout.cjs audit <project-or-dist-dir> [--out <dir>]
 *
 * Safety: Never solves, clicks through, retries, or bypasses 401/403/429 or
 * any anti-bot/CAPTCHA challenge. Immediately aborts and suggests safe presets.
 */
const fs = require("fs");
const path = require("path");
const http = require("http");
const os = require("os");

function loadPlaywright() {
  try { return require("playwright"); } catch {}
  try { return require("playwright-core"); } catch {}
  const home = os.homedir();
  const npxRoot = path.join(home, ".npm", "_npx");
  if (fs.existsSync(npxRoot)) {
    for (const d of fs.readdirSync(npxRoot)) {
      const candidate = path.join(npxRoot, d, "node_modules", "playwright");
      if (fs.existsSync(candidate)) return require(candidate);
    }
  }
  throw new Error("Playwright not found. Install via `npm i -D playwright` or run `npx playwright --version` once.");
}

async function launchBrowser(chromium) {
  try {
    return await chromium.launch({ headless: true });
  } catch {
    return await chromium.launch({ headless: true, channel: "chrome" });
  }
}

const PRESETS = {
  godly: "https://recent.design/websites",
  awwwards: "https://www.awwwards.com/websites/",
  minimal: "https://minimal.gallery/",
  "navbar-megamenu": "https://www.navbar.gallery/type/mega-menu",
  "navbar-minimal": "https://www.navbar.gallery/style/minimal",
  "footer-typographic": "https://www.footer.design/styles/typographic",
  "footer-dark": "https://www.footer.design/styles/dark",
  curated: "https://curated.design/",
  httpster: "https://httpster.net/",
  onepagelove: "https://onepagelove.com/inspiration",
  websitevice: "https://websitevice.com/",
  brutalist: "https://brutalistwebsites.com/",
};

const BLOCKED_HOSTS = ["lapa.ninja", "saaspo.com"];
const SKIP_EXTERNAL = [
  "twitter.com", "x.com", "instagram.com", "linkedin.com", "facebook.com",
  "youtube.com", "github.com", "figma.com", "webflow.com", "framer.com",
  "pinterest.com", "mobbin.com", "substack.com", "dub.sh", "readymag.com",
  "sponsor", "submit", "login", "signup", "privacy", "terms", "mailto:",
  "utm_campaign=", "checkout"
];

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".mjs": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".webp": "image/webp",
  ".json": "application/json",
  ".woff2": "font/woff2",
};

function parseArgs(argv) {
  const pos = [];
  const flags = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith("--")) {
      const k = argv[i].slice(2);
      flags[k] = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : "true";
    } else {
      pos.push(argv[i]);
    }
  }
  return { pos, flags };
}

function serveStatic(rootDir) {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      let u = decodeURIComponent((req.url || "/").split("?")[0]);
      if (u === "/favicon.ico") { res.writeHead(204); res.end(); return; }
      if (u === "/") u = "/index.html";
      const fp = path.join(rootDir, u);
      if (!fp.startsWith(rootDir) || !fs.existsSync(fp) || fs.statSync(fp).isDirectory()) {
        res.writeHead(404); res.end("Not found"); return;
      }
      const ext = path.extname(fp).toLowerCase();
      res.writeHead(200, { "Content-Type": MIME[ext] || "application/octet-stream" });
      fs.createReadStream(fp).pipe(res);
    });
    srv.listen(0, "127.0.0.1", () => resolve({ srv, port: srv.address().port }));
  });
}

async function extractLiveSiteDna(page) {
  return page.evaluate(() => {
    const cs = (el) => (el ? getComputedStyle(el) : null);
    const body = cs(document.body);
    const h1El = document.querySelector("h1, [class*=\"hero\" i] h2");
    const h1 = cs(h1El);
    const navEl = document.querySelector("header, nav");
    const navRect = navEl ? navEl.getBoundingClientRect() : null;
    const sections = Array.from(document.querySelectorAll("main > section, section, article")).slice(0, 6).map((s) => {
      const st = getComputedStyle(s);
      return { padTop: st.paddingTop, padBottom: st.paddingBottom, bg: st.backgroundColor, display: st.display };
    });
    return {
      title: document.title.slice(0, 80),
      bodyBg: body ? body.backgroundColor : "",
      bodyColor: body ? body.color : "",
      bodyFont: body ? body.fontFamily.slice(0, 90) : "",
      navHeightPx: navRect ? Math.round(navRect.height) : null,
      h1: h1 ? {
        text: (h1El.innerText || "").trim().replace(/\s+/g, " ").slice(0, 70),
        fontFamily: h1.fontFamily.slice(0, 90),
        fontSize: h1.fontSize,
        lineHeight: h1.lineHeight,
        letterSpacing: h1.letterSpacing,
        fontWeight: h1.fontWeight,
      } : null,
      sectionRhythm: sections,
    };
  });
}

async function isPageGated(page, status) {
  if (status === 401 || status === 403 || status === 429) return true;
  return page.evaluate(() => {
    const txt = (document.title + " " + (document.body ? document.body.innerText.slice(0, 500) : "")).toLowerCase();
    return /attention required|cloudflare|verify you are human|captcha|turnstile|too many requests|access denied/.test(txt);
  }).catch(() => true);
}

async function cmdScout(target, outDir, deepCount) {
  const url = PRESETS[target] || target;
  if (!/^https?:\/\//i.test(url)) {
    console.error(`Unknown preset "${target}". Available presets: ${Object.keys(PRESETS).join(", ")}`);
    process.exit(1);
  }
  if (BLOCKED_HOSTS.some((h) => url.includes(h))) {
    console.log(JSON.stringify({ ok: false, gated: true, reason: "Host excluded due to 403/429 gate; use minimal, godly, curated, navbar-megamenu, footer-typographic, or onepagelove." }, null, 2));
    return;
  }
  fs.mkdirSync(outDir, { recursive: true });
  const { chromium } = loadPlaywright();
  const browser = await launchBrowser(chromium);
  try {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 960 }, deviceScaleFactor: 1.5 });
    const page = await ctx.newPage();
    const resp = await page.goto(url, { waitUntil: "domcontentloaded", timeout: 12000 });
    const status = resp ? resp.status() : 0;
    await page.waitForTimeout(1400);
    if (await isPageGated(page, status)) {
      console.log(JSON.stringify({ ok: false, status, gated: true, stopGate: "Aborted immediately without retry. Switch to minimal, godly, curated, or httpster." }, null, 2));
      return;
    }
    await page.addStyleTag({ content: "#onetrust-banner-sdk, .fc-consent-root, [id*=\"cookie\" i][class*=\"banner\" i] { display: none !important; }" }).catch(() => {});
    // If target is already a direct non-preset studio URL, extract DNA directly
    const isPreset = Boolean(PRESETS[target]);
    if (!isPreset) {
      const heroShot = path.join(outDir, `live-1-hero.png`);
      await page.screenshot({ path: heroShot, fullPage: false });
      const dna = await extractLiveSiteDna(page);
      await page.evaluate(() => window.scrollBy(0, 860));
      await page.waitForTimeout(700);
      const midShot = path.join(outDir, `live-1-mid.png`);
      await page.screenshot({ path: midShot });
      console.log(JSON.stringify({ ok: true, mode: "direct-site", url, screenshots: { hero: heroShot, mid: midShot }, dna }, null, 2));
      return;
    }

    const galleryShot = path.join(outDir, `gallery-overview.png`);
    await page.screenshot({ path: galleryShot, fullPage: false });

    // Discover real external featured websites from the gallery
    const candidateUrls = await page.evaluate((skipList) => {
      const host = location.hostname;
      const found = [];
      for (const a of document.querySelectorAll("a[href]")) {
        const h = a.href;
        const low = h.toLowerCase();
        if (!low.startsWith("http") || skipList.some((w) => low.includes(w))) continue;
        try {
          const u = new URL(h);
          if (u.hostname !== host && !u.hostname.endsWith("." + host) && !found.some((x) => new URL(x).hostname === u.hostname)) {
            found.push(h);
          }
        } catch {}
      }
      return found.slice(0, 8);
    }, SKIP_EXTERNAL);

    const liveSites = [];
    const want = Math.max(1, Math.min(3, Number(deepCount) || 2));
    for (const extUrl of candidateUrls) {
      if (liveSites.length >= want) break;
      if (BLOCKED_HOSTS.some((h) => extUrl.includes(h))) continue;
      const sp = await ctx.newPage();
      try {
        const r = await sp.goto(extUrl, { waitUntil: "domcontentloaded", timeout: 10000 });
        const st = r ? r.status() : 0;
        await sp.waitForTimeout(1500);
        if (await isPageGated(sp, st)) { await sp.close(); continue; }
        await sp.addStyleTag({ content: "#onetrust-banner-sdk, .fc-consent-root { display: none !important; }" }).catch(() => {});
        const idx = liveSites.length + 1;
        const heroPath = path.join(outDir, `live-${idx}-hero.png`);
        await sp.screenshot({ path: heroPath });
        const dna = await extractLiveSiteDna(sp);
        await sp.evaluate(() => window.scrollBy(0, 860));
        await sp.waitForTimeout(700);
        const midPath = path.join(outDir, `live-${idx}-mid.png`);
        await sp.screenshot({ path: midPath });
        liveSites.push({ index: idx, url: sp.url(), screenshots: { hero: heroPath, mid: midPath }, dna });
      } catch {
        // Skip slow/unreachable external site cleanly
      } finally {
        await sp.close();
      }
    }
    console.log(JSON.stringify({ ok: true, gallery: url, galleryOverview: galleryShot, liveFeaturedSites: liveSites }, null, 2));
  } finally {
    await browser.close();
  }
}

async function cmdAudit(targetPath, outDir) {
  const resolved = path.resolve(targetPath);
  const distDir = fs.existsSync(path.join(resolved, "dist", "index.html"))
    ? path.join(resolved, "dist")
    : resolved;
  if (!fs.existsSync(path.join(distDir, "index.html"))) {
    console.error(`No index.html found in ${distDir}. Run vite build first.`);
    process.exit(1);
  }
  fs.mkdirSync(outDir, { recursive: true });
  const { srv, port } = await serveStatic(distDir);
  const { chromium } = loadPlaywright();
  const browser = await launchBrowser(chromium);
  try {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 960 }, deviceScaleFactor: 1.5 });
    const page = await ctx.newPage();
    const runtimeErrors = [];
    page.on("pageerror", (e) => runtimeErrors.push("PAGEERROR: " + e.message));
    page.on("console", (m) => {
      if (m.type() === "error" && !m.text().includes("ERR_NAME_NOT_RESOLVED") && !m.text().includes("fonts.g")) {
        runtimeErrors.push("CONSOLE: " + m.text());
      }
    });
    await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: "domcontentloaded", timeout: 15000 });
    await page.waitForTimeout(1500);

    const heroShot = path.join(outDir, "audit-desktop-hero.png");
    await page.screenshot({ path: heroShot });

    const diagnostics = await page.evaluate(() => {
      const h1 = document.querySelector("h1");
      const h1Px = h1 ? parseFloat(getComputedStyle(h1).fontSize) : 0;
      const desktopOverflowPx = Math.max(0, document.documentElement.scrollWidth - window.innerWidth);
      const brokenImages = Array.from(document.querySelectorAll("img"))
        .filter((img) => img.complete && img.naturalWidth === 0)
        .map((img) => img.getAttribute("src") || "unknown");
      const canvases = Array.from(document.querySelectorAll("canvas")).map((c) => ({ w: c.width, h: c.height, clientW: c.clientWidth, clientH: c.clientHeight }));
      const clipped = [];
      for (const el of document.querySelectorAll("h1, h2, h3, button, badge, span, p")) {
        const st = getComputedStyle(el);
        if ((st.overflowX === "hidden" || st.overflowY === "hidden") && el.children.length === 0) {
          if (el.scrollWidth > el.clientWidth + 4 || el.scrollHeight > el.clientHeight + 8) {
            clipped.push({ tag: el.tagName, text: (el.innerText || "").slice(0, 40), clientW: el.clientWidth, scrollW: el.scrollWidth, clientH: el.clientHeight, scrollH: el.scrollHeight });
          }
        }
      }
      return { h1FontSizePx: h1Px, desktopOverflowPx, brokenImages, canvasCount: canvases.length, canvases, clippedText: clipped.slice(0, 8), totalHeight: document.body.scrollHeight };
    });

    await page.evaluate(() => window.scrollTo(0, Math.min(960, document.body.scrollHeight - 960)));
    await page.waitForTimeout(700);
    const midShot = path.join(outDir, "audit-desktop-mid.png");
    await page.screenshot({ path: midShot });

    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(600);
    const bottomShot = path.join(outDir, "audit-desktop-bottom.png");
    await page.screenshot({ path: bottomShot });

    await page.setViewportSize({ width: 390, height: 844 });
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(600);
    const mobileOverflowPx = await page.evaluate(() => Math.max(0, document.documentElement.scrollWidth - window.innerWidth));
    const mobileShot = path.join(outDir, "audit-mobile.png");
    await page.screenshot({ path: mobileShot });

    console.log(JSON.stringify({
      ok: runtimeErrors.length === 0 && diagnostics.desktopOverflowPx <= 2 && mobileOverflowPx <= 2 && diagnostics.brokenImages.length === 0 && diagnostics.clippedText.length === 0,
      runtimeErrors,
      horizontalOverflow: { desktopPx: diagnostics.desktopOverflowPx, mobilePx: mobileOverflowPx },
      brokenImages: diagnostics.brokenImages,
      clippedText: diagnostics.clippedText,
      metrics: { h1FontSizePx: diagnostics.h1FontSizePx, canvasCount: diagnostics.canvasCount, totalHeight: diagnostics.totalHeight },
      screenshots: { hero: heroShot, mid: midShot, bottom: bottomShot, mobile: mobileShot },
    }, null, 2));
  } finally {
    await browser.close();
    srv.close();
  }
}

(async () => {
  const { pos, flags } = parseArgs(process.argv.slice(2));
  const [cmd, target] = pos;
  const outDir = path.resolve(flags.out || path.join(os.tmpdir(), "ui-lookbook-scout"));
  if (cmd === "scout" && target) return cmdScout(target, outDir, flags.deep || 2);
  if (cmd === "audit" && target) return cmdAudit(target, outDir);
  console.error("Usage:\n  node visual_scout.cjs scout <godly|awwwards|minimal|navbar-megamenu|footer-typographic|curated|httpster|onepagelove|websitevice|brutalist|URL> [--out <dir>]\n  node visual_scout.cjs audit <project-dir> [--out <dir>]");
  process.exit(1);
})();
