#!/usr/bin/env python3
"""Checks the built site before it is published (run by CI on every pull request and before every deploy).

  python3 tools/check_site.py [--site site] [--handoffs handoffs] [--strict]

Errors (exit 1):
  site.json       missing or incomplete (languages with one source, pages with routes)
  pages           a "live" page in site.json without its index.html; an HTML file not listed as a page
  html            no <html lang>, no data-site-root (or a wrong one), not exactly one <h1>, <img> without alt
  links           an internal link to a file that doesn't exist, an anchor to an id that doesn't exist; links to
                  planned pages are warnings (they become errors with --strict)
  assets          src, href, srcset or CSS url() pointing at a missing file
  i18n            a data-i18n / data-i18n-<attr> key missing from any language file; a language file that isn't
                  listed in site.json; the language switcher missing on a page with keys
  leftovers       canvas-only bits: /_blob/ urls, board-NN.dc.html, sec-tag / role-tag, {{template holes}},
                  data-dc-tpl
  parts           a shared part (data-part="<name>") differs between pages, or from site/partials/<name>.html when
                  that file exists (aria-current and the language picker's state are ignored)
  handoffs        every handoffs/<ID>/<package>/handoff.json: its files exist and assets match their sha256
Warnings: href="#" (no destination yet), links to planned pages, external links (not fetched).
Only the Python standard library is used.
"""
import os, re, sys, json, hashlib, argparse
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

LEFTOVERS = [(r'/_blob/[0-9a-f]{8,}', 'canvas asset url /_blob/'), (r'board-\d+\.dc\.html', 'canvas artboard link'),
             (r'class="[^"]*\b(sec-tag|role-tag)\b', 'canvas label or chip'), (r'\{\{[A-Za-z_.]+\}\}', 'template hole {{…}}'),
             (r'data-dc-tpl=', 'canvas runtime attribute')]


class Doc(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.html_attrs, self.h1, self.ids, self.links, self.res, self.imgs = {}, 0, set(), [], [], []
        self.keys, self.attr_keys, self.switch, self.i18n_js, self.styles, self._in_style = set(), set(), False, False, [], False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html':
            self.html_attrs = a
        if tag == 'h1':
            self.h1 += 1
        if a.get('id'):
            self.ids.add(a['id'])
        if tag == 'a' and 'name' in a:
            self.ids.add(a['name'])
        if tag == 'a' and a.get('href') is not None:
            self.links.append(a['href'])
        for k in ('src', 'poster'):
            if a.get(k):
                self.res.append(a[k])
        if tag == 'link' and a.get('href'):
            self.res.append(a['href'])
        for k in ('srcset',):
            if a.get(k):
                self.res += [p.strip().split(' ')[0] for p in a[k].split(',') if p.strip()]
        if tag == 'img':
            self.imgs.append(a)
        if tag == 'script' and a.get('src', '').endswith('i18n.js'):
            self.i18n_js = True
        if 'data-i18n' in a:
            self.keys.add(a['data-i18n'])
        for k, v in a.items():
            if k.startswith('data-i18n-'):
                self.attr_keys.add(v)
        if 'data-lang-switch' in a:
            self.switch = True
        if a.get('style'):
            self.styles.append(a['style'])
        self._in_style = tag == 'style'

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == 'style':
            self._in_style = False

    def handle_data(self, d):
        if self._in_style:
            self.styles.append(d)


VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


def parts_of(src):
    """{name: outer HTML} of every element with data-part (the first of each name)."""
    out = {}
    for m in re.finditer(r'<([a-zA-Z][\w-]*)\b[^>]*\bdata-part="([^"]+)"[^>]*>', src):
        tag, name = m.group(1).lower(), m.group(2)
        if name in out:
            continue
        depth, i = 1, m.end()
        for t in re.finditer(r'<(/?)([a-zA-Z][\w-]*)\b[^>]*?(/?)>', src[m.end():]):
            if t.group(2).lower() != tag or t.group(2).lower() in VOID:
                continue
            depth += -1 if t.group(1) else (0 if t.group(3) else 1)
            if depth == 0:
                i = m.end() + t.end()
                break
        out[name] = src[m.start():i]
    return out


def norm_part(h):
    h = re.sub(r'\s+aria-current="[^"]*"', '', h)
    h = re.sub(r'\s+', ' ', h)
    return h.strip()


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 16), b''):
            h.update(b)
    return h.hexdigest()


def resolve(site, page_file, ref):
    """Path of an internal reference relative to the page, or None for external ones."""
    u = urlsplit(ref)
    if u.scheme or u.netloc or ref.startswith('//'):
        return None
    path = unquote(u.path)
    if not path:
        return page_file
    if path.startswith('/'):
        return 'ABSOLUTE'
    p = os.path.normpath(os.path.join(os.path.dirname(page_file), path))
    if path.endswith('/') or os.path.isdir(p):
        p = os.path.join(p, 'index.html')
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--site', default='site')
    ap.add_argument('--handoffs', default='handoffs')
    ap.add_argument('--strict', action='store_true', help='links to planned pages and href="#" are errors')
    a = ap.parse_args()
    errors, warnings = [], []
    site = os.path.abspath(a.site)
    E = lambda m: errors.append(m)
    W = lambda m: warnings.append(m)

    # site.json
    try:
        cfg = json.load(open(os.path.join(site, 'site.json'), encoding='utf-8'))
    except Exception as e:
        print('ERROR site/site.json: %s' % e)
        sys.exit(1)
    langs = cfg.get('languages') or []
    if sum(1 for l in langs if l.get('source')) != 1:
        E('site.json: exactly one language must have "source": true')
    codes = [l.get('code') for l in langs]
    pages = cfg.get('pages') or []
    live = {p['route']: p for p in pages if p.get('status') == 'live'}
    planned = {p['route']: p for p in pages if p.get('status') != 'live'}
    for r, p in live.items():
        f = os.path.join(site, r, 'index.html')
        if not os.path.exists(f):
            E('site.json: live page "%s" has no %s' % (p.get('name'), os.path.relpath(f)))

    # language files
    tables = {}
    for c in codes:
        f = os.path.join(site, 'i18n', '%s.json' % c)
        if not os.path.exists(f):
            E('i18n/%s.json missing (site.json lists %s)' % (c, c))
            continue
        try:
            tables[c] = json.load(open(f, encoding='utf-8'))
        except Exception as e:
            E('i18n/%s.json: %s' % (c, e))
    for f in os.listdir(os.path.join(site, 'i18n')) if os.path.isdir(os.path.join(site, 'i18n')) else []:
        if f.endswith('.json') and f[:-5] not in codes:
            E('i18n/%s is not a language in site.json' % f)

    # pages
    html_files = []
    for d, _, fs in os.walk(site):
        for f in fs:
            if f.endswith('.html'):
                html_files.append(os.path.join(d, f))
    routes_found = set()
    part_seen = {}
    pdir = os.path.join(site, 'partials')
    for p in sorted(html_files):
        if os.path.abspath(p).startswith(os.path.abspath(pdir) + os.sep):
            continue
        rel = os.path.relpath(p, site)
        src = open(p, encoding='utf-8').read()
        doc = Doc()
        doc.feed(src)
        if rel == '404.html':
            route = None
        else:
            route = '' if rel == 'index.html' else (os.path.dirname(rel) + '/' if rel.endswith('/index.html') or os.path.basename(rel) == 'index.html' else None)
        if route is not None:
            routes_found.add(route)
            if route not in live:
                E('%s: not a live page in site.json' % rel)
        elif rel != '404.html':
            W('%s: an HTML file that is not a page (not index.html)' % rel)
        for name, h in parts_of(src).items():
            master = os.path.join(pdir, name + '.html')
            ref = norm_part(open(master, encoding='utf-8').read()) if os.path.exists(master) else None
            if ref is not None and norm_part(h) != ref:
                E('%s: shared part "%s" differs from partials/%s.html' % (rel, name, name))
            elif ref is None:
                if name in part_seen and norm_part(h) != part_seen[name][1]:
                    E('%s: shared part "%s" differs from the one in %s' % (rel, name, part_seen[name][0]))
                part_seen.setdefault(name, (rel, norm_part(h)))
        for rx, what in LEFTOVERS:
            if re.search(rx, src):
                E('%s: %s left in' % (rel, what))
        if not doc.html_attrs.get('lang'):
            E('%s: <html> has no lang' % rel)
        root = doc.html_attrs.get('data-site-root')
        if rel == '404.html':
            pass       # served at any address: it links with the repository's path instead
        elif root is None:
            E('%s: <html> has no data-site-root' % rel)
        elif os.path.normpath(os.path.join(os.path.dirname(p), root)) != os.path.normpath(site):
            E('%s: data-site-root="%s" does not lead to the site root' % (rel, root))
        if doc.h1 != 1:
            E('%s: %d <h1> (exactly one expected)' % (rel, doc.h1))
        for im in doc.imgs:
            if 'alt' not in im:
                E('%s: <img src="%s"> has no alt (alt="" for decoration)' % (rel, im.get('src')))
        # links
        for h in doc.links:
            if h in ('', '#'):
                W('%s: a link with no destination (href="%s")' % (rel, h))
                continue
            if h.startswith(('mailto:', 'tel:', 'javascript:')):
                continue
            r = resolve(site, p, h)
            if r is None:
                continue
            if r == 'ABSOLUTE':
                if rel != '404.html':
                    E('%s: "%s" starts at the domain root; use a relative link (the site lives under /<repo>/)' % (rel, h))
                continue
            frag = urlsplit(h).fragment
            if not os.path.exists(r):
                rr = os.path.relpath(os.path.dirname(r), site).replace(os.sep, '/') + '/'
                rr = '' if rr == './' else rr
                if rr in planned:
                    (E if a.strict else W)('%s: links to planned page "%s" (%s)' % (rel, planned[rr].get('name'), h))
                else:
                    E('%s: broken link %s' % (rel, h))
                continue
            if frag and os.path.abspath(r) == os.path.abspath(p) and frag not in doc.ids:
                E('%s: anchor #%s has no element with that id' % (rel, frag))
        # assets
        refs = list(doc.res)
        for st in doc.styles:
            refs += re.findall(r'url\(\s*[\'"]?([^\'")]+)', st)
        for r0 in refs:
            if r0.startswith('data:'):
                continue
            r = resolve(site, p, r0)
            if r == 'ABSOLUTE':
                E('%s: "%s" starts at the domain root; use a relative path' % (rel, r0))
            elif r and not os.path.exists(r):
                E('%s: missing file %s' % (rel, r0))
        # i18n
        if doc.keys or doc.attr_keys:
            if not doc.i18n_js:
                E('%s: has data-i18n keys but does not load assets/js/i18n.js' % rel)
            if len(codes) > 1 and not doc.switch:
                W('%s: no language picker (data-lang-switch)' % rel)
            for c, t in tables.items():
                miss = sorted(k for k in doc.keys if k not in t.get('text', {}))
                miss_a = sorted(k for k in doc.attr_keys if k not in t.get('attr', {}))
                if miss:
                    E('%s: %d text(s) missing in i18n/%s.json, e.g. %s' % (rel, len(miss), c, ', '.join(miss[:5])))
                if miss_a:
                    E('%s: %d attribute text(s) missing in i18n/%s.json, e.g. %s' % (rel, len(miss_a), c, ', '.join(miss_a[:5])))
    # css files
    for d, _, fs in os.walk(site):
        for f in fs:
            if f.endswith('.css'):
                p = os.path.join(d, f)
                for r0 in re.findall(r'url\(\s*[\'"]?([^\'")]+)', open(p, encoding='utf-8').read()):
                    if r0.startswith('data:') or r0.startswith('#'):
                        continue
                    r = resolve(site, p, r0)
                    if r == 'ABSOLUTE':
                        E('%s: "%s" starts at the domain root' % (os.path.relpath(p, site), r0))
                    elif r and not os.path.exists(r):
                        E('%s: missing file %s' % (os.path.relpath(p, site), r0))

    # handoff packages
    hdir = os.path.abspath(a.handoffs)
    n_pk = 0
    if os.path.isdir(hdir):
        for d, _, fs in os.walk(hdir):
            if 'handoff.json' not in fs:
                continue
            n_pk += 1
            rel = os.path.relpath(d, os.path.dirname(hdir))
            try:
                hj = json.load(open(os.path.join(d, 'handoff.json'), encoding='utf-8'))
            except Exception as e:
                E('%s/handoff.json: %s' % (rel, e))
                continue
            need = [hj.get('brief', {}).get('copy')] + [x for b in hj.get('artboards', []) for x in [b.get('source'), b.get('static')] + list(b.get('screenshots', {}).values())]
            for x in need:
                if x and not os.path.exists(os.path.join(d, x)):
                    E('%s: %s missing' % (rel, x))
            for asset in hj.get('assets', []):
                f = os.path.join(d, asset['path'])
                if not os.path.exists(f):
                    E('%s: %s missing' % (rel, asset['path']))
                elif sha(f) != asset['sha256']:
                    E('%s: %s changed since the handoff (sha256); packages never change' % (rel, asset['path']))

    for w in warnings:
        print('warning: ' + w)
    for e in errors:
        print('ERROR: ' + e)
    print('\n%d page(s), %d language(s), %d handoff package(s): %d error(s), %d warning(s)' % (
        len(html_files), len(codes), n_pk, len(errors), len(warnings)))
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
