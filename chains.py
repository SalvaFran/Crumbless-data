"""Chains with a formal gluten-free protocol for celiacs, per country, each backed by an official or association source (listed in the app).
Matched on OpenStreetMap's brand / operator tags (or the exact name for distinctive names), and only inside that country."""
import json, os, re, urllib.request
# key: (country ISO code, names, match the plain name too?)
CHAINS = {
  'gb-pizzaexpress': ('GB', ['PizzaExpress', 'Pizza Express'], True), 'gb-prezzo': ('GB', ['Prezzo'], True), 'gb-pizzahut': ('GB', ['Pizza Hut', 'Pizza Hut Delivery'], True),
  'gb-dominos': ('GB', ["Domino's", "Domino's Pizza"], True), 'gb-cote': ('GB', ['Côte', 'Côte Brasserie'], True), 'gb-bills': ('GB', ["Bill's"], False),
  'gb-browns': ('GB', ['Browns', 'Browns Brasserie & Bar'], False), 'gb-brunningprice': ('GB', ['Brunning & Price'], False), 'gb-millercarter': ('GB', ['Miller & Carter'], True),
  'gb-pho': ('GB', ['Pho'], False), 'gb-wadworth': ('GB', ['Wadworth'], False),
  'es-fosters': ('ES', ["Foster's Hollywood"], True),
  'ar-mcdonalds': ('AR', ["McDonald's"], True),
}
key = lambda s: re.sub(r'[^a-z0-9]', '', s.lower().replace('&', 'and'))
BRANDS = {key(n): k for k, (_, ns, _) in CHAINS.items() for n in ns}
NAMES = {key(n): k for k, (_, ns, plain) in CHAINS.items() if plain for n in ns}
def candidate(t):
    """Chain key from tags (any country), or None."""
    for f in ('brand', 'operator'):
        if t.get(f) and key(t[f]) in BRANDS: return BRANDS[key(t[f])]
    return NAMES.get(key(t.get('name', '')))

_shapes = None
def country(lat, lon):
    """ISO code of the country at a point (Natural Earth borders, downloaded once)."""
    global _shapes
    if _shapes is None:
        from shapely.geometry import shape
        p = 'countries.geojson'
        if not os.path.exists(p): urllib.request.urlretrieve('https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson', p)
        want = {c for c, _, _ in CHAINS.values()}
        _shapes = [(f['properties']['ISO_A2_EH'], shape(f['geometry'])) for f in json.load(open(p))['features'] if f['properties'].get('ISO_A2_EH') in want]
    from shapely.geometry import Point
    pt = Point(lon, lat); return next((c for c, s in _shapes if s.contains(pt)), None)

def chain_of(t, lat, lon):
    k = candidate(t)
    return k if k and country(lat, lon) == CHAINS[k][0] else None
