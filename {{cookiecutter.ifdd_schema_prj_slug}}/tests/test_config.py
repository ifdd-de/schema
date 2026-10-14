"""Static checks of this instance.

They read the files as they are in this repository and assert what the
template promises. Docker is not needed; if an nginx binary is installed, the
configuration is also loaded by nginx itself. tests/smoke.sh covers the
running container.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
SERVICE = "schema"
PREFIX = "IFDD_SCHEMA_"
COMPOSE_FILES = ["docker-compose-production.yml", "docker-compose-development.yml"]
NGINX_CONF = ROOT / "nginx" / "default.conf"
EXAMPLES = ROOT / "examples" / "json-ld"


def load(path):
    return yaml.safe_load(Path(path).read_text())


def service(compose_file):
    return load(ROOT / compose_file)["services"][SERVICE]


def labels(compose_file):
    return service(compose_file)["labels"]


def nginx_conf():
    return NGINX_CONF.read_text()


def location_block(prefix):
    """The body of the first location block whose header starts with prefix."""
    text = nginx_conf()
    start = text.index(prefix)
    depth, begin = 0, text.index("{", start)
    for index in range(begin, len(text)):
        depth += {"{": 1, "}": -1}.get(text[index], 0)
        if depth == 0:
            return text[begin:index]
    raise AssertionError(f"unbalanced braces after {prefix!r}")


# --- compose -----------------------------------------------------------------

@pytest.mark.parametrize("compose_file", COMPOSE_FILES)
def test_compose_file_parses(compose_file):
    assert service(compose_file)["image"]


@pytest.mark.parametrize("compose_file", COMPOSE_FILES)
def test_nothing_from_dotenv_reaches_the_container(compose_file):
    # .env only feeds the ${...} interpolation; nginx needs none of it.
    assert "env_file" not in service(compose_file)
    assert "environment" not in service(compose_file)


@pytest.mark.parametrize("compose_file", COMPOSE_FILES)
def test_no_router_tls_or_entrypoint_labels(compose_file):
    # A router tls section replaces the TLS configuration of the proxy entry
    # point, Let's Encrypt resolver included; routers without entrypoints
    # attach to the default entry point. See the README of ifdd-de/proxy.
    for label in labels(compose_file):
        assert ".tls" not in label and ".entrypoints" not in label, label


@pytest.mark.parametrize("compose_file", COMPOSE_FILES)
def test_router_and_service_share_one_name(compose_file):
    routers = {m.group(1) for label in labels(compose_file) if (m := re.match(r"traefik\.http\.routers\.([^.]+)\.", label))}
    services = {m.group(1) for label in labels(compose_file) if (m := re.match(r"traefik\.http\.services\.([^.]+)\.", label))}
    assert len(routers) == 1 and routers == services


@pytest.mark.parametrize("compose_file", COMPOSE_FILES)
def test_host_rule_requires_the_host_variable(compose_file):
    rules = [label for label in labels(compose_file) if ".rule=" in label]
    assert rules and all(f"${{{PREFIX}HOST:?" in rule for rule in rules)


@pytest.mark.parametrize("compose_file", COMPOSE_FILES)
def test_load_balancer_port_matches_nginx(compose_file):
    listen = re.search(r"^\s*listen\s+(\d+);", nginx_conf(), re.M).group(1)
    ports = [label.split("=", 1)[1] for label in labels(compose_file) if "loadbalancer.server.port=" in label]
    assert ports == [listen]


@pytest.mark.parametrize("compose_file", COMPOSE_FILES)
def test_docker_network_label_matches_the_external_network(compose_file):
    network = load(ROOT / compose_file)["networks"]["ext-proxy-net"]
    assert network["external"] is True
    assert f"traefik.docker.network={network['name']}" in labels(compose_file)


@pytest.mark.parametrize("compose_file", COMPOSE_FILES)
def test_container_is_hardened(compose_file):
    svc = service(compose_file)
    assert svc["read_only"] is True
    assert "/tmp" in svc["tmpfs"]
    assert svc["cap_drop"] == ["ALL"]
    assert "no-new-privileges:true" in svc["security_opt"]


@pytest.mark.parametrize("compose_file", COMPOSE_FILES)
def test_health_check_uses_the_health_endpoint(compose_file):
    assert "http://127.0.0.1:8080/healthz" in service(compose_file)["healthcheck"]["test"]
    assert "location = /healthz" in nginx_conf()


@pytest.mark.parametrize("compose_file", COMPOSE_FILES)
def test_configuration_is_mounted_read_only_and_exists(compose_file):
    volumes = service(compose_file)["volumes"]
    for source, target in (("./nginx/default.conf", "/etc/nginx/conf.d/default.conf"), ("./nginx/mime.types", "/etc/nginx/mime.types")):
        assert f"{source}:{target}:ro" in volumes
        assert (ROOT / source).is_file()


def content_volume(compose_file):
    volumes = [v for v in service(compose_file)["volumes"] if v.endswith(":/usr/share/nginx/html:ro")]
    assert len(volumes) == 1, "exactly one read-only content mount expected"
    return volumes[0]


def test_production_refuses_to_start_without_a_content_directory():
    assert content_volume("docker-compose-production.yml").startswith(f"${{{PREFIX}CONTENT_DIR:?")


def test_development_falls_back_to_the_examples():
    assert content_volume("docker-compose-development.yml").startswith(f"${{{PREFIX}CONTENT_DIR:-./examples/json-ld}}")
    assert EXAMPLES.is_dir()


def test_development_port_is_bound_to_loopback_only():
    assert all(port.startswith("127.0.0.1:") for port in service("docker-compose-development.yml")["ports"])


def test_production_publishes_no_port():
    assert "ports" not in service("docker-compose-production.yml")


# --- nginx ---------------------------------------------------------------------

def test_hidden_files_are_never_served():
    assert re.search(r"location ~ /\\\.\s*\{\s*return 404;\s*\}", nginx_conf())


def test_cors_headers_are_sent_on_every_response():
    block = location_block("location / ")
    for header in ("Access-Control-Allow-Origin", "Access-Control-Allow-Methods", "Access-Control-Allow-Headers"):
        assert re.search(rf'add_header {header} "[^"]+" always;', block), header


def test_preflight_is_answered_without_content():
    assert re.search(r"if \(\$request_method = OPTIONS\)\s*\{\s*return 204;\s*\}", location_block("location / "))


def test_server_version_is_not_disclosed():
    assert re.search(r"^\s*server_tokens off;", nginx_conf(), re.M)


def test_json_ld_has_its_media_type():
    assert re.search(r"application/ld\+json\s+jsonld;", (ROOT / "nginx" / "mime.types").read_text())


@pytest.mark.skipif(shutil.which("nginx") is None, reason="no nginx binary installed")
def test_nginx_accepts_the_configuration(tmp_path):
    # Mirrors the http block of the unprivileged image closely enough for a
    # syntax and semantics check (includes, directives, contexts).
    main = tmp_path / "nginx.conf"
    main.write_text(
        f"pid {tmp_path}/nginx.pid;\n"
        f"error_log {tmp_path}/error.log;\n"
        "events {}\n"
        "http {\n"
        f"    include {ROOT}/nginx/mime.types;\n"
        "    default_type application/octet-stream;\n"
        f"    access_log {tmp_path}/access.log;\n"
        f"    client_body_temp_path {tmp_path}/client_temp;\n"
        f"    proxy_temp_path {tmp_path}/proxy_temp;\n"
        f"    fastcgi_temp_path {tmp_path}/fastcgi_temp;\n"
        f"    uwsgi_temp_path {tmp_path}/uwsgi_temp;\n"
        f"    scgi_temp_path {tmp_path}/scgi_temp;\n"
        "    sendfile on;\n"
        f"    include {NGINX_CONF};\n"
        "}\n"
    )
    result = subprocess.run(["nginx", "-t", "-q", "-p", str(tmp_path), "-c", str(main)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


# --- files -------------------------------------------------------------------

def test_dotenv_holds_only_variables_of_this_service():
    for line in (ROOT / "dotenv.dist").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            assert line.startswith(PREFIX), line


def test_env_file_is_git_ignored():
    assert ".env" in (ROOT / ".gitignore").read_text().splitlines()


@pytest.mark.parametrize(
    "path",
    sorted(p.relative_to(ROOT).as_posix() for p in EXAMPLES.rglob("*.jsonld")) or [None],
)
def test_json_ld_examples_parse(path):
    if path is None:
        pytest.skip("no .jsonld examples")
    document = json.loads((ROOT / path).read_text())
    assert "@context" in document


# --- cache metadata terms ----------------------------------------------------
# ifdd-be-core strips the c_* terms from a document before it stores it, keeps
# their values in table columns and adds them again on read, with the IRI of
# the namespace of the context the document was stored with. It finds that
# namespace by expanding the six terms with the context (contexts.py,
# cache_namespace): all six must lie in one namespace that ends with "/" or
# "#". The name of the prefix does not matter (product.jsonld uses "product:",
# breaker.grid.example.ifdd.de.jsonld uses "breaker:").

CACHE_TERMS = (
    "c_created",
    "c_modified",
    "c_cacheCreated",
    "c_cacheUpdated",
    "c_validNotBefore",
    "c_validNotAfter",
)
# Names used up to schemaVersion 0.9.1; "expire" was dropped without successor.
RETIRED_TERMS = (
    "created",
    "modified",
    "expire",
    "cacheCreated",
    "cacheUpdated",
    "validNotBefore",
    "validNotAfter",
)
SCHEMAS = sorted(p.relative_to(ROOT).as_posix() for p in (EXAMPLES / "v1").glob("*.jsonld"))


def expand_iri(value, context):
    """Expand a compact IRI (prefix:suffix) with the prefixes of a context."""
    prefix, colon, suffix = value.partition(":")
    if colon and not suffix.startswith("//") and prefix in context:
        base = context[prefix]
        base = base.get("@id", "") if isinstance(base, dict) else base
        return f"{base}{suffix}"
    return value


def cache_namespace_problems(context):
    """What ifdd-be-core would reject in the c_* terms of a context ([] = fine)."""
    problems, namespaces = [], set()
    for term in CACHE_TERMS:
        definition = context.get(term)
        if not isinstance(definition, dict) or definition.get("@type") != "xsd:dateTime":
            problems.append(f"{term}: not defined as xsd:dateTime")
            continue
        iri = expand_iri(definition.get("@id", ""), context)
        if not iri.endswith(term):
            problems.append(f"{term}: expands to {iri!r}")
            continue
        namespaces.add(iri[: -len(term)])
    if len(namespaces) > 1:
        problems.append(f"c_* terms in several namespaces: {sorted(namespaces)}")
    for namespace in namespaces:
        if not namespace.endswith(("/", "#")):
            problems.append(f"namespace {namespace!r} does not end with / or #")
    return problems


@pytest.mark.parametrize("path", SCHEMAS or [None])
def test_schema_defines_every_cache_term_in_one_namespace(path):
    if path is None:
        pytest.skip("no .jsonld schemas")
    context = json.loads((ROOT / path).read_text())["@context"]
    assert cache_namespace_problems(context) == []


@pytest.mark.parametrize("change, problem", [
    ({"c_modified": {"@id": "other:c_modified", "@type": "xsd:dateTime"}}, "several namespaces"),
    ({"x": "https://type.test/x"}, "does not end with / or #"),
    ({"c_created": {"@id": "x:c_created"}}, "c_created: not defined as xsd:dateTime"),
    ({"c_cacheUpdated": "x:c_cacheUpdated"}, "c_cacheUpdated: not defined"),
])
def test_cache_namespace_check_rejects_what_ifdd_be_core_rejects(change, problem):
    context = {"x": "https://type.test/x/", "other": "https://type.test/other/",
               "xsd": "http://www.w3.org/2001/XMLSchema#"}
    context.update({term: {"@id": f"x:{term}", "@type": "xsd:dateTime"} for term in CACHE_TERMS})
    assert cache_namespace_problems(context) == []
    context.update(change)
    assert any(problem in p for p in cache_namespace_problems(context))


@pytest.mark.parametrize("path", SCHEMAS or [None])
def test_schema_no_longer_defines_the_retired_time_terms(path):
    if path is None:
        pytest.skip("no .jsonld schemas")
    context = json.loads((ROOT / path).read_text())["@context"]
    assert not set(RETIRED_TERMS) & set(context)
