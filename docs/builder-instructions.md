# Content Site - Builder v1 — Project Instructions

## Purpose
This project is the **builder**. It turns handoff packages from the design project ("Content Site - Design Agent v1")
into a real static website (HTML, CSS and a little JavaScript, no build step, no backend) and publishes it through
GitHub. It is the only project that uses git.

- Repository: https://github.com/bjathoeger/Claude-Static-Site-Designer (public)
- Live site: https://bjathoeger.github.io/Claude-Static-Site-Designer/ (GitHub Pages, deployed by the repository's
  workflow after the checks pass)

## How work arrives
The design project writes each package to its project folder on Bjarke's computer:
`C:\Users\BjarkeThøger\Documents\Content Site v5\Content Site - Design Agent v1\designs\<brief ID>\handoff-<date>\`
(also as `handoff-<date>.zip` beside it). Bjarke starts a session here linked to that computer and names the package
("build rune1 handoff-2026-10-30"). The package's format is in the repository's `docs/handoff-format.md`; start with
its `README.md` and `handoff.json`.

## Git and access
- Work in a clone of the repository in the cloud workspace, on a new branch per build:
  `build/<brief ID>-<page route or "home">-<handoff date>`. Never commit to `main` and never force-push. Bjarke
  reviews the pull request. Merge it only when he says to (his go-ahead in the chat) and its checks have passed;
  the merge deploys the site.
- GitHub access is given to this project's sessions for this one repository only. Never ask for a token in the chat,
  never write one into a file, a commit or a project doc. If access is missing, say so and stop.
- One commit per logical step is fine; the pull request is the unit of review.

## The routine for a package
1. **Read the package.** Request access to the brief's `designs\<ID>` folder if needed and read README.md, handoff.json, the brief copy, every artboard's HANDOFF comment, the
   screenshots (Lead and phone version, every state) and interactions.txt. Note `approved`: an unapproved package is
   built only when Bjarke says so, and the pull request says it is not approved.
2. **Copy the package unchanged** into the repository at `handoffs/<brief ID>/handoff-<date>/` (stage the zip and
   unpack it); `python3 tools/check_site.py` then confirms every file is there and unchanged (sha256). Packages never
   change; a later handoff of the same page is a new folder.
3. **Build the page** at `site/<route>/index.html` (the route is in handoff.json; the home page is `site/index.html`):
   - **Match the design.** The static export in `design/static/` is the reference for markup, CSS and content at the
     design widths; the screenshots are the truth. Desktop at the Lead's width and the phone version at its width must
     look like their screenshots; between and beyond them the layout is fluid. Unless a HANDOFF gives a breakpoint,
     the phone layout applies below 768 px and the desktop layout from 1024 px, with the content scaling in between:
     record the choice in BUILDLOG.md. Behaviour (menus, tabs, accordions,
     scrolling), motion (durations, easing) and `prefers-reduced-motion` come from the HANDOFF comments and the
     source's script; each tweak state in `screenshots/states/` is a state the built page must reach.
   - **Structure**: semantic HTML (real links and buttons, one `h1`, headings in order, labelled controls, visible
     focus, alt texts from the package). `<html lang="<source>" data-site-root="<path to the site root>">`.
   - **Shared parts** (`data-part`, e.g. the site menu): the desktop and phone designs of a part become one
     responsive part; one master copy in `site/partials/<name>.html`, pasted unchanged into every page (the check
     compares them); per-page differences (e.g. "you are here") via `aria-current` only.
   - **CSS**: `site/assets/css/tokens.css` (the guide and derived colours from handoff.json's `colours`, each derived
     one with its recipe as a comment; fonts as `@font-face` from `site/assets/fonts/`), `base.css` (shared rules),
     and one file per page or component. No CSS frameworks, no external fonts or CDNs.
   - **JavaScript**: small vanilla scripts in `site/assets/js/` (one per behaviour), `defer`, no frameworks, no
     tracking, nothing external.
   - **Assets**: copy the package's `assets/` files the page uses into `site/assets/` (same relative paths). All paths
     relative (the site lives under `/Claude-Static-Site-Designer/`).
   - **Links**: to the route of the page they name. A planned page with a fallback (`data-goto-else`, a subpage):
     link to the fallback's route until the page is live. Any other page that isn't built yet: link to its route
     anyway (the site's 404 page says it is coming) and keep it `planned` in site.json; `href="#"` stays where the design has no
     destination yet (list those in the pull request).
   - **Languages**: keep the `data-i18n` and `data-i18n-<attr>` keys from the static export, load
     `assets/js/i18n.js`, add the head snippet that avoids a flash of the wrong language (see `site/index.html`), and
     merge the package's texts with `python3 tools/merge_i18n.py <package>`. The language picker uses
     `data-lang-switch="<code>"` (already on it in the static export). Texts the design doesn't have but the build needs (the page `<title>`, meta
     description, a skip link, a menu button's label) get keys too: draft them in every language yourself and list
     them in BUILDLOG.md as machine-drafted. Translations are machine-drafted throughout (by the design project);
     no native-speaker review is expected.
   - **site.json**: the page's status `live`, its handoff (`handoffs/<ID>/handoff-<date>`), every other website page
     from the package's `site.pages` as `planned` with its route.
   - Strip everything handoff.json's `strip` lists (it is already out of the static export; don't bring it back from
     the source files).
4. **Check** in the cloud workspace (Playwright and Chromium are installed):
   - `npm ci`, then `python3 tools/check_site.py`, `npx html-validate "site/**/*.html"`, and
     `CHROMIUM_PATH=$(ls -d /opt/pw-browsers/chromium-*/chrome-linux/chrome) node tools/a11y.mjs`. All must pass.
   - `python3 tools/visual_compare.py handoffs/<ID>/handoff-<date>` and look at every sheet it writes (design,
     build, differences). Fix real differences; explain the rest in the pull request. States (menus open, other
     tabs, accordion items) are compared by eye with `screenshots/states/` and the State artboards' screenshots.
   - Click through every state (menus, tabs, accordions, language picker) at desktop and phone width, keyboard
     included.
5. **Record**: a BUILDLOG.md entry (handoff, branch, what was built, check results, build-only decisions and drafted
   texts, open questions); anything the handoff didn't settle goes into QUESTIONS.md with a recommendation, and is
   built the recommended way meanwhile when that is safe to change later.
6. **Pull request** to `main`: title `Build <page> from <ID> handoff-<date>`; body: approved or not (and why),
   what was built, check results, the visual comparison numbers per artboard and language, links with no
   destination, questions, and that merging it publishes the site. The repository's checks run on the pull
   request: wait for them and fix failures.
7. **Tell Bjarke** the pull request link and anything that needs his decision. On his go-ahead, merge it (once the
   checks have passed), or he merges it himself. The deploy workflow then publishes the site (one or two minutes):
   check that the deploy run succeeded and check the live page in every language.

## Always
- **The design is decided in the design project.** Never change a design to make building easier; when something
  can't be built as designed (or isn't specified), ask in QUESTIONS.md.
- **Design guide**: only the fonts and colours in the package (they follow the design guide); WCAG 2.1 AA as built,
  checked in every language at desktop and phone width.
- **Packages are read-only**: never edit anything under `handoffs/`.
- **Restricted images** (`restricted: true` in handoff.json: customer and partner logos, employee and event photos,
  awards) are used only where the package uses them. Publishing them in this public repository was accepted by
  Bjarke (22 Oct 2026).
- **The repository is public**: the briefs, designs and images in it can be read by anyone. Never commit secrets,
  tokens, or anything not in a package or built from one.
- **No build step, no backend, no external services** (fonts, scripts and images are all self-hosted).

## Where things live (repository)
`site/` the website (the only folder published) · `handoffs/` the packages · `tools/` the checks and helpers ·
`.github/workflows/` checks on pull requests and the Pages deployment · `docs/` the handoff format and these
instructions · `BUILDLOG.md` · `QUESTIONS.md`.
