"""Chains with a formal gluten-free protocol for celiacs, per country, each backed by an official or association source (listed in the app).
Matched on OpenStreetMap's brand / operator tags (or the exact name for distinctive names), and only inside that country."""
import json, os, re, urllib.request
# key: (countries, names, also match the plain name?, whole place is 100% gluten-free?). Generic words (Vicio, Totale, Pho...) match the brand tag only.
CHAINS = {
  # United Kingdom: Coeliac UK GF accreditation
  'gb-pizzaexpress': ('GB', ['PizzaExpress', 'Pizza Express'], True, False), 'gb-prezzo': ('GB', ['Prezzo'], True, False), 'gb-pizzahut': ('GB', ['Pizza Hut', 'Pizza Hut Delivery'], True, False),
  'gb-dominos': ('GB', ["Domino's", "Domino's Pizza"], True, False), 'gb-cote': ('GB', ['Côte', 'Côte Brasserie'], True, False), 'gb-bills': ('GB', ["Bill's"], False, False),
  'gb-browns': ('GB', ['Browns', 'Browns Brasserie & Bar'], False, False), 'gb-brunningprice': ('GB', ['Brunning & Price'], False, False), 'gb-millercarter': ('GB', ['Miller & Carter'], True, False),
  'gb-pho': ('GB', ['Pho'], False, False), 'gb-wadworth': ('GB', ['Wadworth'], False, False),
  # Spain: FACE programmes and own protocols
  'es-fosters': ('ES', ["Foster's Hollywood"], True, False), 'es-mcdonalds': ('ES', ["McDonald's"], True, False), 'es-telepizza': ('ES', ['Telepizza'], True, False),
  'es-vicio': ('ES', ['Vicio', 'VICIO'], False, False), 'es-xpecado': ('ES', ['XPecado', 'X Pecado'], True, False), 'es-totale': ('ES', ['Totale', 'TOTALE'], False, False),
  'es-sushigourmet': ('ES', ['Sushi Gourmet'], True, False), 'es-grossogf': ('ES', ['Senza Glutine di GROSSO', 'Senza Glutine di Grosso'], True, True),
  'es-tagliatellagf': ('ES', ['La Tagliatella Senza Glutine'], True, True), 'es-goikogf': ('ES', ['Goiko Gluten Free'], True, True),
  # Norway: Norsk cøliakiforening collaboration
  'no-mcdonalds': ('NO', ["McDonald's"], True, False), 'no-peppes': ('NO', ['Peppes Pizza'], True, False), 'no-circlek': ('NO', ['Circle K'], True, False), 'no-labaguette': ('NO', ['La Baguette'], True, False),
  # Poland, France/Belgium, Italy
  'pl-wolna': ('PL', ['WOLNA', 'Wolna Piekarnia', 'WOLNA piekarnia bezglutenowa'], False, True),
  'fr-copains': ('FR BE', ['Copains', 'Copains Boulangerie'], True, True),
  'it-mcdonalds': ('IT', ["McDonald's"], True, False),
  # Americas
  'ar-mcdonalds': ('AR', ["McDonald's"], True, False), 'ar-gout': ('AR CL', ['Goût', 'Gôut', 'Goût Gluten Free', 'Gout Gluten Free'], True, True),
  'ar-sintaxis': ('AR', ['Sintaxis', 'Sintaxis Sin TACC', 'Sintaxis Resto'], True, True), 'ar-eggsgreens': ('AR', ['Eggs & Greens', 'Eggs and Greens'], True, True),
  'ar-campobravo': ('AR', ['Campobravo', 'Campo Bravo'], True, True), 'ar-launion': ('AR', ['La Unión Gluten Free Bakery', 'La Union Gluten Free Bakery'], True, True),
  'br-pizzaforfun': ('BR', ['Pizza For Fun'], True, True), 'br-deliburger': ('BR', ['Deliburger'], True, True),
  'us-bibibop': ('US', ['BIBIBOP', 'BIBIBOP Asian Grill'], True, True), 'us-bolay': ('US', ['Bolay'], True, True), 'us-naminori': ('US', ['Nami Nori'], True, True),
  'us-tap': ('US', ['TAP Brazilian Café', 'TAP NYC', 'TAP'], False, True), 'us-posana': ('US', ['Posana'], True, True), 'us-cpk': ('US', ['California Pizza Kitchen', 'CPK'], True, False),
  # Asia-Pacific, Middle East
  'nz-hell': ('NZ', ['Hell Pizza', 'HELL Pizza', 'Hell'], False, False), 'au-hellagood': ('AU', ['Hella Good'], True, False), 'au-a25': ('AU', ['A25 Pizzeria', 'A25'], False, False),
  'ae-wildmoon': ('AE FR QA', ['Wild & The Moon', 'Wild and The Moon'], True, True), 'jp-tskitchen': ('JP', ["Gluten Free T's Kitchen", 'グルテンフリー ティーズキッチン'], True, True),
}
key = lambda s: re.sub(r'[^\w]', '', s.lower().replace('&', 'and'))
# Same brand in several countries (McDonald's): a name maps to all its chain keys; the country decides.
BRANDS, NAMES = {}, {}
for k, (_, ns, plain, _) in CHAINS.items():
    for n in ns: BRANDS.setdefault(key(n), []).append(k); plain and NAMES.setdefault(key(n), []).append(k)
def candidate(t):
    """Possible chain keys from tags (any country), or []."""
    for f in ('brand', 'operator'):
        if t.get(f) and key(t[f]) in BRANDS: return BRANDS[key(t[f])]
    return NAMES.get(key(t.get('name', '')), [])

_shapes = None
def country(lat, lon):
    """ISO code of the country at a point (Natural Earth borders, downloaded once)."""
    global _shapes
    if _shapes is None:
        from shapely.geometry import shape
        p = 'countries.geojson'
        if not os.path.exists(p): urllib.request.urlretrieve('https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson', p)
        want = {c for cs, *_ in CHAINS.values() for c in cs.split()}
        _shapes = [(f['properties']['ISO_A2_EH'], shape(f['geometry'])) for f in json.load(open(p))['features'] if f['properties'].get('ISO_A2_EH') in want]
    from shapely.geometry import Point
    pt = Point(lon, lat); return next((c for c, s in _shapes if s.contains(pt)), None)

def chain_of(t, lat, lon):
    ks = candidate(t)
    if not ks: return None
    cc = country(lat, lon); return next((k for k in ks if cc in CHAINS[k][0].split()), None)
