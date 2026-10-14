(ifdd-schema-troubleshooting)=
# Fehlersuche

Bekannte Fehlerbilder. Beginnen mit
`docker compose -f docker-compose-production.yml logs schema` und einem `curl`
der betroffenen URL.

| Symptom | Ursache | Abhilfe |
|---|---|---|
| `docker compose` bricht mit `set IFDD_SCHEMA_CONTENT_DIR in .env` oder `set IFDD_SCHEMA_HOST in .env` ab | der Eintrag fehlt in `.env` | ihn setzen ({ref}`ifdd-schema-setup`) |
| `docker compose` bricht mit `refers to undefined volume` ab | `IFDD_SCHEMA_CONTENT_DIR` ist relativ ohne `./` oder `../` | einen absoluten Pfad nehmen oder mit `./` beginnen |
| jede Datei antwortet 403 oder 404 | das Inhaltsverzeichnis stimmt nicht, oder seine Dateien sind für UID 101 nicht lesbar | Pfad in `.env` und Rechte prüfen (`umask 022` für den Klon) |
| ein Verzeichnis antwortet 403 | Verzeichnislisten sind aus (`ifdd_schema_autoindex`) | erwartet; eine Datei anfragen |
| eine Datei unter `.git` oder einem anderen versteckten Pfad antwortet 404 | versteckte Dateien werden nie ausgeliefert | erwartet |
| ein neuer Inhaltsstand ist nicht zu sehen | Clients nutzen noch ihre zwischengespeicherte Kopie | `{{ cookiecutter.ifdd_schema_cache_max_age }}` Sekunden warten oder ohne Cache neu laden |
| eine Änderung in `nginx/` wirkt nicht | nginx liest seine Konfiguration beim Start | den Dienst neu starten |
| der Browser meldet einen CORS-Fehler | der Ursprung der Seite ist nicht `{{ cookiecutter.ifdd_schema_cors_origin }}`, oder die CSP der Seite erlaubt diesen Host nicht | die Browser-Konsole prüfen; `ifdd_schema_cors_origin` und `connect-src` der aufrufenden Seite |
| der Dienst antwortet hinter dem Proxy 404 | der Router fehlt: Container nicht in `{{ cookiecutter.ifdd_proxy_network }}`, noch nicht healthy, oder `IFDD_SCHEMA_HOST` weicht vom angefragten Host ab | den Router im Dashboard des Proxys prüfen |
| das Backend antwortet 502 `... [loading remote context failed] ...` | dieser Dienst ist aus dem Backend-Container nicht erreichbar, sein Zertifikat wird dort nicht vertraut, oder das Ratenlimit des Proxys hat 429 geantwortet | siehe Fehlersuche des Backends; die URL aus der Meldung im Backend-Container mit `curl` abrufen |
| das Backend antwortet 422 `context ... is not below ...` | das Dokument nennt einen Kontext außerhalb der `IFDD_SCHEMA_URL` des Backends | einen Kontext dieses Dienstes nehmen, unter dem eingestellten Versionsverzeichnis |
