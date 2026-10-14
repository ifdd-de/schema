(ifdd-schema-index)=
# {{ cookiecutter.ifdd_schema_prj_name }} (schema)

The static content service `schema` of an IFDD node: it serves the JSON-LD
contexts of the aspects, which every stored document names in its
`@context`. It runs the upstream nginx image as an unprivileged user behind the
proxy and builds no image of its own: the configuration and the content are
mounted read-only. This chapter describes the instance
`{{ cookiecutter.ifdd_schema_prj_slug }}`, generated from the template
`ifdd-de/schema`, from the point of view of the people who set it up, run and
secure it.

| | |
|---|---|
| Host | `{{ cookiecutter.ifdd_schema_host }}` (default of `IFDD_SCHEMA_HOST` in `.env`; routed by the proxy) |
| Image | `{{ cookiecutter.ifdd_nginx_image }}` (shared by schema, type and unit) |
| Content | the directory `IFDD_SCHEMA_CONTENT_DIR` in `.env`, usually a clone of a separate content repository |
| Network | `{{ cookiecutter.ifdd_proxy_network }}` |
| Development | `http://127.0.0.1:{{ cookiecutter.ifdd_schema_dev_port }}/` |

## What the instance contains

The nginx configuration (`nginx/default.conf`, `nginx/mime.types`), two
compose files, `.env`, and example content in `examples/json-ld/`. The real
content is not part of the instance: it lives in its own repository, whose
clone is mounted read-only. `ifdd-de/schema`, `ifdd-de/type` and
`ifdd-de/unit` share this structure.

## Contexts

The content is a set of JSON-LD contexts, one file `<name>.jsonld` per
context below a version directory such as `v1/`. The backend loads the
context of every document it stores from here. Rules for every context,
checked by ifdd-be-core when a document is written:

- the file name without `.jsonld` is the context name: `base`, an aspect, or
  lower-case labels separated by dots (a domain context such as
  `breaker.grid.example.ifdd.de`, which the backend gives only to clients
  with a matching context pattern);
- the six `c_*` terms (`c_created`, `c_modified`, `c_cacheCreated`,
  `c_cacheUpdated`, `c_validNotBefore`, `c_validNotAfter`) are defined, in
  one namespace that ends with `/` or `#`;
- the namespace is `{{ cookiecutter.ifdd_type_url }}/<context name>/`, so its
  vocabulary in the type service explains every term.

The examples in `examples/json-ld/v1/` hold the five generic contexts
(`base`, `product`, `function`, `location`, `organisation`) and two example
domain contexts.

## Architecture

```{mermaid}
flowchart LR
  Clients[browsers, services] -->|HTTPS| Proxy[proxy: Traefik]
  Proxy -->|"{{ cookiecutter.ifdd_schema_host }}, port 8080"| Nginx[schema: nginx]
  Nginx -->|read-only| Content[(content clone)]
  Repo[content repository] -->|git pull| Content
```

| Who | Uses this service for |
|---|---|
| be | the context of every document it stores; the context must lie below its `IFDD_SCHEMA_URL` |
| ct | the fake data of its profiles names contexts of this service |
| clients reading documents | the `@context` IRIs in the documents |

## Chapters

```{toctree}
:maxdepth: 2

setup
build-release
operations
security
troubleshooting
reference
```

The values of the variables of this instance and how they relate to the
other services are listed in the chapter on the service instances
({ref}`ifdd-instances-static`).
