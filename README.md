# Claude Static Site Designer

A static website built from designs made on Claude Design canvases, published with GitHub Pages:
https://bjathoeger.github.io/Claude-Static-Site-Designer/

Two Claude projects work on it. The **design project** designs each page on a canvas and, when a page is approved,
writes a frozen **handoff package** (the brief, the designs, screenshots, translations and assets). The **builder
project** turns a package into the page, copies the package into this repository next to the site it built, and
opens a pull request. Merging the pull request publishes the site.

## Layout
| Path | What |
|---|---|
| `site/` | the website, the only folder that is published |
| `site/site.json` | the site's languages and pages (live or planned, with their routes) |
| `site/i18n/<lang>.json` | every text in every language, by key |
| `site/assets/js/i18n.js` | the language switcher (`?lang=sv`, remembered between pages) |
| `handoffs/<brief ID>/handoff-<date>/` | each handoff package, unchanged (format: `docs/handoff-format.md`) |
| `tools/` | the checks and the builder's helpers |
| `.github/workflows/` | checks on every pull request; deployment to Pages from `main` |
| `docs/` | the handoff format and the builder project's instructions |
| `BUILDLOG.md`, `QUESTIONS.md` | what was built from which handoff; questions for the design project |

Because the repository is public, the briefs and designs in `handoffs/` can be read by anyone on GitHub; only
`site/` is published as the website.

## Checks (pull requests, and before every deploy)
- `tools/check_site.py`: site.json, pages, `lang` and site-root markers, one `h1`, alt texts, internal links and
  anchors, missing files, translations complete in every language, shared parts identical on every page, no canvas
  leftovers, and every handoff package intact (sha256).
- `html-validate`: valid HTML (config: `.htmlvalidate.json`).
- `tools/a11y.mjs`: axe-core, WCAG 2.0/2.1 A and AA, every live page in every language at 1440 and 390 px.

Run them locally: `npm ci`, then `npm run check` (`npx playwright install chromium` once).
`tools/visual_compare.py <package>` compares a built page with its design screenshots.

## One-time setup (repository settings)
1. **Settings › Pages › Build and deployment › Source: GitHub Actions.**
2. **Settings › Branches › Add rule for `main`**: require a pull request before merging, and require the status check
   "checks" to pass. Then nothing reaches the live site without passing the checks and a merge you have approved.
3. Give the builder project access to this repository only (Contents, Pull requests and Workflows: read and write),
   never as a token pasted into a chat.
