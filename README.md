# TravelGuide - Intelligenter Reiseplanungs-Bot

Ein KI-gestützter Chatbot zur intelligenten Reiseplanung mit schrittweiser Datensammlung.

## Funktionen

- **Schrittweise Dialogführung**: Sammelt systematisch Reiseziel, Daten und Budget
- **Intelligente Intent-Erkennung**: Regex-basierte Erkennung von Benutzerabsichten
- **KI-Integration**: OpenRouter API für intelligente Reiseberatung
- **Wetter-API**: Echte Wetterdaten über OpenWeatherMap API
- **Flugsuche**: Generierte Flugdaten mit deduplizierten Ergebnissen
- **Hotelsuche**: Realistische Hoteldaten basierend auf echten Hotels
- **Web-Interface**: Moderne Chat-Oberfläche mit klickbaren Links
- **Session-Management**: Benutzer-Sessions mit "Alles zurücksetzen" Funktion

## Installation

1. **Python-Umgebung einrichten**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate     # Windows
```

2. **Abhängigkeiten installieren**:
```bash
pip install -r requirements.txt
```

3. **API-Keys konfigurieren**:
Bearbeiten Sie die `config.env` Datei:

```env
# OpenWeatherMap API Key für Wetterdaten (KOSTENLOS)
OPENWEATHER_API_KEY=your-openweather-api-key-here

# OpenRouter API Key für KI-Integration (KOSTENLOS mit Limits)
OPENROUTER_API_KEY=your-openrouter-api-key-here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

### API-Keys erhalten:

- **OpenWeatherMap API Key**: Registrieren Sie sich auf [openweathermap.org](https://openweathermap.org) - **KOSTENLOS**
- **OpenRouter API Key**: Registrieren Sie sich auf [openrouter.ai](https://openrouter.ai) - **KOSTENLOS** (mit Limits)

## Verwendung

1. **Bot starten**:
```bash
python main.py
```

2. **Web-Interface öffnen**:
Öffnen Sie http://localhost:5000 in Ihrem Browser

3. **Mit dem Bot chatten**:
- Der Bot fragt schrittweise nach: Reiseziel → Reisedaten → Budget
- Fragen Sie nach Wetter: "Wie ist das Wetter in Paris?"
- Lassen Sie sich Flüge oder Hotels zeigen
- Nutzen Sie "Alles zurücksetzen" für eine neue Reiseplanung

## Projektstruktur

```
TravelGuide/
├── main.py                 # Hauptanwendung
├── decision_logic.py       # Entscheidungslogik und Session-Management
├── config.env             # API-Keys und Konfiguration
├── rasa_bot/              # Intent-Erkennung
│   ├── __init__.py
│   └── rasa_handler.py    # Regex-basierte Intent-Erkennung
├── api_services/          # API-Integrationen
│   ├── __init__.py
│   ├── weather_service.py # OpenWeatherMap API
│   ├── flight_service.py  # Generierte Flugdaten
│   ├── hotel_service.py   # Realistische Hoteldaten
│   └── openrouter_service.py # OpenRouter KI-API
├── templates/             # Flask Templates
│   └── index.html         # Moderne Chat-Interface
└── requirements.txt       # Python-Abhängigkeiten
```

## Features im Detail

### Schrittweise Dialogführung
- Sammelt systematisch: Reiseziel → Reisedaten → Budget
- Verhindert Duplikate durch Session-Management
- Kontextbewusste Antworten und Vorschläge

### Intelligente Intent-Erkennung
- Erkennt automatisch Reiseziele, Daten, Budget und Präferenzen
- Fallback für unbekannte Intents
- Einzelne Städtenamen werden automatisch als Reiseziel erkannt

### Wetter-API (OpenWeatherMap)
- **Aktuelle Wetterdaten** für beliebige Reiseziele
- **Wettervorhersagen** für Reisezeiträume

### Flugsuche (Generierte Daten)
- Generierte Flugdaten mit Deduplizierung
- Vollständige Airline-Namen statt Codes
- Abflugzeiten und Flugdauer
- Klickbare Google Flights Links

### Hotelsuche (Realistische Daten)
- Vorgefertigte, realistische Hoteldaten
- Basierend auf echten Hotels in beliebten Städten
- Keine API-Abhängigkeit oder Webscraping
- Klickbare Hotel-Links

### KI-Integration (OpenRouter)
- Intelligente Reiseberatung mit verschiedenen KI-Modellen
- Kontextbewusste Antworten basierend auf der Reiseplanung
- Unterstützung für Claude, GPT-4, Gemini und andere Modelle
- Automatischer Fallback bei API-Problemen

### Web-Interface
- Moderne, responsive Chat-Oberfläche
- Klickbare Vorschläge
- Klickbare Links für Flüge und Hotels
- "Alles zurücksetzen" Button für neue Reiseplanung

## Lizenz

Dieses Projekt ist für Bildungszwecke erstellt. 