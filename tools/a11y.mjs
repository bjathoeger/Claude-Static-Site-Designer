// Accessibility scan (axe-core, WCAG 2.0/2.1 A and AA) of every live page, in every language, at desktop and phone
// width. Run by CI on every pull request and before every deploy:  node tools/a11y.mjs [--site site]
// Exit 1 on any violation. Needs: npm ci && npx playwright install --with-deps chromium
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const argSite = process.argv.indexOf('--site');
const SITE = path.resolve(argSite > 0 ? process.argv[argSite + 1] : 'site');
const BASE = '/site-root/';            // pages are served below a sub-path, as on GitHub Pages (/<repo>/)
const WIDTHS = [1440, 390];
const TYPES = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp',
  '.gif': 'image/gif', '.woff2': 'font/woff2', '.woff': 'font/woff', '.mp4': 'video/mp4', '.ico': 'image/x-icon' };

const cfg = JSON.parse(fs.readFileSync(path.join(SITE, 'site.json'), 'utf8'));
const pages = (cfg.pages || []).filter(p => p.status === 'live');
const langs = (cfg.languages || []).map(l => l.code);

const server = http.createServer((req, res) => {
  let u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (!u.startsWith(BASE)) { res.writeHead(404); return res.end(); }
  let f = path.join(SITE, u.slice(BASE.length));
  if (!f.startsWith(SITE)) { res.writeHead(403); return res.end(); }
  if (fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, 'index.html');
  if (!fs.existsSync(f)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'content-type': TYPES[path.extname(f).toLowerCase()] || 'application/octet-stream' });
  fs.createReadStream(f).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const origin = `http://127.0.0.1:${server.address().port}`;

const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
let failed = 0, checked = 0;
for (const p of pages) {
  for (const lang of langs) {
    for (const w of WIDTHS) {
      const ctx = await browser.newContext({ viewport: { width: w, height: 900 }, reducedMotion: 'reduce' });
      const page = await ctx.newPage();
      const errors = [];
      page.on('pageerror', e => errors.push(String(e)));
      page.on('console', m => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) errors.push(m.text()); });
      page.on('response', r => { if (r.status() >= 400 && !r.url().endsWith('/favicon.ico')) errors.push(`${r.status()} ${r.url().replace(origin, '')}`); });
      const url = `${origin}${BASE}${p.route}?lang=${lang}`;
      await page.goto(url, { waitUntil: 'networkidle' });
      await page.waitForFunction(l => document.documentElement.lang === l && !document.documentElement.classList.contains('i18n-pending'), lang, { timeout: 5000 })
        .catch(() => errors.push(`the page did not switch to ${lang}`));
      const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
      checked++;
      const label = `${p.route || '/'} [${lang}, ${w}px]`;
      if (r.violations.length || errors.length) failed++;
      for (const v of r.violations) {
        console.log(`ERROR ${label}: ${v.id} (${v.impact}) ${v.help}`);
        for (const n of v.nodes.slice(0, 5)) console.log(`    ${n.target.join(' ')}  ${n.failureSummary.split('\n').slice(1, 2).join(' ').trim()}`);
        if (v.nodes.length > 5) console.log(`    … and ${v.nodes.length - 5} more`);
      }
      for (const e of errors) console.log(`ERROR ${label}: ${e}`);
      if (!r.violations.length && !errors.length) console.log(`ok    ${label}`);
      await ctx.close();
    }
  }
}
await browser.close();
server.close();
console.log(`\n${checked} page views checked, ${failed} with problems`);
process.exit(failed ? 1 : 0);
