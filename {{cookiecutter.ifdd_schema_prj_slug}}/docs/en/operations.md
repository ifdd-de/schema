(ifdd-schema-operations)=
# Operations

## Start, stop, order

```bash
docker compose -f docker-compose-production.yml up -d
docker compose -f docker-compose-production.yml ps
docker compose -f docker-compose-production.yml down
```

The service needs the proxy network at start and nothing else.
`.adm_03_up_services.sh` of the meta repository starts all services in the
order the node needs (proxy first).

## Health check

| Container | Check | Interval |
|---|---|---|
| `schema` | `wget` on `http://127.0.0.1:8080/healthz` (answers 200, not logged) | 30 s, timeout 5 s, 3 retries, start period 5 s |

## Logs

```bash
docker compose -f docker-compose-production.yml logs -f schema
```

## Content updates

`git pull` in the clone; the change is served immediately, without a
restart. A response stays in the caches of clients for
`{{ cookiecutter.ifdd_schema_cache_max_age }}` seconds (`ifdd_schema_cache_max_age`; `0`
means `no-cache`); afterwards they revalidate with the ETag. The cache
lifetime is a trade-off, not a measured value: longer means fewer requests,
but a `git pull` reaches clients only after it expires.

## Applying changes

| Changed | To do |
|---|---|
| the content | nothing |
| `nginx/*` | `docker compose -f docker-compose-production.yml restart schema` |
| `.env` | `docker compose -f docker-compose-production.yml up -d` (recreates the container) |

## Resources

| Setting | Here |
|---|---|
| memory limit | `{{ cookiecutter.ifdd_schema_memory_limit }}` (`ifdd_schema_memory_limit`) |
| restart | `always` (production) |
| root file system | read-only, `/tmp` as tmpfs |

```{note}
Not tested: whether the memory limit and the cache lifetime fit real
traffic. Both are starting values, not measured.
```

## Backup

The instance holds no data of its own: `.env` and, if edited, the examples.
The content is backed up with its repository.

## Updates

New template states arrive with `cruft update`; `.env` and `examples` are on
the skip list. Run the tests and restart the service afterwards.
