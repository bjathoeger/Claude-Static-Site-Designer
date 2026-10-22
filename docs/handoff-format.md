# Handoff package format (`content-site-handoff/1`)

The contract between the design project (which writes packages) and the build project (which reads them). A package
is a folder `handoff-<YYYY-MM-DD>[-n]/` and never changes after it is delivered.

## Folder

```
README.md                    summary for people
handoff.json                 the manifest (below)
brief/<brief file>.md        copy of the brief
design/source/<slug>.dc.html canvas source per artboard (annotations stripped; behaviour code in its <script>)
design/static/<slug>.html    rendered HTML + CSS per artboard, default state, at the design width
screenshots/<slug>.<lang>.png        full page per language (Lead and phone version); states: source language
screenshots/states/<slug>--<tweak>-<value>.png   a tweak state, clipped to the sections it changes
i18n/<lang>.json             texts per language (only when the page has languages)
assets/fonts/…, assets/images/…      the files the page uses (same paths as the design project's folder)
interactions.txt             every link and button and what it does
```

Slugs: `rune1-d` (the Lead), `rune1-d-mobile` (phone version), `rune1-d-mobile-part-2` (a part),
`rune1-d-s4-finance-open` (a State artboard).

## design/static

- A complete HTML document: one `<style>` (the artboard's CSS, fonts as `@font-face` pointing at `../../assets/fonts/…`)
  and the page markup (`<div class="page">` whose children are the sections, in order).
- Fixed at the design width (the CSS sets `.page{width:…}`); the desktop and phone files together describe the
  responsive page. It is a reference and a starting point: the build makes it responsive, adds behaviour, and moves
  shared parts (data-part) into components.
- `data-i18n="<key>"`: the element's inner HTML is a translatable block (keep inline tags). `data-i18n-alt="<key>"`,
  `data-i18n-aria-label="<key>"` …: that attribute's text is translatable. Elements with `translate="no"` are the same
  in every language.
- Links: `href` is the target page's route relative to the site root (`productivity/`, `./` for the home page);
  `data-goto` names the website page, `data-goto-else` the page to use until it exists.
  The language picker carries `data-lang-switch="<code>"` (the site's i18n.js hook) as well as the canvas's `data-lang`. `href="#"` means no
  destination decided yet. `data-lang` marks the language picker (`aria-current` on the current language).
  `data-current-for="<page>|<page>"`: "you are here" on those pages.
- `data-part="<name>"`: a part shared by several pages (a site menu): build it once.
- Behaviour (tabs, menus, accordions) is not in the static file: it is described in the artboard's HANDOFF comment,
  coded in the source file's `renderVals()` and handlers, and shown in `screenshots/states/`.

## i18n/<lang>.json

```json
{"language": "sv", "name": "Svenska", "source": false, "note": "machine-drafted by Claude, not reviewed by a native speaker",
 "text": {"<key>": "<inner HTML>", …}, "attr": {"<key>": "<text>", …}}
```
Every `data-i18n` key in the static files has an entry in every language file when `languages.complete[<lang>]` is
true (handoff.py verify checks this).

## handoff.json

| Field | Meaning |
|---|---|
| `format` | `content-site-handoff/1` |
| `created` | UTC time |
| `brief` | `{id, file, copy}` |
| `canvas` | `{title, url}` of the Design canvas |
| `approved` | true when every section of the Lead was approved and the checks passed |
| `override`, `blockers` | when not approved: the user's reason and what was not ready |
| `notes` | things the builder should know (e.g. a HANDOFF that refers to an artboard outside the package) |
| `site` | `{home, pages: [{name, route, in_this_handoff, planned?, fallback?, fallback_route?}]}`: every website page and its route; planned subpages that links already point to |
| `page` | `{name, route, lead, desktop_width, phone_width}` |
| `languages` | `{source, names: {code: name}, complete: {code: bool}, files: {code: path}, translations: note}`, or `{source: null}` without languages |
| `artboards[]` | `{title, kind (lead, lead-part, phone, phone-part, state), slug, width, height, source, static, screenshots: {lang: path}, languages, handoff_comment, sections[], tweaks[], metrics}` |
| `artboards[].sections[]` | `{index, name, tag, class, id, top, height, background, approved, fingerprint}` (an unlabelled header is named "<next section> (its header)"; `approved` is null on phone versions and states: approval lives on the Lead's sections) |
| `artboards[].tweaks[]` | `{name, group, options, default, states: [{value, sections, screenshot}]}`: the design's interactive states, shown in place on the page. A State artboard (kind `state`) draws one of them as its own reference; where both exist, the State artboard is the reference and the tweak screenshot shows it in context |
| `artboards[].metrics` | `typography[]` (font, weight, style, size, lineHeight, letterSpacing, transform, count, tags, colours, sample), `colours` ({css colour: {text, background, border, outline, svg: count}}), `images[]` (path, alt, w, h, natural, objectFit, objectPosition, filter, opacity), `backgroundImages`, `fonts` |
| `links[]` | `{artboard, text, goto, else, route, status}` for page links (status: this page, planned page, planned subpage …), `{artboard, text, href, status}` for anchors, external links and links with no destination |
| `colours[]` | every colour rendered or written in the CSS (hover and other states included): `{css, hex, alpha, kind (guide, derived, unlisted), name, role?, uses, artboards}`; derived names are the recipes from the HANDOFF comments, to turn into tokens |
| `fonts[]` | font faces in use (family weight style) |
| `assets[]` | `{path, sha256, bytes, restricted, used_by}`; `restricted`: from the design guide's restricted folders (customer and partner logos, employee and event photos, awards): use only where the package uses them |
| `interactions` | path of interactions.txt |
| `changes` | with a previous package: `{previous, changed, added, removed}` sections (by artboard kind and name) |
| `strip` | canvas-only things that must not be built |
