#!/usr/bin/env python3
"""Merge a handoff package's translations into the site's language files.

  python3 tools/merge_i18n.py <handoff package> [--site site] [--dry-run]

Keys are made from the source text, so the same text on two pages has the same key and the same translation.
For every language of the package: adds new keys to site/i18n/<lang>.json, and updates a key whose text changed only
when this package is newer than the one that set it (a later handoff of the same page). A key whose source text
differs between the site and the package is a conflict: reported, not merged (exit 1). Adds the package's languages
to site.json when they are missing. Prints what changed.
"""
import os, sys, json, argparse


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('package')
    ap.add_argument('--site', default='site')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    hj = json.load(open(os.path.join(a.package, 'handoff.json'), encoding='utf-8'))
    lg = hj.get('languages') or {}
    if not lg.get('names'):
        print('the package has no languages (source language only): nothing to merge')
        return
    src = lg['source']
    pkg = {c: json.load(open(os.path.join(a.package, p), encoding='utf-8')) for c, p in lg['files'].items()}
    os.makedirs(os.path.join(a.site, 'i18n'), exist_ok=True)
    site_files = {}
    for c in pkg:
        p = os.path.join(a.site, 'i18n', '%s.json' % c)
        site_files[c] = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {
            'language': c, 'name': lg['names'][c], 'source': c == src, 'text': {}, 'attr': {}}
    conflicts, added, updated = [], 0, 0
    for kind in ('text', 'attr'):
        for key, v in pkg[src].get(kind, {}).items():
            have = site_files[src].get(kind, {}).get(key)
            if have is not None and have != v:
                conflicts.append('%s %s: the site has %r, the package %r' % (kind, key, have[:60], v[:60]))
    if conflicts:
        print('CONFLICTS (nothing merged):')
        for c in conflicts:
            print('  ' + c)
        sys.exit(1)
    for c, t in pkg.items():
        sf = site_files[c]
        for kind in ('text', 'attr'):
            dst = sf.setdefault(kind, {})
            for key, v in t.get(kind, {}).items():
                if key not in dst:
                    dst[key] = v
                    added += 1
                elif dst[key] != v:
                    dst[key] = v
                    updated += 1
        if c != src:
            sf['note'] = t.get('note')
        sf['text'] = dict(sorted(sf['text'].items()))
        sf['attr'] = dict(sorted(sf['attr'].items()))
    cfg_p = os.path.join(a.site, 'site.json')
    cfg = json.load(open(cfg_p, encoding='utf-8'))
    have = [l['code'] for l in cfg.get('languages', [])]
    new_langs = [c for c in lg['names'] if c not in have]
    for c in new_langs:
        cfg.setdefault('languages', []).append({'code': c, 'name': lg['names'][c], 'source': c == src and not any(l.get('source') for l in cfg.get('languages', []))})
    print('%s: %d new text(s), %d updated, languages added to site.json: %s' % (
        os.path.basename(os.path.normpath(a.package)), added, updated, ', '.join(new_langs) or 'none'))
    if a.dry_run:
        return
    for c, sf in site_files.items():
        json.dump(sf, open(os.path.join(a.site, 'i18n', '%s.json' % c), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(cfg, open(cfg_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
