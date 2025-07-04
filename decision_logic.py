import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class TravelGuideDecisionLogic:
    def __init__(self, hotel_service, weather_service, rasa_handler):
        self.hotel_service = hotel_service
        self.weather_service = weather_service
        self.rasa_handler = rasa_handler
        self.user_sessions = {}
        self.dialog_states = {
            'greeting': 'greeting',
            'collecting_preferences': 'collecting_preferences',
            'searching_options': 'searching_options',
            'presenting_results': 'presenting_results',
            'finalizing_plan': 'finalizing_plan'
        }
    
    def process_user_message(self, message: str, user_id: str) -> Dict[str, Any]:
        try:
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = self._initialize_user_session()
            
            session = self.user_sessions[user_id]
            
            rasa_response = self.rasa_handler.process_message(message, user_id)
            intent = rasa_response.get('intent', 'unknown')
            confidence = rasa_response.get('confidence', 0.0)
            entities = rasa_response.get('entities', {})
            
            logger.info(f"Intent erkannt: {intent} (Confidence: {confidence})")
            logger.info(f"Entitäten extrahiert: {entities}")
            
            self._update_session_with_entities(session, entities)
            
            current_state = session['state']
            progress = self._check_conversation_progress(session)
            
            if intent == 'greet':
                return self._handle_greeting(user_id)
            
            elif intent == 'new_trip':
                return self.reset_user_session(user_id)
            
            elif intent == 'continue_trip':
                return self._handle_continue_trip(user_id)
            
            elif intent == 'reset_session':
                return self.reset_user_session(user_id)
            
            elif intent == 'get_weather':
                return self._handle_weather_request(user_id, entities, message)
            
            elif intent == 'provide_destination':
                if session['preferences'].get('destination') and not self._is_new_destination(entities, session):
                    return self._handle_already_known_info('destination', session['preferences']['destination'], user_id)
                return self._handle_destination_provided(message, user_id, entities)
            
            elif intent == 'provide_dates':
                if session['preferences'].get('start_date') and session['preferences'].get('end_date'):
                    return self._handle_already_known_info('dates', f"{session['preferences']['start_date']} bis {session['preferences']['end_date']}", user_id)
                return self._handle_dates_provided(message, user_id, entities)
            
            elif intent == 'provide_preferences':
                return self._handle_preferences_provided(message, user_id)
            
            elif intent == 'search_hotels':
                return self._handle_hotel_search_request(user_id, entities)
            
            elif intent == 'create_plan':
                return self._handle_plan_creation(user_id)
            
            elif intent == 'goodbye':
                return self._handle_goodbye(user_id)
            
            elif intent == 'unknown':
                if len(message.strip().split()) == 1 and message.strip().isalpha():
                    return self._handle_destination_provided(message, user_id, {'destination': message.strip()})
                else:
                    return self._handle_general_question(message, user_id)
            
            else:
                return self._handle_general_question(message, user_id)
                
        except Exception as e:
            logger.error(f"Fehler bei der Nachrichtenverarbeitung: {e}")
            return {
                'type': 'error',
                'message': 'Entschuldigung, es gab einen Fehler bei der Verarbeitung Ihrer Anfrage.',
                'suggestions': ['Versuchen Sie es erneut', 'Formulieren Sie Ihre Anfrage anders']
            }
    
    def _check_conversation_progress(self, session: Dict[str, Any]) -> Dict[str, Any]:
        prefs = session['preferences']
        progress = {
            'destination': bool(prefs.get('destination')),
            'dates': bool(prefs.get('start_date') and prefs.get('end_date')),
            'complete': False
        }
        
        # Nur Destination ist erforderlich für Hotel-Suche
        if progress['destination']:
            progress['complete'] = True
            session['state'] = self.dialog_states['searching_options']
        
        return progress
    
    def _clean_destination(self, destination: str) -> str:
        if not destination:
            return destination
        
        unwanted_words = ['suchen', 'finden', 'reisen', 'nach', 'zu']
        
        cleaned = destination
        for word in unwanted_words:
            cleaned = cleaned.replace(f' {word}', '').replace(f'{word} ', '')
        
        for word in unwanted_words:
            cleaned = re.sub(rf'^{word}$', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(rf'^{word}\s+', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(rf'\s+{word}$', '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    def _is_new_destination(self, entities: Dict[str, Any], session: Dict[str, Any]) -> bool:
        new_destination = self._clean_destination(entities.get('destination', ''))
        current_destination = session['preferences'].get('destination', '')
        return new_destination.lower() != current_destination.lower()
    
    def _handle_already_known_info(self, info_type: str, current_value: Any, user_id: str) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        progress = self._check_conversation_progress(session)
        
        messages = {
            'destination': f'Ihr Reiseziel ist bereits {current_value}.',
            'dates': f'Ihre Reisedaten sind bereits {current_value}.'
        }
        
        if progress['complete']:
            # Automatisch nach Hotels suchen, wenn alle Informationen vorhanden sind
            return self._handle_hotel_search_request(user_id, {})
        else:
            if not progress['destination']:
                return {
                    'type': 'info_partial',
                    'message': f"{messages[info_type]} Noch benötigt: Reiseziel",
                    'suggestions': [
                        'Hotels in Paris finden',
                        'Hotels in London finden',
                        'Hotels in Rom finden',
                        'Hotels in Amsterdam finden',
                        'Alles zurücksetzen'
                    ]
                }
            elif not progress['destination']:
                return {
                    'type': 'info_partial',
                    'message': f"{messages[info_type]} Noch benötigt: Reiseziel",
                    'suggestions': [
                        'Hotels in Paris finden',
                        'Hotels in London finden',
                        'Hotels in Rom finden',
                        'Hotels in Amsterdam finden',
                        'Alles zurücksetzen'
                    ]
                }
    
    def _get_next_questions(self, progress: Dict[str, Any]) -> List[str]:
        suggestions = []
        
        if not progress['destination']:
            suggestions.append('Wo möchten Sie hinreisen?')
        elif not progress['duration']:
            suggestions.append('Was ist Ihre Reisedauer?')
        
        return suggestions
    
    def _update_session_with_entities(self, session: Dict[str, Any], entities: Dict[str, Any]):
        if 'destination' in entities:
            session['preferences']['destination'] = self._clean_destination(entities['destination'])
        if 'start_date' in entities:
            session['preferences']['start_date'] = entities['start_date']
        if 'end_date' in entities:
            session['preferences']['end_date'] = entities['end_date']
        if 'duration' in entities:
            session['preferences']['duration'] = entities['duration']
    
    def _initialize_user_session(self) -> Dict[str, Any]:
        return {
            'state': self.dialog_states['greeting'],
            'preferences': {
                'destination': None,
                'start_date': None,
                'end_date': None,
                'duration': None,
                'travelers': 1,
                'accommodation_type': 'hotel',
                'activities': [],
                'dietary_restrictions': [],
                'accessibility_needs': []
            },
            'search_results': {
                'hotels': [],
                'weather': None
            },
            'conversation_history': [],
            'created_at': datetime.now()
        }
    
    def _handle_greeting(self, user_id: str) -> Dict[str, Any]:
        return {
            'type': 'greeting',
            'message': 'Hallo! Ich bin Ihr TravelGuide. Wie kann ich Ihnen helfen?',
            'suggestions': [
                'Wie ist das Wetter in Wien?',
                'Hotels in Barcelona finden',
                'Hotels in Kopenhagen finden',
                'Wetter in London abfragen',
                'Unterkunft in Stockholm suchen'
            ]
        }
    
    def reset_user_session(self, user_id: str) -> Dict[str, Any]:
        self.user_sessions[user_id] = self._initialize_user_session()
        
        return {
            'type': 'session_reset',
            'message': 'Perfekt! Lassen Sie uns eine neue Reise planen! \n\nIch helfe Ihnen gerne bei der Reiseplanung! Hier sind einige Möglichkeiten:',
            'suggestions': [
                'Wie ist das Wetter in Wien?',
                'Hotels in Barcelona finden',
                'Hotels in Kopenhagen finden',
                'Wetter in London abfragen',
                'Unterkunft in Stockholm suchen'
            ]
        }
    
    def _handle_continue_trip(self, user_id: str) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        progress = self._check_conversation_progress(session)
        
        if progress['complete']:
            # Automatisch nach Hotels suchen, wenn alle Informationen vorhanden sind
            return self._handle_hotel_search_request(user_id, {})
        else:
            if not progress['destination']:
                return {
                    'type': 'continue_partial',
                    'message': 'Lassen Sie uns Ihre Reiseplanung vervollständigen! Wo möchten Sie hinreisen?',
                    'suggestions': [
                        'Hotels in Paris finden',
                        'Hotels in London finden',
                        'Hotels in Amsterdam finden',
                        'Hotels in Rom finden',
                        'Wetter in Barcelona',
                        'Alles zurücksetzen'
                    ]
                }
            else:
                # Wenn Destination vorhanden ist, automatisch nach Hotels suchen
                return self._handle_hotel_search_request(user_id, {})
    
    def _handle_destination_provided(self, message: str, user_id: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        
        destination = entities.get('destination')
        if destination:
            destination = self._clean_destination(destination)
            session['preferences']['destination'] = destination
            
            # Automatisch nach Hotels suchen
            return self._handle_hotel_search_request(user_id, {})
        else:
            return {
                'type': 'clarification_needed',
                'message': 'Bitte geben Sie Ihr Reiseziel an.',
                'suggestions': [
                    'Paris',
                    'London', 
                    'Rom',
                    'Amsterdam',
                    'Barcelona',
                    'Prag'
                ]
            }
    
    def _handle_dates_provided(self, message: str, user_id: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        
        start_date = entities.get('start_date')
        end_date = entities.get('end_date')
        
        if start_date and end_date:
            session['preferences']['start_date'] = start_date
            session['preferences']['end_date'] = end_date
            
            progress = self._check_conversation_progress(session)
            
            if progress['complete']:
                return {
                    'type': 'dates_confirmed_complete',
                    'message': f'Verstanden! Reisezeitraum: {start_date} bis {end_date} 📅 Alle Informationen sind vollständig!',
                    'start_date': start_date,
                    'end_date': end_date,
                    'suggestions': [
                        'Hotels suchen',
                        'Wetter abfragen',
                        'Alles zurücksetzen'
                    ]
                }
            else:
                return {
                    'type': 'dates_confirmed',
                    'message': f'Verstanden! Reisezeitraum: {start_date} bis {end_date} \nWas ist Ihre Reisedauer?',
                    'start_date': start_date,
                    'end_date': end_date,
                    'suggestions': [
                        '5 Tage',
                        '1 Woche',
                        '10 Tage'
                    ]
                }
        else:
            return {
                'type': 'clarification_needed',
                'message': 'Bitte geben Sie Ihren Reisezeitraum an:',
                'suggestions': [
                    '15.07.2024 bis 22.07.2024',
                    '01.08.2024 bis 08.08.2024',
                    '23.12.2024 bis 30.12.2024',
                    'Nächsten Monat',
                    'In 3 Monaten'
                ]
            }
    
    def _handle_duration_provided(self, message: str, user_id: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        
        duration = entities.get('duration')
        
        if duration:
            session['preferences']['duration'] = duration
            
            progress = self._check_conversation_progress(session)
            
            if progress['complete']:
                return {
                    'type': 'duration_confirmed_complete',
                    'message': f'Verstanden! Reisedauer: {duration} Tage Alle Informationen sind vollständig!',
                    'duration': duration,
                    'suggestions': [
                        'Hotels suchen',
                        'Wetter abfragen',
                        'Alles zurücksetzen'
                    ]
                }
            else:
                return {
                    'type': 'duration_confirmed',
                    'message': f'Verstanden! Reisedauer: {duration} Tage',
                    'duration': duration,
                    'suggestions': self._get_next_questions(progress)
                }
        else:
            return {
                'type': 'clarification_needed',
                'message': 'Bitte geben Sie Ihre Reisedauer an:',
                'suggestions': ['5 Tage', '1 Woche', '10 Tage']
            }
    
    def _handle_preferences_provided(self, message: str, user_id: str) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        
        return {
            'type': 'preferences_updated',
            'message': 'Danke für die Informationen! Ich kann Ihnen jetzt bei der Reiseplanung helfen.',
            'suggestions': [
                'Hotels suchen',
                'Wetter abfragen',
                'Alles zurücksetzen'
            ]
        }
    
    def _handle_hotel_search_request(self, user_id: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        prefs = session['preferences']
        
        hotel_location = entities.get('hotel_location')
        if hotel_location:
            prefs['destination'] = hotel_location
            session['preferences'] = prefs
        
        if not prefs.get('destination'):
            return {
                'type': 'missing_info',
                'message': 'Bitte geben Sie zuerst Ihr Reiseziel an.',
                'suggestions': [
                    'Hotels in Paris',
                    'Unterkunft in London',
                    'Hotel in Rom',
                    'Hotels in Amsterdam',
                    'Unterkunft in Barcelona'
                ]
            }
        
        try:
            location = prefs.get('destination')
            check_in = prefs.get('start_date')
            check_out = prefs.get('end_date')
            guests = prefs.get('travelers', 1)
            
            # Wenn keine Daten angegeben sind, verwende aktuelles Datum
            if not check_in or not check_out:
                today = datetime.now()
                check_in = today.strftime("%Y-%m-%d")
                check_out = (today + timedelta(days=7)).strftime("%Y-%m-%d")
            
            hotels = self.hotel_service.search_hotels(
                location=location,
                check_in=check_in,
                check_out=check_out,
                guests=guests
            )
            
            session['search_results']['hotels'] = hotels
            
            hotel_summary = self.hotel_service.get_hotel_summary(hotels, location, check_in, check_out, guests)
            
            return {
                'type': 'hotel_results',
                'message': hotel_summary,
                'hotels': hotels,
                'suggestions': [
                    'Alles zurücksetzen'
                ]
            }
            
        except Exception as e:
            logger.error(f"Fehler bei der Hotelsuche: {e}")
            return {
                'type': 'error',
                'message': 'Entschuldigung, bei der Hotelsuche ist ein Fehler aufgetreten.',
                'suggestions': ['Versuchen Sie es später erneut', 'Alles zurücksetzen']
            }
    
    def _handle_plan_creation(self, user_id: str) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        prefs = session['preferences']
        results = session['search_results']
        
        if not prefs.get('destination'):
            return {
                'type': 'missing_info',
                'message': 'Bitte geben Sie zuerst Ihr Reiseziel an.',
                'suggestions': ['Wo möchten Sie hinreisen?', 'Alles zurücksetzen']
            }
        
        try:
            destination = prefs.get('destination', 'Ihr Reiseziel')
            start_date = prefs.get('start_date', 'Startdatum')
            end_date = prefs.get('end_date', 'Enddatum')
            travelers = prefs.get('travelers', 1)
            
            hotels_count = len(results.get('hotels', []))
            weather_info = results.get('weather', {})
            
            plan = f"""
🌍 Reiseplan für {destination}

Reisezeitraum: {start_date} bis {end_date}
Reisende: {travelers} Person(en)

Verfügbare Optionen:
• Hotels: {hotels_count} verfügbar
• Wetter: {weather_info.get('description', 'Informationen verfügbar')}

Empfohlene Aktivitäten:
• Sehenswürdigkeiten erkunden
• Lokale Küche probieren
• Stadtführungen buchen
• Museen und Kultur besuchen

Restaurant-Tipps:
• Lokale Restaurants bevorzugen
• Bewertungen prüfen
• Reservierungen für beliebte Orte

Praktische Tipps:
• Öffentliche Verkehrsmittel nutzen
• Wettervorhersage prüfen
• Notfallnummern notieren
• Reiseversicherung abschließen

Budget-Tipps:
• Frühzeitig buchen
• Nebensaison wählen
• Günstige Unterkünfte suchen
• Lokale Angebote nutzen
"""
            
            return {
                'type': 'trip_plan',
                'message': plan,
                'suggestions': [
                    'Hotels suchen',
                    'Wetter abfragen',
                    'Alles zurücksetzen'
                ]
            }
            
        except Exception as e:
            logger.error(f"Fehler bei Reiseplan-Erstellung: {e}")
            return {
                'type': 'error',
                'message': 'Entschuldigung, bei der Reiseplan-Erstellung ist ein Fehler aufgetreten.',
                'suggestions': ['Versuchen Sie es später erneut']
            }
    
    def _extract_location_from_message(self, message: str) -> Optional[str]:
        """Extrahiert einen Ort aus der Nachricht"""
        # Liste bekannter Städte
        cities = [
            'berlin', 'hamburg', 'münchen', 'köln', 'frankfurt', 'stuttgart', 'düsseldorf', 'dortmund', 'essen', 'leipzig',
            'bremen', 'dresden', 'hannover', 'nürnberg', 'duisburg', 'bochum', 'wuppertal', 'bielefeld', 'bonn', 'mannheim',
            'karlsruhe', 'augsburg', 'wiesbaden', 'gelsenkirchen', 'münster', 'aachen', 'braunschweig', 'chemnitz', 'kiel',
            'halle', 'magdeburg', 'freiburg', 'krefeld', 'lübeck', 'oberhausen', 'erfurt', 'mainz', 'rostock', 'kassel',
            'potsdam', 'hagen', 'hamm', 'saarbrücken', 'mülheim', 'ludwigshafen', 'leverkusen', 'oldenburg', 'osnabrück',
            'solingen', 'herne', 'neuss', 'heidelberg', 'darmstadt', 'paderborn', 'regensburg', 'ingolstadt', 'würzburg',
            'fürth', 'wolfsburg', 'offenbach', 'ulm', 'heilbronn', 'pforzheim', 'göttingen', 'bottrop', 'trier', 'reutlingen',
            'bremerhaven', 'koblenz', 'bergisch gladbach', 'jena', 'erlangen', 'moers', 'siegen', 'hildesheim', 'salzgitter',
            'cottbus', 'kaiserslautern', 'gütersloh', 'schwerin', 'düren', 'essen', 'ratingen', 'tübingen', 'lünen',
            'villingen-schwenningen', 'konstanz', 'flensburg', 'ludwigsburg', 'minden', 'velbert', 'neuwied', 'delmenhorst',
            'brandenburg', 'wilhelmshaven', 'bamberg', 'celle', 'landshut', 'aschaffenburg', 'rheine', 'rosenheim',
            'sindelfingen', 'kempten', 'zwickau', 'aalen', 'bocholt', 'bayreuth', 'coburg', 'detmold', 'dinslaken',
            'euskirchen', 'frechen', 'goch', 'gummersbach', 'hagen', 'hamm', 'hattingen', 'heidenheim', 'herford',
            'herne', 'hilden', 'hürth', 'ibbenbüren', 'iserlohn', 'kamen', 'kerpen', 'kleve', 'königswinter',
            'krefeld', 'langenfeld', 'leer', 'leinfelden-echterdingen', 'lengerich', 'lingen', 'lüdenscheid',
            'lüneburg', 'marl', 'meerbusch', 'menden', 'minden', 'moers', 'mönchengladbach', 'mülheim', 'neuss',
            'oberhausen', 'offenbach', 'oldenburg', 'osnabrück', 'paderborn', 'pforzheim', 'potsdam', 'ratingen',
            'recklinghausen', 'regensburg', 'rheine', 'rheinfelden', 'rheinbach', 'rheinberg', 'rheine', 'rheinfelden',
            'rheinbach', 'rheinberg', 'rheine', 'rheinfelden', 'rheinbach', 'rheinberg', 'rheine', 'rheinfelden',
            'paris', 'london', 'rom', 'madrid', 'barcelona', 'amsterdam', 'berlin', 'wien', 'prag', 'budapest',
            'stockholm', 'kopenhagen', 'oslo', 'helsinki', 'warschau', 'athen', 'istanbul', 'dubai', 'tokio',
            'singapur', 'bangkok', 'sydney', 'melbourne', 'new york', 'los angeles', 'chicago', 'miami', 'toronto',
            'montreal', 'vancouver', 'mexiko', 'rio de janeiro', 'sao paulo', 'buenos aires', 'santiago', 'lima',
            'bogota', 'caracas', 'havanna', 'kingston', 'port-au-prince', 'santo domingo', 'san juan', 'bridgetown',
            'port of spain', 'georgetown', 'paramaribo', 'cayenne', 'fortaleza', 'recife', 'salvador', 'belo horizonte',
            'brasilia', 'curitiba', 'porto alegre', 'montevideo', 'asuncion', 'la paz', 'sucre', 'lima', 'quito',
            'guayaquil', 'bogota', 'medellin', 'cali', 'caracas', 'maracaibo', 'valencia', 'barquisimeto',
            'maracay', 'ciudad guayana', 'maturin', 'barcelona', 'puerto la cruz', 'petare', 'baruta', 'chacao',
            'catia la mar', 'guarenas', 'guatire', 'los teques', 'petare', 'baruta', 'chacao', 'catia la mar',
            'guarenas', 'guatire', 'los teques', 'petare', 'baruta', 'chacao', 'catia la mar', 'guarenas',
            'guatire', 'los teques', 'petare', 'baruta', 'chacao', 'catia la mar', 'guarenas', 'guatire',
            'los teques', 'petare', 'baruta', 'chacao', 'catia la mar', 'guarenas', 'guatire', 'los teques'
        ]
        
        message_lower = message.lower()
        
        # Suche nach Städtenamen in der Nachricht
        for city in cities:
            if city in message_lower:
                return city.title()
        
        return None

    def _handle_general_question(self, message: str, user_id: str) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        
        message_lower = message.lower()
        
        if 'wetter' in message_lower or 'klima' in message_lower:
            # Versuche einen Ort aus der Nachricht zu extrahieren
            location = self._extract_location_from_message(message)
            if location:
                # Automatisch Wetter abrufen
                return self._handle_weather_request(user_id, {'weather_location': location}, message)
            else:
                return {
                    'type': 'missing_info',
                    'message': 'Für Wetterinformationen können Sie fragen: "Wie ist das Wetter in [Ort]?"',
                    'suggestions': ['Wie ist das Wetter in Berlin?', 'Wetter in München', 'Temperatur in Hamburg']
                }
        
        elif 'hotel' in message_lower or 'unterkunft' in message_lower:
            # Versuche einen Ort aus der Nachricht zu extrahieren
            location = self._extract_location_from_message(message)
            if location:
                # Automatisch nach Hotels suchen
                session['preferences']['destination'] = location
                return self._handle_hotel_search_request(user_id, {})
            else:
                return {
                    'type': 'missing_info',
                    'message': 'Für Hotelsuche können Sie fragen: "Hotels in [Ort] finden"',
                    'suggestions': ['Hotels in Berlin finden', 'Hotels in München finden', 'Hotels in Hamburg finden']
                }
        
        else:
            return {
                'type': 'general',
                'message': 'Ich helfe Ihnen gerne bei der Reiseplanung! Hier sind einige Möglichkeiten:',
                'suggestions': [
                'Wie ist das Wetter in Wien?',
                'Hotels in Barcelona finden',
                'Hotels in Kopenhagen finden',
                'Wetter in London abfragen',
                'Unterkunft in Stockholm suchen'
                ]
            }
    
    def _handle_weather_request(self, user_id: str, entities: Dict[str, Any], original_message: str = "") -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        
        weather_location = entities.get('weather_location')
        
        # Wenn keine Location in den Entitäten, versuche sie aus der Nachricht zu extrahieren
        if not weather_location and original_message:
            weather_location = self._extract_location_from_message(original_message)
        
        if not weather_location:
            return {
                'type': 'missing_info',
                'message': 'Bitte geben Sie einen Ort für die Wetterabfrage an.',
                'suggestions': [
                    'Wie ist das Wetter in Berlin?',
                    'Wetter in München',
                    'Temperatur in Hamburg',
                    'Klima in Wien'
                ]
            }
        
        try:
            weather_data = self.weather_service.get_weather(weather_location)
            
            if weather_data:
                session['search_results']['weather'] = weather_data
                
                # Verwende die get_weather_summary Methode für eine formatierte Nachricht
                weather_message = self.weather_service.get_weather_summary(weather_location)
                
                return {
                    'type': 'weather_results',
                    'message': weather_message,
                    'suggestions': [
                        'Hotels in ' + weather_location.title() + ' finden',
                        'Alles zurücksetzen'
                    ]
                }
            else:
                return {
                    'type': 'error',
                    'message': f'Entschuldigung, ich konnte keine Wetterinformationen für {weather_location} finden.',
                    'suggestions': [
                        'Versuchen Sie einen anderen Ort',
                        'Alles zurücksetzen'
                    ]
                }
                
        except Exception as e:
            logger.error(f"Fehler bei der Wetterabfrage: {e}")
            return {
                'type': 'error',
                'message': 'Entschuldigung, bei der Wetterabfrage ist ein Fehler aufgetreten.',
                'suggestions': ['Versuchen Sie es später erneut', 'Alles zurücksetzen']
            }

    def _handle_goodbye(self, user_id: str) -> Dict[str, Any]:
        return {
            'type': 'goodbye',
            'message': 'Vielen Dank für die Nutzung des TravelGuide! Ich wünsche Ihnen eine wundervolle Reise! 🌍',
            'suggestions': ['Neue Reise planen']
        } 