# Changelog

The version scheme follows the other IFDD templates: `YY.MM.N`.

## [26.10.2] - 2026-10-14

- Instance test of the `c_*` terms follows the rule of ifdd-be-core: all six
  `xsd:dateTime` terms in one namespace ending with `/` or `#`, whatever the
  prefix is called. The previous test demanded a prefix named like the file
  and failed for the two example domain contexts (prefixes `breaker`,
  `maintenance`), so the template CI was red.
- Documentation of the instance in `docs/en` and `docs/de` (Sphinx sources,
  MyST Markdown): index, setup, build and release, operations, security,
  troubleshooting, reference. The instance README is now an entry point with
  a quick start, the links, the honesty notes and the license; its former
  sections moved into the documentation.
- `docs/_build/` in `.gitignore` of the instance.
- Template CI: `tests/check_docs.py` checks that both languages match and
  build without warnings (`tests/docs/conf.py`, `tests/docs/requirements.txt`).

- Two example **domain contexts** (ifdd-be-core "Contexts and access"):
  `breaker.grid.example.ifdd.de.jsonld` (circuit breakers, simplified: serial
  number, manufacturer, year of manufacture, rated voltage and current as
  QUDT quantity values, operating mechanism) and
  `maintenance.ops.example.ifdd.de.jsonld` (maintenance interval, last and
  next inspection, condition). Like every context they define `objName`,
  `objType`, `objScope`, `origin`, `publisher` (values per context and
  source) and the six `c_*` terms; their namespace is
  `<ifdd_type_url>/<context name>/`, whose vocabulary ifdd-de/type serves.
  The five generic contexts are unchanged.

- `examples/json-ld/v1/product.jsonld`: `containedIn` (product -> location).
- `schemaVersion` 0.10.0 of all example schemas: `created`, `modified`,
  `cacheCreated`, `cacheUpdated`, `validNotBefore`, `validNotAfter` renamed to
  `c_created`, `c_modified`, `c_cacheCreated`, `c_cacheUpdated`,
  `c_validNotBefore`, `c_validNotAfter` (IRIs `<prefix>:c_<name>`); `expire`
  removed. Needed by the bitemporal storage of `ifdd-de/be-core`. `examples`
  is on the cruft skip list: existing instances and the content repository
  need the change by hand.
- Instance tests: every schema defines the c_* terms in its own namespace and
  none of the retired names.

## [26.10.1]

First release as `ifdd-de/schema`, successor of `dd4-schema`.

- Variables renamed from `dd4_schema_*` to `ifdd_schema_*`, environment
  variables from `DD4_SCHEMA_*` to `IFDD_SCHEMA_*`.
- No image of its own any more: runs the upstream unprivileged nginx image
  (`ifdd_nginx_image`), configuration and content mounted read-only.
  `Dockerfile.nginx`, the image tag and `dd4_registry_url` are gone.
- Content from a separate clone (`IFDD_SCHEMA_CONTENT_DIR`, required in
  production); the template ships examples in `examples/json-ld` only.
- No router `tls`/`certresolver`/`entrypoints` labels, and therefore no
  `..._enable_tls`/`..._enable_letsencrypt` variables: the proxy sets TLS on
  its entry point. Router and service are named after the slug.
- Proxy network from `ifdd_proxy_network`, with `traefik.docker.network`.
- nginx: CORS on every response (`always`), preflight 204, hidden files never
  served, `server_tokens off`, gzip for JSON-LD, `Cache-Control` from
  `ifdd_schema_cache_max_age`, directory listing from `ifdd_schema_autoindex`,
  `/healthz`, port 8080, IPv4 only.
- Container: read-only root file system, `cap_drop: ALL`,
  `no-new-privileges`, health check, memory limit; no `env_file`.
- Development compose file with a port on 127.0.0.1.
- Hooks: validation of all values; the post hook only creates `.env` (the
  unused password generator of the old hook is gone).
- Static checks and a Docker smoke test in every instance; template render,
  check and smoke test over two fixtures; cruft update test.
