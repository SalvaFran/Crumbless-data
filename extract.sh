#!/usr/bin/env bash
# Stream the whole OpenStreetMap planet (never stored on disk) and keep only what Crumbless needs.
# Pass 1: every node/way/relation with a diet:gluten_free tag. Pass 2: coordinates of the nodes those ways use.
set -euo pipefail
MIRRORS=(https://ftp5.gwdg.de/pub/misc/openstreetmap/planet.openstreetmap.org/pbf/planet-latest.osm.pbf
         https://ftp.fau.de/osm-planet/pbf/planet-latest.osm.pbf
         https://planet.openstreetmap.org/pbf/planet-latest.osm.pbf)
stream() { for u in "${MIRRORS[@]}"; do echo "  from $u" >&2; curl -fsSL --retry 2 "$u" | "$@" && return 0; echo "  failed, next mirror" >&2; done; return 1; }

t=$(date +%s)
stream osmium tags-filter -F pbf - nwr/diet:gluten_free --omit-referenced -f opl -o gf.opl --overwrite
echo "pass 1: $(wc -l < gf.opl) tagged objects in $(( $(date +%s) - t )) s"

python3 -c "
import re
ids = set()
for l in open('gf.opl'):
    if l[0] == 'w': m = re.search(r' N(\S+)', l); ids.update(m[1].split(',') if m else [])
open('nodes.txt', 'w').write('\n'.join(sorted(ids)) + '\n')
print('way nodes needed:', len(ids))"

t=$(date +%s)
stream osmium getid -F pbf - -i nodes.txt -f opl -o nodes.opl --overwrite
echo "pass 2: $(wc -l < nodes.opl) node locations in $(( $(date +%s) - t )) s"
