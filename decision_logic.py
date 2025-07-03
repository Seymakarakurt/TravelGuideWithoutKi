import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re
import random

logger = logging.getLogger(__name__)

class TravelGuideDecisionLogic:
    def __init__(self, flight_service, hotel_service, weather_service, rasa_handler):
        self.flight_service = flight_service
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
            
            # KI-gestützte Verhaltensanalyse
            self._analyze_user_behavior(session, message)
            
            # Füge Nachricht zur Konversationshistorie hinzu
            session['conversation_history'].append({
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'type': 'user'
            })
            
            rasa_response = self.rasa_handler.process_message(message, user_id)
            intent = rasa_response.get('intent', 'unknown')
            confidence = rasa_response.get('confidence', 0.0)
            entities = rasa_response.get('entities', {})
            
            logger.info(f"Intent erkannt: {intent} (Confidence: {confidence})")
            logger.info(f"Entitäten extrahiert: {entities}")
            
            self._update_session_with_entities(session, entities)
            
            current_state = session['state']
            progress = self._check_conversation_progress(session)
            
            # Intelligente Intent-Verarbeitung mit KI-gestützter Entscheidungslogik
            if intent == 'greet':
                response = self._handle_greeting(user_id)
            elif intent == 'new_trip':
                response = self.reset_user_session(user_id)
            elif intent == 'continue_trip':
                response = self._handle_continue_trip(user_id)
            elif intent == 'reset_session':
                response = self.reset_user_session(user_id)
            elif intent == 'goodbye':
                response = self._handle_goodbye(user_id)
            elif intent == 'unknown':
                if len(message.strip().split()) == 1 and message.strip().isalpha():
                    response = self._handle_destination_provided(message, user_id, {'destination': message.strip()})
                else:
                    response = self._handle_general_question(message, user_id)
            else:
                response = self._get_response_for_intent(intent, user_id, entities, message)
            
            # KI-gestützte Antwort zur Konversationshistorie hinzufügen
            response = self._get_response_for_intent(intent, user_id, entities, message)
            session['conversation_history'].append({
                'message': response.get('message', ''),
                'timestamp': datetime.now().isoformat(),
                'type': 'assistant',
                'intent': intent
            })
            
            return response
                
        except Exception as e:
            logger.error(f"Fehler bei der Nachrichtenverarbeitung: {e}")
            return {
                'type': 'error',
                'message': 'Entschuldigung, es gab einen Fehler bei der Verarbeitung Ihrer Anfrage.',
                'suggestions': ['Versuchen Sie es erneut', 'Formulieren Sie Ihre Anfrage anders']
            }
    
    def _get_response_for_intent(self, intent: str, user_id: str, entities: Dict[str, Any], message: str) -> Dict[str, Any]:
        """Intelligente Entscheidungslogik für Intent-Verarbeitung"""
        session = self.user_sessions[user_id]
        ai_profile = session['ai_profile']
        
        # Intelligente Routing-Logik basierend auf KI-Profil
        if intent == 'search_hotels':
            return self._handle_hotel_search_request(user_id, entities)
        
        elif intent == 'search_flights':
            return self._handle_flight_search_request(user_id, entities)
        
        elif intent == 'get_weather':
            return self._handle_weather_request(user_id, entities, message)
        
        elif intent == 'provide_destination':
            # Intelligente Weiterleitung basierend auf Benutzerverhalten
            if session['preferences'].get('destination') and not self._is_new_destination(entities, session):
                return self._handle_already_known_info('destination', session['preferences']['destination'], user_id)
            return self._handle_destination_provided(message, user_id, entities)
        
        elif intent == 'provide_dates':
            if session['preferences'].get('start_date') and session['preferences'].get('end_date'):
                return self._handle_already_known_info('dates', f"{session['preferences']['start_date']} bis {session['preferences']['end_date']}", user_id)
            return self._handle_dates_provided(message, user_id, entities)
        
        elif intent == 'provide_preferences':
            return self._handle_preferences_provided(message, user_id)
        
        elif intent == 'create_plan':
            # Prüfe ob genug Informationen für Reiseplan vorhanden sind
            progress = self._check_conversation_progress(session)
            if progress['complete']:
                return self._handle_plan_creation(user_id)
            else:
                # Intelligente Nachfrage basierend auf fehlenden Informationen
                return self._handle_incomplete_plan_request(user_id)
        
        else:
            return self._handle_general_question(message, user_id)
    
    def _handle_incomplete_plan_request(self, user_id: str) -> Dict[str, Any]:
        """Behandelt unvollständige Reiseplan-Anfragen intelligent"""
        session = self.user_sessions[user_id]
        ai_profile = session['ai_profile']
        preferences = session['preferences']
        
        missing_info = []
        if not preferences.get('destination'):
            missing_info.append('Reiseziel')
        if not preferences.get('start_date'):
            missing_info.append('Reisedaten')
        
        # Personalisierte Nachricht basierend auf Benutzerprofil
        if ai_profile['interaction_pattern'] == 'detailed':
            message = f"Um einen vollständigen Reiseplan zu erstellen, benötige ich noch: {', '.join(missing_info)}. "
            message += "Möchten Sie diese Informationen jetzt angeben?"
        else:
            message = f"Noch benötigt: {', '.join(missing_info)}"
        
        # Intelligente Vorschläge basierend auf fehlenden Informationen
        suggestions = []
        if 'Reiseziel' in missing_info:
            if ai_profile['travel_style'] == 'budget':
                suggestions.extend(['Günstige Hotels in Prag', 'Budget-Reise nach Budapest'])
            elif ai_profile['travel_style'] == 'luxury':
                suggestions.extend(['Luxus-Hotels in Paris', 'Premium-Reise nach London'])
            else:
                suggestions.extend(['Hotels in Paris', 'Flüge nach Rom'])
        
        if 'Reisedaten' in missing_info:
            suggestions.extend(['15.07.2024 bis 22.07.2024', 'Nächsten Monat'])
        
        suggestions.append('Alles zurücksetzen')
        
        return {
            'type': 'incomplete_plan',
            'message': message,
            'suggestions': suggestions
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
        
        # KI-gestützte Profilaktualisierung
        self._update_ai_profile(session, entities)
    
    def _update_ai_profile(self, session: Dict[str, Any], entities: Dict[str, Any]):
        """Aktualisiert das KI-Profil basierend auf Benutzerinteraktionen"""
        ai_profile = session['ai_profile']
        
        # Aktualisiere Suchhistorie
        if 'destination' in entities:
            destination = self._clean_destination(entities['destination'])
            if destination not in ai_profile['last_searches']:
                ai_profile['last_searches'].append(destination)
                if len(ai_profile['last_searches']) > 5:
                    ai_profile['last_searches'].pop(0)
        
        # Erkenne Reiseerfahrung basierend auf Interaktionen
        interaction_count = len(session['conversation_history'])
        if interaction_count > 10:
            ai_profile['travel_experience'] = 'expert'
        elif interaction_count > 5:
            ai_profile['travel_experience'] = 'intermediate'
        
        # Erkenne Budget-Präferenzen basierend auf Suchverhalten
        if 'budget' in entities:
            budget = entities['budget']
            if budget < 100:
                ai_profile['budget_range'] = 'low'
            elif budget < 500:
                ai_profile['budget_range'] = 'medium'
            else:
                ai_profile['budget_range'] = 'high'
    
    def _analyze_user_behavior(self, session: Dict[str, Any], message: str) -> Dict[str, Any]:
        """Analysiert Benutzerverhalten für personalisierte Empfehlungen"""
        ai_profile = session['ai_profile']
        
        # Analysiere Nachrichtenlänge für Interaktionsmuster
        message_length = len(message.split())
        if message_length > 20:
            ai_profile['interaction_pattern'] = 'detailed'
        elif message_length > 10:
            ai_profile['interaction_pattern'] = 'exploratory'
        else:
            ai_profile['interaction_pattern'] = 'direct'
        
        # Erkenne Reiseart basierend auf Schlüsselwörtern
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['günstig', 'billig', 'budget', 'sparen']):
            ai_profile['travel_style'] = 'budget'
        elif any(word in message_lower for word in ['luxus', 'teuer', 'premium', '5 sterne']):
            ai_profile['travel_style'] = 'luxury'
        elif any(word in message_lower for word in ['abenteuer', 'wanderung', 'aktiv']):
            ai_profile['travel_style'] = 'adventure'
        elif any(word in message_lower for word in ['kultur', 'museum', 'geschichte']):
            ai_profile['travel_style'] = 'culture'
        elif any(word in message_lower for word in ['entspannung', 'wellness', 'ruhig']):
            ai_profile['travel_style'] = 'relaxation'
        
        # Erkenne Gruppentyp
        if any(word in message_lower for word in ['familie', 'kinder', 'kind']):
            ai_profile['group_type'] = 'family'
        elif any(word in message_lower for word in ['paar', 'zusammen', 'romantisch']):
            ai_profile['group_type'] = 'couple'
        elif any(word in message_lower for word in ['geschäft', 'business', 'arbeit']):
            ai_profile['group_type'] = 'business'
        
        return ai_profile
    
    def _generate_personalized_suggestions(self, session: Dict[str, Any], context: str = 'general') -> List[str]:
        """Generiert personalisierte Vorschläge basierend auf KI-Profil"""
        ai_profile = session['ai_profile']
        preferences = session['preferences']
        
        suggestions = []
        
        # Basis-Vorschläge je nach Kontext
        if context == 'greeting':
            if ai_profile['travel_style'] == 'budget':
                suggestions = [
                    'Günstige Hotels in Barcelona',
                    'Flüge nach Prag (günstig)',
                    'Budget-Hotels in Amsterdam'
                ]
            elif ai_profile['travel_style'] == 'luxury':
                suggestions = [
                    'Luxus-Hotels in Paris',
                    'Premium Flüge nach London',
                    '5-Sterne Hotels in Rom'
                ]
            elif ai_profile['travel_style'] == 'adventure':
                suggestions = [
                    'Aktivitäten in den Alpen',
                    'Wanderungen in Norwegen',
                    'Abenteuer in Island'
                ]
            elif ai_profile['travel_style'] == 'culture':
                suggestions = [
                    'Museen in Florenz',
                    'Kultur in Wien',
                    'Geschichte in Athen'
                ]
            else:
                # Standard-Vorschläge
                suggestions = [
                    'Hotels in Barcelona finden',
                    'Flüge nach Paris',
                    'Wetter in London abfragen'
                ]
        
        elif context == 'destination':
            # Personalisierte Ziele basierend auf Suchhistorie
            if ai_profile['last_searches']:
                last_destinations = ai_profile['last_searches'][-2:]
                for dest in last_destinations:
                    suggestions.append(f'Weitere Hotels in {dest.title()}')
                    suggestions.append(f'Flüge nach {dest.title()}')
            
            # Empfehlungen basierend auf Reiseart
            if ai_profile['travel_style'] == 'budget':
                budget_destinations = ['Prag', 'Budapest', 'Krakau', 'Lissabon', 'Porto']
                suggestions.extend([f'Günstige Hotels in {dest}' for dest in budget_destinations[:2]])
            elif ai_profile['travel_style'] == 'luxury':
                luxury_destinations = ['Paris', 'London', 'Rom', 'Venedig', 'Florenz']
                suggestions.extend([f'Luxus-Hotels in {dest}' for dest in luxury_destinations[:2]])
        
        elif context == 'post_search':
            destination = preferences.get('destination', '')
            if destination:
                suggestions = [
                    f'Wetter in {destination.title()} abfragen',
                    f'Flüge nach {destination.title()}',
                    f'Weitere Hotels in {destination.title()}',
                    'Reiseplan erstellen'
                ]
        
        # Füge immer "Alles zurücksetzen" hinzu
        if 'Alles zurücksetzen' not in suggestions:
            suggestions.append('Alles zurücksetzen')
        
        return suggestions[:5]  # Maximal 5 Vorschläge
    
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
                'flights': [],
                'weather': None
            },
            'conversation_history': [],
            'ai_profile': {
                'travel_style': None,  # 'budget', 'luxury', 'adventure', 'culture', 'relaxation'
                'preferred_activities': [],
                'budget_range': None,  # 'low', 'medium', 'high'
                'travel_experience': 'beginner',  # 'beginner', 'intermediate', 'expert'
                'group_type': 'solo',  # 'solo', 'couple', 'family', 'business'
                'seasonal_preferences': [],
                'last_searches': [],
                'interaction_pattern': 'direct'  # 'direct', 'exploratory', 'detailed'
            },
            'created_at': datetime.now()
        }
    
    def _handle_greeting(self, user_id: str) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        
        # Personalisierte Begrüßung basierend auf KI-Profil
        ai_profile = session['ai_profile']
        message = 'Hallo! Ich bin Ihr TravelGuide. Wie kann ich Ihnen helfen?'
        
        # Personalisierte Begrüßung basierend auf Reiseerfahrung
        if ai_profile['travel_experience'] == 'expert':
            message = 'Willkommen zurück! Als erfahrener Reisender kann ich Ihnen bei der Planung helfen.'
        elif ai_profile['travel_experience'] == 'intermediate':
            message = 'Hallo! Ich helfe Ihnen gerne bei der Reiseplanung.'
        
        # Personalisierte Empfehlungen
        suggestions = self._generate_personalized_suggestions(session, 'greeting')
        
        return {
            'type': 'greeting',
            'message': message,
            'suggestions': suggestions
        }
    
    def reset_user_session(self, user_id: str) -> Dict[str, Any]:
        self.user_sessions[user_id] = self._initialize_user_session()
        
        return {
            'type': 'session_reset',
            'message': 'Perfekt! Lassen Sie uns eine neue Reise planen! \n\nIch helfe Ihnen gerne bei der Reiseplanung! Hier sind einige Möglichkeiten:',
            'suggestions': [
                'Wie ist das Wetter in Wien?',
                'Hotels in Barcelona finden',
                'Flüge nach Paris',
                'Wetter in London abfragen',
                'Flüge nach Rom'
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
                        'Flüge nach London',
                        'Hotels in Amsterdam finden',
                        'Flüge nach Rom',
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
                        'Flüge suchen',
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
                        'Flüge suchen',
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
                'Flüge suchen',
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
            
            # Personalisierte Empfehlungen nach Hotelsuche
            suggestions = self._generate_personalized_suggestions(session, 'post_search')
            
            return {
                'type': 'hotel_results',
                'message': hotel_summary,
                'hotels': hotels,
                'suggestions': suggestions
            }
            
        except Exception as e:
            logger.error(f"Fehler bei der Hotelsuche: {e}")
            return {
                'type': 'error',
                'message': 'Entschuldigung, bei der Hotelsuche ist ein Fehler aufgetreten.',
                'suggestions': ['Versuchen Sie es später erneut', 'Alles zurücksetzen']
            }
    
    def _handle_flight_search_request(self, user_id: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        prefs = session['preferences']
        
        flight_destination = entities.get('flight_destination')
        if flight_destination:
            prefs['destination'] = flight_destination
            session['preferences'] = prefs
        
        if not prefs.get('destination'):
            return {
                'type': 'missing_info',
                'message': 'Bitte geben Sie zuerst Ihr Reiseziel an.',
                'suggestions': [
                    'Flüge nach Paris',
                    'Flüge nach London',
                    'Flüge nach Rom',
                    'Flüge nach Amsterdam',
                    'Flüge nach Barcelona'
                ]
            }
        
        try:
            # Standard-Abflugort (kann später erweitert werden)
            origin = "Berlin"
            destination = prefs.get('destination')
            start_date = prefs.get('start_date')
            
            # Wenn kein Datum angegeben ist, verwende aktuelles Datum + 7 Tage
            if not start_date:
                start_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            
            flights = self.flight_service.search_flights(
                origin=origin,
                destination=destination,
                start_date=start_date
            )
            
            session['search_results']['flights'] = flights
            
            flight_summary = self.flight_service.get_flight_summary(flights, origin, destination, start_date)
            
            # Personalisierte Empfehlungen nach Flugsuche
            suggestions = self._generate_personalized_suggestions(session, 'post_search')
            
            return {
                'type': 'flight_results',
                'message': flight_summary,
                'flights': flights,
                'suggestions': suggestions
            }
            
        except Exception as e:
            logger.error(f"Fehler bei der Flugsuche: {e}")
            return {
                'type': 'error',
                'message': 'Entschuldigung, bei der Flugsuche ist ein Fehler aufgetreten.',
                'suggestions': ['Versuchen Sie es später erneut', 'Alles zurücksetzen']
            }
    
    def _handle_plan_creation(self, user_id: str) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        preferences = session['preferences']
        search_results = session['search_results']
        ai_profile = session['ai_profile']
        
        if not preferences.get('destination'):
            return {
                'type': 'error',
                'message': 'Bitte geben Sie zuerst ein Reiseziel an.',
                'suggestions': ['Hotels in Paris', 'Flüge nach Rom', 'Alles zurücksetzen']
            }
        
        destination = preferences['destination']
        
        # KI-gestützte Reiseplanung basierend auf Benutzerprofil
        plan = self._create_intelligent_travel_plan(session, destination)
        
        # Speichere den Plan in der Session
        session['current_plan'] = plan
        
        # Erstelle eine personalisierte Zusammenfassung
        summary = self._generate_personalized_plan_summary(plan, ai_profile)
        
        return {
            'type': 'plan_created',
            'message': summary,
            'plan': plan,
            'suggestions': self._generate_personalized_suggestions(session, 'post_search')
        }
    
    def _create_intelligent_travel_plan(self, session: Dict[str, Any], destination: str) -> Dict[str, Any]:
        """Erstellt einen intelligenten Reiseplan basierend auf KI-Profil"""
        preferences = session['preferences']
        search_results = session['search_results']
        ai_profile = session['ai_profile']
        
        plan = {
            'destination': destination,
            'created_at': datetime.now().isoformat(),
            'hotels': search_results.get('hotels', []),
            'flights': search_results.get('flights', []),
            'weather': search_results.get('weather'),
            'ai_recommendations': [],
            'personalized_activities': [],
            'budget_estimate': None
        }
        
        # KI-gestützte Aktivitätsempfehlungen basierend auf Reiseart
        if ai_profile['travel_style'] == 'culture':
            plan['personalized_activities'] = [
                f"Museen in {destination.title()} besuchen",
                f"Historische Sehenswürdigkeiten erkunden",
                f"Lokale Kulturveranstaltungen besuchen"
            ]
        elif ai_profile['travel_style'] == 'adventure':
            plan['personalized_activities'] = [
                f"Wanderungen in der Umgebung von {destination.title()}",
                f"Aktivitäten im Freien",
                f"Abenteuer-Touren buchen"
            ]
        elif ai_profile['travel_style'] == 'relaxation':
            plan['personalized_activities'] = [
                f"Wellness-Angebote in {destination.title()}",
                f"Entspannende Spaziergänge",
                f"Ruhige Cafés besuchen"
            ]
        elif ai_profile['travel_style'] == 'budget':
            plan['personalized_activities'] = [
                f"Kostenlose Sehenswürdigkeiten in {destination.title()}",
                f"Öffentliche Verkehrsmittel nutzen",
                f"Lokale Märkte besuchen"
            ]
        elif ai_profile['travel_style'] == 'luxury':
            plan['personalized_activities'] = [
                f"Premium-Restaurants in {destination.title()}",
                f"Exklusive Touren buchen",
                f"Luxus-Shopping-Erlebnisse"
            ]
        
        # Budget-Schätzung basierend auf Reiseart und Gruppentyp
        plan['budget_estimate'] = self._estimate_travel_budget(ai_profile, preferences)
        
        # KI-Empfehlungen basierend auf Suchhistorie
        if ai_profile['last_searches']:
            plan['ai_recommendations'].append(
                f"Basierend auf Ihren vorherigen Reisen nach {', '.join(ai_profile['last_searches'][-2:])}"
            )
        
        # Personalisierte Empfehlungen basierend auf Gruppentyp
        if ai_profile['group_type'] == 'family':
            plan['ai_recommendations'].append("Familienfreundliche Aktivitäten empfohlen")
        elif ai_profile['group_type'] == 'couple':
            plan['ai_recommendations'].append("Romantische Aktivitäten empfohlen")
        elif ai_profile['group_type'] == 'business':
            plan['ai_recommendations'].append("Business-freundliche Optionen empfohlen")
        
        return plan
    
    def _generate_personalized_plan_summary(self, plan: Dict[str, Any], ai_profile: Dict[str, Any]) -> str:
        """Generiert eine personalisierte Zusammenfassung des Reiseplans"""
        destination = plan['destination']
        summary_parts = [f"📋 Intelligenter Reiseplan für {destination.title()} erstellt!"]
        
        if plan['hotels']:
            summary_parts.append(f"🏨 {len(plan['hotels'])} Hotels gefunden")
        if plan['flights']:
            summary_parts.append(f"✈️ {len(plan['flights'])} Flüge verfügbar")
        if plan['weather']:
            summary_parts.append("🌤️ Wetterinformationen verfügbar")
        
        # Personalisierte Nachricht basierend auf Reiseart
        if ai_profile['travel_style'] == 'budget':
            summary_parts.append("💰 Budget-optimierte Empfehlungen")
        elif ai_profile['travel_style'] == 'luxury':
            summary_parts.append("✨ Premium-Empfehlungen")
        elif ai_profile['travel_style'] == 'adventure':
            summary_parts.append("🏔️ Abenteuer-Empfehlungen")
        elif ai_profile['travel_style'] == 'culture':
            summary_parts.append("🏛️ Kultur-Empfehlungen")
        elif ai_profile['travel_style'] == 'relaxation':
            summary_parts.append("🧘 Entspannungs-Empfehlungen")
        
        if plan['budget_estimate']:
            summary_parts.append(f"💳 Geschätztes Budget: {plan['budget_estimate']}")
        
        return " ".join(summary_parts)
    
    def _estimate_travel_budget(self, ai_profile: Dict[str, Any], preferences: Dict[str, Any]) -> str:
        """Schätzt das Reisebudget basierend auf KI-Profil"""
        base_budget = 500  # Basis-Budget in Euro
        
        # Anpassung basierend auf Reiseart
        if ai_profile['travel_style'] == 'budget':
            base_budget *= 0.6
        elif ai_profile['travel_style'] == 'luxury':
            base_budget *= 2.5
        elif ai_profile['travel_style'] == 'adventure':
            base_budget *= 1.2
        elif ai_profile['travel_style'] == 'culture':
            base_budget *= 0.9
        elif ai_profile['travel_style'] == 'relaxation':
            base_budget *= 1.1
        
        # Anpassung basierend auf Gruppentyp
        travelers = preferences.get('travelers', 1)
        if ai_profile['group_type'] == 'family':
            base_budget *= 1.5 * travelers
        elif ai_profile['group_type'] == 'couple':
            base_budget *= 1.3 * travelers
        elif ai_profile['group_type'] == 'business':
            base_budget *= 1.4 * travelers
        else:  # solo
            base_budget *= travelers
        
        return f"€{int(base_budget)} - €{int(base_budget * 1.3)}"
    
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
        
        elif 'flug' in message_lower or 'fliegen' in message_lower:
            # Versuche einen Ort aus der Nachricht zu extrahieren
            location = self._extract_location_from_message(message)
            if location:
                # Automatisch nach Flügen suchen
                session['preferences']['destination'] = location
                return self._handle_flight_search_request(user_id, {})
            else:
                return {
                    'type': 'missing_info',
                    'message': 'Für Flugsuche können Sie fragen: "Flüge nach [Ort]"',
                    'suggestions': ['Flüge nach Paris', 'Flüge nach London', 'Flüge nach Rom']
                }
        
        else:
            return {
                'type': 'general',
                'message': 'Ich helfe Ihnen gerne bei der Reiseplanung! Hier sind einige Möglichkeiten:',
                'suggestions': [
                'Wie ist das Wetter in Wien?',
                'Hotels in Barcelona finden',
                'Flüge nach Paris',
                'Wetter in London abfragen',
                'Flüge nach Rom'
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