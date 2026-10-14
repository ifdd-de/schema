(ifdd-schema-reference)=
# Reference

The variables of the template and their values in this instance are listed
in {ref}`ifdd-instances-static`. This page lists what is not a template
variable.

## Layout

| Path | Purpose |
|---|---|
| `nginx/default.conf` | server configuration (CORS, caching, compression, health endpoint) |
| `nginx/mime.types` | media types, including `application/ld+json` for `.jsonld` |
| `docker-compose-production.yml` | production: content from a separate clone |
| `docker-compose-development.yml` | local development: port on 127.0.0.1, examples as fallback content |
| `examples/json-ld/` | example content, instance-owned (on the cruft skip list) |
| `dotenv.dist` → `.env` | host name, content directory, development port; compose interpolation only |
| `tests/` | static checks and a Docker smoke test |

## Container

| | |
|---|---|
| port | 8080 (unprivileged nginx), routed by the proxy; not published in production |
| user | UID 101 |
| mounts | content → `/usr/share/nginx/html`, `nginx/default.conf` → `/etc/nginx/conf.d/default.conf`, `nginx/mime.types` → `/etc/nginx/mime.types`, all read-only |
| network | `{{ cookiecutter.ifdd_proxy_network }}` (external) |
| router and service | `{{ cookiecutter.ifdd_schema_prj_slug }}`, rule `Host(<IFDD_SCHEMA_HOST>)` |

## HTTP behaviour

| Aspect | Setting |
|---|---|
| CORS | `Access-Control-Allow-Origin: {{ cookiecutter.ifdd_schema_cors_origin }}` on every response, including errors; `OPTIONS` answers 204 |
| Caching | {% if cookiecutter.ifdd_schema_cache_max_age == "0" %}`Cache-Control: no-cache`{% else %}`Cache-Control: public, max-age={{ cookiecutter.ifdd_schema_cache_max_age }}`{% endif %} on successful responses, revalidation by ETag |
| Compression | gzip for JSON-LD, JSON and text from 1 KiB |
| Directory listing | {{ "on" if cookiecutter.ifdd_schema_autoindex == "y" else "off (directories answer 403)" }} |
| Files without extension | `text/plain; charset=utf-8` |
| Hidden files | 404 |
| Health | `GET /healthz` answers 200 |
