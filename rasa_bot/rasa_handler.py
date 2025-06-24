import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RasaHandler:
    def __init__(self):

        self.intent_patterns = {
            'greet': [
                r'\b(hallo|hi|hey|guten tag|guten morgen|guten abend)\b',
                r'\b(ich bin|mein name ist)\b'
            ],
            'get_weather': [
                r'\b(wetter|wettervorhersage|temperatur)\s+(in|für|von)\s+([a-zA-Zäöüß\s]+)\b',
                r'\b(wie ist das wetter)\s+(in|für|von)\s+([a-zA-Zäöüß\s]+)\b',
                r'\b(wetter|temperatur)\s+([a-zA-Zäöüß\s]+)\b',
                r'\b(regnet|sonnig|kalt|warm)\s+(in|für)\s+([a-zA-Zäöüß\s]+)\b',
                r'\b(klima|jahreszeit)\s+(in|für)\s+([a-zA-Zäöüß\s]+)\b'
            ],
            'search_flights': [
                r'\b(flug|flüge|fliegen)\s+(suchen|finden|buchen)\b',
                r'\b(flugticket|flugbuchung)\b',
                r'\b(fliegen|flug)\s+(nach|zu)\s+([a-zA-Zäöüß\s]+)\b',
                r'\b(flugpreise|flugkosten)\b',
                r'\b(flugverbindung|flugroute)\b',
                r'\b(flüge|flug)\s+(nach|zu)\s+([a-zA-Zäöüß\s]+)\s+(suchen|finden)\b',
                r'\b(flüge|flug)\s+(suchen|finden)\b'
            ],
            'search_hotels': [
                r'\b(hotels|hotel)\s+(in|in)\s+([a-zA-Zäöüß\s]+)\s+(finden|suchen)\b',
                r'\b(hotel|hotels|unterkunft)\s+(suchen|finden|buchen)\b',
                r'\b(zimmer|übernachtung)\b',
                r'\b(wohnen|schlafen)\s+(in|in)\s+([a-zA-Zäöüß\s]+)\b'
            ],
            'goodbye': [
                r'\b(tschüss|auf wiedersehen|bye|danke)\b',
                r'\b(ende|beenden|fertig)\b'
            ],
            'provide_destination': [
                r'\b(nach|zu|in|nach)\s+([a-zA-Zäöüß\s]+)\b',
                r'\b(reise|fliege|gehe|fahre)\s+(nach|zu|in)\s+([a-zA-Zäöüß\s]+)\b',
                r'\b(ich möchte|ich will|ich plane)\s+(nach|zu|in)\s+([a-zA-Zäöüß\s]+)\b',
                r'^([a-zA-Zäöüß]+)$' 
            ],
            'provide_dates': [
                r'\b(vom|ab|seit)\s+(\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{1,2})\s+(bis|bis zum)\s+(\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{1,2})\b',
                r'\b(\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{1,2})\s+(bis|bis zum)\s+(\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{1,2})\b',
                r'\b(woche|monat|jahr)\b',
                r'\b(wann möchten sie reisen)\b',
                r'\b(reisedatum|reisezeitraum)\b'
            ],
            'provide_duration': [
                r'\b(wie lange möchten sie bleiben)\b',
                r'\b(aufenthalt|dauer|zeitraum)\b',
                r'\b(\d+)\s*(tag|tage|woche|wochen|monat|monate)\b'
            ],
            'provide_budget': [
                r'^(\d+)$',  
                r'^(\d+)(€|eur)$',  
                r'\b(\d+)\s*(euro|eur|€)\b',
                r'\b(\d+)(€|eur)\b',
                r'\b(budget|preis|kosten)\s+(von|bis)\s+(\d+)\s*(euro|eur|€)\b',
                r'\b(teuer|günstig|billig|luxus)\b',
                r'\b(was ist ihr budget)\b',
                r'\b(budget angeben)\b'
            ],
            'create_plan': [
                r'\b(reiseplan|plan|planung)\s+(erstellen|machen)\b',
                r'\b(empfehlung|vorschlag)\b',
                r'\b(was kann ich|was sollte ich)\b'
            ],
            'reset_session': [
                r'\b(alles zurücksetzen|zurücksetzen|neu starten|neue reise)\b',
                r'\b(reset|start over|new trip)\b',
                r'\b(von vorne beginnen|alles löschen)\b'
            ]
        }

    def process_message(self, message: str, user_id: str) -> Dict[str, Any]:
        """
        Verarbeitet eine Nachricht und erkennt den Intent
        """
        try:
            message_lower = message.lower().strip()
            

            best_intent = 'unknown'
            best_confidence = 0.0
            
            for intent, patterns in self.intent_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, message_lower)
                    if matches:

                        if isinstance(matches[0], tuple):

                            confidence = 0.5
                        else:

                            confidence = len(matches[0]) / len(message_lower) if isinstance(matches[0], str) else 0.5
                        
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_intent = intent
            

            if best_confidence < 0.1:
                best_intent = 'unknown'
                best_confidence = 0.0
            
            logger.info(f"Intent erkannt: {best_intent} (Confidence: {best_confidence:.2f})")
            
            return {
                'intent': best_intent,
                'confidence': best_confidence,
                'entities': self._extract_entities(message_lower, best_intent)
            }
            
        except Exception as e:
            logger.error(f"Fehler bei der Intent-Erkennung: {e}")
            return {
                'intent': 'unknown',
                'confidence': 0.0,
                'entities': {}
            }
    
    def _extract_entities(self, message: str, intent: str) -> Dict[str, Any]:

        entities = {}
        
        if intent == 'get_weather':

            weather_patterns = [
                r'\b(wetter|wettervorhersage|temperatur)\s+(in|für|von)\s+([a-zA-Zäöüß\s]+)\b',
                r'\b(wie ist das wetter)\s+(in|für|von)\s+([a-zA-Zäöüß\s]+)\b',
                r'\b(wetter|temperatur)\s+([a-zA-Zäöüß\s]+)\b',
                r'\b(regnet|sonnig|kalt|warm)\s+(in|für)\s+([a-zA-Zäöüß\s]+)\b'
            ]
            for pattern in weather_patterns:
                matches = re.findall(pattern, message)
                if matches:
                    if len(matches[0]) == 3:
                        entities['weather_location'] = matches[0][2].strip()
                    elif len(matches[0]) == 2:
                        entities['weather_location'] = matches[0][1].strip()
                    break
        
        elif intent == 'provide_destination':

            destination_patterns = [
                r'\b(nach|zu|in)\s+([a-zA-Zäöüß\s]+)\b',
                r'\b(reise|fliege|gehe|fahre)\s+(nach|zu|in)\s+([a-zA-Zäöüß\s]+)\b',
                r'\b(ich möchte|ich will|ich plane)\s+(nach|zu|in)\s+([a-zA-Zäöüß\s]+)\b',
                r'^([a-zA-Zäöüß]+)$' 
            ]
            for pattern in destination_patterns:
                matches = re.findall(pattern, message)
                if matches:
                    if len(matches[0]) == 2:
                        entities['destination'] = matches[0][1].strip()
                    elif len(matches[0]) == 3:
                        entities['destination'] = matches[0][2].strip()
                    elif len(matches[0]) == 1:
                        entities['destination'] = matches[0][0].strip()
                    else:
                        entities['destination'] = message.strip()
                    break
        
        elif intent == 'provide_dates':
            date_patterns = [
                r'\b(vom|ab)\s+(\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{1,2})\s+(bis|bis zum)\s+(\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{1,2})\b',
                r'\b(\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{1,2})\s+(bis|bis zum)\s+(\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{1,2})\b'
            ]
            for pattern in date_patterns:
                matches = re.findall(pattern, message)
                if matches:
                    entities['start_date'] = matches[0][1] if len(matches[0]) == 4 else matches[0][0]
                    entities['end_date'] = matches[0][3] if len(matches[0]) == 4 else matches[0][2]
                    break
        
        elif intent == 'provide_duration':

            duration_patterns = [
                r'\b(\d+)\s*(tag|tage|woche|wochen|monat|monate)\b'
            ]
            for pattern in duration_patterns:
                matches = re.findall(pattern, message)
                if matches:
                    entities['duration'] = int(matches[0][0])
                    break
        
        elif intent == 'provide_budget':

            budget_patterns = [
                r'^(\d+)$',
                r'^(\d+)(€|eur)$',
                r'\b(\d+)\s*(euro|eur|€)\b',
                r'\b(\d+)(€|eur)\b',
                r'\b(budget|preis|kosten)\s+(von|bis)\s+(\d+)\s*(euro|eur|€)\b'
            ]
            for pattern in budget_patterns:
                matches = re.findall(pattern, message)
                if matches:
                    if len(matches[0]) == 2:
                        entities['budget'] = int(matches[0][0])
                    elif len(matches[0]) == 4:
                        entities['budget'] = int(matches[0][2])
                    elif len(matches[0]) == 1:
                        entities['budget'] = int(matches[0][0])
                    break
        
        elif intent == 'search_flights':

            flight_patterns = [
                r'\b(flüge|flug)\s+(nach|zu)\s+([a-zA-Zäöüß\s]+)\s+(suchen|finden)\b',
                r'\b(fliegen|flug)\s+(nach|zu)\s+([a-zA-Zäöüß\s]+)\b'
            ]
            for pattern in flight_patterns:
                matches = re.findall(pattern, message)
                if matches:
                    if len(matches[0]) == 4:
                        entities['flight_destination'] = matches[0][2].strip()
                    elif len(matches[0]) == 3:
                        entities['flight_destination'] = matches[0][2].strip()
                    break
        
        elif intent == 'search_hotels':

            hotel_patterns = [
                r'\b(hotels|hotel)\s+(in|in)\s+([a-zA-Zäöüß\s]+)\s+(finden|suchen)\b',
                r'\b(hotel|hotels|unterkunft)\s+(suchen|finden|buchen)\b',
                r'\b(zimmer|übernachtung)\b',
                r'\b(wohnen|schlafen)\s+(in|in)\s+([a-zA-Zäöüß\s]+)\b'
            ]
            for pattern in hotel_patterns:
                matches = re.findall(pattern, message)
                if matches:
                    if len(matches[0]) == 4:
                        entities['hotel_location'] = matches[0][2].strip()
                    elif len(matches[0]) == 2:

                        pass
                    break
        

        if not entities.get('budget'):
            if message.strip().isdigit():
                entities['budget'] = int(message.strip())
        
        return entities 