(ifdd-schema-security)=
# Sicherheit

Der Dienst liefert öffentlichen Inhalt nur lesend aus. Er hat keine
Anmeldung: Alles im Inhaltsverzeichnis geht an jeden Client, der den Proxy
erreicht.

| Thema | Hier |
|---|---|
| wer lesen darf | jeder; nichts ins Inhalts-Repository legen, was nicht öffentlich sein soll |
| Verzeichnislisten | {{ "an" if cookiecutter.ifdd_schema_autoindex == "y" else "aus (Verzeichnisse antworten 403)" }} (`ifdd_schema_autoindex`) |
| versteckte Dateien (`.git`, ...) | nie ausgeliefert (404) |
| Transport | TLS endet am Proxy; keine `tls`-Labels am Router |

## Zugriff aus dem Browser (CORS und Header)

nginx sendet `Access-Control-Allow-Origin: {{ cookiecutter.ifdd_schema_cors_origin }}`
(`ifdd_schema_cors_origin`) bei jeder Antwort, auch bei Fehlern, und beantwortet den
Preflight (`OPTIONS`) mit 204. `*` passt zu öffentlichem Inhalt; ein
einzelner Ursprung schränkt ein, welche Webseiten ihn im Browser lesen
dürfen, nicht, wer ihn überhaupt lesen darf.

nginx setzt `X-Content-Type-Options: nosniff` und verrät seine Version nicht
(`server_tokens off`). Der Proxy setzt in Produktion `security-headers` und
die strenge `csp-api`: Nichts wird geladen, nichts eingebettet.

## Container

| Maßnahme | Einstellung |
|---|---|
| Benutzer | unprivilegiert (UID 101) |
| Capabilities | alle entzogen (`cap_drop: ALL`), `no-new-privileges` |
| Dateisystem | Root nur lesend, `/tmp` als tmpfs; Inhalt und Konfiguration nur lesend eingebunden |
| Ports | in Produktion keiner veröffentlicht; die Entwicklung bindet nur 127.0.0.1 |
| Konfiguration | nichts aus `.env` erreicht den Container |
