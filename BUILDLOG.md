# Build log

One entry per build, newest first: the handoff it was built from, the branch and pull request, what was built, the
check results, build-only decisions (and any texts the builder drafted itself, machine-drafted in every language),
and open questions.

## 2026-10-23 · Blog overview (home) from abigail1 handoff-2026-10-23
- **Handoff**: `handoffs/abigail1/handoff-2026-10-23` (approved; Lead abigail1-a · Library, phone abigail1-a · Mobile
  and its Part 2). English only. The package was unpacked from the zip unchanged; `.gitattributes` keeps every file
  under `handoffs/` byte for byte (no line-ending conversion), so the sha256 check holds on any checkout.
- **Branch**: `build/abigail1-home-2026-10-23`.
- **Built**: `site/index.html` (blog header, hero and featured, All stories with topic filter, sort, search and
  "Load more", Go deeper, footer); `assets/css/tokens.css`, `base.css`, `blog.css`, `site-footer.css`;
  `assets/js/story-filter.js`; `partials/site-footer.html`; the fonts and images the page uses; site.json (Blog
  overview live, Blog post planned at `blog-post/`); `i18n/en.json` (the package's texts plus the build's, the
  placeholder page's texts removed). The placeholder front page is replaced.
- **Checks**: Python and Node aren't installed on the machine this was built on, so `check_site.py`, html-validate,
  `a11y.mjs` and `visual_compare.py` didn't run locally: the first three run in CI on the pull request. The page was
  checked in a browser instead: at a 1440px content width the sections measure 77 / 1087 / 2105 / 638 / 335px
  (design 77 / 1087 / 2106 / 638 / 336); at 390px 65 / 1201 / 4538 / 822 / 804 (design 65 / 1203 / 4538 / 822 /
  805). No horizontal scrolling and no header or tool-bar overflow at 320, 600, 768, 900, 1024, 1180 and 1920px.
  Every target is at least 44px tall at phone width. Topic panel (open, Escape, outside click, picking), header
  topic shortcuts, sort, search, empty state and "Load more" all checked; the open panel matches
  `screenshots/states/abigail1-a-mobile--topicmenuopen-true.png`. No console errors. External links all return
  200.
- **Build-only decisions**:
  - Breakpoints: phone layout below 768px, desktop layout from 1024px. Between them the grid has 2 columns, Go deeper
    stacks, and the big type scales with the width (h1 58–112px, All stories 42–64px, Go deeper 38–56px, featured
    titles 30–44px / 26–30px). The header drops the qualiware.com link below 1180px and the topic shortcuts below
    1024px, because they don't fit (the Topic filter in All stories does the same job, as on the phone design).
    Above 1440px the content stays 1312px wide and centred; backgrounds run full width.
  - All 15 stories are in the HTML (newest first), so the page works without JavaScript; the script shows 9 and
    reveals the rest with "Load more" (focus moves to the first new story).
  - The topic panel also closes on a click outside it.
  - The header's topic shortcuts scroll to All stories after setting the filter (see QUESTIONS.md).
  - The footer is built as drawn (see QUESTIONS.md).
  - The French story's title has `lang="fr"`.
- **Texts drafted by the builder** (English only for now): page title "The QualiWare blog", meta description, "Skip
  to content", "Topic:", "All" (topic panel), the status line's parts ("All topics", "newest first", "oldest
  first", "A to Z", "matching “…”"), "No stories match. Try another topic or search word." and "Load more stories"
  (the last two and "Topic:" are the design's words; the static export had no keys for them).
- **Not translatable yet**: the story cards' titles, topics and dates and the topic panel's topic names come from
  the design's sample data without keys. They need keys (or a data file) when a second language arrives.
- **Open**:
  - The footer part links with `./` and `assets/…`, which only work on pages at the site root. When
    `blog-post/` is built, the shared part can't be byte-identical at both depths, which `check_site.py` requires.
    Suggestion: let the check compare parts after resolving links against each page's `data-site-root`, or write
    the part's links from the site root at build time.
  - The two questions in QUESTIONS.md.

## 2026-10-22 · Repository set up
- The checks and the Pages deployment (see README.md), a placeholder front page, the language switcher.
