(ifdd-schema-security)=
# Security

The service serves public, read-only content. It has no login: everything in
the content directory is delivered to every client that reaches the proxy.

| Concern | Here |
|---|---|
| who may read | everyone; put nothing into the content repository that is not meant to be public |
| directory listings | {{ "on" if cookiecutter.ifdd_schema_autoindex == "y" else "off (directories answer 403)" }} (`ifdd_schema_autoindex`) |
| hidden files (`.git`, ...) | never served (404) |
| transport | TLS ends at the proxy; no router `tls` labels |

## Browser access (CORS and headers)

nginx sends `Access-Control-Allow-Origin: {{ cookiecutter.ifdd_schema_cors_origin }}`
(`ifdd_schema_cors_origin`) on every response, including errors, and answers the
preflight (`OPTIONS`) with 204. `*` suits public content; a single origin
restricts which web pages may read it from the browser, not who may read it
at all.

nginx adds `X-Content-Type-Options: nosniff` and does not disclose its
version (`server_tokens off`). The proxy adds `security-headers` and the
strict `csp-api` in production: nothing is loaded, nothing is framed.

## Container

| Measure | Setting |
|---|---|
| user | unprivileged (UID 101) |
| capabilities | all dropped (`cap_drop: ALL`), `no-new-privileges` |
| file system | read-only root, `/tmp` as tmpfs; content and configuration mounted read-only |
| ports | none published in production; development binds 127.0.0.1 only |
| configuration | nothing from `.env` reaches the container |
