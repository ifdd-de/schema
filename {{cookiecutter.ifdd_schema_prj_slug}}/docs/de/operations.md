(ifdd-schema-operations)=
# Betrieb

## Starten, Stoppen, Reihenfolge

```bash
docker compose -f docker-compose-production.yml up -d
docker compose -f docker-compose-production.yml ps
docker compose -f docker-compose-production.yml down
```

Der Dienst braucht beim Start das Proxy-Netz und sonst nichts.
`.adm_03_up_services.sh` des Meta-Repositorys startet alle Dienste in der
Reihenfolge, die der Knoten braucht (Proxy zuerst).

## Healthcheck

| Container | Prüfung | Intervall |
|---|---|---|
| `schema` | `wget` auf `http://127.0.0.1:8080/healthz` (antwortet 200, wird nicht protokolliert) | 30 s, Timeout 5 s, 3 Versuche, Startphase 5 s |

## Logs

```bash
docker compose -f docker-compose-production.yml logs -f schema
```

## Inhalte aktualisieren

`git pull` im Klon; die Änderung wird sofort ausgeliefert, ohne Neustart.
Eine Antwort bleibt `{{ cookiecutter.ifdd_schema_cache_max_age }}` Sekunden in den
Caches der Clients (`ifdd_schema_cache_max_age`; `0` bedeutet `no-cache`); danach
prüfen sie mit dem ETag neu. Die Cache-Dauer ist ein Kompromiss, kein
gemessener Wert: länger heißt weniger Anfragen, aber ein `git pull` erreicht
die Clients erst, wenn sie abläuft.

## Änderungen übernehmen

| Geändert | Zu tun |
|---|---|
| der Inhalt | nichts |
| `nginx/*` | `docker compose -f docker-compose-production.yml restart schema` |
| `.env` | `docker compose -f docker-compose-production.yml up -d` (erzeugt den Container neu) |

## Ressourcen

| Einstellung | Hier |
|---|---|
| Speichergrenze | `{{ cookiecutter.ifdd_schema_memory_limit }}` (`ifdd_schema_memory_limit`) |
| Neustart | `always` (Produktion) |
| Root-Dateisystem | nur lesend, `/tmp` als tmpfs |

```{note}
Nicht getestet: ob Speichergrenze und Cache-Dauer zu echtem Verkehr passen.
Beide sind Startwerte, nicht gemessen.
```

## Sicherung

Die Instanz hält keine eigenen Daten: `.env` und, falls bearbeitet, die
Beispiele. Der Inhalt wird mit seinem Repository gesichert.

## Aktualisieren

Neue Template-Stände kommen mit `cruft update`; `.env` und `examples` stehen
auf der Skip-Liste. Danach die Tests laufen lassen und den Dienst neu
starten.
