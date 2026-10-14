"""Validation before generation.

Rejects values that would render but not work, so a mistake shows up here
and not later as a container that does not start or a router Traefik drops.
"""

import re
import sys

VALUES = {
    "slug": """{{ cookiecutter.ifdd_schema_prj_slug }}""",
    "host": """{{ cookiecutter.ifdd_schema_host }}""",
    "dev_port": """{{ cookiecutter.ifdd_schema_dev_port }}""",
    "autoindex": """{{ cookiecutter.ifdd_schema_autoindex }}""",
    "cors_origin": """{{ cookiecutter.ifdd_schema_cors_origin }}""",
    "cache_max_age": """{{ cookiecutter.ifdd_schema_cache_max_age }}""",
    "memory_limit": """{{ cookiecutter.ifdd_schema_memory_limit }}""",
    "nginx_image": """{{ cookiecutter.ifdd_nginx_image }}""",
    "proxy_network": """{{ cookiecutter.ifdd_proxy_network }}""",
    "type_url": """{{ cookiecutter.ifdd_type_url }}""",
}

# (value, pattern, explanation)
CHECKS = {
    # Directory name and Traefik router name.
    "slug": (r"[A-Za-z_][A-Za-z0-9_-]+", "letters, digits, _ and -, not starting with a digit or -"),
    "host": (r"[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?", "a host name"),
    "dev_port": (r"[0-9]{1,5}", "a port number"),
    "autoindex": (r"[yn]", "y or n"),
    "cors_origin": (r"\*|https?://[A-Za-z0-9.-]+(:[0-9]+)?", "* or one origin such as https://ui.example.org"),
    "cache_max_age": (r"[0-9]+", "seconds, 0 for no-cache"),
    "memory_limit": (r"[0-9]+[bkmgBKMG]?", "a compose memory limit such as 128M"),
    "nginx_image": (r"\S+", "an image reference without spaces"),
    "proxy_network": (r"[A-Za-z0-9][A-Za-z0-9_.-]*", "a Docker network name"),
    # Joined with "/<aspect>/" in the example schemas: no trailing slash.
    "type_url": (r"https?://\S*[^/\s]", "an http(s) URL without trailing slash"),
}

errors = []
for name, (pattern, explanation) in CHECKS.items():
    if not re.fullmatch(pattern, VALUES[name]):
        errors.append(f"{name} = {VALUES[name]!r}: expected {explanation}")

if not errors and not 1 <= int(VALUES["dev_port"]) <= 65535:
    errors.append(f"dev_port = {VALUES['dev_port']}: outside 1-65535")

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    sys.exit(1)
