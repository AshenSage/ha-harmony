# Harmony – Blue & Green

Ein gemeinsamer Home-Assistant-Stil mit zwei Farbwelten:

| Theme | Grundfarbe |
|---|---|
| **Harmony Blue** | Himmelblau / Oberbipp |
| **Harmony Green** | Mintgrün / Aranđelovac |

Beide Varianten sind in **einer Datei** `themes/harmony.yaml` enthalten und werden
auf beiden HA-Instanzen gleich installiert. Die Farbwelt entspricht der dunklen,
getönten Gestaltung: ruhige Grundflächen, sanfte Verläufe, farbige Iconflächen,
lesbare Hauptwerte und abgesetzte Status- bzw. Bedienbereiche.

Version **1.0.1** · Home Assistant **2026.10.0+**.

## Installation

### Über HACS

Das Repository muss dafür auf GitHub **öffentlich** sein. HACS kann private
Repositories nicht installieren. Eine Sichtbarkeitsänderung ist unabhängig
von den hier enthaltenen Dateien und erfolgt durch den Repository-Eigentümer.

1. HACS → **⋮ → Benutzerdefinierte Repositories**.
2. `https://github.com/AshenSage/ha-harmony` hinzufügen, Kategorie **Theme**.
3. **Harmony – Blue & Green** herunterladen.
4. Im Benutzerprofil **Harmony Blue** oder **Harmony Green** auswählen.

HACS legt die Datei unter `/config/themes/harmony/harmony.yaml` ab und lädt Themes
neu. Beide Themes sind bewusst als Dark-Mode-Themes definiert, passend zum Entwurf.

### Direkt installieren

1. `themes/harmony.yaml` herunterladen und auf beiden Instanzen unter
   `/config/themes/harmony/harmony.yaml` speichern.
2. Vorhandene Theme-Einbindung prüfen:

   ```yaml
   frontend:
     themes: !include_dir_merge_named themes
   ```

   Dies in einen bestehenden `frontend:`-Block einfügen. Ist die Einbindung
   bereits aktiv, ist dafür keine Änderung nötig.
3. Unter Entwicklerwerkzeuge → Aktionen ausführen:

   ```yaml
   action: frontend.reload_themes
   data: {}
   ```

   Bei erstmaliger Einrichtung der Theme-Einbindung HA neu starten.
4. Im Profil das gewünschte Theme auswählen.

## Theme und Karten

Das Theme liefert gemeinsame Farben, Flächen, Schriftgrössen, Rundungen und Schatten.
Eine bestehende Karte mit fest eingebautem schwarzem Hintergrund benötigt einmalig
eine Anpassung an diese Variablen. Danach folgen diese Werte den Theme-Updates.

Die vorbereiteten Dashboard-Kopien werden separat übergeben. Sie gehören zur
jeweiligen privaten HA-Konfiguration und sind kein Bestandteil dieses Repositories.
HACS verändert keine im Dashboard gespeicherte Karten-YAML.

Für diese Kopien werden die bereits vorhandenen **button-card 6+**, **card-mod 4.2+**
und **Mushroom** verwendet. Weitere vorhandene Karten bleiben eingebunden.
Licht-, Ventilator- und Klimabedienung verwenden weiterhin HA-eigene Tile-Features.
Das Theme selbst lässt sich auch ohne diese zusätzlichen Karten verwenden.

### Gemeinsame Kartenklassen

| Zweck | Variablen / Vorlage |
|---|---|
| Wetter | `--harmony-weather-surface`, `--harmony-blue` |
| Temperatur | `--harmony-peach` |
| Luftfeuchte / Lüftung | `--harmony-cyan` |
| Gute Luft / geschlossene Türen | `--harmony-mint` |
| Eingeschaltetes Licht | `--harmony-gold` |
| Warnung / Fehler | `--harmony-warning`, `--harmony-error` |
| Messwert mit Statuszeile | `harmony_metric` aus `templates/button_card_templates.yaml` |

Für eine Karte eine lokale Akzentfarbe setzen:

```yaml
card_mod:
  class: harmony harmony-status
  style: |
    ha-card {
      --harmony-tone: var(--harmony-cyan);
      background: var(--harmony-status-surface);
    }
```

Eigene Karten können die gemeinsamen CSS-Variablen direkt nutzen. Die vorhandenen
Wetter-, Umwelt- und Feiertagskarten verwenden bereits HA-Theme-Variablen;
Harmony ergänzt deren unterstützte Farbvariablen.

### Wiederverwendbare Messwertkarte

Die Definitionen aus `templates/button_card_templates.yaml` einmal in die
Dashboard-Rohkonfiguration übernehmen. Dann etwa:

```yaml
type: custom:button-card
template: harmony_metric
entity: sensor.raum_temperatur # durch eigene Entität ersetzen
name: Temperatur
icon: mdi:thermometer
variables:
  harmony_kind: temperature
  harmony_unit: °C
  harmony_decimals: 1
  harmony_note: Wohnzimmer
```

Weitere Typen sind `humidity`, `co2`, `pm25` und `generic`.
Ungültige, fehlende, nicht verfügbare und wiederhergestellte Messwerte erhalten
eine ausdrückliche Statusanzeige. Sie werden nicht als 0 oder gesund dargestellt.
Statusgrenzen dienen der Dashboardanzeige; sie ändern keine Automationen.

## Ein vorhandenes Dashboard lokal vorbereiten

Python 3 und PyYAML installieren. Das Werkzeug verarbeitet eine YAML-/JSON-Datei
oder ein Prüfexport-ZIP mit genau einem benannten Dashboard:

```bash
python tools/prepare_dashboard.py export.zip --theme "Harmony Blue" --output output/dashboard.yaml
```

Die Ausgabe bleibt lokal. Das Werkzeug schreibt weder in Home Assistant noch in
`.storage`. Es setzt das View-Theme, stellt feste dunkle Kartenflächen um,
vereinheitlicht vorhandene Karten und bindet passende ALPSTUGA-Messwertkarten an
die gemeinsame Vorlage. Entitäten, Bedienaktionen und HA-Tile-Features bleiben
zugeordnet. Ein bereits vorbereitetes Dashboard wird nicht erneut verarbeitet.

## Updates und Rückweg

Theme-Updates auf beiden HA-Instanzen installieren und gegebenenfalls
`frontend.reload_themes` ausführen. Bei einer direkten Installation dieselbe Datei
ersetzen. Änderungen an Kartentypen oder ihrem Aufbau werden gesondert dokumentiert;
ein Theme-Update allein ersetzt keine Dashboard-Konfiguration.

Vor dem Übernehmen einer Dashboard-Kopie die bisherige Rohkonfiguration sichern.
Zuerst in einem zusätzlichen Dashboard prüfen. Bei Bedarf die gesicherte
Rohkonfiguration und das zuvor gewählte Theme wieder auswählen.

## Entwicklung

```bash
python tools/build_theme.py
python tools/build_templates.py
python tools/validate.py
```

Die Prüfungen validieren das Theme, die lokalen CSS-Verweise und Messwertzustände.
Sie ersetzen keine Sichtprüfung in der tatsächlich installierten HA-Oberfläche.

Dokumentation:
[HA-Themes](https://www.home-assistant.io/integrations/frontend/),
[HACS-Themes](https://www.hacs.dev/docs/publish/theme/),
[card-mod](https://github.com/thomasloven/lovelace-card-mod).
