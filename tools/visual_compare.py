#!/usr/bin/env python3
"""Compare a built page with its handoff's reference screenshots (for the builder, before opening a pull request).

  python3 tools/visual_compare.py <handoff package> [--site site] [--artboard rune1-d] [--lang en] [--out compare/]

For each artboard of kind lead and phone (or the one named) and each language it was screenshotted in (or the one
named): renders the built page (its route from handoff.json) at the artboard's width, full page, animations paused
and reduced motion on, and writes <out>/<slug>.<lang>.png with three columns: design, build, differences (red).
Prints the share of pixels that differ and the rows where the build is taller or shorter. A large difference is a
reason to look, not a verdict: animations, a responsive layout at exactly the design width, and fonts can differ a
little. Needs Playwright (Python) and Pillow.
"""
import os, sys, json, argparse, threading, http.server, functools
from PIL import Image, ImageChops


def serve(root):
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=os.path.dirname(root))
    h.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, 'http://127.0.0.1:%d/%s/' % (srv.server_address[1], os.path.basename(root))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('package')
    ap.add_argument('--site', default='site')
    ap.add_argument('--artboard')
    ap.add_argument('--lang')
    ap.add_argument('--out', default='compare')
    a = ap.parse_args()
    hj = json.load(open(os.path.join(a.package, 'handoff.json'), encoding='utf-8'))
    route = hj['page']['route']
    os.makedirs(a.out, exist_ok=True)
    srv, base = serve(os.path.abspath(a.site))
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        for ab in hj['artboards']:
            if a.artboard and ab['slug'] != a.artboard and ab['title'] != a.artboard:
                continue
            if not a.artboard and ab['kind'] not in ('lead', 'phone'):
                continue
            for lang, shot in ab['screenshots'].items():
                if a.lang and lang != a.lang:
                    continue
                ctx = b.new_context(viewport={'width': ab['width'], 'height': 900}, reduced_motion='reduce')
                pg = ctx.new_page()
                q = '' if lang in ('source', hj['languages'].get('source')) else '?lang=' + lang
                pg.goto(base + route + q, wait_until='networkidle')
                pg.wait_for_timeout(800)
                pg.evaluate("() => { for (const x of document.getAnimations()) { try { x.pause(); x.currentTime = 0; } catch (e) {} } }")
                built = os.path.join(a.out, '%s.%s.build.png' % (ab['slug'], lang))
                pg.screenshot(path=built, full_page=True)
                ctx.close()
                ref = Image.open(os.path.join(a.package, shot)).convert('RGB')
                got = Image.open(built).convert('RGB')
                w = max(ref.width, got.width)
                h = max(ref.height, got.height)
                pad = lambda im: (lambda c: (c.paste(im, (0, 0)), c)[1])(Image.new('RGB', (w, h), 'white'))
                r2, g2 = pad(ref), pad(got)
                diff = ImageChops.difference(r2, g2).convert('L').point(lambda v: 255 if v > 32 else 0)
                share = diff.histogram()[255] / float(w * h)
                red = Image.new('RGB', (w, h), (255, 255, 255))
                red.paste((220, 0, 0), mask=diff)
                sheet = Image.new('RGB', (w * 3 + 40, h), (240, 240, 240))
                for i, im in enumerate((r2, g2, red)):
                    sheet.paste(im, (i * (w + 20), 0))
                outp = os.path.join(a.out, '%s.%s.png' % (ab['slug'], lang))
                sheet.save(outp)
                print('%-28s %-4s design %dx%d, build %dx%d, %.1f%% of pixels differ -> %s' % (
                    ab['slug'], lang, ref.width, ref.height, got.width, got.height, share * 100, outp))
        b.close()
    srv.shutdown()


if __name__ == '__main__':
    main()
