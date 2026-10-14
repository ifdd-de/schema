# {{ cookiecutter.ifdd_schema_prj_name }}

Static content service `schema`, generated from the `ifdd-de/schema` template.
It serves the JSON-LD contexts of the IFDD aspects. It runs the upstream image `{{ cookiecutter.ifdd_nginx_image }}`
behind the IFDD proxy on the Docker network
`{{ cookiecutter.ifdd_proxy_network }}`; the configuration and the content are
mounted read-only.

## Quick start

```bash
git clone <content repository> /srv/ifdd/schema-content
# in .env: IFDD_SCHEMA_CONTENT_DIR=/srv/ifdd/schema-content
docker compose -f docker-compose-production.yml up -d
docker compose -f docker-compose-production.yml ps
```

Local development serves `examples/json-ld` on
`http://127.0.0.1:{{ cookiecutter.ifdd_schema_dev_port }}/`
(`docker compose -f docker-compose-development.yml up -d`).

## Documentation

Setup, build and release, operations, security, troubleshooting and
reference of this instance:

- English: [docs/en/index.md](docs/en/index.md)
- Deutsch: [docs/de/index.md](docs/de/index.md)

The pages are Sphinx sources in MyST Markdown, meant to be copied into a
documentation project that covers all services; GitHub shows them as plain
Markdown.

## Honesty notes

The nginx configuration was loaded and exercised with a real nginx binary
(1.24, outside Docker) while the template was built: CORS on success and
error responses, preflight, hidden files, content types, compression, cache
header, directory listing, health endpoint. The compose files were validated
with `docker compose config` (v5.5.1), including the refusal to start without
`IFDD_SCHEMA_HOST` or `IFDD_SCHEMA_CONTENT_DIR`.

Not verified at build time, because no Docker daemon was available: pulling
the image tag, the read-only root file system together with the entrypoint
scripts of the image, and the health check in the running container.
`tests/smoke.sh` in CI covers these.

## License

BSD-3-Clause, see `LICENSE`.
