import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re

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
                return self._handle_weather_request(user_id, entities)
            
            elif intent == 'provide_destination':
                if session['preferences'].get('destination') and not self._is_new_destination(entities, session):
                    return self._handle_already_known_info('destination', session['preferences']['destination'], user_id)
                return self._handle_destination_provided(message, user_id, entities)
            
            elif intent == 'provide_dates':
                if session['preferences'].get('start_date') and session['preferences'].get('end_date'):
                    return self._handle_already_known_info('dates', f"{session['preferences']['start_date']} bis {session['preferences']['end_date']}", user_id)
                return self._handle_dates_provided(message, user_id, entities)
            
            elif intent == 'provide_duration':
                if session['preferences'].get('duration'):
                    return self._handle_already_known_info('duration', session['preferences']['duration'], user_id)
                return self._handle_duration_provided(message, user_id, entities)
            
            elif intent == 'provide_budget':
                if session['preferences'].get('budget'):
                    return self._handle_already_known_info('budget', session['preferences']['budget'], user_id)
                return self._handle_budget_provided(message, user_id, entities)
            
            elif intent == 'provide_preferences':
                return self._handle_preferences_provided(message, user_id)
            
            elif intent == 'search_flights':
                return self._handle_flight_search_request(user_id, entities)
            
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
            'duration': bool(prefs.get('duration')),
            'budget': bool(prefs.get('budget')),
            'complete': False
        }
        
        if progress['destination'] and progress['dates'] and progress['budget']:
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
            'dates': f'Ihre Reisedaten sind bereits {current_value}.',
            'duration': f'Ihre Reisedauer ist bereits {current_value} Tage.',
            'budget': f'Ihr Budget ist bereits {current_value}€.'
        }
        
        if progress['complete']:
            return {
                'type': 'info_complete',
                'message': f"{messages[info_type]} Alle Informationen sind vollständig! Was möchten Sie als nächstes tun?",
                'suggestions': [
                    'Flüge suchen',
                    'Hotels suchen',
                    'Wetter abfragen',
                    'Alles zurücksetzen'
                ]
            }
        else:
            if not progress['destination']:
                return {
                    'type': 'info_partial',
                    'message': f"{messages[info_type]} Noch benötigt: Reiseziel",
                    'suggestions': ['Wo möchten Sie hinreisen?', 'Alles zurücksetzen']
                }
            elif not progress['dates']:
                today = datetime.now()
                
                example1_start = today + timedelta(days=30)
                example1_end = example1_start + timedelta(days=7)
                example2_start = today + timedelta(days=60)
                example2_end = example2_start + timedelta(days=7)
                example3_start = today + timedelta(days=90)
                example3_end = example3_start + timedelta(days=7)
                
                suggestions = []
                suggestions.append(f'{example1_start.strftime("%d.%m.%Y")} bis {example1_end.strftime("%d.%m.%Y")}')
                suggestions.append(f'{example2_start.strftime("%d.%m.%Y")} bis {example2_end.strftime("%d.%m.%Y")}')
                suggestions.append(f'{example3_start.strftime("%d.%m.%Y")} bis {example3_end.strftime("%d.%m.%Y")}')
                
                return {
                    'type': 'info_partial',
                    'message': f"{messages[info_type]} Noch benötigt: Reisedaten\nWann möchten Sie reisen? (z.B. {example1_start.strftime('%d.%m.%Y')} bis {example1_end.strftime('%d.%m.%Y')})",
                    'suggestions': suggestions
                }
            elif not progress['budget']:
                return {
                    'type': 'info_partial',
                    'message': 'Noch benötigt: Budget\nWas ist Ihr Budget? (z.B. 500€ für 7 Tage)',
                    'suggestions': ['100€', '300€', '500€', '1000€']
                }
    
    def _get_next_questions(self, progress: Dict[str, Any]) -> List[str]:
        suggestions = []
        
        if not progress['destination']:
            suggestions.append('Wo möchten Sie hinreisen?')
        elif not progress['dates']:
            today = datetime.now()
            
            example1_start = today + timedelta(days=30)
            example1_end = example1_start + timedelta(days=7)
            example2_start = today + timedelta(days=60)
            example2_end = example2_start + timedelta(days=7)
            example3_start = today + timedelta(days=90)
            example3_end = example3_start + timedelta(days=7)
            
            suggestions.append(f'{example1_start.strftime("%d.%m.%Y")} bis {example1_end.strftime("%d.%m.%Y")}')
            suggestions.append(f'{example2_start.strftime("%d.%m.%Y")} bis {example2_end.strftime("%d.%m.%Y")}')
            suggestions.append(f'{example3_start.strftime("%d.%m.%Y")} bis {example3_end.strftime("%d.%m.%Y")}')
        elif not progress['budget']:
            suggestions.append('Was ist Ihr Budget? (z.B. 500€ für 7 Tage)')
            suggestions.append('100€')
            suggestions.append('300€')
            suggestions.append('500€')
            suggestions.append('1000€')
        
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
        if 'budget' in entities:
            session['preferences']['budget'] = entities['budget']
    
    def _initialize_user_session(self) -> Dict[str, Any]:
        return {
            'state': self.dialog_states['greeting'],
            'preferences': {
                'destination': None,
                'start_date': None,
                'end_date': None,
                'duration': None,
                'budget': None,
                'travelers': 1,
                'accommodation_type': 'hotel',
                'activities': [],
                'dietary_restrictions': [],
                'accessibility_needs': []
            },
            'search_results': {
                'flights': [],
                'hotels': [],
                'weather': None
            },
            'conversation_history': [],
            'created_at': datetime.now()
        }
    
    def _handle_greeting(self, user_id: str) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        
        if session['preferences'].get('destination') and session['preferences'].get('start_date'):
            return {
                'type': 'greeting_existing',
                'message': 'Willkommen zurück! Ich sehe, dass Sie bereits eine Reise nach ' + session['preferences']['destination'] + ' geplant haben. Möchten Sie diese fortsetzen oder eine neue Reise planen?',
                'suggestions': [
                    'Aktuelle Reise fortsetzen',
                    'Neue Reise planen',
                    'Flüge suchen',
                    'Hotels suchen'
                ]
            }
        
        session['state'] = self.dialog_states['collecting_preferences']
        
        return {
            'type': 'greeting',
            'message': 'Hallo! Ich bin Ihr intelligenter TravelGuide. Ich helfe Ihnen gerne bei der Planung Ihrer nächsten Reise!',
            'suggestions': [
                'Wohin möchten Sie reisen?'
            ],
            'next_questions': [
                'Wo möchten Sie hinreisen?'
            ]
        }
    
    def reset_user_session(self, user_id: str) -> Dict[str, Any]:
        self.user_sessions[user_id] = self._initialize_user_session()
        
        return {
            'type': 'session_reset',
            'message': 'Perfekt! Lassen Sie uns eine neue Reise planen! \n\nIch helfe Ihnen gerne bei der Reiseplanung! Hier sind einige Möglichkeiten:',
            'suggestions': [
                'Wie ist das Wetter in Berlin?',
                'Flüge nach Paris suchen',
                'Hotels in München finden',
                'Ich möchte nach Rom reisen'
            ]
        }
    
    def _handle_continue_trip(self, user_id: str) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        progress = self._check_conversation_progress(session)
        
        if progress['complete']:
            return {
                'type': 'continue_complete',
                'message': 'Perfekt! Ihre Reiseplanung ist vollständig. Was möchten Sie als nächstes tun?',
                'suggestions': [
                    'Flüge suchen',
                    'Hotels suchen',
                    'Wetter abfragen',
                    'Alles zurücksetzen'
                ]
            }
        else:
            if not progress['destination']:
                return {
                    'type': 'continue_partial',
                    'message': 'Lassen Sie uns Ihre Reiseplanung vervollständigen!',
                    'suggestions': ['Wo möchten Sie hinreisen?', 'Alles zurücksetzen']
                }
            elif not progress['dates']:
                today = datetime.now()
                
                example1_start = today + timedelta(days=30)
                example1_end = example1_start + timedelta(days=7)
                example2_start = today + timedelta(days=60)
                example2_end = example2_start + timedelta(days=7)
                example3_start = today + timedelta(days=90)
                example3_end = example3_start + timedelta(days=7)
                
                return {
                    'type': 'continue_partial',
                    'message': f'Lassen Sie uns Ihre Reiseplanung vervollständigen!\nWann möchten Sie reisen? (z.B. {example1_start.strftime("%d.%m.%Y")} bis {example1_end.strftime("%d.%m.%Y")})',
                    'suggestions': [
                        f'{example1_start.strftime("%d.%m.%Y")} bis {example1_end.strftime("%d.%m.%Y")}',
                        f'{example2_start.strftime("%d.%m.%Y")} bis {example2_end.strftime("%d.%m.%Y")}',
                        f'{example3_start.strftime("%d.%m.%Y")} bis {example3_end.strftime("%d.%m.%Y")}'
                    ]
                }
            elif not progress['budget']:
                return {
                    'type': 'continue_partial',
                    'message': 'Lassen Sie uns Ihre Reiseplanung vervollständigen!\nWas ist Ihr Budget? (z.B. 500€)',
                    'suggestions': ['100€', '300€', '500€', '1000€']
                }
    
    def _handle_destination_provided(self, message: str, user_id: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        
        destination = entities.get('destination')
        if destination:
            destination = self._clean_destination(destination)
            session['preferences']['destination'] = destination
            
            progress = self._check_conversation_progress(session)
            
            if progress['complete']:
                return {
                    'type': 'destination_confirmed_complete',
                    'message': f'Perfekt! {destination.title()} ist ein tolles Reiseziel! 🌍 Alle Informationen sind vollständig!',
                    'destination': destination,
                    'suggestions': [
                        'Flüge suchen',
                        'Hotels suchen',
                        'Wetter abfragen',
                        'Alles zurücksetzen'
                    ]
                }
            else:
                today = datetime.now()
                
                example1_start = today + timedelta(days=30)
                example1_end = example1_start + timedelta(days=7)
                example2_start = today + timedelta(days=60)
                example2_end = example2_start + timedelta(days=7)
                example3_start = today + timedelta(days=90)
                example3_end = example3_start + timedelta(days=7)
                
                return {
                    'type': 'destination_confirmed',
                    'message': f'Perfekt! {destination.title()} ist ein tolles Reiseziel! 🌍',
                    'destination': destination,
                    'suggestions': [
                        f'Wann möchten Sie reisen? (z.B. {example1_start.strftime("%d.%m.%Y")} bis {example1_end.strftime("%d.%m.%Y")})',
                        f'{example1_start.strftime("%d.%m.%Y")} bis {example1_end.strftime("%d.%m.%Y")}',
                        f'{example2_start.strftime("%d.%m.%Y")} bis {example2_end.strftime("%d.%m.%Y")}',
                        f'{example3_start.strftime("%d.%m.%Y")} bis {example3_end.strftime("%d.%m.%Y")}'
                    ]
                }
        else:
            return {
                'type': 'clarification_needed',
                'message': 'Bitte geben Sie Ihr Reiseziel an.',
                'suggestions': ['Paris', 'Rom', 'London', 'Berlin', 'München']
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
                        'Flüge suchen',
                        'Hotels suchen',
                        'Wetter abfragen',
                        'Alles zurücksetzen'
                    ]
                }
            else:
                return {
                    'type': 'dates_confirmed',
                    'message': f'Verstanden! Reisezeitraum: {start_date} bis {end_date} \nWas ist Ihr Budget? (z.B. 500€)',
                    'start_date': start_date,
                    'end_date': end_date,
                    'suggestions': ['100€', '300€', '500€', '1000€']
                }
        else:
            return {
                'type': 'clarification_needed',
                'message': 'Bitte geben Sie Ihren Reisezeitraum an (Format: DD.MM.YYYY bis DD.MM.YYYY):',
                'suggestions': ['15.07.2024 bis 22.07.2024', '01.08.2024 bis 08.08.2024', '23.12.2024 bis 30.12.2024']
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
                        'Flüge suchen',
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
    
    def _handle_budget_provided(self, message: str, user_id: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        
        budget = entities.get('budget')
        
        if budget:
            session['preferences']['budget'] = budget
            
            destination = session['preferences'].get('destination', 'Ihr Ziel')
            
            progress = self._check_conversation_progress(session)
            
            if progress['complete']:
                try:
                    flights = self.flight_service.search_flights(
                        origin='BER',
                        destination=session['preferences']['destination'],
                        start_date=session['preferences']['start_date'],
                        end_date=session['preferences']['end_date'],
                        budget=session['preferences']['budget']
                    )
                    
                    session['search_results']['flights'] = flights
                    flight_summary = self.flight_service.get_flight_summary(flights)
                    
                    return {
                        'type': 'budget_confirmed_with_flights',
                        'message': f'Verstanden! Budget: {budget}€ Alle Informationen sind vollständig! Hier sind Ihre Flugoptionen:',
                        'budget': budget,
                        'flight_summary': flight_summary,
                        'flights': flights,
                        'suggestions': [
                            'Hotels suchen',
                            'Wetter abfragen',
                            'Alles zurücksetzen',
                            'Weitere Flüge suchen'
                        ]
                    }
                except Exception as e:
                    logger.error(f"Fehler bei automatischer Flugsuche: {e}")
                    return {
                        'type': 'budget_confirmed_complete',
                        'message': f'Verstanden! Budget: {budget}€ Alle Informationen sind vollständig!',
                        'budget': budget,
                        'suggestions': [
                            'Flüge suchen',
                            'Hotels suchen',
                            'Wetter abfragen',
                            'Alles zurücksetzen'
                        ]
                    }
            else:
                return {
                    'type': 'budget_confirmed',
                    'message': f'Verstanden! Budget: {budget}€',
                    'budget': budget,
                    'suggestions': self._get_next_questions(progress)
                }
        else:
            return {
                'type': 'clarification_needed',
                'message': 'Bitte geben Sie Ihr Budget an:',
                'suggestions': ['100€', '300€', '500€', '1000€']
            }
    
    def _handle_preferences_provided(self, message: str, user_id: str) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        
        extracted_info = self.chatgpt_service.extract_travel_info(message)
        
        for key, value in extracted_info.items():
            if value and key in session['preferences']:
                session['preferences'][key] = value
        
        return {
            'type': 'preferences_updated',
            'message': 'Danke für die Informationen! Ich kann Ihnen jetzt bei der Reiseplanung helfen.',
            'suggestions': [
                'Flüge suchen',
                'Hotels suchen',
                'Wetter abfragen',
                'Alles zurücksetzen'
            ]
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
                'suggestions': ['Wo möchten Sie hinreisen?', 'Alles zurücksetzen']
            }
        
        try:
            origin = prefs.get('origin', 'BER')
            destination = prefs.get('destination')
            start_date = prefs.get('start_date')
            end_date = prefs.get('end_date')
            budget = prefs.get('budget')
            
            flights = self.flight_service.search_flights(
                origin=origin,
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                budget=budget
            )
            
            session['search_results']['flights'] = flights
            
            flight_summary = self.flight_service.get_flight_summary(flights)
            
            return {
                'type': 'flight_results',
                'message': flight_summary,
                'flights': flights,
                'suggestions': [
                    'Hotels suchen',
                    'Alles zurücksetzen',
                    'Wetter abfragen'
                ]
            }
            
        except Exception as e:
            logger.error(f"Fehler bei der Flugsuche: {e}")
            return {
                'type': 'error',
                'message': 'Entschuldigung, bei der Flugsuche ist ein Fehler aufgetreten.',
                'suggestions': ['Versuchen Sie es später erneut']
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
                'suggestions': ['Wo möchten Sie hinreisen?', 'Alles zurücksetzen']
            }
        
        try:
            location = prefs.get('destination')
            check_in = prefs.get('start_date')
            check_out = prefs.get('end_date')
            guests = prefs.get('travelers', 1)
            budget = prefs.get('budget')
            
            hotels = self.hotel_service.search_hotels(
                location=location,
                check_in=check_in,
                check_out=check_out,
                guests=guests,
                budget=budget
            )
            
            session['search_results']['hotels'] = hotels
            
            hotel_summary = self.hotel_service.get_hotel_summary(hotels)
            
            return {
                'type': 'hotel_results',
                'message': hotel_summary,
                'hotels': hotels,
                'suggestions': [
                    'Flüge suchen',
                    'Alles zurücksetzen',
                    'Wetter abfragen'
                ]
            }
            
        except Exception as e:
            logger.error(f"Fehler bei der Hotelsuche: {e}")
            return {
                'type': 'error',
                'message': 'Entschuldigung, bei der Hotelsuche ist ein Fehler aufgetreten.',
                'suggestions': ['Versuchen Sie es später erneut']
            }
    
    def _handle_weather_request(self, user_id: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        prefs = session['preferences']
        
        weather_location = entities.get('weather_location')
        if not weather_location:
            weather_location = prefs.get('destination')
        
        if not weather_location:
            return {
                'type': 'missing_info',
                'message': 'Bitte geben Sie einen Ort an, für den Sie das Wetter wissen möchten.',
                'suggestions': ['Wie ist das Wetter in Berlin?', 'Wetter in München', 'Temperatur in Hamburg']
            }
        
        try:
            start_date = prefs.get('start_date')
            weather = self.weather_service.get_weather(
                location=weather_location,
                date=start_date
            )
            
            session['search_results']['weather'] = weather
            
            weather_summary = self.weather_service.get_weather_summary(weather_location)
            
            if start_date:
                weather_summary += f"\n\n Wettervorhersage für Ihr Reisedatum: {start_date}"
            
            return {
                'type': 'weather_info',
                'message': weather_summary,
                'weather': weather,
                'suggestions': [
                    'Flüge suchen',
                    'Hotels suchen',
                    'Alles zurücksetzen'
                ]
            }
            
        except Exception as e:
            logger.error(f"Fehler bei der Wetterabfrage: {e}")
            return {
                'type': 'error',
                'message': 'Entschuldigung, bei der Wetterabfrage ist ein Fehler aufgetreten.',
                'suggestions': ['Versuchen Sie es später erneut']
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
            budget = prefs.get('budget', 'Ihr Budget')
            travelers = prefs.get('travelers', 1)
            
            flights_count = len(results.get('flights', []))
            hotels_count = len(results.get('hotels', []))
            weather_info = results.get('weather', {})
            
            plan = f"""
🌍 Reiseplan für {destination}

Reisezeitraum: {start_date} bis {end_date}
Budget: {budget}€
Reisende: {travelers} Person(en)

Verfügbare Optionen:
• Flüge: {flights_count} verfügbar
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
                    'Flüge suchen',
                    'Hotels suchen',
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
    
    def _handle_general_question(self, message: str, user_id: str) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        
        message_lower = message.lower()
        
        if 'wetter' in message_lower:
            return {
                'type': 'missing_info',
                'message': 'Für Wetterinformationen können Sie fragen: "Wie ist das Wetter in [Ort]?"',
                'suggestions': ['Wie ist das Wetter in Berlin?', 'Wetter in München', 'Temperatur in Hamburg']
            }
        
        elif 'flug' in message_lower or 'fliegen' in message_lower:
            return {
                'type': 'missing_info',
                'message': 'Für Flugsuche können Sie fragen: "Flüge nach [Ort] suchen"',
                'suggestions': ['Flüge nach Paris suchen', 'Flüge nach Rom suchen', 'Flüge nach London suchen']
            }
        
        elif 'hotel' in message_lower or 'unterkunft' in message_lower:
            return {
                'type': 'missing_info',
                'message': 'Für Hotelsuche können Sie fragen: "Hotels in [Ort] finden"',
                'suggestions': ['Hotels in Berlin finden', 'Hotels in München finden', 'Hotels in Hamburg finden']
            }
        
        elif 'budget' in message_lower or 'preis' in message_lower:
            return {
                'type': 'missing_info',
                'message': 'Bitte geben Sie Ihr Budget an, z.B.: "100 Euro" oder "500€"',
                'suggestions': ['100 Euro', '500 Euro', '1000 Euro']
            }
        
        else:
            return {
                'type': 'general',
                'message': 'Ich helfe Ihnen gerne bei der Reiseplanung! Hier sind einige Möglichkeiten:',
                'suggestions': [
                    'Wie ist das Wetter in Berlin?',
                    'Flüge nach Paris suchen',
                    'Hotels in München finden',
                    'Ich möchte nach Rom reisen'
                ]
            }
    
    def _handle_goodbye(self, user_id: str) -> Dict[str, Any]:
        return {
            'type': 'goodbye',
            'message': 'Vielen Dank für die Nutzung des TravelGuide! Ich wünsche Ihnen eine wundervolle Reise! ✈️🌍',
            'suggestions': ['Neue Reise planen']
        } 