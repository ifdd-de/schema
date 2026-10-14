(ifdd-schema-index)=
# {{ cookiecutter.ifdd_schema_prj_name }} (schema)

Der statische Inhaltsdienst `schema` eines IFDD-Knotens: Er liefert die
JSON-LD-Kontexte der Aspekte, die jedes gespeicherte Dokument in seinem
`@context` nennt. Er betreibt das Upstream-nginx-Image als unprivilegierter Benutzer hinter
dem Proxy und baut kein eigenes Image: Konfiguration und Inhalt werden nur
lesend eingebunden. Dieses Kapitel beschreibt die Instanz
`{{ cookiecutter.ifdd_schema_prj_slug }}`, erzeugt aus dem Template `ifdd-de/schema`,
aus Sicht derer, die sie einrichten, betreiben und absichern.

| | |
|---|---|
| Host | `{{ cookiecutter.ifdd_schema_host }}` (Vorgabe von `IFDD_SCHEMA_HOST` in `.env`; vom Proxy geroutet) |
| Image | `{{ cookiecutter.ifdd_nginx_image }}` (gemeinsam für schema, type und unit) |
| Inhalt | das Verzeichnis `IFDD_SCHEMA_CONTENT_DIR` in `.env`, meist ein Klon eines eigenen Inhalts-Repositorys |
| Netz | `{{ cookiecutter.ifdd_proxy_network }}` |
| Entwicklung | `http://127.0.0.1:{{ cookiecutter.ifdd_schema_dev_port }}/` |

## Was die Instanz enthält

Die nginx-Konfiguration (`nginx/default.conf`, `nginx/mime.types`), zwei
Compose-Dateien, `.env` und Beispielinhalt in `examples/json-ld/`. Der
eigentliche Inhalt gehört nicht zur Instanz: Er liegt in einem eigenen
Repository, dessen Klon nur lesend eingebunden wird. `ifdd-de/schema`,
`ifdd-de/type` und `ifdd-de/unit` teilen diesen Aufbau.

## Kontexte

Der Inhalt ist eine Menge von JSON-LD-Kontexten, eine Datei
`<name>.jsonld` je Kontext unter einem Versionsverzeichnis wie `v1/`. Das
Backend lädt von hier den Kontext jedes Dokuments, das es speichert. Regeln
für jeden Kontext, von ifdd-be-core beim Schreiben eines Dokuments geprüft:

- der Dateiname ohne `.jsonld` ist der Kontextname: `base`, ein Aspekt oder
  durch Punkte getrennte Labels in Kleinbuchstaben (ein Domain-Kontext wie
  `breaker.grid.example.ifdd.de`, den das Backend nur Clients mit passendem
  Kontextmuster gibt);
- die sechs `c_*`-Terme (`c_created`, `c_modified`, `c_cacheCreated`,
  `c_cacheUpdated`, `c_validNotBefore`, `c_validNotAfter`) sind definiert,
  in einem Namensraum, der auf `/` oder `#` endet;
- der Namensraum ist `{{ cookiecutter.ifdd_type_url }}/<Kontextname>/`, damit
  sein Vokabular im Dienst type jeden Term erklärt.

Die Beispiele in `examples/json-ld/v1/` enthalten die fünf generischen
Kontexte (`base`, `product`, `function`, `location`, `organisation`) und zwei
Beispiel-Domain-Kontexte.

## Architektur

```{mermaid}
flowchart LR
  Clients[Browser, Dienste] -->|HTTPS| Proxy[proxy: Traefik]
  Proxy -->|"{{ cookiecutter.ifdd_schema_host }}, Port 8080"| Nginx[schema: nginx]
  Nginx -->|nur lesend| Content[(Inhalts-Klon)]
  Repo[Inhalts-Repository] -->|git pull| Content
```

| Wer | Nutzt diesen Dienst für |
|---|---|
| be | den Kontext jedes Dokuments, das es speichert; der Kontext muss unter seiner `IFDD_SCHEMA_URL` liegen |
| ct | die Testdaten seiner Profile nennen Kontexte dieses Dienstes |
| Clients, die Dokumente lesen | die `@context`-IRIs in den Dokumenten |

## Kapitel

```{toctree}
:maxdepth: 2

setup
build-release
operations
security
troubleshooting
reference
```

Die Werte der Variablen dieser Instanz und ihre Beziehungen zu den anderen
Diensten stehen im Kapitel über die Dienst-Instanzen
({ref}`ifdd-instances-static`).
