import os
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger(__name__)

class FlightService:
    def __init__(self):
        # Cache für gespeicherte Flugpreise
        self.price_cache = {}
        self.cache_file = 'flight_prices_cache.json'
        self._load_cache()
        
        # Selenium WebDriver Setup
        self.driver = None
    
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
        """Sucht Flüge mit Selenium WebDriver"""
        try:
            if not self._setup_selenium_driver():
                return []
            
            # Öffne Google Flights
            self.driver.get("https://www.google.com/travel/flights")
            self._human_like_delay(2, 4)
            
            # Cookie-Banner akzeptieren
            self._accept_cookies()
            
            # Warte auf die Seite zu laden
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Warte, bis kein Overlay mehr sichtbar ist
            try:
                WebDriverWait(self.driver, 5).until_not(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, ".VfPpkd-RLmnJb"))
                )
                logger.info("Overlay '.VfPpkd-RLmnJb' ist verschwunden.")
            except Exception:
                logger.info("Kein Overlay '.VfPpkd-RLmnJb' sichtbar oder bereits verschwunden.")
            
            # Suche nach Flügen
            try:
                # Klicke auf "Von" Feld
                from_field = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='Von'], input[aria-label*='Von'], input[name*='origin']"))
                )
                self._click_element_safely(from_field, "Von-Feld")
                
                # Lösche vorhandenen Text und tippe Abflugort
                from_field.clear()
                self._human_like_delay(0.5, 1)
                
                for char in origin:
                    from_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
                
                self._human_like_delay(1, 2)
                
                # Wähle den ersten Vorschlag
                try:
                    suggestions = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul[role='listbox'] li, .aajZCb li, .erkvQe li"))
                    )
                    if suggestions:
                        self._click_element_safely(suggestions[0], "Abflugort-Vorschlag")
                        self._human_like_delay(1, 2)
                except Exception as e:
                    logger.info(f"Keine Abflugort-Vorschläge gefunden: {e}")
                    from_field.send_keys(Keys.ENTER)
                    self._human_like_delay(1, 2)
                
                # Klicke auf "Nach" Feld
                to_field = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='Nach'], input[aria-label*='Nach'], input[name*='destination']"))
                )
                self._click_element_safely(to_field, "Nach-Feld")
                
                # Lösche vorhandenen Text und tippe Zielort
                to_field.clear()
                self._human_like_delay(0.5, 1)
                
                for char in destination:
                    to_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
                
                self._human_like_delay(1, 2)
                
                # Wähle den ersten Vorschlag
                try:
                    suggestions = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul[role='listbox'] li, .aajZCb li, .erkvQe li"))
                    )
                    if suggestions:
                        self._click_element_safely(suggestions[0], "Zielort-Vorschlag")
                        self._human_like_delay(1, 2)
                except Exception as e:
                    logger.info(f"Keine Zielort-Vorschläge gefunden: {e}")
                    to_field.send_keys(Keys.ENTER)
                    self._human_like_delay(1, 2)
                
                # Klicke auf "Suchen" Button
                search_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label*='Suchen'], button:contains('Suchen'), button[type='submit']"))
                )
                self._click_element_safely(search_button, "Suchen-Button")
                
            except Exception as e:
                logger.warning(f"Fehler beim Suchen: {e}")
            
            # Warte auf Suchergebnisse
            self._human_like_delay(5, 8)
            
            # Scroll durch die Ergebnisse
            self._scroll_page()
            
            # Extrahiere Flüge aus den Suchergebnissen
            flights = []
            seen_flights = set()  # Set für eindeutige Flüge
            
            # Suche nach Flug-Karten
            flight_cards = self.driver.find_elements(By.CSS_SELECTOR, "[class*='flight'], [class*='itinerary'], [data-flight-id]")
            logger.info(f"Gefunden: {len(flight_cards)} Flug-Karten")
            
            for i, card in enumerate(flight_cards[:10]):  # Maximal 10 Flüge
                try:
                    flight_info = self._extract_flight_from_card(card, origin, destination, start_date)
                    if flight_info:
                        # Erstelle einen eindeutigen Schlüssel für den Flug
                        flight_key = (
                            flight_info.get('airline', ''),
                            flight_info.get('departure_time', ''),
                            flight_info.get('price', 0)
                        )
                        
                        if flight_key not in seen_flights:
                            seen_flights.add(flight_key)
                            flights.append(flight_info)
                            logger.info(f"Flug extrahiert: {flight_info.get('airline', '')} - {flight_info.get('price', 0)} EUR")
                
                except Exception as e:
                    logger.warning(f"Fehler beim Extrahieren der Flug-Karte {i+1}: {e}")
                    continue
            
            # Wenn keine Karten gefunden, versuche andere Selektoren
            if not flights:
                flights = self._extract_flights_from_list_view(origin, destination, start_date)
            
            return flights
            
        except Exception as e:
            logger.error(f"Fehler bei Selenium-Flugsuche: {e}")
            return []
        
        finally:
            self._close_selenium_driver()
    
    def _extract_flight_from_card(self, card, origin: str, destination: str, start_date: str) -> Optional[Dict[str, Any]]:
        """Extrahiert Flug-Daten aus einer Google Flights Karte"""
        try:
            # Alle sichtbaren Texte in der Karte
            all_texts = [el.text.strip() for el in card.find_elements(By.XPATH, './/*') if el.text.strip()]
            
            if not all_texts:
                return None
            
            # Preis-Extraktion: Suche nach Text mit '€'
            price = 0
            price_text = next((t for t in all_texts if '€' in t), None)
            if price_text:
                price_match = re.search(r'(\d+(?:[.,]\d+)?)', price_text.replace(',', '.'))
                if price_match:
                    price = float(price_match.group(1))
            
            # Airline-Extraktion: Suche nach bekannten Airlines
            airline = "Unbekannt"
            airline_codes = ['LH', 'AF', 'BA', 'KL', 'IB', 'AZ', 'OS', 'LX', 'SK', 'AY', 'LO', 'TK', 'EK', 'QR', 'EY', 'FR', 'U2', 'W6']
            for text in all_texts:
                for code in airline_codes:
                    if code in text:
                        airline = self._get_airline_name(code)
                        break
                if airline != "Unbekannt":
                    break
            
            # Zeit-Extraktion: Suche nach Zeit-Format (HH:MM)
            departure_time = ""
            time_match = re.search(r'(\d{1,2}:\d{2})', ' '.join(all_texts))
            if time_match:
                departure_time = time_match.group(1)
            
            # Dauer-Extraktion: Suche nach "Xh Ym" Format
            duration_hours = 1.5
            duration_match = re.search(r'(\d+)h\s*(\d+)?m?', ' '.join(all_texts))
            if duration_match:
                hours = int(duration_match.group(1))
                minutes = int(duration_match.group(2)) if duration_match.group(2) else 0
                duration_hours = hours + (minutes / 60)
            
            # Stopps-Extraktion
            stops = 0
            if any('Direkt' in text or 'Direct' in text for text in all_texts):
                stops = 0
            elif any('1 Stopp' in text or '1 stop' in text for text in all_texts):
                stops = 1
            elif any('2 Stopps' in text or '2 stops' in text for text in all_texts):
                stops = 2
            
            # URL-sichere Versionen
            origin_safe = origin.replace(' ', '+').replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
            destination_safe = destination.replace(' ', '+').replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
            
            # Google Flights URL mit Datum
            google_flights_url = f"https://www.google.com/travel/flights?hl=de&tfs={origin_safe}_{destination_safe}_{start_date}"
            
            return {
                'id': f'flight_{hash(f"{airline}{departure_time}{price}") % 10000}',
                'price': price,
                'currency': 'EUR',
                'airline': airline,
                'flight_number': f"{airline[:2]}{random.randint(100, 999)}",
                'departure_airport': origin,
                'arrival_airport': destination,
                'departure_time': departure_time,
                'arrival_time': '',
                'duration_hours': duration_hours,
                'stops': stops,
                'return_flight': False,
                'booking_links': {
                    'Google Flights': google_flights_url
                },
                'airline_logo': f"https://images.kiwi.com/airlines/64/{airline[:2]}.png"
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Extrahieren der Flug-Karte: {e}")
            return None
    
    def _extract_flights_from_list_view(self, origin: str, destination: str, start_date: str) -> List[Dict[str, Any]]:
        """Extrahiert Flüge aus der Listen-Ansicht"""
        try:
            flights = []
            
            # Suche nach Flug-Listen-Elementen
            list_items = self.driver.find_elements(By.CSS_SELECTOR, 
                "[class*='flight-item'], [class*='itinerary-item'], [class*='listing-item'], li")
            
            for item in list_items[:5]:  # Maximal 5 Flüge
                try:
                    # Versuche Flug-Daten zu extrahieren
                    all_texts = [el.text.strip() for el in item.find_elements(By.XPATH, './/*') if el.text.strip()]
                    
                    if all_texts:
                        flight_info = self._extract_flight_from_card(item, origin, destination, start_date)
                        if flight_info:
                            flights.append(flight_info)
                
                except Exception as e:
                    continue
            
            return flights
            
        except Exception as e:
            logger.error(f"Fehler beim Extrahieren der Listen-Ansicht: {e}")
            return []
    
    def get_flight_summary(self, flights: List[Dict[str, Any]]) -> str:
        if not flights:
            return "Keine Flüge gefunden. Mögliche Gründe:\n• Keine direkten Flüge verfügbar\n• Falsche Flughafen-Codes\n• Keine Flüge für das gewählte Datum\n\nVersuchen Sie es mit einem anderen Datum oder Ziel."

        outbound_flights = [f for f in flights if not f.get('return_flight', False)]
        return_flights = [f for f in flights if f.get('return_flight', False)]
        
        summary = ""

        if outbound_flights:
            summary += "Hinflüge:\n"
            for i, flight in enumerate(outbound_flights[:3], 1):  # Maximal 3 Hinflüge
                price = flight.get('price', 0)
                airline_code = flight.get('airline', 'Unbekannt')
                airline_name = self._get_airline_name(airline_code)
                duration = flight.get('duration_hours', 0)
                stops = flight.get('stops', 0)
                booking_links = flight.get('booking_links', {})
                
                duration_formatted = self._format_duration_display(duration)
                departure_time = flight.get('departure_time', '')
                departure_formatted = self._format_departure_time(departure_time)
                
                summary += f"{i}. {airline_name} - {price:.0f}€\n"
                summary += f"   {duration_formatted}, {stops} Stopp(s)\n"
                summary += f"   {departure_formatted}\n"
                if booking_links:
                    summary += f"   Buchung: {booking_links.get('Google Flights', '')}\n"
                summary += "\n"

        if return_flights:
            summary += "Rückflüge:\n"
            for i, flight in enumerate(return_flights[:3], 1):
                price = flight.get('price', 0)
                airline_code = flight.get('airline', 'Unbekannt')
                airline_name = self._get_airline_name(airline_code)
                duration = flight.get('duration_hours', 0)
                stops = flight.get('stops', 0)
                booking_links = flight.get('booking_links', {})
                
                duration_formatted = self._format_duration_display(duration)
                departure_time = flight.get('departure_time', '')
                departure_formatted = self._format_departure_time(departure_time)
                
                summary += f"{i}. {airline_name} - {price:.0f}€\n"
                summary += f"   {duration_formatted}, {stops} Stopp(s)\n"
                summary += f"   {departure_formatted}\n"
                if booking_links:
                    summary += f"   Buchung: {booking_links.get('Google Flights', '')}\n"
                summary += "\n"
        
        return summary
    
    def _get_airline_name(self, airline_code: str) -> str:
        airline_names = {
            'LH': 'Lufthansa',
            'AF': 'Air France',
            'BA': 'British Airways',
            'KL': 'KLM',
            'IB': 'Iberia',
            'AZ': 'Alitalia',
            'OS': 'Austrian Airlines',
            'LX': 'Swiss',
            'SK': 'SAS Scandinavian Airlines',
            'SAS': 'SAS Scandinavian Airlines',
            'AY': 'Finnair',
            'LO': 'LOT Polish Airlines',
            'OK': 'Czech Airlines',
            'MA': 'Malev',
            'OA': 'Olympic Air',
            'TK': 'Turkish Airlines',
            'EK': 'Emirates',
            'QR': 'Qatar Airways',
            'EY': 'Etihad Airways',
            'NH': 'ANA',
            'JL': 'Japan Airlines',
            'SQ': 'Singapore Airlines',
            'TG': 'Thai Airways',
            'QF': 'Qantas',
            'AA': 'American Airlines',
            'UA': 'United Airlines',
            'DL': 'Delta Air Lines',
            'AC': 'Air Canada',
            'WS': 'WestJet',
            'D8': 'Norwegian Air International',
            'VF': 'Vueling',
            'FR': 'Ryanair',
            'U2': 'easyJet',
            'W6': 'Wizz Air',
            'HV': 'Transavia',
            'DY': 'Norwegian Air Shuttle',
            'FI': 'Icelandair',
            'PC': 'Pegasus Airlines',
            'JU': 'Air Serbia'
        }
        
        return airline_names.get(airline_code.upper(), airline_code.upper())
    
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
    
    def _format_departure_time(self, departure_time: str) -> str:
        try:
            if not departure_time:
                return "Zeit unbekannt"

            if 'T' in departure_time:
                date_part, time_part = departure_time.split('T')
                date_obj = datetime.strptime(date_part, '%Y-%m-%d')
                time_obj = datetime.strptime(time_part[:5], '%H:%M')
                
                return f"{date_obj.strftime('%d.%m.%Y')} {time_obj.strftime('%H:%M')}"
            else:
                return departure_time
        except:
            return departure_time
    
    def _get_airport_code(self, city: str) -> str:
        airport_codes = {
            'paris': 'CDG',
            'berlin': 'BER',
            'münchen': 'MUC',
            'hamburg': 'HAM',
            'frankfurt': 'FRA',
            'köln': 'CGN',
            'düsseldorf': 'DUS',
            'stuttgart': 'STR',
            'rom': 'FCO',
            'milan': 'MXP',
            'venedig': 'VCE',
            'florenz': 'FLR',
            'london': 'LHR',
            'madrid': 'MAD',
            'barcelona': 'BCN',
            'amsterdam': 'AMS',
            'brüssel': 'BRU',
            'wien': 'VIE',
            'zürich': 'ZRH',
            'genf': 'GVA',
            'stockholm': 'ARN',
            'oslo': 'OSL',
            'kopenhagen': 'CPH',
            'helsinki': 'HEL',
            'warschau': 'WAW',
            'prag': 'PRG',
            'budapest': 'BUD',
            'athen': 'ATH',
            'istanbul': 'IST',
            'dubai': 'DXB',
            'tokio': 'NRT',
            'singapur': 'SIN',
            'bangkok': 'BKK',
            'sydney': 'SYD',
            'melbourne': 'MEL',
            'new york': 'JFK',
            'los angeles': 'LAX',
            'chicago': 'ORD',
            'miami': 'MIA',
            'toronto': 'YYZ',
            'montreal': 'YUL',
            'vancouver': 'YVR'
        }
        
        city_lower = city.lower().strip()
        
        # Versuche zuerst den exakten Match
        if city_lower in airport_codes:
            return airport_codes[city_lower]
        
        # Suche nach dem ersten Wort (Stadtname)
        first_word = city_lower.split()[0] if city_lower else city_lower
        if first_word in airport_codes:
            return airport_codes[first_word]
        
        # Fallback: Gib den ursprünglichen String zurück, aber nur die ersten 3 Zeichen
        return city.upper()[:3] if len(city) >= 3 else city.upper()
    
    def test_connection(self) -> Dict[str, Any]:
        """Testet die Verbindung und gibt Status-Informationen zurück"""
        try:
            # Teste mit einer einfachen Suche
            test_origin = 'BER'
            test_destination = 'CDG'
            test_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            
            logger.info(f"Teste Verbindung: {test_origin} -> {test_destination} am {test_date}")
            
            flights = self.search_flights(test_origin, test_destination, test_date)
            
            if flights:
                return {
                    'status': 'success',
                    'message': f'Verbindung erfolgreich - {len(flights)} Test-Flüge gefunden',
                    'details': f'Status: {len(flights)} Flüge gefunden'
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Keine Flüge gefunden',
                    'details': 'Keine Flüge gefunden'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Verbindungsfehler: {str(e)}',
                'details': 'Exception beim Test'
            }
    
    def _setup_selenium_driver(self):
        """Richtet den Selenium WebDriver ein"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Headless-Modus für Server-Umgebung
            chrome_options.add_argument('--headless')
            
            # Fenstergröße setzen
            chrome_options.add_argument('--window-size=1920,1080')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Selenium WebDriver erfolgreich eingerichtet")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Einrichten des Selenium WebDrivers: {e}")
            return False
    
    def _close_selenium_driver(self):
        """Schließt den Selenium WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logger.info("Selenium WebDriver geschlossen")
            except Exception as e:
                logger.error(f"Fehler beim Schließen des WebDrivers: {e}")
    
    def _human_like_delay(self, min_seconds=1, max_seconds=3):
        """Macht eine menschlich wirkende Verzögerung"""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def _scroll_page(self):
        """Scrollt die Seite wie ein Mensch"""
        try:
            # Scroll nach unten
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            self._human_like_delay(1, 2)
            
            # Scroll weiter nach unten
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._human_like_delay(1, 2)
            
            # Scroll zurück nach oben
            self.driver.execute_script("window.scrollTo(0, 0);")
            self._human_like_delay(1, 2)
            
        except Exception as e:
            logger.warning(f"Fehler beim Scrollen: {e}")
    
    def _click_element_safely(self, element, description=""):
        """Klickt sicher auf ein Element"""
        try:
            # Scroll zum Element
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            self._human_like_delay(0.5, 1)
            
            # Klicke auf das Element
            element.click()
            self._human_like_delay(1, 2)
            
            logger.info(f"Erfolgreich geklickt: {description}")
            return True
            
        except Exception as e:
            logger.warning(f"Fehler beim Klicken auf {description}: {e}")
            return False
    
    def _accept_cookies(self):
        """Akzeptiert den Cookie-Banner, falls vorhanden"""
        try:
            if not self.driver:
                return False
            # Warte auf Cookie-Banner (verschiedene Varianten)
            possible_selectors = [
                "button[aria-label*='Alle akzeptieren']",
                "button[aria-label*='Accept all']",
                "button[aria-label*='Zustimmen']",
                "button[aria-label*='Ich stimme zu']",
                "button[aria-label*='Agree']",
                "button[aria-label*='Akzeptieren']",
                "button[role='button'] span:contains('Alle akzeptieren')",
                "button:contains('Alle akzeptieren')",
                "button:contains('Accept all')",
                "div[role='dialog'] button",
            ]
            for selector in possible_selectors:
                try:
                    cookie_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    if cookie_btn:
                        self._click_element_safely(cookie_btn, "Cookie-Banner")
                        logger.info(f"Cookie-Banner akzeptiert mit Selektor: {selector}")
                        self._human_like_delay(1, 2)
                        return True
                except Exception:
                    continue
            logger.info("Kein Cookie-Banner gefunden oder bereits akzeptiert.")
            return False
        except Exception as e:
            logger.warning(f"Fehler beim Akzeptieren des Cookie-Banners: {e}")
            return False
    
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