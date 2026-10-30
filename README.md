# ifdd-de/schema

cookiecutter/cruft template for the static content service `schema` of IFDD.
It serves the JSON-LD schemas (vocabulary) of the IFDD aspects.

The generated instance runs the upstream unprivileged nginx image behind the
IFDD proxy (`ifdd-de/proxy`) and builds no image of its own. The content is
not part of the instance: it lives in a separate repository whose clone is
mounted read-only. `ifdd-de/schema`, `ifdd-de/type` and `ifdd-de/unit` share
the same structure and differ only in names and examples.

## Generate an instance

```bash
cruft create --no-input --checkout <tag> \
  --config-file cookiecutter_all.yaml \
  --skip .env --skip examples \
  --output-dir ../instances https://github.com/ifdd-de/schema
```

The skip list keeps `.env` and the examples, both instance-owned, out of
every later `cruft update`. Then set `IFDD_SCHEMA_CONTENT_DIR` in `.env` of
the instance (see its README).

## Variables

| Variable | Default | Meaning |
|---|---|---|
| `ifdd_schema_prj_name`, `ifdd_schema_prj_slug` | `IFDD Schema`, derived | name; the slug names the directory and the Traefik router |
| `ifdd_schema_host` | `schema` | host name routed to the service (default for `IFDD_SCHEMA_HOST` in `.env`) |
| `ifdd_schema_dev_port` | `8081` | port on 127.0.0.1 in development (default for `IFDD_SCHEMA_DEV_PORT`) |
| `ifdd_schema_autoindex` | `y` | directory listings |
| `ifdd_schema_cors_origin` | `*` | `Access-Control-Allow-Origin`: `*` or one origin |
| `ifdd_schema_cache_max_age` | `300` | `Cache-Control` max-age in seconds, `0` for `no-cache`; **a starting value, not measured** |
| `ifdd_schema_memory_limit` | `128M` | memory limit of the container; **a starting value, not measured** |
| `ifdd_type_url` | `http://type/v1` | base URL of the `type` service, used in the example schemas; no trailing slash |
| `ifdd_nginx_image` | `nginxinc/nginx-unprivileged:1.30.6-alpine-slim` | nginx image; for a mirror, the image in the internal registry |
| `ifdd_proxy_network` | `proxy-net` | Docker network of the proxy |

`ifdd_nginx_image` and `ifdd_proxy_network` carry no service prefix: they are
the same for `schema`, `type` and `unit` (the network also for `proxy`).
The pre-generation hook rejects values that would render but not work.

## Contexts

The examples hold the five generic contexts (`base`, `product`, `function`,
`location`, `organisation`), readable for everyone with the node read role,
and two example domain contexts with dotted names
(`breaker.grid.example.ifdd.de`, `maintenance.ops.example.ifdd.de`), which
ifdd-be-core gives only to clients with a matching context pattern. Rules
for every context, checked by ifdd-be-core when a document is written:

- the file name without `.jsonld` is the context name: `base`, an aspect, or
  lower-case labels separated by dots;
- the six `c_*` terms are defined, in one namespace that ends with `/` or
  `#`;
- the namespace is `<ifdd_type_url>/<context name>/`, so its vocabulary
  (ifdd-de/type) explains every term.

## Layout

| Path | Purpose |
|---|---|
| `cookiecutter.json` | variables |
| `hooks/` | validation before, `.env` after generation |
| `{{cookiecutter.ifdd_schema_prj_slug}}/` | the instance, see its README |
| `tests/check_docs.py`, `tests/docs/` | used by `template-test.yml`: the documentation of the instance, see below |
| `tests/fixtures/` | `defaults`, `custom` (slug with hyphen, fixed origin, no-cache, no listing, other network) |

`.github` and `tests` inside the instance are on the copy-without-render list:
GitHub Actions expressions and shell syntax collide with Jinja.

## Documentation of the instance (`docs/`)

Every instance carries its operating documentation as Sphinx sources in
MyST Markdown, in English (`docs/en`) and German (`docs/de`), with the same
files, labels and headings in both. The pages follow the work around the
service: `index` (purpose, content rules, architecture), `setup`,
`build-release`, `operations`, `security`, `troubleshooting`, `reference`.
cookiecutter fills in the values of the instance. The instance README is
only an entry point that links to them. The pages of `ifdd-de/schema`,
`ifdd-de/type` and `ifdd-de/unit` have the same structure; keep them in
step.

The pages have no `conf.py` of their own: they are meant to be copied into a
Sphinx project that documents all services. That project needs `myst_parser`
and `sphinxcontrib.mermaid`. Labels start with `ifdd-schema-`; references to
`ifdd-instances-static` (the instance chapter of the meta repository)
resolve only there.

Rules for editing the pages in the template:

- change both languages in the same commit;
- no Jinja syntax in examples (`{{`, `{%`, `{#`); wrap such text in
  `{% raw %}`;
- the placeholder check of the CI greps the rendered instance for the text
  `cookiecutter` followed by a dot; do not write it literally.

`tests/check_docs.py` checks a rendered instance: same files, labels and
headings per level in both languages, every label with the prefix, every
reference to an own label resolvable, and a Sphinx build of each language
with `-W` (configuration `tests/docs/conf.py`, versions
`tests/docs/requirements.txt`).

## CI

| Workflow | Does |
|---|---|
| `template-test.yml` | renders each fixture, checks for leftover placeholders, runs the static checks, checks and builds the documentation (`tests/check_docs.py`), validates both compose files, starts the container in both modes and probes it |
| `template-update-test.yml` | generates from the latest tag, applies the current template with `cruft update`, fails on reject files, runs the static checks |

## Migrating from dd4-schema

The template, its URL and all variable names changed, so `cruft update` cannot
take an existing `dd4-schema` instance across. Generate a new instance, then:

1. Move the content into its own repository and clone it on the host.
2. Carry the host name over: `DD4_SCHEMA_HOST` → `IFDD_SCHEMA_HOST`, and set
   `IFDD_SCHEMA_CONTENT_DIR`.
3. Keep the slug of the old instance (`ifdd_schema_prj_slug`) if other
   configuration refers to its router name.
4. Stop the old container before starting the new one: both announce a
   router for the same host.

## Honesty notes

Documentation `docs/` (2026-10-13): rendered with cookiecutter 2.7.1 for
both fixtures and with the `cookiecutter_all.yaml` of the meta repository;
`tests/check_docs.py` passes for each (Sphinx 9.1.0, myst-parser 5.1.0,
sphinxcontrib-mermaid 2.1.1, Python 3.13) and the placeholder check finds
nothing. The instance tests fail as before this change, twice:
`test_schema_defines_every_cache_term_in_its_own_namespace` expects the
prefix of a context to be named like its file, which the two example domain
contexts (prefixes `breaker`, `maintenance`) do not do; observed on the
unchanged template too, not fixed here. The workflow file passes actionlint
1.7.12; the workflow itself has not run. Content: taken from the previous
instance README, this README and the configuration files; the memory limit
and the cache lifetime are marked as not measured. Also checked
(2026-10-13): one Sphinx project per language with the pages of all ten
service templates (rendered with `cookiecutter_all.yaml`), the instance chapter of
the meta repository and ifdd-be-core with its OpenAPI document builds with
`-W` and no suppressed warnings, so every cross reference resolves; the
Mermaid diagrams of all services, and of the option variants of the
fixtures, render in headless Chromium 141.0.7390.37 (Playwright 1.56.0,
Mermaid 11.12.1 served locally).

See the instance README. In short: the nginx configuration was exercised
with a real nginx binary and the compose files were validated with
`docker compose config`; the image tag and the running read-only container
were not (no Docker daemon at build time) and are covered by the CI smoke
test.

`examples/json-ld/v1/product.jsonld` defines `containedIn` (product -> location)
since 2026-10-05: the energy-grid profile of `ifdd-de/ct` links every product
to a location with it, and its integration test (`check` against these
contexts) found the term missing. `examples` is on the cruft skip list:
existing instances do not get the change with `cruft update`.

`schemaVersion` 0.10.0 (2026-10-06): the time terms of all five example
schemas are renamed to the cache metadata terms of `ifdd-de/be-core`:
`c_created`, `c_modified`, `c_cacheCreated`, `c_cacheUpdated`,
`c_validNotBefore`, `c_validNotAfter`, each with the IRI `<prefix>:c_<name>`
of its own namespace; `expire` is gone. be-core keeps these terms out of the
stored documents and adds them on read. The instance tests check that every
schema defines them and none of the old names; against the 0.9.1 examples
they fail (checked by rendering both states with cookiecutter 2.7.1). As
with `containedIn`, existing instances and the separate content repository
need the change by hand.

Domain contexts (2026-10-12): the two example domain contexts were loaded by
the tests of ifdd-be-core (same shape, test copies) and by its rules: name,
`c_*` terms, namespace ending with `/`. Rendered with cookiecutter 2.7.1;
`tests/test_config.py` parses them. Not checked: the content repository
(it needs the new files by hand, `examples` is on the skip list).

Cache-term test (2026-10-13): the test checks what `cache_namespace` of
ifdd-be-core checks (one namespace for the six `c_*` terms, ending with `/`
or `#`) instead of the prefix name. Rendered with cookiecutter 2.7.1 for both
fixtures and the `cookiecutter_all.yaml`: the instance tests pass, the two
example domain contexts included; the previous test failed for them. A
second test feeds the check contexts with mixed namespaces, a namespace
without `/` or `#`, and terms without `xsd:dateTime`; each is rejected. The
namespace is expanded by the test from the prefixes of the context, not by a
JSON-LD processor. Existing instances get the test with `cruft update`
(`tests/` is not on the skip list).
