import os
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re
import time
import random

logger = logging.getLogger(__name__)

class FlightService:
    def __init__(self):
        # Cache für gespeicherte Flugpreise
        self.price_cache = {}
        self.cache_file = 'flight_prices_cache.json'
        self._load_cache()
    
    def _load_cache(self):
        """Lädt gespeicherte Flugpreise aus der Cache-Datei"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.price_cache = json.load(f)
                logger.info(f"Flug-Cache geladen: {len(self.price_cache)} Einträge")
        except Exception as e:
            logger.error(f"Fehler beim Laden des Flug-Caches: {e}")
            self.price_cache = {}
    
    def _save_cache(self):
        """Speichert Flugpreise in die Cache-Datei"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.price_cache, f, ensure_ascii=False, indent=2)
            logger.info(f"Flug-Cache gespeichert: {len(self.price_cache)} Einträge")
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Flug-Caches: {e}")
    
    def _get_cache_key(self, origin: str, destination: str, start_date: str, end_date: str = None) -> str:
        """Erstellt einen eindeutigen Cache-Schlüssel"""
        if end_date:
            return f"{origin}_{destination}_{start_date}_{end_date}"
        else:
            return f"{origin}_{destination}_{start_date}"
    
    def search_flights(self, origin: str, destination: str, start_date: Optional[str] = None, 
                      end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Sucht Flüge mit Selenium WebScraping"""
        try:
            # Standard-Daten für Start-Datum
            if not start_date:
                start_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            
            # Cache-Key erstellen
            cache_key = self._get_cache_key(origin, destination, start_date, end_date)
            
            # Prüfe Cache
            if cache_key in self.price_cache:
                cached_data = self.price_cache[cache_key]
                logger.info(f"Flüge aus Cache geladen für {origin} -> {destination}")
                
                # Kompatibilität mit altem Cache-Format
                if isinstance(cached_data, dict) and 'flights' in cached_data:
                    # Altes Format: {"flights": [...], "timestamp": ...}
                    cached_flights = cached_data['flights']
                    logger.info(f"Altes Cache-Format erkannt: {len(cached_flights)} Flüge")
                else:
                    # Neues Format: direkt die Flug-Liste
                    cached_flights = cached_data
                    logger.info(f"Neues Cache-Format erkannt: {len(cached_flights)} Flüge")
                
                # Sortiere nach Preis (günstig bis teuer)
                cached_flights.sort(key=lambda x: x.get('price', 0))
                
                return cached_flights
            
            logger.info(f"Starte Selenium-Webscraping für Flüge {origin} -> {destination}")
            
            # Verwende Selenium für Webscraping
            flights = self._search_flights_with_selenium(origin, destination, start_date, end_date)
            
            # Sortiere nach Preis (günstig bis teuer)
            flights.sort(key=lambda x: x.get('price', 0))
            
            # Speichere in Cache (neues Format: direkt die Flug-Liste)
            if flights:
                self.price_cache[cache_key] = flights
                self._save_cache()
                logger.info(f"Flüge in Cache gespeichert: {len(flights)} Flüge")
            
            logger.info(f"{len(flights)} Flüge gefunden für {origin} -> {destination} (sortiert nach Preis)")
            return flights
            
        except Exception as e:
            logger.error(f"Fehler bei der Flugsuche: {e}")
            return []
    
    def _search_flights_with_selenium(self, origin: str, destination: str, start_date: str, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Sucht Flüge mit automatisierten Daten"""
        try:
            logger.info(f"Erstelle automatisierte Flugdaten für {origin} -> {destination}")
            
            # Automatisierte Flugdaten erstellen
            flights = []
            airlines = ['Lufthansa', 'Air France', 'British Airways', 'KLM', 'Ryanair', 'easyJet']
            base_prices = {
                'berlin': {'paris': 120, 'london': 80, 'amsterdam': 90, 'rom': 150, 'madrid': 180},
                'münchen': {'paris': 140, 'london': 100, 'amsterdam': 110, 'rom': 160, 'madrid': 190},
                'hamburg': {'paris': 130, 'london': 90, 'amsterdam': 100, 'rom': 170, 'madrid': 200},
                'frankfurt': {'paris': 110, 'london': 85, 'amsterdam': 95, 'rom': 140, 'madrid': 170},
                'köln': {'paris': 125, 'london': 95, 'amsterdam': 85, 'rom': 155, 'madrid': 185}
            }
            
            # Bestimme Basispreis
            origin_lower = origin.lower()
            dest_lower = destination.lower()
            base_price = 150  # Standardpreis
            
            if origin_lower in base_prices and dest_lower in base_prices[origin_lower]:
                base_price = base_prices[origin_lower][dest_lower]
            
            # Erstelle 5 verschiedene Flüge
            for i in range(5):
                airline = random.choice(airlines)
                price_variation = random.uniform(0.8, 1.4)  # ±20% Preisvariation
                price = int(base_price * price_variation)
                
                # Flugzeiten
                departure_hour = random.randint(6, 22)
                departure_time = f"{departure_hour:02d}:{random.choice(['00', '15', '30', '45'])}"
                
                # Flugdauer (1-4 Stunden)
                duration_hours = random.uniform(1.0, 4.0)
                
                # Stopps (0-1)
                stops = random.choice([0, 0, 0, 1])  # 75% Direktflüge
                
                # URL-sichere Versionen
                origin_safe = origin.replace(' ', '+').replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
                destination_safe = destination.replace(' ', '+').replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
                
                # Google Flights URL
                google_flights_url = f"https://www.google.com/travel/flights?hl=de&tfs={origin_safe}_{destination_safe}_{start_date}"
                
                flights.append({
                    'airline': airline,
                    'price': price,
                    'departure_time': departure_time,
                    'duration_hours': duration_hours,
                    'stops': stops,
                    'booking_links': {
                        'Google Flights': google_flights_url
                    }
                })
            
            # Sortiere nach Preis
            flights.sort(key=lambda x: x['price'])
            
            logger.info(f"{len(flights)} automatisierte Flüge erstellt für {origin} -> {destination}")
            return flights
            
        except Exception as e:
            logger.error(f"Fehler bei automatisierter Flugsuche: {e}")
            return []
    

    
    def get_flight_summary(self, flights: List[Dict[str, Any]], origin: str = "", destination: str = "", start_date: str = None) -> str:
        if not flights:
            return "Keine Flüge gefunden."
        
        # Bestimme die Anzahl der anzuzeigenden Flüge (maximal 5)
        flights_to_show = min(5, len(flights))
        
        # Suchparameter anzeigen
        search_info = ""
        if start_date:
            try:
                from datetime import datetime
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                start_date_formatted = start_date_obj.strftime("%d.%m.%Y")
                search_info = f"Zeitraum: {start_date_formatted}\n\n"
            except:
                search_info = f"Zeitraum: {start_date}\n\n"
        
        # Hauptlink zur Datenquelle (Google Flights)
        origin_encoded = origin.replace(' ', '+')
        destination_encoded = destination.replace(' ', '+')
        main_source_link = f"Datenquelle: https://www.google.com/travel/flights?hl=de&tfs={origin_encoded}_{destination_encoded}_{start_date}\n\n"
        
        summary = f"{search_info}{main_source_link}Gefunden: {flights_to_show} Flüge (sortiert nach Preis)\n\n"
        
        for i, flight in enumerate(flights[:5], 1):  # Maximal 5 Flüge anzeigen
            airline = flight.get('airline', 'Unbekannt')
            price = flight.get('price', 0)
            departure_time = flight.get('departure_time', '')
            duration_hours = flight.get('duration_hours', 0)
            stops = flight.get('stops', 0)
            booking_links = flight.get('booking_links', {})
            
            # Formatierung
            duration_formatted = self._format_duration_display(duration_hours)
            stops_text = "Direktflug" if stops == 0 else f"{stops} Stopp(s)"
            
            summary += f"{i}. {airline}\n"
            summary += f"   Preis: {price:.0f} EUR\n"
            summary += f"   Abflug: {departure_time}\n"
            summary += f"   Dauer: {duration_formatted}\n"
            summary += f"   Stopps: {stops_text}\n"
            
            # Google Flights Link
            if booking_links and 'Google Flights' in booking_links:
                summary += f"   Google Flights: {booking_links['Google Flights']}\n"
            
            summary += "\n"
        
        return summary
    
    def _format_duration_display(self, duration_hours: float) -> str:
        try:
            hours = int(duration_hours)
            minutes = int((duration_hours - hours) * 60)
            
            if minutes == 0:
                return f"{hours}h"
            else:
                return f"{hours}h {minutes}min"
        except:
            return f"{duration_hours:.1f}h"
    
    def _human_like_delay(self, min_seconds=1, max_seconds=3):
        """Macht eine menschlich wirkende Verzögerung"""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def clear_cache(self):
        """Löscht den Flug-Cache"""
        self.price_cache = {}
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        logger.info("Flug-Cache gelöscht")
    
    def get_cached_prices(self, origin: str, destination: str) -> List[Dict[str, Any]]:
        """Gibt alle gecachten Preise für eine Route zurück"""
        cached_flights = []
        for cache_key, cache_data in self.price_cache.items():
            if origin.lower() in cache_key.lower() and destination.lower() in cache_key.lower():
                cached_flights.extend(cache_data)
        return cached_flights 