(ifdd-schema-build-release)=
# Build and release

## Image

| Container | Image |
|---|---|
| `schema` | `{{ cookiecutter.ifdd_nginx_image }}` |

The instance builds no image of its own; it runs the upstream unprivileged
nginx image with `nginx/default.conf`, `nginx/mime.types` and the content
mounted read-only. For a mirror, set `ifdd_nginx_image` to the image in the
internal registry. The variable is shared by schema, type and unit; change it
in `.cookiecutter_all.yaml` and apply it with
`cruft update --variables-to-update '{"ifdd_nginx_image": "<image>"}'`.

## Content releases

The content is released in its own repository. A new state goes live with
`git pull` in the clone on the host, without a restart. How and when that
pull happens (a timer, the deploy script) is up to each environment and not
part of this template. Which content revision is live is not recorded here;
if that matters, log it in the deploy step:

```bash
git -C "$IFDD_SCHEMA_CONTENT_DIR" rev-parse HEAD
```

Clients may keep a cached response for `{{ cookiecutter.ifdd_schema_cache_max_age }}`
seconds before they revalidate ({ref}`ifdd-schema-operations`).

## Tests

```bash
pip install -r tests/requirements.txt
pytest -q tests                  # static checks, no Docker; nginx -t if nginx is installed
tests/smoke.sh development       # starts the container, probes it from the host
tests/smoke.sh production        # health and one request from inside
```

The static checks read the compose files and the nginx configuration: no
router `tls` labels, the container hardening, the health check, no published
port in production, hidden files, CORS, the media type of JSON-LD, and that
the examples parse. Both smoke tests serve `examples/json-ld`, create the
proxy network if it is missing and leave no trace.

## CI of the instance

`.github/workflows/ci.yml` runs the static checks, validates both compose
files, runs both smoke tests and reports template drift (`cruft check`,
`cruft diff`, informational).

## Release

There is no release workflow, because no image is built.
