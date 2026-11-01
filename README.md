# crumbless-data

Every place in the OpenStreetMap planet tagged `diet:gluten_free` = `only`, `yes` or `limited`, extracted every night by GitHub Actions (streamed planet file + osmium, no live query servers) and cut into 1° tiles for the Crumbless app.

- `tiles/{lat}_{lon}.json`: `{"p": [[id, lat, lon, name, level, category, address, website, phone, opening_hours, check_date], ...]}`; `level` is `only` (100% gluten-free) or `options`.
- `meta.json`: last update time and counts.
- Run it by hand: Actions → Update gluten-free places → Run workflow.

Data © OpenStreetMap contributors, available under the [Open Database License](https://www.openstreetmap.org/copyright).
