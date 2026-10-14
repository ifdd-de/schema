#!/usr/bin/env bash
# Starts the service with Docker Compose and probes it.
#
#   tests/smoke.sh development   # full check from the host via the dev port
#   tests/smoke.sh production    # health and one request, from inside
#
# Both modes serve ./examples/json-ld. The proxy network is created if it is
# missing and removed again afterwards. Leaves no trace.
set -euo pipefail
cd "$(dirname "$0")/.."

MODE=${1:-development}
SERVICE=schema
PREFIX=IFDD_SCHEMA
COMPOSE=(docker compose -f "docker-compose-$MODE.yml")
NETWORK=$(sed -n 's/^    name: *//p' "docker-compose-$MODE.yml" | head -1)
HIDDEN=examples/json-ld/.smoke-hidden
CREATED=("$HIDDEN")
NETWORK_CREATED=""

cleanup() {
  "${COMPOSE[@]}" down --remove-orphans >/dev/null 2>&1 || true
  for file in "${CREATED[@]}"; do rm -f "$file"; done
  if [ -n "$NETWORK_CREATED" ]; then docker network rm "$NETWORK" >/dev/null 2>&1 || true; fi
}
trap cleanup EXIT

[ -f .env ] || { cp dotenv.dist .env; CREATED+=(.env); }
set -a; . ./.env; set +a
# The shell environment takes precedence over .env in compose interpolation.
export "${PREFIX}_HOST=$SERVICE.localhost"
export "${PREFIX}_CONTENT_DIR=./examples/json-ld"
DEV_PORT_VAR="${PREFIX}_DEV_PORT"
PORT=${!DEV_PORT_VAR}

echo "secret" > "$HIDDEN"
if ! docker network inspect "$NETWORK" >/dev/null 2>&1; then
  docker network create "$NETWORK" >/dev/null
  NETWORK_CREATED=yes
fi

"${COMPOSE[@]}" up -d --quiet-pull
CONTAINER=$("${COMPOSE[@]}" ps -q "$SERVICE")
for attempt in $(seq 30); do
  STATUS=$(docker inspect --format '{{.State.Health.Status}}' "$CONTAINER")
  [ "$STATUS" = healthy ] && { echo "PASS  container healthy"; break; }
  [ "$attempt" = 30 ] && { echo "FAIL  container not healthy ($STATUS)"; "${COMPOSE[@]}" logs; exit 1; }
  sleep 1
done

FAILURES=0
check() {  # check <name> <condition...>
  local name=$1; shift
  if "$@"; then echo "PASS  $name"; else echo "FAIL  $name"; FAILURES=$((FAILURES + 1)); fi
}

if [ "$MODE" = production ]; then
  check "a request from inside the container" \
    "${COMPOSE[@]}" exec -T "$SERVICE" wget -q -O /dev/null http://127.0.0.1:8080/healthz
  [ "$FAILURES" -eq 0 ] || { "${COMPOSE[@]}" logs; exit 1; }
  echo "smoke test (production) passed"; exit 0
fi

BASE="http://127.0.0.1:$PORT"
status() { curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$@"; }
header() { curl -s -D - -o /dev/null --max-time 5 "${@:2}" | tr -d '\r' | sed -n "s/^$1: //Ip" | head -1; }

EXAMPLE=$(cd examples/json-ld && find . -type f ! -name '.*' | sed 's#^\./##' | sort | head -1)
if [ -z "$EXAMPLE" ]; then echo "FAIL  no example file to request"; exit 1; fi
case "$EXAMPLE" in
  *.jsonld) WANT_TYPE="application/ld+json" ;;
  *.json)   WANT_TYPE="application/json" ;;
  *)        WANT_TYPE="text/plain" ;;
esac

check "health endpoint answers 200" [ "$(status "$BASE/healthz")" = 200 ]
check "example file answers 200" [ "$(status "$BASE/$EXAMPLE")" = 200 ]
check "example file has type $WANT_TYPE" [ "$(header Content-Type "$BASE/$EXAMPLE" | cut -d';' -f1)" = "$WANT_TYPE" ]
check "CORS header on success" [ -n "$(header Access-Control-Allow-Origin "$BASE/$EXAMPLE")" ]
check "missing file answers 404" [ "$(status "$BASE/does-not-exist")" = 404 ]
check "CORS header on 404" [ -n "$(header Access-Control-Allow-Origin "$BASE/does-not-exist")" ]
check "preflight answers 204" [ "$(status -X OPTIONS -H 'Origin: https://ui.example.org' -H 'Access-Control-Request-Method: GET' "$BASE/$EXAMPLE")" = 204 ]
check "hidden file is not served" [ "$(status "$BASE/.smoke-hidden")" = 404 ]
check "server version is not disclosed" [ "$(header Server "$BASE/healthz")" = nginx ]
if grep -q "autoindex on;" nginx/default.conf; then
  check "directory listing answers 200" [ "$(status "$BASE/")" = 200 ]
else
  check "directory listing is refused" [ "$(status "$BASE/")" = 403 ]
fi
check "root file system is read-only" [ "$(docker inspect --format '{{.HostConfig.ReadonlyRootfs}}' "$CONTAINER")" = true ]

[ "$FAILURES" -eq 0 ] || { "${COMPOSE[@]}" logs; exit 1; }
echo "smoke test (development) passed"
