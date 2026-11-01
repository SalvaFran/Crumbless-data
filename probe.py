"""Quick health check of each data source with tiny queries (Actions → Probe sources)."""
import time, urllib.request, urllib.parse
def go(name, url, data=None, headers={}, timeout=90):
    t0 = time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers={'User-Agent': 'crumbless-data probe', **headers}), timeout=timeout) as r:
            print(f'OK   {name}: {time.time()-t0:.1f}s {r.read(300).decode(errors="replace")!r}', flush=True)
    except Exception as e: print(f'FAIL {name}: {time.time()-t0:.1f}s {str(e)[:160]}', flush=True)
Q = 'PREFIX osmkey: <https://www.openstreetmap.org/wiki/Key:>\nSELECT (COUNT(?osm) AS ?n) WHERE { ?osm osmkey:diet:gluten_free ?gf }'
import http.client
c = http.client.HTTPSConnection('qlever.cs.uni-freiburg.de', timeout=20); c.request('GET', '/api/osm-planet?query=x'); r = c.getresponse(); print('REDIRECT', r.status, r.getheader('Location'), flush=True)
for base in ['https://qlever.dev/api/osm-planet', (r.getheader('Location') or '').split('?')[0]]:
    if base: go('qlever count ' + base, base, urllib.parse.urlencode({'query': Q}).encode(), {'Accept': 'text/tab-separated-values'})
go('qlever count', 'https://qlever.cs.uni-freiburg.de/api/osm-planet', urllib.parse.urlencode({'query': Q}).encode(), {'Accept': 'text/tab-separated-values'})
Q2 = 'PREFIX osmkey: <https://www.openstreetmap.org/wiki/Key:>\nPREFIX geo: <http://www.opengis.net/ont/geosparql#>\nSELECT ?osm ?gf ?name ?wkt WHERE { ?osm osmkey:diet:gluten_free ?gf . ?osm osmkey:name ?name . ?osm geo:hasGeometry/geo:asWKT ?wkt } LIMIT 3'
go('qlever sample', 'https://qlever.dev/api/osm-planet', urllib.parse.urlencode({'query': Q2}).encode(), {'Accept': 'text/tab-separated-values'})
for u in ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter', 'https://overpass.private.coffee/api/interpreter', 'https://overpass.osm.jp/api/interpreter', 'https://overpass.openstreetmap.ru/api/interpreter']:
    go(u.split('/')[2], u, urllib.parse.urlencode({'data': '[out:csv(::id;false)][timeout:25];node["diet:gluten_free"="only"](53.5,9.9,53.6,10.0);out;'}).encode(), timeout=40)
go('overpass status', 'https://overpass-api.de/api/status', timeout=20)
