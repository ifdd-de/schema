(ifdd-schema-setup)=
# Setup

## Prerequisites

| What | Why |
|---|---|
| Docker with Compose | nginx runs as a container |
| the external network `{{ cookiecutter.ifdd_proxy_network }}` and a running proxy instance | Traefik routes `{{ cookiecutter.ifdd_schema_host }}` to this service by its labels |
| name resolution inside containers | the backend loads contexts from here inside its container, so the proxy must list `{{ cookiecutter.ifdd_schema_host }}` in `ifdd_proxy_internal_hosts` |
| a clone of the content repository on the host | the content is served from there |

## Create the instance

Usually the meta repository creates every instance in one go
(`.adm_meta_01_all.sh`, step `.adm_01_create_services.sh`) with the shared
variable file `.cookiecutter_all.yaml`. By hand, from the directory that
holds the instances:

```bash
cruft create --no-input --config-file .cookiecutter_all.yaml \
  --skip .env --skip examples \
  https://github.com/ifdd-de/schema
```

The skip list keeps `.env` and the examples, both instance-owned, out of
every later `cruft update`. The meta repository passes `--skip envs --skip
.env`.

## Configuration

The post-generation hook writes `.env` from `dotenv.dist` (mode 0600; an
existing `.env` is never touched). `.env` only feeds the `${...}` of the
compose files; nothing from it reaches the container.

| Entry | Default here | Meaning |
|---|---|---|
| `IFDD_SCHEMA_HOST` | `{{ cookiecutter.ifdd_schema_host }}` | host name the proxy routes to this service; required |
| `IFDD_SCHEMA_CONTENT_DIR` | `{{ cookiecutter.ifdd_schema_content_dir }}` | directory to serve; required in production |
| `IFDD_SCHEMA_DEV_PORT` | `{{ cookiecutter.ifdd_schema_dev_port }}` | port on 127.0.0.1 in development |

Every other value comes from the variables of the template; they are listed
with their values and meaning in {ref}`ifdd-instances-static`.

## Content

The content lives in its own repository, cloned separately on the host. This
service only needs the path of the directory to serve:

```bash
git clone <content repository> /srv/ifdd/schema-content
# in .env:
IFDD_SCHEMA_CONTENT_DIR=/srv/ifdd/schema-content
```

`/srv/ifdd/schema-content` is an example.

- Point the variable at the directory whose files are to be served. If the
  content repository keeps them in a subdirectory, point it there.
- Use an absolute path, or a relative one starting with `./` or `../`.
  Without that prefix compose reads the value as a volume name and refuses
  to start (`refers to undefined volume`).
- The container runs as UID 101 and needs read access: files must be
  readable for "others", which a clone with the usual `umask 022` is.
- Hidden files and directories (`.git`, `.gitignore`, ...) are never served,
  so mounting the root of a clone is safe.

## First start

```bash
docker network create {{ cookiecutter.ifdd_proxy_network }}   # once per host, unless the proxy already did
docker compose -f docker-compose-production.yml up -d
docker compose -f docker-compose-production.yml ps
```

Without `IFDD_SCHEMA_HOST` or `IFDD_SCHEMA_CONTENT_DIR` in `.env`, `docker compose` refuses
to start with a message naming the variable. `ps` should report the service
as healthy.

## Local development

```bash
docker compose -f docker-compose-development.yml up -d
curl http://127.0.0.1:{{ cookiecutter.ifdd_schema_dev_port }}/
```

Serves `examples/json-ld` unless `IFDD_SCHEMA_CONTENT_DIR` is set; the port comes
from `IFDD_SCHEMA_DEV_PORT` and is bound to 127.0.0.1 only. The network
`{{ cookiecutter.ifdd_proxy_network }}` must exist.

## Behind the proxy

The labels announce one router and one service, both named
`{{ cookiecutter.ifdd_schema_prj_slug }}`, for `Host(${IFDD_SCHEMA_HOST})` on port 8080, with
the middlewares `security-headers@file` and `csp-api@file` of the proxy in
production. There are deliberately no `tls` or `entrypoints` labels: TLS,
certificates and the DoS baseline are set on the proxy entry point, and a
router with a `tls` section of its own would lose that configuration.
