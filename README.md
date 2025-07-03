# TravelGuide - Intelligenter Reiseplanungs-Bot mit KI

Ein KI-gestützter Chatbot zur intelligenten Reiseplanung mit **personalisierte Empfehlungen** und **erweiterte Entscheidungslogik**.

## 🚀 Neue KI-Funktionen

### 1. Personalisierte Empfehlungen durch KI-gestützte Vorschläge
- **Intelligente Destination-Auswahl**: Basierend auf Benutzerpräferenzen (Budget, Reiseart, Gruppengröße, Jahreszeit)
- **Dynamische Bewertung**: KI-Algorithmus bewertet Destinationen nach Übereinstimmung mit Benutzerprofil
- **Budget-Schätzungen**: Automatische Kostenkalkulation pro Person/Woche
- **Aktivitätsempfehlungen**: Personalisierte Vorschläge für Sehenswürdigkeiten und Aktivitäten

### 2. Erweiterte Entscheidungslogik
- **Intelligentes Intent-Routing**: Vermittelt zwischen Dialogsystem (Rasa), Suchmodulen und generativer KI
- **Kontextbewusste Verarbeitung**: Berücksichtigt Benutzerhistorie und Präferenzen
- **Adaptive Antworten**: Passt sich an Benutzerverhalten an
- **KI-gestützte Hotel-Filterung**: Filtert Hotels basierend auf Budget-Präferenzen

## Funktionen

- **Schrittweise Dialogführung**: Sammelt systematisch Reiseziel, Daten und Budget
- **Intelligente Intent-Erkennung**: Regex-basierte Erkennung von Benutzerabsichten
- **Wetter-API**: Echte Wetterdaten über OpenWeatherMap API
- **Flugsuche**: Integration der Amadeus API mit deduplizierten Ergebnissen
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

# Amadeus API Keys für Flugdaten
AMADEUS_CLIENT_ID=your-amadeus-client-id-here
AMADEUS_CLIENT_SECRET=your-amadeus-client-secret-here
```

### API-Keys erhalten:

- **OpenWeatherMap API Key**: Registrieren Sie sich auf [openweathermap.org](https://openweathermap.org) - **KOSTENLOS**
- **Amadeus API Keys**: Registrieren Sie sich auf [amadeus.com](https://amadeus.com)

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
├── enhanced_decision_logic.py    # Erweiterte Entscheidungslogik mit KI
├── ai_recommendation_engine.py   # KI-Empfehlungsmaschine
├── decision_logic.py             # Ursprüngliche Entscheidungslogik
├── main.py                       # Flask-App mit neuen KI-APIs
├── config.env                    # API-Keys und Konfiguration
├── rasa_bot/                     # Intent-Erkennung
│   ├── __init__.py
│   └── rasa_handler.py          # Regex-basierte Intent-Erkennung
├── api_services/                 # API-Integrationen
│   ├── __init__.py
│   ├── weather_service.py       # OpenWeatherMap API
│   ├── flight_service.py        # Amadeus API (Flüge)
│   └── hotel_service.py         # Realistische Hoteldaten
├── templates/                    # Flask Templates
│   └── index.html               # Erweiterte UI mit KI-Features
└── requirements.txt              # Python-Abhängigkeiten
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

### Flugsuche (Amadeus API)
- Echte Flugdaten mit Deduplizierung
- Vollständige Airline-Namen statt Codes
- Abflugzeiten und Flugdauer
- Klickbare Google Flights Links

### Hotelsuche (Realistische Daten)
- Vorgefertigte, realistische Hoteldaten
- Basierend auf echten Hotels in beliebten Städten
- Keine API-Abhängigkeit oder Webscraping
- Klickbare Hotel-Links

### Web-Interface
- Moderne, responsive Chat-Oberfläche
- Klickbare Vorschläge
- Klickbare Links für Flüge und Hotels
- "Alles zurücksetzen" Button für neue Reiseplanung

## Lizenz

Dieses Projekt ist für Bildungszwecke erstellt. 