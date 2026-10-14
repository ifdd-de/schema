(ifdd-schema-reference)=
# Referenz

Die Variablen des Templates und ihre Werte in dieser Instanz stehen in
{ref}`ifdd-instances-static`. Diese Seite führt auf, was keine
Template-Variable ist.

## Aufbau

| Pfad | Zweck |
|---|---|
| `nginx/default.conf` | Server-Konfiguration (CORS, Caching, Kompression, Health-Endpunkt) |
| `nginx/mime.types` | Medientypen, darunter `application/ld+json` für `.jsonld` |
| `docker-compose-production.yml` | Produktion: Inhalt aus einem eigenen Klon |
| `docker-compose-development.yml` | lokale Entwicklung: Port auf 127.0.0.1, Beispiele als Ersatzinhalt |
| `examples/json-ld/` | Beispielinhalt, instanzeigen (auf der cruft-Skip-Liste) |
| `dotenv.dist` → `.env` | Hostname, Inhaltsverzeichnis, Entwicklungsport; nur für compose |
| `tests/` | statische Prüfungen und ein Docker-Smoke-Test |

## Container

| | |
|---|---|
| Port | 8080 (unprivilegiertes nginx), vom Proxy geroutet; in Produktion nicht veröffentlicht |
| Benutzer | UID 101 |
| Mounts | Inhalt → `/usr/share/nginx/html`, `nginx/default.conf` → `/etc/nginx/conf.d/default.conf`, `nginx/mime.types` → `/etc/nginx/mime.types`, alle nur lesend |
| Netz | `{{ cookiecutter.ifdd_proxy_network }}` (extern) |
| Router und Dienst | `{{ cookiecutter.ifdd_schema_prj_slug }}`, Regel `Host(<IFDD_SCHEMA_HOST>)` |

## HTTP-Verhalten

| Aspekt | Einstellung |
|---|---|
| CORS | `Access-Control-Allow-Origin: {{ cookiecutter.ifdd_schema_cors_origin }}` bei jeder Antwort, auch bei Fehlern; `OPTIONS` antwortet 204 |
| Caching | {% if cookiecutter.ifdd_schema_cache_max_age == "0" %}`Cache-Control: no-cache`{% else %}`Cache-Control: public, max-age={{ cookiecutter.ifdd_schema_cache_max_age }}`{% endif %} bei erfolgreichen Antworten, Neuprüfung über ETag |
| Kompression | gzip für JSON-LD, JSON und Text ab 1 KiB |
| Verzeichnislisten | {{ "an" if cookiecutter.ifdd_schema_autoindex == "y" else "aus (Verzeichnisse antworten 403)" }} |
| Dateien ohne Endung | `text/plain; charset=utf-8` |
| Versteckte Dateien | 404 |
| Health | `GET /healthz` antwortet 200 |
