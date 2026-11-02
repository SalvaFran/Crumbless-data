"""Turn the planet extract (gf.opl + nodes.opl, made by extract.sh) into 1-degree tiles for the Crumbless app.

Standard library only. Refuses to overwrite the data if the extract looks broken.
"""
import json, os, re, sys, glob
from datetime import datetime, timezone

OUT = 'tiles'
un = lambda s: re.sub(r'%([0-9a-fA-F]+)%', lambda m: chr(int(m[1], 16)), s)  # OPL escapes: %20% etc.

def opl(path):
    for l in open(path, encoding='utf-8'):
        f = {x[0]: x[1:] for x in l.rstrip('\n').split(' ') if x}
        yield l[0], l[1:].split(' ', 1)[0], f

def tags(s):
    return dict(un(kv).split('=', 1) if '=' in kv else (un(kv), '') for kv in s.split(',') if kv) if s else {}

def cat(t):
    a, s = t.get('amenity', ''), t.get('shop', '')
    if a in ('restaurant', 'fast_food', 'food_court', 'pub', 'bar', 'biergarten'): return 'restaurant'
    if a in ('cafe', 'ice_cream'): return 'cafe'
    if s in ('bakery', 'pastry', 'confectionery'): return 'bakery'
    return 'supermarket' if s else 'other'

from gfwords import GF  # noqa: E402  (same gluten-free words)
from chains import candidate, chain_of  # noqa: E402
norm = lambda s: {w for w in re.sub(r'[^a-z0-9 ]', '', s.lower()).split() if len(w) > 2}

def overture(tiles):
    """Add Overture Maps places (overture.json). Same place as an OpenStreetMap one (very close, or close with a shared name word): add the evidence to it."""
    if not os.path.exists('overture.json'): return 0
    new = merged = 0
    for oid, lat, lon, name, why, kind, addr, web, phone, conf, srcs in json.load(open('overture.json', encoding='utf-8')):
        ts = tiles.setdefault(f'{int(lat // 1)}_{int(lon // 1)}', []); nm = norm(name)
        m = next((p for p in ts if p[0][0] != 'o' and abs(p[1] - lat) < .0025 and abs(p[2] - lon) < .004 and (abs(p[1] - lat) < .0005 and abs(p[2] - lon) < .0008 or nm & norm(p[3]))), None)
        if m: m[17], m[18] = why, srcs; m[12] = 0 if why == 'cat' else m[12]; m[7] = m[7] or web; m[8] = m[8] or phone; m[6] = m[6] or addr; merged += 1
        else: ts.append(['o' + oid, lat, lon, name, 'options', kind, addr, web, phone, '', '', '', 1 if why == 'name' else 0, '', '', '', 0, why, srcs, '']); new += 1
    print(f'Overture: {new} new places, {merged} merged into OpenStreetMap ones')
    return new

def main():
    loc = {f'n{i}': (float(f['y']), float(f['x'])) for k, i, f in opl('nodes.opl') if k == 'n' and f.get('x')}
    tiles, n, skipped = {}, 0, 0
    for k, i, f in opl('gf.opl'):
        t = tags(f.get('T', ''))
        if not t.get('name'): continue
        g = t.get('diet:gluten_free') or t.get('gluten_free'); hint = 0 if g in ('only', 'yes', 'limited') else 1  # 1 = detected by name/cuisine
        img = t.get('image', '') if t.get('image', '').startswith('http') else (f"https://commons.wikimedia.org/wiki/Special:FilePath/{t['wikimedia_commons'][5:]}?width=800" if t.get('wikimedia_commons', '').startswith('File:') else '')
        if k == 'n' and f.get('x'): lat, lon = float(f['y']), float(f['x'])
        elif k == 'w':
            pts = [loc[r] for r in f.get('N', '').split(',') if r in loc]
            if not pts: skipped += 1; continue
            lat, lon = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        else: skipped += 1; continue  # relations (rare) have no simple point
        co = t.get('diet:coeliac') or t.get('diet:celiac'); g = g if g in ('only', 'yes', 'limited') else ('yes' if co in ('yes', 'only') else None)
        named = bool(GF.search(' '.join(v for kk, v in t.items() if kk in ('name', 'cuisine', 'description', 'website') or kk.startswith(('name:', 'description:', 'diet:gluten_free:')))))
        ch = chain_of(t, lat, lon) if candidate(t) else None
        if not g and not named and not ch: continue  # a chain outlet outside the chain's country
        hint = 0 if g or ch else 1
        note = next((t[k] for k in ('diet:gluten_free:note', 'diet:gluten_free:description', 'description') if t.get(k) and (k != 'description' or GF.search(t[k]))), '')[:240]
        p = [k + i, round(lat, 5), round(lon, 5), t['name'], 'only' if g == 'only' else 'options', cat(t),
             ', '.join(x for x in [' '.join(x for x in [t.get('addr:street', ''), t.get('addr:housenumber', '')] if x), t.get('addr:city', '')] if x),
             t.get('website') or t.get('contact:website', ''), t.get('phone') or t.get('contact:phone', ''), t.get('opening_hours', ''),
             t.get('check_date:diet:gluten_free') or t.get('check_date', ''), t.get('cuisine', ''), hint, img,
             g or '', note, 1 if t.get('check_date:diet:gluten_free') else 0, '', '', ch or '']
        tiles.setdefault(f'{int(lat // 1)}_{int(lon // 1)}', []).append(p); n += 1
    print(f'{n} OpenStreetMap places ({skipped} without a usable location)')
    n += overture(tiles)
    print(f'{n} places in {len(tiles)} tiles')
    if n < 5000: sys.exit(f'Only {n} places, refusing to overwrite the data')
    os.makedirs(OUT, exist_ok=True)
    for path in glob.glob(f'{OUT}/*.json'):
        if os.path.basename(path)[:-5] not in tiles: os.remove(path)
    for k, ps in tiles.items():
        with open(f'{OUT}/{k}.json', 'w', encoding='utf-8') as fh: json.dump({'p': sorted(ps)}, fh, ensure_ascii=False, separators=(',', ':'))
    with open('meta.json', 'w') as fh:
        json.dump({'updated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ'), 'places': n, 'tiles': len(tiles), 'source': 'OpenStreetMap planet'}, fh)

if __name__ == '__main__':
    main()
