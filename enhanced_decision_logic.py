import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re

from ai_recommendation_engine import AIRecommendationEngine

logger = logging.getLogger(__name__)

class EnhancedDecisionLogic:
    def __init__(self, flight_service, hotel_service, weather_service, rasa_handler):
        self.flight_service = flight_service
        self.hotel_service = hotel_service
        self.weather_service = weather_service
        self.rasa_handler = rasa_handler
        self.ai_recommendation_engine = AIRecommendationEngine()
        
        self.user_sessions = {}
        self.interaction_history = {}
        self.dialog_states = {
            'greeting': 'greeting',
            'collecting_preferences': 'collecting_preferences',
            'ai_recommendations': 'ai_recommendations',
            'searching_options': 'searching_options',
            'presenting_results': 'presenting_results',
            'finalizing_plan': 'finalizing_plan'
        }
        
        # KI-Entscheidungslogik für Intent-Routing
        self.ai_intent_routing = {
            'recommendation_request': ['empfehlung', 'vorschlag', 'sollte ich', 'kann ich', 'was ist gut'],
            'preference_collection': ['budget', 'stil', 'gruppe', 'dauer', 'jahreszeit'],
            'search_request': ['suchen', 'finden', 'flug', 'hotel', 'wetter'],
            'planning_request': ['plan', 'planung', 'organisieren', 'buchen'],
            'general_question': ['wie', 'was', 'wann', 'wo', 'warum']
        }
    
    def process_user_message(self, message: str, user_id: str) -> Dict[str, Any]:
        """Erweiterte Nachrichtenverarbeitung mit KI-gestützter Entscheidungslogik"""
        try:
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = self._initialize_user_session()
            
            session = self.user_sessions[user_id]
            
            # Speichere Interaktion in Historie
            self._add_to_interaction_history(user_id, message)
            
            # Rasa Intent-Erkennung
            rasa_response = self.rasa_handler.process_message(message, user_id)
            intent = rasa_response.get('intent', 'unknown')
            confidence = rasa_response.get('confidence', 0.0)
            entities = rasa_response.get('entities', {})
            
            logger.info(f"Rasa Intent: {intent} (Confidence: {confidence})")
            
            # KI-gestützte Intent-Verfeinerung
            ai_intent = self._determine_ai_intent(message, intent, confidence)
            logger.info(f"KI-gestützter Intent: {ai_intent}")
            
            # Aktualisiere Session mit Entitäten
            self._update_session_with_entities(session, entities)
            
            # Entscheidungslogik basierend auf AI Intent
            if ai_intent == 'recommendation_request':
                return self._handle_ai_recommendation_request(user_id, message, session)
            
            elif ai_intent == 'preference_collection':
                return self._handle_preference_collection(user_id, message, session)
            
            elif ai_intent == 'search_request':
                return self._handle_search_request(user_id, intent, entities, session)
            
            elif ai_intent == 'planning_request':
                return self._handle_planning_request(user_id, message, session)
            
            elif ai_intent == 'general_question':
                return self._handle_general_question_with_ai(user_id, message, session)
            
            else:
                # Fallback zur ursprünglichen Logik
                return self._handle_legacy_intent(user_id, intent, entities, message, session)
                
        except Exception as e:
            logger.error(f"Fehler bei der erweiterten Nachrichtenverarbeitung: {e}")
            return {
                'type': 'error',
                'message': 'Entschuldigung, es gab einen Fehler bei der Verarbeitung Ihrer Anfrage.',
                'suggestions': ['Versuchen Sie es erneut', 'Formulieren Sie Ihre Anfrage anders']
            }
    
    def _determine_ai_intent(self, message: str, rasa_intent: str, rasa_confidence: float) -> str:
        """KI-gestützte Intent-Bestimmung basierend auf Nachrichteninhalt und Rasa-Ergebnis"""
        message_lower = message.lower()
        
        # Gewichtete Bewertung verschiedener Faktoren
        scores = {}
        
        # 1. Keyword-basierte Bewertung
        for intent, keywords in self.ai_intent_routing.items():
            score = 0
            for keyword in keywords:
                if keyword in message_lower:
                    score += 1
            scores[intent] = score
        
        # 2. Rasa-Confidence Integration
        if rasa_confidence > 0.7:
            # Hohe Rasa-Confidence hat Vorrang
            if rasa_intent in ['search_hotels', 'search_flights', 'get_weather']:
                return 'search_request'
            elif rasa_intent in ['create_plan']:
                return 'planning_request'
        
        # 3. Präferenz-Änderung (höhere Priorität)
        preference_change_keywords = ['präferenzen ändern', 'präferenzen bearbeiten', 'einstellungen ändern', 'weitere präferenzen']
        if any(keyword in message_lower for keyword in preference_change_keywords):
            return 'preference_collection'
        
        # 4. Spezielle Empfehlungslogik
        recommendation_keywords = ['empfehlung', 'vorschlag', 'sollte ich', 'kann ich', 'was ist gut', 'was passt']
        if any(keyword in message_lower for keyword in recommendation_keywords):
            return 'recommendation_request'
        
        # 5. Präferenz-Sammlung
        preference_keywords = ['budget', 'stil', 'gruppe', 'dauer', 'jahreszeit', 'preferiere', 'möchte']
        if any(keyword in message_lower for keyword in preference_keywords):
            return 'preference_collection'
        
        # 6. Allgemeine Fragen
        question_words = ['wie', 'was', 'wann', 'wo', 'warum']
        if any(word in message_lower.split() for word in question_words):
            return 'general_question'
        
        # Fallback basierend auf höchstem Score
        if scores:
            return max(scores, key=scores.get)
        
        return 'general_question'
    
    def _handle_ai_recommendation_request(self, user_id: str, message: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt KI-gestützte Empfehlungsanfragen"""
        try:
            # Extrahiere Präferenzen aus der Nachricht
            extracted_preferences = self._extract_preferences_from_message(message)
            
            # Aktualisiere Benutzerprofil
            if extracted_preferences:
                self.ai_recommendation_engine.update_user_preferences(user_id, extracted_preferences)
            
            # Generiere personalisierte Empfehlungen
            recommendations = self.ai_recommendation_engine.generate_personalized_recommendations(
                user_id, 
                current_preferences=extracted_preferences,
                num_recommendations=3
            )
            
            # Formatiere Empfehlungen für die Antwort
            formatted_recommendations = []
            for rec in recommendations:
                formatted_rec = {
                    'destination': rec.destination,
                    'confidence': f"{rec.confidence_score:.1%}",
                    'reasoning': rec.reasoning,
                    'activities': rec.activities[:3],  # Top 3 Aktivitäten
                    'budget_estimate': f"€{rec.estimated_budget['total_weekly_per_person']:.0f} pro Person/Woche",
                    'best_time': rec.best_time_to_visit
                }
                formatted_recommendations.append(formatted_rec)
            
            # Erstelle Antwort
            response_message = "Basierend auf Ihren Präferenzen empfehle ich Ihnen folgende Destinationen:\n\n"
            
            for i, rec in enumerate(formatted_recommendations, 1):
                response_message += f"**{i}. {rec['destination']}** ({rec['confidence']} Übereinstimmung)\n"
                response_message += f"   {rec['reasoning']}\n"
                response_message += f"   💰 Budget: {rec['budget_estimate']}\n"
                response_message += f"   🕒 {rec['best_time']}\n"
                response_message += f"   🎯 Aktivitäten: {', '.join(rec['activities'])}\n\n"
            
            response_message += "Möchten Sie mehr Details zu einer dieser Destinationen oder soll ich Hotels/Flüge für Sie suchen?"
            
            return {
                'type': 'ai_recommendations',
                'message': response_message,
                'recommendations': formatted_recommendations,
                'suggestions': [
                    f"Hotels in {formatted_recommendations[0]['destination']} finden",
                    f"Flüge nach {formatted_recommendations[0]['destination']} suchen",
                    "Weitere Empfehlungen",
                    "Meine Präferenzen ändern"
                ]
            }
            
        except Exception as e:
            logger.error(f"Fehler bei KI-Empfehlungen: {e}")
            return {
                'type': 'error',
                'message': 'Entschuldigung, ich konnte keine Empfehlungen generieren.',
                'suggestions': ['Versuchen Sie es erneut', 'Geben Sie mehr Details an']
            }
    
    def _handle_preference_collection(self, user_id: str, message: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt Präferenz-Sammlung mit KI-Unterstützung"""
        extracted_preferences = self._extract_preferences_from_message(message)
        
        if extracted_preferences:
            self.ai_recommendation_engine.update_user_preferences(user_id, extracted_preferences)
            
            return {
                'type': 'preferences_updated',
                'message': f"Vielen Dank! Ich habe Ihre Präferenzen aktualisiert. Möchten Sie jetzt personalisierte Empfehlungen erhalten?",
                'updated_preferences': extracted_preferences,
                'suggestions': [
                    "Empfehlungen anzeigen",
                    "Weitere Präferenzen angeben",
                    "Hotels suchen",
                    "Flüge suchen"
                ]
            }
        else:
            return {
                'type': 'preference_help',
                'message': "Ich kann Ihnen helfen, Ihre Reisevorlieben zu definieren. Was ist Ihnen wichtig?\n\n" +
                          "• Budget (günstig, mittel, luxuriös)\n" +
                          "• Reiseart (kulturell, entspannt, aktiv, luxuriös)\n" +
                          "• Gruppengröße (allein, zu zweit, Familie, Gruppe)\n" +
                          "• Jahreszeit (Frühling, Sommer, Herbst, Winter)\n" +
                          "• Reisedauer (Wochenende, Woche, länger)",
                'suggestions': [
                    "Budget: günstig",
                    "Reiseart: kulturell", 
                    "Gruppe: zu zweit",
                    "Jahreszeit: Frühling",
                    "Empfehlungen basierend auf Standard-Präferenzen"
                ]
            }
    
    def _handle_search_request(self, user_id: str, rasa_intent: str, entities: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt Suchanfragen mit KI-Erweiterung"""
        if rasa_intent == 'search_hotels':
            return self._handle_hotel_search_with_ai(user_id, entities, session)
        elif rasa_intent == 'search_flights':
            return self._handle_flight_search_with_ai(user_id, entities, session)
        elif rasa_intent == 'get_weather':
            return self._handle_weather_request(user_id, entities, session)
        else:
            return self._handle_standard_general_question(message, user_id, session)
    
    def _handle_hotel_search_with_ai(self, user_id: str, entities: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
        """Hotel-Suche mit KI-gestützten Empfehlungen"""
        destination = entities.get('destination') or session['preferences'].get('destination')
        
        if not destination:
            return {
                'type': 'missing_destination',
                'message': 'Für welche Destination möchten Sie Hotels finden?',
                'suggestions': [
                    'Hotels in Paris finden',
                    'Hotels in London finden', 
                    'Hotels in Rom finden',
                    'Empfehlungen anzeigen'
                ]
            }
        
        try:
            # Standard Hotel-Suche
            hotels = self.hotel_service.search_hotels(location=destination)
            
            # KI-gestützte Hotel-Empfehlungen basierend auf Benutzerprofil
            if user_id in self.ai_recommendation_engine.user_profiles:
                profile = self.ai_recommendation_engine.user_profiles[user_id]
                
                # Filtere Hotels basierend auf Budget-Präferenzen
                filtered_hotels = self._filter_hotels_by_preferences(hotels, profile)
                
                response_message = f"Hier sind Hotels in {destination} (angepasst an Ihre Präferenzen):\n\n"
                
                for i, hotel in enumerate(filtered_hotels[:5], 1):
                    response_message += f"**{i}. {hotel['name']}**\n"
                    response_message += f"   💰 {hotel.get('price', 'Preis auf Anfrage')}\n"
                    response_message += f"   ⭐ {hotel.get('rating', 'N/A')}\n"
                    response_message += f"   📍 {hotel.get('location', 'N/A')}\n\n"
                
                return {
                    'type': 'hotels_with_ai',
                    'message': response_message,
                    'hotels': filtered_hotels[:5],
                    'destination': destination,
                    'ai_filtered': True,
                    'suggestions': [
                        f"Flüge nach {destination} suchen",
                        f"Wetter in {destination}",
                        "Weitere Empfehlungen",
                        "Reiseplan erstellen"
                    ]
                }
            else:
                # Standard-Antwort ohne KI-Filterung
                return self._handle_standard_hotel_search(destination, hotels)
                
        except Exception as e:
            logger.error(f"Fehler bei Hotel-Suche mit AI: {e}")
            return {
                'type': 'error',
                'message': f'Entschuldigung, ich konnte keine Hotels in {destination} finden.',
                'suggestions': ['Versuchen Sie es erneut', 'Andere Destination']
            }
    
    def _filter_hotels_by_preferences(self, hotels: List[Dict[str, Any]], profile) -> List[Dict[str, Any]]:
        """Filtert Hotels basierend auf Benutzerpräferenzen"""
        if not hotels:
            return hotels
        
        # Einfache Budget-Filterung basierend auf Profil
        budget_ranges = {
            'budget': (0, 100),
            'mid-range': (80, 200),
            'luxury': (150, 1000)
        }
        
        min_price, max_price = budget_ranges.get(profile.budget_range, (0, 1000))
        
        filtered_hotels = []
        for hotel in hotels:
            price_str = hotel.get('price', '')
            if price_str and '€' in price_str:
                try:
                    price = float(re.findall(r'\d+', price_str)[0])
                    if min_price <= price <= max_price:
                        filtered_hotels.append(hotel)
                except (ValueError, IndexError):
                    filtered_hotels.append(hotel)  # Bei Preis-Parsing-Fehlern trotzdem hinzufügen
            else:
                filtered_hotels.append(hotel)
        
        return filtered_hotels if filtered_hotels else hotels
    
    def _handle_planning_request(self, user_id: str, message: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt Planungsanfragen mit KI-Unterstützung"""
        destination = session['preferences'].get('destination')
        
        if not destination:
            return {
                'type': 'planning_help',
                'message': "Ich kann Ihnen bei der Reiseplanung helfen! Zuerst brauche ich ein paar Informationen:\n\n" +
                          "1. **Reiseziel**: Wohin möchten Sie reisen?\n" +
                          "2. **Reisedaten**: Wann möchten Sie reisen?\n" +
                          "3. **Budget**: Was ist Ihr Budget?\n\n" +
                          "Oder soll ich Ihnen zuerst Empfehlungen geben?",
                'suggestions': [
                    "Empfehlungen anzeigen",
                    "Reiseziel angeben",
                    "Budget angeben",
                    "Reisedaten angeben"
                ]
            }
        
        # Erstelle einen umfassenden Reiseplan
        try:
            plan = self._create_comprehensive_travel_plan(user_id, destination, session)
            
            return {
                'type': 'travel_plan',
                'message': plan['summary'],
                'plan_details': plan['details'],
                'suggestions': [
                    "Plan anpassen",
                    "Hotels buchen",
                    "Flüge buchen",
                    "Weitere Empfehlungen"
                ]
            }
            
        except Exception as e:
            logger.error(f"Fehler bei Reiseplanung: {e}")
            return {
                'type': 'error',
                'message': 'Entschuldigung, ich konnte keinen Reiseplan erstellen.',
                'suggestions': ['Versuchen Sie es erneut', 'Mehr Details angeben']
            }
    
    def _create_comprehensive_travel_plan(self, user_id: str, destination: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt einen umfassenden Reiseplan mit KI-Unterstützung"""
        plan = {
            'destination': destination,
            'summary': f"**Reiseplan für {destination}**\n\n",
            'details': {}
        }
        
        # 1. Wetter-Informationen
        try:
            weather = self.weather_service.get_weather(destination)
            plan['details']['weather'] = weather
            plan['summary'] += f"🌤️ **Wetter**: {weather.get('description', 'N/A')}, {weather.get('temperature', 'N/A')}°C\n"
        except:
            plan['summary'] += "🌤️ **Wetter**: Informationen nicht verfügbar\n"
        
        # 2. Hotel-Empfehlungen
        try:
            hotels = self.hotel_service.search_hotels(location=destination)
            if hotels:
                plan['details']['hotels'] = hotels[:3]
                plan['summary'] += f"🏨 **Hotels**: {len(hotels)} Optionen gefunden\n"
        except:
            plan['summary'] += "🏨 **Hotels**: Suche nicht verfügbar\n"
        
        # 3. Flug-Informationen
        try:
            flights = self.flight_service.search_flights(destination=destination)
            if flights:
                plan['details']['flights'] = flights[:3]
                plan['summary'] += f"✈️ **Flüge**: {len(flights)} Optionen gefunden\n"
        except:
            plan['summary'] += "✈️ **Flüge**: Suche nicht verfügbar\n"
        
        # 4. KI-gestützte Aktivitätsempfehlungen
        if user_id in self.ai_recommendation_engine.user_profiles:
            profile = self.ai_recommendation_engine.user_profiles[user_id]
            dest_data = self.ai_recommendation_engine.destination_database.get(destination.lower())
            
            if dest_data:
                activities = dest_data['activities'][:5]
                plan['details']['activities'] = activities
                plan['summary'] += f"🎯 **Aktivitäten**: {', '.join(activities)}\n"
        
        # 5. Budget-Schätzung
        if user_id in self.ai_recommendation_engine.user_profiles:
            profile = self.ai_recommendation_engine.user_profiles[user_id]
            dest_data = self.ai_recommendation_engine.destination_database.get(destination.lower())
            
            if dest_data:
                budget = self.ai_recommendation_engine._calculate_budget_estimate(dest_data, profile)
                plan['details']['budget'] = budget
                plan['summary'] += f"💰 **Budget-Schätzung**: €{budget['total_weekly_per_person']:.0f} pro Person/Woche\n"
        
        plan['summary'] += "\nMöchten Sie Details zu einem bestimmten Aspekt oder soll ich Ihnen bei der Buchung helfen?"
        
        return plan
    
    def _handle_general_question_with_ai(self, user_id: str, message: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt allgemeine Fragen mit KI-Unterstützung"""
        message_lower = message.lower()
        
        # Spezielle Frage-Behandlung
        if 'wetter' in message_lower:
            destination = session['preferences'].get('destination')
            if destination:
                return self._handle_weather_request(user_id, {'weather_location': destination}, session)
            else:
                return {
                    'type': 'weather_help',
                    'message': 'Für welche Destination möchten Sie das Wetter wissen?',
                    'suggestions': ['Paris', 'London', 'Rom', 'Berlin', 'Empfehlungen anzeigen']
                }
        
        elif 'budget' in message_lower or 'kosten' in message_lower:
            return {
                'type': 'budget_help',
                'message': 'Ich kann Ihnen bei Budget-Fragen helfen! Was möchten Sie wissen?\n\n' +
                          '• Durchschnittliche Kosten für verschiedene Destinationen\n' +
                          '• Budget-freundliche Reiseziele\n' +
                          '• Kostenaufschlüsselung (Flug, Hotel, Aktivitäten)',
                'suggestions': [
                    'Günstige Destinationen',
                    'Budget für Paris',
                    'Budget für London',
                    'Empfehlungen basierend auf Budget'
                ]
            }
        
        elif 'beste zeit' in message_lower or 'wann reisen' in message_lower:
            destination = session['preferences'].get('destination')
            if destination:
                dest_data = self.ai_recommendation_engine.destination_database.get(destination.lower())
                if dest_data:
                    best_seasons = ', '.join([s.title() for s in dest_data['best_seasons']])
                    return {
                        'type': 'best_time',
                        'message': f'Die beste Reisezeit für {destination} ist: {best_seasons}',
                        'suggestions': [
                            f'Wetter in {destination}',
                            f'Hotels in {destination}',
                            'Weitere Empfehlungen'
                        ]
                    }
        
        # Fallback zur Standard-Fragenbehandlung
        return self._handle_standard_general_question(message, user_id, session)
    
    def _extract_preferences_from_message(self, message: str) -> Dict[str, Any]:
        """Extrahiert Präferenzen aus einer Nachricht"""
        preferences = {}
        message_lower = message.lower()
        
        # Budget-Präferenzen
        if any(word in message_lower for word in ['günstig', 'billig', 'budget', 'sparsam']):
            preferences['budget_range'] = 'budget'
        elif any(word in message_lower for word in ['luxus', 'teuer', 'premium', 'exklusiv']):
            preferences['budget_range'] = 'luxury'
        elif any(word in message_lower for word in ['mittel', 'normal', 'standard']):
            preferences['budget_range'] = 'mid-range'
        
        # Reiseart
        if any(word in message_lower for word in ['kultur', 'museen', 'geschichte', 'kunst']):
            preferences['travel_style'] = 'cultural'
        elif any(word in message_lower for word in ['entspannt', 'ruhig', 'erholung']):
            preferences['travel_style'] = 'relaxed'
        elif any(word in message_lower for word in ['aktiv', 'sport', 'abenteuer']):
            preferences['travel_style'] = 'active'
        elif any(word in message_lower for word in ['luxus', 'premium', 'exklusiv']):
            preferences['travel_style'] = 'luxury'
        
        # Gruppengröße
        if any(word in message_lower for word in ['allein', 'solo', 'einzel']):
            preferences['group_size'] = 1
        elif any(word in message_lower for word in ['paar', 'zu zweit', 'zusammen']):
            preferences['group_size'] = 2
        elif any(word in message_lower for word in ['familie', 'gruppe', 'mehrere']):
            preferences['group_size'] = 4
        
        # Jahreszeit
        if 'frühling' in message_lower:
            preferences['season_preference'] = 'spring'
        elif 'sommer' in message_lower:
            preferences['season_preference'] = 'summer'
        elif 'herbst' in message_lower:
            preferences['season_preference'] = 'autumn'
        elif 'winter' in message_lower:
            preferences['season_preference'] = 'winter'
        
        return preferences
    
    def _add_to_interaction_history(self, user_id: str, message: str):
        """Fügt Nachricht zur Interaktionshistorie hinzu"""
        if user_id not in self.interaction_history:
            self.interaction_history[user_id] = []
        
        self.interaction_history[user_id].append({
            'timestamp': datetime.now().isoformat(),
            'message': message
        })
        
        # Behalte nur die letzten 50 Interaktionen
        if len(self.interaction_history[user_id]) > 50:
            self.interaction_history[user_id] = self.interaction_history[user_id][-50:]
    
    def _initialize_user_session(self) -> Dict[str, Any]:
        """Initialisiert eine neue Benutzersession"""
        return {
            'state': self.dialog_states['greeting'],
            'preferences': {
                'destination': None,
                'start_date': None,
                'end_date': None,
                'duration': None,
                'budget': None
            },
            'interaction_count': 0,
            'last_interaction': datetime.now().isoformat()
        }
    
    def _update_session_with_entities(self, session: Dict[str, Any], entities: Dict[str, Any]):
        """Aktualisiert Session mit extrahierten Entitäten"""
        if 'destination' in entities:
            session['preferences']['destination'] = entities['destination']
        if 'start_date' in entities:
            session['preferences']['start_date'] = entities['start_date']
        if 'end_date' in entities:
            session['preferences']['end_date'] = entities['end_date']
        if 'duration' in entities:
            session['preferences']['duration'] = entities['duration']
    
    # Fallback-Methoden für Legacy-Funktionalität
    def _handle_legacy_intent(self, user_id: str, intent: str, entities: Dict[str, Any], message: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback zur ursprünglichen Intent-Behandlung"""
        # Hier können Sie die ursprüngliche Logik aus decision_logic.py einbauen
        return {
            'type': 'legacy_fallback',
            'message': 'Ich verstehe Ihre Anfrage. Lassen Sie mich Ihnen dabei helfen.',
            'suggestions': ['Empfehlungen anzeigen', 'Hotels suchen', 'Flüge suchen']
        }
    
    def _handle_standard_hotel_search(self, destination: str, hotels: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Standard Hotel-Suche ohne KI-Filterung"""
        response_message = f"Hier sind Hotels in {destination}:\n\n"
        
        for i, hotel in enumerate(hotels[:5], 1):
            response_message += f"**{i}. {hotel['name']}**\n"
            response_message += f"   💰 {hotel.get('price', 'Preis auf Anfrage')}\n"
            response_message += f"   ⭐ {hotel.get('rating', 'N/A')}\n\n"
        
        return {
            'type': 'hotels',
            'message': response_message,
            'hotels': hotels[:5],
            'destination': destination,
            'suggestions': [
                f"Flüge nach {destination} suchen",
                f"Wetter in {destination}",
                "Empfehlungen anzeigen"
            ]
        }
    
    def _handle_weather_request(self, user_id: str, entities: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt Wetteranfragen"""
        location = entities.get('weather_location') or session['preferences'].get('destination')
        
        if not location:
            return {
                'type': 'missing_location',
                'message': 'Für welche Destination möchten Sie das Wetter wissen?',
                'suggestions': ['Paris', 'London', 'Rom', 'Berlin']
            }
        
        try:
            weather = self.weather_service.get_weather(location)
            return {
                'type': 'weather',
                'message': f"🌤️ **Wetter in {location}**:\n" +
                          f"Temperatur: {weather.get('temperature', 'N/A')}°C\n" +
                          f"Beschreibung: {weather.get('description', 'N/A')}\n" +
                          f"Luftfeuchtigkeit: {weather.get('humidity', 'N/A')}%",
                'weather_data': weather,
                'location': location,
                'suggestions': [
                    f"Hotels in {location} finden",
                    f"Flüge nach {location} suchen",
                    "Empfehlungen anzeigen"
                ]
            }
        except Exception as e:
            logger.error(f"Fehler bei Wetterabfrage: {e}")
            return {
                'type': 'weather_error',
                'message': f'Entschuldigung, ich konnte das Wetter für {location} nicht abrufen.',
                'suggestions': ['Andere Destination', 'Hotels suchen', 'Empfehlungen anzeigen']
            }
    
    def _handle_standard_general_question(self, message: str, user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt allgemeine Fragen ohne spezielle KI-Logik"""
        return {
            'type': 'general_help',
            'message': 'Ich kann Ihnen bei verschiedenen Reisefragen helfen! Was möchten Sie wissen?\n\n' +
                      '• Reiseempfehlungen\n' +
                      '• Hotel- und Flugsuche\n' +
                      '• Wetterinformationen\n' +
                      '• Reiseplanung',
            'suggestions': [
                'Empfehlungen anzeigen',
                'Hotels suchen',
                'Flüge suchen',
                'Wetter abfragen'
            ]
        } 