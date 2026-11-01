"""Nightly export of every gluten-free place in OpenStreetMap, cut into 1-degree tiles the Crumbless app downloads.

Runs on GitHub Actions (no server needed). Standard library only.
Regions that fail after all retries keep yesterday's tiles, so a bad night never empties the map.
"""
import json, os, sys, time, glob, urllib.request, urllib.parse
from datetime import datetime, timezone

MIRRORS = ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter', 'https://overpass.private.coffee/api/interpreter']
F = ['::type', '::id', '::lat', '::lon', 'name', 'amenity', 'shop', 'cuisine', 'diet:gluten_free', 'addr:street', 'addr:housenumber', 'addr:city',
     'website', 'contact:website', 'phone', 'contact:phone', 'opening_hours', 'check_date', 'check_date:diet:gluten_free']
HEAD = f'[out:csv({",".join(f if f[0] == ":" else chr(34) + f + chr(34) for f in F)};false)][timeout:600][maxsize:1073741824];'
OUT = 'tiles'
# World cut in 20x30 degree regions (empty ocean regions answer in a second); dense areas are split further on failure.
REGIONS = [(s, w, s + 20, w + 30) for s in range(-60, 80, 20) for w in range(-180, 180, 30)]

def cat(t):
    a, s = t.get('amenity', ''), t.get('shop', '')
    if a in ('restaurant', 'fast_food', 'food_court', 'pub', 'bar', 'biergarten'): return 'restaurant'
    if a in ('cafe', 'ice_cream'): return 'cafe'
    if s in ('bakery', 'pastry', 'confectionery'): return 'bakery'
    return 'supermarket' if s else 'other'

def query(box, tries=2, timeout=200):
    q = HEAD + ('nwr["diet:gluten_free"~"^(only|yes|limited)$"](%s,%s,%s,%s);out center;' % box if box else 'nwr["diet:gluten_free"~"^(only|yes|limited)$"];out center;')
    for attempt in range(tries):
        for url in MIRRORS:
            t0 = time.time()
            try:
                req = urllib.request.Request(url, data=urllib.parse.urlencode({'data': q}).encode(), headers={'User-Agent': 'crumbless-data (github.com/SalvaFran/Crumbless-data)'})
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    x = r.read().decode()
                if 'runtime error' in x[:400] or 'rate_limited' in x[:400]: raise RuntimeError(x[:200])
                print(f'  {url.split("/")[2]} answered {box or "world"} in {time.time() - t0:.0f} s', flush=True)
                return [dict(zip(F, l.split('\t'))) for l in x.splitlines() if l]
            except Exception as e:
                print(f'  {url.split("/")[2]} failed for {box or "world"} after {time.time() - t0:.0f} s: {str(e)[:120]}', flush=True); time.sleep(5)
        time.sleep(30)
    return None

# QLever (University of Freiburg): the whole OpenStreetMap planet behind a fast SPARQL endpoint. Primary source.
QLEVER = 'https://qlever.cs.uni-freiburg.de/api/osm-planet'
QCOLS = ['amenity', 'shop', 'cuisine', 'addr:street', 'addr:housenumber', 'addr:city', 'website', 'contact:website', 'phone', 'contact:phone', 'opening_hours', 'check_date', 'check_date:diet:gluten_free']
QVARS = ['v%d' % i for i in range(len(QCOLS))]
SPARQL = ('PREFIX osmkey: <https://www.openstreetmap.org/wiki/Key:>\nPREFIX geo: <http://www.opengis.net/ont/geosparql#>\n'
  'SELECT ?osm ?gf ?name ?wkt ' + ' '.join('?' + v for v in QVARS) + ' WHERE {\n ?osm osmkey:diet:gluten_free ?gf . FILTER(?gf IN ("only", "yes", "limited"))\n'
  ' ?osm osmkey:name ?name .\n ?osm geo:hasGeometry/geo:asWKT ?wkt .\n' + ''.join(' OPTIONAL { ?osm <https://www.openstreetmap.org/wiki/Key:%s> ?%s }\n' % (c, v) for c, v in zip(QCOLS, QVARS)) + '}')

def lit(x):
    x = x.strip()
    if x.startswith('<') and x.endswith('>'): return x[1:-1]
    if x.startswith('"'): x = x[1:x.rfind('"')] if x.rfind('"') > 0 else x[1:]
    return x.replace('\\"', '"').replace('\\\\', '\\')

def centroid(wkt):
    nums = [float(v) for v in __import__('re').findall(r'-?\d+(?:\.\d+)?(?:e-?\d+)?', wkt.split('(', 1)[-1])]
    xs, ys = nums[0::2], nums[1::2]
    return (sum(ys) / len(ys), sum(xs) / len(xs)) if xs else (None, None)

def qlever():
    t0 = time.time()
    try:
        req = urllib.request.Request(QLEVER, data=urllib.parse.urlencode({'query': SPARQL}).encode(),
          headers={'Accept': 'text/tab-separated-values', 'User-Agent': 'crumbless-data (github.com/SalvaFran/Crumbless-data)'})
        with urllib.request.urlopen(req, timeout=900) as r: lines = r.read().decode().splitlines()
    except Exception as e:
        print(f'  QLever failed after {time.time() - t0:.0f} s: {str(e)[:200]}', flush=True); return None
    print(f'  QLever answered in {time.time() - t0:.0f} s with {len(lines) - 1} rows', flush=True)
    rows = []
    for l in lines[1:]:
        v = [lit(x) for x in l.split('\t')] + [''] * 20
        m = __import__('re').match(r'https://www\.openstreetmap\.org/(node|way|relation)/(\d+)', v[0])
        lat, lon = centroid(v[3])
        if not m or lat is None: continue
        t = {'::type': m[1], '::id': m[2], '::lat': str(lat), '::lon': str(lon), 'name': v[2], 'diet:gluten_free': v[1]}
        t.update({c: v[4 + i] for i, c in enumerate(QCOLS) if v[4 + i]}); rows.append(t)
    return rows

def fetch(box, depth=0):
    rows = query(box, tries=1 if depth < 2 else 2, timeout=120 if depth < 2 else 300)
    if rows is not None: return rows, []
    if depth >= 2: return [], [box]
    s, w, n, e = box; my, mx = (s + n) / 2, (w + e) / 2  # split in 4 and retry the smaller pieces
    out, failed = [], []
    for b in [(s, w, my, mx), (s, mx, my, e), (my, w, n, mx), (my, mx, n, e)]:
        r, f = fetch(b, depth + 1); out += r; failed += f
    return out, failed

def main():
    tiles, failed, n = {}, [], 0
    # One worldwide query first: a single tag lookup is what Overpass does fastest. Regions only if it fails.
    world = qlever()
    if not world: world = query(None, tries=1, timeout=600)
    batches = [(None, world)] if world is not None else ((b, None) for b in REGIONS)
    for i, (box, rows) in enumerate(batches):
        if rows is None: rows, f = fetch(box); failed += f
        for t in rows:
            if not t.get('name') or not t.get('::lat'): continue
            lat, lon = float(t['::lat']), float(t['::lon'])
            p = [t['::type'][0] + t['::id'], round(lat, 5), round(lon, 5), t['name'], 'only' if t.get('diet:gluten_free') == 'only' else 'options', cat(t),
                 ', '.join(x for x in [' '.join(x for x in [t.get('addr:street', ''), t.get('addr:housenumber', '')] if x), t.get('addr:city', '')] if x),
                 t.get('website') or t.get('contact:website', ''), t.get('phone') or t.get('contact:phone', ''), t.get('opening_hours', ''),
                 t.get('check_date:diet:gluten_free') or t.get('check_date', '')]
            tiles.setdefault(f'{int(lat // 1)}_{int(lon // 1)}', {})[p[0]] = p; n += 1
        print(f'[{i + 1}] {box or "world"}: {len(rows)} rows', flush=True)
    if n < 1000: sys.exit(f'Only {n} places, refusing to overwrite the data')
    os.makedirs(OUT, exist_ok=True)
    keep = set()
    for path in glob.glob(f'{OUT}/*.json'):  # tiles inside failed regions keep yesterday's data
        k = os.path.basename(path)[:-5]; la, lo = map(int, k.split('_'))
        if any(s <= la < n_ and w <= lo < e for s, w, n_, e in failed): keep.add(k)
        elif k not in tiles: os.remove(path)
    for k, ps in tiles.items():
        if k in keep: continue
        with open(f'{OUT}/{k}.json', 'w') as fh: json.dump({'p': sorted(ps.values())}, fh, ensure_ascii=False, separators=(',', ':'))
    with open('meta.json', 'w') as fh:
        json.dump({'updated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ'), 'places': n, 'tiles': len(tiles), 'failed_regions': failed}, fh)
    print(f'Done: {n} places in {len(tiles)} tiles, {len(failed)} regions kept from before')

if __name__ == '__main__':
    main()
