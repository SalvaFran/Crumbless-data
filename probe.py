"""Quick health check of each data source with tiny queries (Actions → Probe sources)."""
import time, urllib.request, urllib.parse
def go(name, url, data=None, headers={}, timeout=90):
    t0 = time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers={'User-Agent': 'crumbless-data probe', **headers}), timeout=timeout) as r:
            print(f'OK   {name}: {time.time()-t0:.1f}s {r.read(300).decode(errors="replace")!r}', flush=True)
    except Exception as e: print(f'FAIL {name}: {time.time()-t0:.1f}s {str(e)[:160]}', flush=True)
Q = 'PREFIX osmkey: <https://www.openstreetmap.org/wiki/Key:>\nSELECT (COUNT(?osm) AS ?n) WHERE { ?osm osmkey:diet:gluten_free ?gf }'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'
for ua in [UA, 'crumbless-data/1.0 (+https://github.com/SalvaFran/Crumbless-data)']:
    go('qlever GET ' + ua[:12], 'https://qlever.dev/api/osm-planet?' + urllib.parse.urlencode({'query': Q}), None, {'Accept': 'text/tab-separated-values', 'User-Agent': ua})
    go('qlever POST ' + ua[:12], 'https://qlever.dev/api/osm-planet', urllib.parse.urlencode({'query': Q}).encode(), {'Accept': 'text/tab-separated-values', 'User-Agent': ua, 'Content-Type': 'application/x-www-form-urlencoded'})
    go('qlever GET json ' + ua[:12], 'https://qlever.dev/api/osm-planet?' + urllib.parse.urlencode({'query': Q}), None, {'Accept': 'application/sparql-results+json', 'User-Agent': ua})
import subprocess; print(subprocess.run('curl -sI https://download.geofabrik.de/europe-latest.osm.pbf | head -5; curl -sI https://planet.openstreetmap.org/pbf/planet-latest.osm.pbf | head -4; which osmium; apt-cache policy osmium-tool | head -3', shell=True, capture_output=True, text=True).stdout, flush=True)
