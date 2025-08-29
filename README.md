# Wetterstation

Die Wetterstation soll aus insgesamt drei Stationen zusammengesetzt sein:

1. Die Seonsoranlage gesteuert durch einen Raspberry Pi Pico 2WH, verbunden mit einem Temperatur- und Feuchtigkeitssensor (DHT22) und ggf. mit einem Feinstaubsensor (HM3301).
2. Ein Server, der die Daten der Sensoranlage empfängt und anschließend in einer Datenbank speichert.
3. Eine Website, die die vom Server abgelegten Daten nach benutzerdefinierten Vorgaben sortiert ausgibt.

## Client

Der Client (die Sensoranlage) nimmt die Daten aus den Sensoren auf und verschickt den Datensatz gebündelt an den Server.

```json
{
    "datetime": "2025-08-20 12:00:00",
    "temperature": 23.4,
    "humidity": 45.6
}
```

Es bieten sich zwei mögliche Programmiersprachen für den Client an: Python und Rust. Nachfolgend werden Ideen für beide Varianten exerziert.

### Python

Mit Python wäre man am besten mit [MicroPython](https://micropython.org) beraten. Alles weitere soll hier noch hinzugefügt werden. Der Chip läuft und sendet fleißig Daten an alle Adressen, die man ihm gibt, Python war keine Kunst.

#### HAL-Operations

Mit `machine` ist das eine Kleinigkeit, alles läuft super stabil und einfach (!).

#### DHT22

DHT als Sensorgruppe kommuniziert über das 1-Wire-Protokoll mit dem Chip und entsprechend einfach ist das Auslesen über eine standardisierte Bibliothek.

#### HTTP Connection

Über `network` und `socket` erfolgt das Versenden des `POST`-Requests ganz leicht.

#### `.env`-Handling

`pip` hat hier sicher ein passendes Modul, ein einfacher Parser ist hierfür aber auch schnell gebaut und *embedded* vielleicht sogar die bessere Wahl. Fraglich ist nur, wie das ganze dann auf dem Pico abgelegt werden kann.

### Rust

[`embassy-rp`](https://docs.embassy.dev/embassy-rp/git/rp2040/index.html) scheint gut zu funktionieren. Das ist wirklich eine umfangreiche Bibliothek, die mir hoffentlich das meiste abnehmen kann.

[Murrays Embedded Rust Tutorialreihe](https://murraytodd.medium.com/list/murrays-raspberry-pi-pico-w-embedded-rust-series-fac1064d4d03) sollte mich hoffentlich bei allen Dingen um ein gutes Stück weiter bringen.

- Die LED ist ausschließlich via CWY43 (dem Netzwerkchip) ansprechbar, nicht via GPIO25 o.Ä., einfaches Debugging mittels Lämpchen wird also schwieriger, evtl. über PIO (*programmable input/output*).

Das [Embassy-Buch über Zeit](https://embassy.dev/book/) ist sicher hilfreich beim Scheduling der einzelnen Programmschritte im Loop.

##### Echtzeituhr

Der Pico hat keine eingebaute CMOS-Batterie o. Ä. und ist deshalb explizit darauf angewiesen, mit einer aktuellen Uhrzeit versorgt zu werden.

##### HAL-Operations

Als erstes ist der Zugriff auf grundsätzliche Chip-Funktionen notwendig (I2C (evtl. für Feinstaubsensor), GPIO usw.). Rust hat hierfür [`rp235x_hal`](https://docs.rs/rp235x_hal/latest/rp235x_hal).

#### DHT22

Der Temperatur- und Feuchtesensor sollte eigentlich über ein standardisiertes Interface ansprechbar sein, weswegen hier auch ein Community-betreutes Paket ausreichen sollte: [`embedded-dht-rs`](https://github.com/rust-dd/embedded-dht-rs).

Hier ist für alle Chips dieser Art Unterstützung vorhanden, außerdem ist die letzte Version verhältnismäßig jung.

#### HTTP Connection

Hier brauche ich noch ein Paket, das mir erlaubt, bei erfolgreich gelesenen Sensordaten eine einfache `GET`-Request abzuschicken und bei erhaltener Response im Fehlerfall kurz blau zu leuchten. [`http`](https://docs.rs/http/latest/http) kann das.

#### `.env`-Handling

Daten für die Verbindung zum Router sollten in einer `.env`-Datei ausgelagert sein. Rust hat dafür [`env_file_reader`](https://github.com/jofas/env_file_reader).

Es scheint aber, dass Rust hier auch [bessere Voraussetzungen](https://murraytodd.medium.com/rust-networking-with-the-raspberry-pi-pico-w-00238415954b) mit `Cargo.toml` schafft.

#### Know-how

Zuerst muss ich rausfinden, wie ich mit Rust so klar komme. Da fehlt mir schon noch einiges. Gerade die Frage mit dem Errorhandling und optionalen Funktionsabläufen muss ich mir natürlich sehr genau anschauen, wenn ich ein System bauen will, das nicht nach einem Nachmittag in irgendeinen Fehler läuft und keine Daten mehr liefert.

## Server

Als Server habe ich mir eigentlich schon überlegt, alles in Python zu schreiben. [FastAPI](https://fastapi.tiangolo.com) sollte mir da eigentlich gute Dienste erweisen können. Gerade die CRUD-Operationen für welche Datenbank auch immer sollte damit eigentlich ein Selbstläufer sein (oder zumindest wesentlich viel einfacher).

Die offensichtliche Alternative wäre womöglich dann NodeJS. Aber ob mir das so taugt, das Handling, nehme ich an, ist in Python dann doch schon ziemlich angenehm.

Um den Server zu testen, sind folgendes nützliche `cURL`-Befehle:

```shell
# GET
curl pidog.local:8000 -X GET
# PUT
curl pidog.local:8000 -X PUT -H "X-Authorization: ***" -H "Content-Type: application/json" -d '{"datetime":"2025-08-26","temperature":25.6,"humidity":48.7}'
```

### Weitere Entwicklungen

Für die Ausgabe von vielen Werten über einen längeren Zeitraum wird es eventuell nötig sein, einige Werte zu überspringen (der Sensor schickt jeden Tag etwa 100 Werte an den Server).

Eine Möglichkeit bestünde darin, dass das Frontend einfach alle Werte für den gefragten Zeitraum anfordert und selbst sortiert. Für kleinere bis mittlere Datenmengen wäre das auf jeden Fall ein probates Mittel. Für große Datenmenge stellen sich allerdings zwei Fragen:

1. Warum sollte diese Arbeit der Client überhaupt machen? -> Warum nicht die Datenbank?
2. Warum sollte ein beträchtlicher Anteil an unnötigen Daten versandt werden? Wenn nur jeder zehnte Eintrag für das Frontend relevant ist, warum dann überhaupt mitschicken?

[Stackoverlow](https://stackoverflow.com/questions/4799816/return-row-of-every-nth-record) hat für diesen Fall einige interessante Ideen, vielleicht lassen sich die auf Ebene der Datenbankabfrage einpflegen und mit einem entsprechenden API-Befehl verknüpfen. So sollte die Belastung auch für den Server hoffentlich möglichst gering sein:

```sql
SELECT *
FROM
(
    SELECT *, ROW_NUMBER() OVER (ORDER BY datetime) AS rownum
    FROM messdaten
) AS t
WHERE t.rownum % quota = 0
ORDER BY datetime
```

## Frontend

Mit [ChartJS](https://www.chartjs.org) ließen sich bestimmt sehr schicke erste Darstellungen bauen. Einzig, man muss vermutlich mit React oder vielleicht Svelte arbeiten, wenn man alles schön integrieren möchte, ansonsten wirkt das arg kompliziert. Darüber hinaus sollte das aber ganz gut funktionieren. Die Daten sollten ja immerhin kein Problem sein mit der aktuellen Pipeline.

Eine schöne Website ließe sich mit React auch mit [shadcn/ui](https://ui.shadcn.com/) bauen. Das sollte auch die Gestaltung in schnellen Zügen vorankommen lassen. ChartJS (s. o.) hat sicherlich den Vorteil, dass man kein monströses Framework drumherum bauen muss, das wäre vielleicht ganz fein. Es sei denn, [`<Recharts />`](https://recharts.org/) hat an der Stelle vernünftige Aktionen parat, sodass auch viele Datenpunkte schön dargestellt werden.

Für's erste ist man bei ChartJS gut aufgehoben. Aber gerade mit Blick auf eine Zukunft, in der phasenweise keine Werte aufgenommen werden (können), wäre eine fortgeschrittenere Darstellung angebracht. D3 hat dafür [eine Lösung für unterbrochene](https://observablehq.com/@d3/line-chart-missing-data/2) und für [mehrere gleichzeitige Liniendiagramme](https://observablehq.com/@d3/multi-line-chart/2).

## Development

### Client

### Server

Dev-Server für FastAPI starten (mit Flag für Zugänglichkeit im lokalen Netzwerk):

```shell
uv run fastapi dev --host 0.0.0.0
```

### Frontend

```shell
npm start. # startet den Testserver von PArcel
```
