"""Gluten-free places from Overture Maps (open data from Meta, Microsoft, Foursquare and others, ~60M places).

Keeps a place when its category says gluten-free, or its name says it in one of many languages.
Writes overture.json: [[id, lat, lon, name, why, cat, addr, website, phone, confidence, sources], ...]. Needs: pip install duckdb.
"""
import json, re, subprocess, sys, time, duckdb

rel = sorted(re.findall(r'PRE (\d{4}-\d{2}-\d{2}[\w.\-]*)/', subprocess.run(['aws', 's3', 'ls', 's3://overturemaps-us-west-2/release/', '--no-sign-request'], capture_output=True, text=True).stdout))[-1]
src = f"s3://overturemaps-us-west-2/release/{rel}/theme=places/type=place/*"
print('release', rel, flush=True)
db = duckdb.connect(); db.execute("INSTALL httpfs; LOAD httpfs; SET s3_region='us-west-2'; SET threads=8;")
cols = {r[0] for r in db.execute(f"DESCRIBE SELECT * FROM read_parquet('{src}', hive_partitioning=1) LIMIT 0").fetchall()}
print('columns', sorted(cols), flush=True)
GF = r"(?i)(gluten.?fre|glutenfrei|sin gl[uú]ten|sin tacc|senza glutine|sem gl[uú]ten|glutenvrij|sans gluten|bezglutenow|gluteeniton|glutenfri|bezlepkov|glutenmentes|gluténmentes|glutensiz|celiac|coeliac|cel[ií]ac|celiach|z[öo]liak)"
cat = "to_json(taxonomy)" if 'taxonomy' in cols else "to_json(categories)"
t0 = time.time()
rows = db.execute(f"""
  SELECT id, (bbox.ymin + bbox.ymax) / 2 lat, (bbox.xmin + bbox.xmax) / 2 lon, names.primary name, {cat} cats,
    to_json(addresses[1]) addr, websites[1] web, phones[1] phone, confidence, to_json(list_transform(sources, lambda s: s.dataset)) src
  FROM read_parquet('{src}', hive_partitioning=1)
  WHERE names.primary IS NOT NULL AND coalesce(operating_status, 'open') = 'open' AND coalesce(confidence, 1) >= 0.3
    AND ({cat} ILIKE '%gluten%' OR regexp_matches(names.primary, '{GF}') OR regexp_matches(coalesce(websites[1], ''), '{GF}'))
""").fetchall()
print(f'{len(rows)} places in {time.time() - t0:.0f} s', flush=True)
def kind(c):
    c = c.lower(); return 'bakery' if 'bak' in c or 'pastr' in c else 'cafe' if 'cafe' in c or 'coffee' in c or 'dessert' in c or 'ice_cream' in c else 'supermarket' if 'store' in c or 'market' in c or 'grocer' in c or 'shop' in c else 'restaurant' if 'restaurant' in c or 'food' in c or 'bar' in c or 'pizz' in c else 'other'
out = []
for i, la, lo, nm, cats, ad, web, ph, conf, srcs in rows:
    a = json.loads(ad) if ad else {}
    out.append([i, round(la, 5), round(lo, 5), nm, 'cat' if 'gluten' in (cats or '').lower() else 'name', kind(cats or ''), ', '.join(x for x in [a.get('freeform'), a.get('locality')] if x), web or '', ph or '', round(conf or 0, 2), ','.join(sorted(set(json.loads(srcs or '[]'))))])
json.dump(out, open('overture.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('by category', sum(r[4] == 'cat' for r in out), 'by name', sum(r[4] == 'name' for r in out))
print('sample', out[:3])
