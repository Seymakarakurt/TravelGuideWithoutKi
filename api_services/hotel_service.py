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
from selenium.webdriver.common.action_chains import ActionChains

logger = logging.getLogger(__name__)

class HotelService:
    def __init__(self):
        self.price_cache = {}
        self.cache_file = 'hotel_prices_cache.json'
        self._load_cache()
        self.driver = None
    
    def _load_cache(self):
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.price_cache = json.load(f)
                logger.info(f"Hotel-Cache geladen: {len(self.price_cache)} Einträge")
        except Exception as e:
            logger.error(f"Fehler beim Laden des Hotel-Caches: {e}")
            self.price_cache = {}
    
    def _save_cache(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.price_cache, f, ensure_ascii=False, indent=2)
            logger.info(f"Hotel-Cache gespeichert: {len(self.price_cache)} Einträge")
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Hotel-Caches: {e}")
    
    def _get_cache_key(self, location: str, check_in: str, check_out: str, guests: int) -> str:
        return f"{location}_{check_in}_{check_out}_{guests}"

    def search_hotels(self, location: str, check_in: Optional[str] = None, 
                     check_out: Optional[str] = None, guests: int = 1, 
                     budget: Optional[int] = None) -> List[Dict[str, Any]]:
        try:
            if not check_in:
                check_in = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            if not check_out:
                check_out = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
            
            # Cache-Key erstellen
            cache_key = self._get_cache_key(location, check_in, check_out, guests)
            
            # Prüfe Cache
            if cache_key in self.price_cache:
                cached_data = self.price_cache[cache_key]
                logger.info(f"Hotels aus Cache geladen für {location}")
                
                # Kompatibilität mit altem Cache-Format
                if isinstance(cached_data, dict) and 'hotels' in cached_data:
                    # Altes Format: {"hotels": [...], "timestamp": ...}
                    cached_hotels = cached_data['hotels']
                    logger.info(f"Altes Cache-Format erkannt: {len(cached_hotels)} Hotels")
                else:
                    # Neues Format: direkt die Hotel-Liste
                    cached_hotels = cached_data
                    logger.info(f"Neues Cache-Format erkannt: {len(cached_hotels)} Hotels")
                
                # Filtere und sortiere gecachte Ergebnisse
                hotels = [h for h in cached_hotels if h.get('rating', 0) >= 3.5 or h.get('rating', 0) == 0]
                if budget:
                    hotels = [h for h in hotels if h.get('price', 0) <= budget]
                hotels.sort(key=lambda x: x.get('price', 0))
                
                return hotels
            
            logger.info(f"Starte Selenium-Webscraping für Hotels in {location}")
            
            # Verwende Selenium für Webscraping
            hotels = self._search_hotels_with_selenium(location, check_in, check_out, guests)
            
            # Filtere nur gut bewertete Hotels (Rating >= 3.5) oder Hotels ohne Bewertung
            hotels = [h for h in hotels if h.get('rating', 0) >= 3.5 or h.get('rating', 0) == 0]
            logger.info(f"Nach Bewertungsfilter: {len(hotels)} Hotels")
            
            # Budget-Filter anwenden
            if budget:
                hotels = [h for h in hotels if h.get('price', 0) <= budget]
                logger.info(f"Nach Budget-Filter: {len(hotels)} Hotels")
            
            # Sortiere nach Preis (günstig bis teuer)
            hotels.sort(key=lambda x: x.get('price', 0))
            
            # Speichere in Cache (neues Format: direkt die Hotel-Liste)
            if hotels:
                self.price_cache[cache_key] = hotels
                self._save_cache()
                logger.info(f"Hotels in Cache gespeichert: {len(hotels)} Hotels")
            
            logger.info(f"{len(hotels)} Hotels gefunden für {location} (sortiert nach Preis)")
            return hotels
            
        except Exception as e:
            logger.error(f"Fehler bei der Hotelsuche: {e}")
            return []

    def get_hotel_summary(self, hotels: List[Dict[str, Any]], location: str = "", check_in: str = None, check_out: str = None, guests: int = 1) -> str:
        """Erstellt eine Zusammenfassung der gefundenen Hotels"""
        if not hotels:
            return "Keine gut bewerteten Hotels gefunden."
        
        # Sortiere nach Preis (günstig bis teuer)
        hotels_sorted = sorted(hotels, key=lambda x: x.get('price', 0))
        
        # Suchparameter anzeigen
        search_info = ""
        if check_in and check_out:
            # Datum formatieren
            try:
                from datetime import datetime
                check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
                check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
                check_in_formatted = check_in_date.strftime("%d.%m.%Y")
                check_out_formatted = check_out_date.strftime("%d.%m.%Y")
                search_info = f"Zeitraum: {check_in_formatted} bis {check_out_formatted}\n Personen: {guests}\n\n"
            except:
                search_info = f"Zeitraum: {check_in} bis {check_out}\n Personen: {guests}\n\n"
        
        # Hauptlink zur Datenquelle (Google Hotels) mit spezifischer Stadt
        location_encoded = location.replace(' ', '+')
        main_source_link = f"Datenquelle: https://www.google.com/travel/hotels?q={location_encoded}\n\n"
        
        # Bestimme die Anzahl der anzuzeigenden Hotels (maximal 5)
        hotels_to_show = min(5, len(hotels_sorted))
        summary = f"{search_info}{main_source_link}Gefunden: {hotels_to_show} gut bewertete Hotels (sortiert nach Preis)\n\n"
        
        for i, hotel in enumerate(hotels_sorted[:5], 1):  # Maximal 5 Hotels anzeigen
            name = hotel.get('name', 'Unbekanntes Hotel')
            price = hotel.get('price', 0)
            rating = hotel.get('rating', 0)
            address = hotel.get('address', '')
            amenities = hotel.get('amenities', [])
            
            summary += f"{i}. {name}\n"
            summary += f"   Preis: {price:.0f} EUR pro Nacht\n"
            if rating > 0:
                summary += f"   Bewertung: {rating}/5 ⭐\n"
            if address:
                summary += f"   Adresse: {address}\n"
            if amenities:
                amenities_str = ', '.join(amenities[:3])  # Maximal 3 Amenities
                summary += f"   Ausstattung: {amenities_str}\n"
            
            # Nur Google Hotels Link
            booking_links = hotel.get('booking_links', {})
            if booking_links and 'Google Hotels' in booking_links:
                summary += f"   Google Hotels: {booking_links['Google Hotels']}\n"
            
            summary += "\n"
        
        return summary 
    
    def get_cached_prices(self, location: str) -> List[Dict[str, Any]]:
        """Gibt alle gecachten Preise für einen Ort zurück"""
        cached_hotels = []
        for cache_key, cache_data in self.price_cache.items():
            if location.lower() in cache_key.lower():
                cached_hotels.extend(cache_data.get('hotels', []))
        return cached_hotels
    
    def clear_cache(self):
        """Löscht den Hotel-Cache"""
        self.price_cache = {}
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        logger.info("Hotel-Cache gelöscht")

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

    def _search_hotels_with_selenium(self, location: str, check_in: str, check_out: str, guests: int) -> List[Dict[str, Any]]:
        """Sucht Hotels mit Selenium WebDriver"""
        try:
            if not self._setup_selenium_driver():
                return []
            
            # Öffne Google Hotels
            self.driver.get("https://www.google.com/travel/hotels")
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
            
            try:
                logger.info("Suche alle sichtbaren Suchfelder mit CSS-Selektor input[placeholder*='Unterkunft'] ...")
                search_boxes = self.driver.find_elements(By.CSS_SELECTOR, 'input[placeholder*="Unterkunft"]')
                if not search_boxes:
                    logger.info("Kein Feld mit placeholder*='Unterkunft' gefunden, fallback auf placeholder*='Hotel'.")
                    search_boxes = self.driver.find_elements(By.CSS_SELECTOR, 'input[placeholder*="Hotel"]')
                search_box = None
                for box in search_boxes:
                    if box.is_displayed():
                        search_box = box
                        logger.info(f"Aktives Suchfeld gewählt: value='{box.get_attribute('value')}', placeholder='{box.get_attribute('placeholder')}', autofocus={box.get_attribute('autofocus')}")
                        break
                if not search_box:
                    # Logge alle Input-Felder und ihre Attribute
                    inputs = self.driver.find_elements(By.TAG_NAME, 'input')
                    for i, inp in enumerate(inputs):
                        logger.info(f"Input {i}: value='{inp.get_attribute('value')}', placeholder='{inp.get_attribute('placeholder')}', aria-label='{inp.get_attribute('aria-label')}', jsname='{inp.get_attribute('jsname')}', autofocus='{inp.get_attribute('autofocus')}', displayed={inp.is_displayed()}")
                    logger.error("Kein aktives Suchfeld gefunden! Abbruch.")
                    return []
                # Versuche, den Löschen-Button zu klicken, falls vorhanden
                try:
                    clear_btn = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Löschen"]')
                    if clear_btn.is_displayed():
                        clear_btn.click()
                        logger.info("Löschen-Button erfolgreich geklickt.")
                        self._human_like_delay(0.2, 0.5)
                except Exception as e:
                    logger.info(f"Löschen-Button nicht gefunden oder nicht klickbar: {e}")
                # NICHT erneut das Suchfeld anklicken, sondern direkt Suchtext tippen
                
                search_query = f"hotel {location}"
                actions = ActionChains(self.driver)
                actions.move_to_element(search_box).click().perform()
                self._human_like_delay(0.2, 0.5)
                for char in search_query:
                    actions.send_keys(char)
                    actions.pause(random.uniform(0.1, 0.25))
                actions.perform()
                search_box.send_keys(Keys.ENTER)
                self._human_like_delay(2, 3)
                
                # Vorschläge loggen
                vorschlaege = self.driver.find_elements(By.CSS_SELECTOR, 'li[data-suggestion]')
                alle_suggestions = [v.get_attribute('data-suggestion') for v in vorschlaege]
                logger.info(f"Gefundene Vorschläge: {alle_suggestions}")
                # Versuche exakten Treffer
                li_elem = None
                for v in vorschlaege:
                    if v.get_attribute('data-suggestion') == search_query:
                        li_elem = v
                        logger.info(f"Exakter Vorschlag gefunden: {search_query}")
                        break
                # Falls kein exakter Treffer, suche nach erstem Vorschlag mit hotel und location
                if not li_elem:
                    for v in vorschlaege:
                        suggestion = v.get_attribute('data-suggestion') or ''
                        if 'hotel' in suggestion.lower() and location.lower() in suggestion.lower():
                            li_elem = v
                            logger.info(f"Dynamischer Vorschlag gewählt: {suggestion}")
                            break
                # Klicke, falls gefunden
                if li_elem:
                    try:
                        self._click_element_safely(li_elem, f"Vorschlag '{li_elem.get_attribute('data-suggestion')}'")
                        self._human_like_delay(2, 3)
                    except Exception as e:
                        logger.warning(f"Vorschlag gefunden, aber nicht anklickbar: {e}")
                        logger.info(f"Drücke Enter nach Eintippen von: {search_query}")
                        search_box.send_keys(Keys.ENTER)
                        self._human_like_delay(2, 3)
                else:
                    logger.warning(f"Kein passender Vorschlag gefunden. Drücke Enter nach Eintippen von: {search_query}")
                    search_box.send_keys(Keys.ENTER)
                    self._human_like_delay(2, 3)
            except Exception as e:
                logger.error(f"Suchfeld NICHT gefunden oder nicht anklickbar! Exception: {e}")
            
            # Warte auf Suchergebnisse
            self._human_like_delay(3, 5)
            
            # Scroll durch die Ergebnisse
            self._scroll_page()
            
            # Nach dem Laden und Cookie-Akzeptieren: Seite mehrfach scrollen
            for _ in range(5):
                self.driver.execute_script("window.scrollBy(0, 600);")
                self._human_like_delay(0.5, 1.2)
            
            # Extrahiere Hotels direkt aus <a>-Elementen mit aria-label
            hotels = []
            seen_hotels = set()  # Set für eindeutige Hotelnamen
            a_elements = self.driver.find_elements(By.CSS_SELECTOR, "a.W8vlAc.lRagtb[aria-label]")
            logger.info(f"Gefunden: {len(a_elements)} <a>-Elemente mit Klasse 'W8vlAc lRagtb' und aria-label")
            
            for i, a in enumerate(a_elements):
                try:
                    aria_label = a.get_attribute('aria-label')
                    logger.info(f"Verarbeite aria-label {i+1}: '{aria_label}'")
                    match = re.search(r'Preise ab (\d+(?:[.,]\d+)?)\s*€\s+für\s+(.+)', aria_label)
                    if match:
                        price = float(match.group(1).replace(',', '.'))
                        name = match.group(2).strip()
                        
                        # Prüfe ob Hotel bereits gesehen wurde
                        if name in seen_hotels:
                            logger.info(f"Hotel bereits gesehen, überspringe: {name}")
                            continue
                        
                        seen_hotels.add(name)  # Füge zur "gesehen"-Liste hinzu
                        
                        # URL-sichere Versionen
                        name_safe = name.replace(' ', '+').replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
                        location_safe = location.replace(' ', '+').replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
                        
                        # Google Hotels URL mit Check-in/Check-out Daten
                        google_hotels_url = f"https://www.google.com/travel/hotels?q={name_safe}+{location_safe}&checkin={check_in}&checkout={check_out}&adults={guests}&hl=de&gl=de&curr=EUR"
                        
                        hotels.append({
                            'name': name,
                            'price': price,
                            'rating': 0,
                            'booking_links': {
                                'Google Hotels': google_hotels_url
                            }
                        })
                        logger.info(f"Hotel extrahiert (aria-label): {name} | {price} €")
                    else:
                        logger.warning(f"Regex-Match fehlgeschlagen für aria-label: '{aria_label}'")
                except Exception as e:
                    logger.warning(f"Fehler beim Extrahieren aus aria-label: {e}")
            

            
            # Wenn Hotels gefunden, direkt zurückgeben
            if hotels:
                logger.info(f"{len(hotels)} Hotels erfolgreich aus aria-label extrahiert.")
                return hotels

            logger.warning("Keine Hotels aus aria-label extrahiert.")
            return []
            
        except Exception as e:
            logger.error(f"Fehler bei Selenium-Hotelsuche: {e}")
            return []
        
        finally:
            self._close_selenium_driver()