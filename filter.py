"""Keep the objects from all.opl that are gluten-free (tagged, legacy tag, or gluten-free word in name/cuisine) -> gf.opl, nodes.txt."""
import re
GF = re.compile(r'gluten.?fre|glutenfrei|sin gluten|sin tacc|senza glutine|sem gl[uú]ten|glutenvrij|sans gluten|z[öo]liak|celiac|coeliac', re.I)
un = lambda s: re.sub(r'%([0-9a-fA-F]+)%', lambda m: chr(int(m[1], 16)), s)
ids, n = set(), 0
with open('gf.opl', 'w', encoding='utf-8') as out:
    for l in open('all.opl', encoding='utf-8'):
        m = re.search(r' T(\S*)', l); t = un(m[1]) if m else ''
        g = re.search(r'(?:^|,)(?:diet:gluten_free|gluten_free)=([^,]*)', t)
        name = re.search(r'(?:^|,)name=([^,]*)', t); cui = re.search(r'(?:^|,)cuisine=([^,]*)', t)
        if (g and g[1] in ('only', 'yes', 'limited')) or (not g and GF.search(f"{name[1] if name else ''} {cui[1] if cui else ''}")):
            out.write(l); n += 1
            if l[0] == 'w': w = re.search(r' N(\S+)', l); ids.update(w[1].split(',') if w else [])
open('nodes.txt', 'w').write('\n'.join(sorted(ids)) + '\n')
print(f'kept {n} gluten-free objects, {len(ids)} way nodes needed')
