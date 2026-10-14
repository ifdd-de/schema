(ifdd-schema-build-release)=
# Bauen und Freigeben

## Image

| Container | Image |
|---|---|
| `schema` | `{{ cookiecutter.ifdd_nginx_image }}` |

Die Instanz baut kein eigenes Image; sie betreibt das unprivilegierte
Upstream-nginx-Image mit `nginx/default.conf`, `nginx/mime.types` und dem
Inhalt, alle nur lesend eingebunden. Für einen Mirror `ifdd_nginx_image` auf
das Image in der internen Registry setzen. Die Variable teilen sich schema,
type und unit; sie in `.cookiecutter_all.yaml` ändern und mit
`cruft update --variables-to-update '{"ifdd_nginx_image": "<image>"}'`
übernehmen.

## Inhalte freigeben

Der Inhalt wird in seinem eigenen Repository freigegeben. Ein neuer Stand
geht mit `git pull` im Klon auf dem Host live, ohne Neustart. Wie und wann
dieses Pull geschieht (ein Timer, das Deploy-Skript), entscheidet jede
Umgebung selbst; das Template regelt es nicht. Welche Inhaltsrevision live
ist, wird hier nicht festgehalten; wenn es darauf ankommt, im Deploy-Schritt
protokollieren:

```bash
git -C "$IFDD_SCHEMA_CONTENT_DIR" rev-parse HEAD
```

Clients dürfen eine Antwort `{{ cookiecutter.ifdd_schema_cache_max_age }}` Sekunden
zwischenspeichern, bevor sie neu prüfen ({ref}`ifdd-schema-operations`).

## Tests

```bash
pip install -r tests/requirements.txt
pytest -q tests                  # statische Prüfungen, ohne Docker; nginx -t, wenn nginx installiert ist
tests/smoke.sh development       # startet den Container und prüft ihn vom Host aus
tests/smoke.sh production        # Health und eine Anfrage von innen
```

Die statischen Prüfungen lesen die Compose-Dateien und die
nginx-Konfiguration: keine `tls`-Labels am Router, die Härtung des
Containers, der Healthcheck, kein veröffentlichter Port in Produktion,
versteckte Dateien, CORS, der Medientyp von JSON-LD und dass die Beispiele
sich parsen lassen. Beide Smoke-Tests liefern `examples/json-ld` aus, legen
das Proxy-Netz an, wenn es fehlt, und hinterlassen keine Spuren.

## CI der Instanz

`.github/workflows/ci.yml` führt die statischen Prüfungen aus, validiert
beide Compose-Dateien, startet beide Smoke-Tests und meldet Abweichungen vom
Template (`cruft check`, `cruft diff`, nur informativ).

## Freigabe

Es gibt keinen Release-Workflow, weil kein Image gebaut wird.
