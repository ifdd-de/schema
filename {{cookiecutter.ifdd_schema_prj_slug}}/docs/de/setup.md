(ifdd-schema-setup)=
# Einrichtung

## Voraussetzungen

| Was | Warum |
|---|---|
| Docker mit Compose | nginx läuft als Container |
| das externe Netz `{{ cookiecutter.ifdd_proxy_network }}` und eine laufende Proxy-Instanz | Traefik routet `{{ cookiecutter.ifdd_schema_host }}` anhand der Labels zu diesem Dienst |
| Namensauflösung in Containern | das Backend lädt Kontexte von hier aus seinem Container, daher muss der Proxy `{{ cookiecutter.ifdd_schema_host }}` in `ifdd_proxy_internal_hosts` führen |
| ein Klon des Inhalts-Repositorys auf dem Host | der Inhalt wird von dort ausgeliefert |

## Instanz anlegen

Üblicherweise legt das Meta-Repository alle Instanzen in einem Zug an
(`.adm_meta_01_all.sh`, Schritt `.adm_01_create_services.sh`), mit der
gemeinsamen Variablendatei `.cookiecutter_all.yaml`. Von Hand, im
Verzeichnis der Instanzen:

```bash
cruft create --no-input --config-file .cookiecutter_all.yaml \
  --skip .env --skip examples \
  https://github.com/ifdd-de/schema
```

Die Skip-Liste hält `.env` und die Beispiele, beide instanzeigen, aus jedem
späteren `cruft update` heraus. Das Meta-Repository übergibt `--skip envs
--skip .env`.

## Konfiguration

Der Post-Generation-Hook schreibt `.env` aus `dotenv.dist` (Modus 0600; eine
vorhandene `.env` bleibt unberührt). `.env` speist nur die `${...}` der
Compose-Dateien; nichts daraus erreicht den Container.

| Eintrag | Vorgabe hier | Bedeutung |
|---|---|---|
| `IFDD_SCHEMA_HOST` | `{{ cookiecutter.ifdd_schema_host }}` | Hostname, den der Proxy zu diesem Dienst routet; Pflicht |
| `IFDD_SCHEMA_CONTENT_DIR` | `{{ cookiecutter.ifdd_schema_content_dir }}` | auszuliefernde Verzeichnis; Pflicht in Produktion |
| `IFDD_SCHEMA_DEV_PORT` | `{{ cookiecutter.ifdd_schema_dev_port }}` | Port auf 127.0.0.1 in der Entwicklung |

Alle übrigen Werte kommen aus den Variablen des Templates; sie stehen mit
ihren Werten und ihrer Bedeutung in {ref}`ifdd-instances-static`.

## Inhalt

Der Inhalt liegt in einem eigenen Repository, getrennt auf dem Host geklont.
Dieser Dienst braucht nur den Pfad des auszuliefernden Verzeichnisses:

```bash
git clone <content repository> /srv/ifdd/schema-content
# in .env:
IFDD_SCHEMA_CONTENT_DIR=/srv/ifdd/schema-content
```

`/srv/ifdd/schema-content` ist ein Beispiel.

- Die Variable auf das Verzeichnis zeigen lassen, dessen Dateien
  ausgeliefert werden sollen. Hält das Inhalts-Repository sie in einem
  Unterverzeichnis, dorthin.
- Einen absoluten Pfad nehmen oder einen relativen, der mit `./` oder `../`
  beginnt. Ohne dieses Präfix liest compose den Wert als Volume-Namen und
  startet nicht (`refers to undefined volume`).
- Der Container läuft als UID 101 und braucht Lesezugriff: Dateien müssen für
  „andere“ lesbar sein, was ein Klon mit dem üblichen `umask 022` ist.
- Versteckte Dateien und Verzeichnisse (`.git`, `.gitignore`, ...) werden nie
  ausgeliefert; die Wurzel eines Klons einzubinden ist daher sicher.

## Erster Start

```bash
docker network create {{ cookiecutter.ifdd_proxy_network }}   # einmal je Host, falls der Proxy es nicht schon angelegt hat
docker compose -f docker-compose-production.yml up -d
docker compose -f docker-compose-production.yml ps
```

Ohne `IFDD_SCHEMA_HOST` oder `IFDD_SCHEMA_CONTENT_DIR` in `.env` verweigert
`docker compose` den Start mit einer Meldung, die die Variable nennt. `ps`
sollte den Dienst als healthy melden.

## Lokale Entwicklung

```bash
docker compose -f docker-compose-development.yml up -d
curl http://127.0.0.1:{{ cookiecutter.ifdd_schema_dev_port }}/
```

Liefert `examples/json-ld` aus, solange `IFDD_SCHEMA_CONTENT_DIR` nicht gesetzt ist;
der Port kommt aus `IFDD_SCHEMA_DEV_PORT` und ist nur an 127.0.0.1 gebunden. Das Netz
`{{ cookiecutter.ifdd_proxy_network }}` muss existieren.

## Hinter dem Proxy

Die Labels melden einen Router und einen Dienst, beide
`{{ cookiecutter.ifdd_schema_prj_slug }}` genannt, für `Host(${IFDD_SCHEMA_HOST})` auf Port
8080, in Produktion mit den Middlewares `security-headers@file` und
`csp-api@file` des Proxys. Es gibt bewusst keine `tls`- oder
`entrypoints`-Labels: TLS, Zertifikate und der DoS-Grundschutz sitzen am
Entry Point des Proxys, und ein Router mit eigenem `tls`-Abschnitt verlöre
diese Konfiguration.
