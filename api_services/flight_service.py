import os
import requests
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FlightService:
    def __init__(self):
        self.client_id = os.getenv('AMADEUS_CLIENT_ID')
        self.client_secret = os.getenv('AMADEUS_CLIENT_SECRET')
        self.base_url = "https://test.api.amadeus.com/v2"
        
        if not self.client_id or not self.client_secret:
            logger.warning("Amadeus API Credentials nicht gefunden")
            self.access_token = None
        else:
            self.access_token = self._get_access_token()
            if not self.access_token:
                logger.warning("Amadeus API Token konnte nicht geholt werden")
    
    def _get_access_token(self) -> Optional[str]:
        try:
            url = "https://test.api.amadeus.com/v1/security/oauth2/token"
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            return token_data.get('access_token')
            
        except Exception as e:
            logger.error(f"Fehler beim Token-Holen: {e}")
            return None
    
    def search_flights(self, origin: str, destination: str, start_date: Optional[str] = None, 
                      end_date: Optional[str] = None, budget: Optional[int] = None) -> List[Dict[str, Any]]:

        try:
            if not self.access_token:
                return []
            

            departure_date = self._format_date(start_date) if start_date else (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            return_date = self._format_date(end_date) if end_date else None
            

            outbound_flights = self._search_amadeus_flights(origin, destination, departure_date, None, budget)
            

            return_flights = []
            if return_date:
                return_flights = self._search_amadeus_flights(destination, origin, return_date, None, budget)

                for flight in return_flights:
                    flight['return_flight'] = True
            

            all_flights = outbound_flights + return_flights
            
            return all_flights
            
        except Exception as e:
            logger.error(f"Fehler bei der Flugsuche: {e}")
            return []
    
    def _search_amadeus_flights(self, origin: str, destination: str, departure_date: str, 
                               return_date: Optional[str] = None, budget: Optional[int] = None) -> List[Dict[str, Any]]:

        try:
            url = f"{self.base_url}/shopping/flight-offers"
            

            origin_code = self._get_airport_code(origin)
            destination_code = self._get_airport_code(destination)
            
            params = {
                'originLocationCode': origin_code,
                'destinationLocationCode': destination_code,
                'departureDate': departure_date,
                'adults': 1,
                'max': 10,
                'currencyCode': 'EUR'
            }
            
            if return_date:
                params['returnDate'] = return_date
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Suche Flüge: {origin_code} -> {destination_code} am {departure_date}")
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            flights = []
            seen_flights = set()
            
            for flight in data.get('data', []):
                flight_info = self._parse_amadeus_flight_data(flight)
                if flight_info:
                    flight_key = (
                        flight_info.get('airline', ''),
                        flight_info.get('flight_number', ''),
                        flight_info.get('departure_time', ''),
                        flight_info.get('price', 0)
                    )
                    
                    if flight_key not in seen_flights:
                        seen_flights.add(flight_key)
                        flights.append(flight_info)
            
            return flights
            
        except Exception as e:
            logger.error(f"Fehler bei Amadeus API: {e}")
            return []
    
    def _parse_amadeus_flight_data(self, flight: Dict[str, Any]) -> Optional[Dict[str, Any]]:

        try:

            pricing = flight.get('pricingOptions', {})
            price = pricing.get('fareBreakdowns', [{}])[0].get('includedCheckedBags', {}).get('weight', 0)
            if not price:
                price = flight.get('price', {}).get('total', 0)
            

            itineraries = flight.get('itineraries', [])
            if not itineraries:
                return None
            
            outbound = itineraries[0].get('segments', [])
            inbound = itineraries[1].get('segments', []) if len(itineraries) > 1 else []
            

            if not outbound:
                return None
            
            first_segment = outbound[0]
            

            duration = flight.get('itineraries', [{}])[0].get('duration', 'PT1H30M')
            duration_hours = self._parse_duration(duration)
            

            stops = len(outbound) - 1
            

            departure_airport = first_segment.get('departure', {}).get('iataCode', '')
            arrival_airport = first_segment.get('arrival', {}).get('iataCode', '')
            departure_date = first_segment.get('departure', {}).get('at', '')[:10]
            
            booking_links = self._create_booking_links(departure_airport, arrival_airport, departure_date)
            
            return {
                'id': flight.get('id', ''),
                'price': float(price) if price else 0,
                'currency': flight.get('price', {}).get('currency', 'EUR'),
                'airline': first_segment.get('carrierCode', ''),
                'flight_number': f"{first_segment.get('carrierCode', '')}{first_segment.get('number', '')}",
                'departure_airport': departure_airport,
                'arrival_airport': arrival_airport,
                'departure_time': first_segment.get('departure', {}).get('at', ''),
                'arrival_time': first_segment.get('arrival', {}).get('at', ''),
                'duration_hours': duration_hours,
                'stops': stops,
                'return_flight': bool(inbound),
                'booking_links': booking_links,
                'airline_logo': f"https://images.kiwi.com/airlines/64/{first_segment.get('carrierCode', '')}.png"
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Parsen der Flugdaten: {e}")
            return None
    
    def _create_booking_links(self, origin: str, destination: str, date: str) -> Dict[str, str]:

        try:
            links = {
                'Google Flights': f"https://www.google.com/travel/flights?hl=de&tfs={origin}_{destination}_{date}"
            }
            
            return links
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Buchungslinks: {e}")
            return {}
    
    def _parse_duration(self, duration: str) -> float:

        try:

            hours = 0
            minutes = 0
            
            if 'H' in duration:
                hours = int(duration.split('H')[0].replace('PT', ''))
            if 'M' in duration:
                minutes_part = duration.split('H')[1] if 'H' in duration else duration.replace('PT', '')
                minutes = int(minutes_part.replace('M', ''))
            
            return hours + (minutes / 60)
        except:
            return 1.5  
    
    def _format_date(self, date_str: str) -> str:

        try:

            for fmt in ['%d.%m.%Y', '%d.%m', '%Y-%m-%d', '%d/%m/%Y']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    if fmt == '%d.%m':
                        dt = dt.replace(year=datetime.now().year)
                    

                    if dt < datetime.now():

                        dt = dt.replace(year=dt.year + 1)
                    
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            

            return (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            
        except Exception as e:
            logger.error(f"Fehler beim Datumsformat: {e}")
            return (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    def get_flight_summary(self, flights: List[Dict[str, Any]]) -> str:

        if not flights:
            return "Keine Flüge gefunden."
        

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
            'JU': 'Air Serbia',
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
            'WS': 'WestJet'
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