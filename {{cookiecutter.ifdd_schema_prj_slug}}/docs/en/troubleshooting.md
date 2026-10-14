(ifdd-schema-troubleshooting)=
# Troubleshooting

Known failure patterns. Start with
`docker compose -f docker-compose-production.yml logs schema` and a `curl` of
the failing URL.

| Symptom | Cause | Remedy |
|---|---|---|
| `docker compose` stops with `set IFDD_SCHEMA_CONTENT_DIR in .env` or `set IFDD_SCHEMA_HOST in .env` | the entry is missing in `.env` | set it ({ref}`ifdd-schema-setup`) |
| `docker compose` stops with `refers to undefined volume` | `IFDD_SCHEMA_CONTENT_DIR` is relative without `./` or `../` | use an absolute path or start it with `./` |
| every file answers 403 or 404 | the content directory is wrong, or its files are not readable for UID 101 | check the path in `.env` and the permissions (`umask 022` for the clone) |
| a directory answers 403 | directory listings are off (`ifdd_schema_autoindex`) | expected; request a file |
| a file under `.git` or another hidden path answers 404 | hidden files are never served | expected |
| a new content state is not visible | clients still use their cached copy | wait `{{ cookiecutter.ifdd_schema_cache_max_age }}` seconds, or reload without cache |
| a change in `nginx/` has no effect | nginx reads its configuration at start | restart the service |
| the browser reports a CORS error | the page's origin is not `{{ cookiecutter.ifdd_schema_cors_origin }}`, or the CSP of the page does not allow this host | check the browser console; `ifdd_schema_cors_origin`, and `connect-src` of the calling page |
| the service is 404 behind the proxy | the router is missing: container not on `{{ cookiecutter.ifdd_proxy_network }}`, not healthy yet, or `IFDD_SCHEMA_HOST` differs from the requested host | check the router in the proxy dashboard |
| the backend answers 502 `... [loading remote context failed] ...` | this service is not reachable from the backend container, its certificate is not trusted there, or the proxy's rate limit answered 429 | see the troubleshooting of the backend; `curl` the URL from its message inside the backend container |
| the backend answers 422 `context ... is not below ...` | the document names a context outside the backend's `IFDD_SCHEMA_URL` | use a context of this service, under the configured version directory |
