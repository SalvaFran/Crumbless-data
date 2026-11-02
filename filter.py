"""Keep the objects from all.opl that are gluten-free (tagged, legacy tag, or gluten-free word in name/cuisine) -> gf.opl, nodes.txt."""
import re
from gfwords import GF
from chains import candidate
un = lambda s: re.sub(r'%([0-9a-fA-F]+)%', lambda m: chr(int(m[1], 16)), s)
ids, n = set(), 0
with open('gf.opl', 'w', encoding='utf-8') as out:
    for l in open('all.opl', encoding='utf-8'):
        m = re.search(r' T(\S*)', l); t = un(m[1]) if m else ''
        g = re.search(r'(?:^|,)(?:diet:gluten_free|gluten_free)=([^,]*)', t)
        co = re.search(r'(?:^|,)diet:c[o]?eliac=(yes|only)', t)
        # Words checked: name, cuisine, description, notes about the gluten-free tag, website address.
        txt = ' '.join(m[1] for m in re.finditer(r'(?:^|,)(?:name|name:\w+|cuisine|description|description:\w+|diet:gluten_free:\w+|website)=([^,]*)', t))
        tt = dict(kv.split('=', 1) for kv in t.split(',') if '=' in kv) if ('brand=' in t or 'operator=' in t or 'name=' in t) else {}
        if (g and g[1] in ('only', 'yes', 'limited')) or co or (not g and GF.search(txt)) or candidate(tt):
            out.write(l); n += 1
            if l[0] == 'w': w = re.search(r' N(\S+)', l); ids.update(w[1].split(',') if w else [])
open('nodes.txt', 'w').write('\n'.join(sorted(ids)) + '\n')
print(f'kept {n} gluten-free objects, {len(ids)} way nodes needed')
