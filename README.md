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

Mit Python wäre man am besten mit [MicroPython](https://micropython.org) beraten. Alles weitere soll hier noch hinzugefügt werden.

#### HAL-Operations

#### DHT22

#### HTTP Connection

#### `.env`-Handling

`pip` hat hier sicher ein passendes Modul, ein einfacher Parser ist hierfür aber auch schnell gebaut und *embedded* vielleicht sogar die bessere Wahl.

### Rust

[`embassy-rp`](https://docs.embassy.dev/embassy-rp/git/rp2040/index.html) scheint gut zu funktionieren. Das ist wirklich eine umfangreiche Bibliothek, die mir hoffentlich das meiste abnehmen kann.

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

## Frontend

Mit [ChartJS](https://www.chartjs.org) ließen sich bestimmt sehr schicke erste Darstellungen bauen. Einzig, man muss vermutlich mit React oder vielleicht Svelte arbeiten, wenn man alles schön integrieren möchte, ansonsten wirkt das arg kompliziert. Darüber hinaus sollte das aber ganz gut funktionieren. Die Daten sollten ja immerhin kein Problem sein mit der aktuellen Pipeline.

Eine schöne Website ließe sich mit React auch mit [shadcn/ui](https://ui.shadcn.com/) bauen. Das sollte auch die Gestaltung in schnellen Zügen vorankommen lassen.

## Development

### Client

### Server

Dev-Server für FastAPI starten (mit Flag für Zugänglichkeit im lokalen Netzwerk):

```shell
uv run fastapi dev --host 0.0.0.0
```
