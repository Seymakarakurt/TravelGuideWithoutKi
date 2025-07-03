import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import random
import re

logger = logging.getLogger(__name__)

class AIEnhancements:
    """KI-gestützte Erweiterungen für personalisierte Reiseempfehlungen"""
    
    def __init__(self):
        self.travel_patterns = {
            'budget': {
                'keywords': ['günstig', 'billig', 'budget', 'sparen', 'preiswert'],
                'destinations': ['Prag', 'Budapest', 'Krakau', 'Lissabon', 'Porto', 'Bratislava'],
                'activities': ['kostenlose Sehenswürdigkeiten', 'öffentliche Verkehrsmittel', 'lokale Märkte'],
                'accommodation': ['Hostel', 'Pension', 'Gästehaus']
            },
            'luxury': {
                'keywords': ['luxus', 'teuer', 'premium', '5 sterne', 'exklusiv'],
                'destinations': ['Paris', 'London', 'Rom', 'Venedig', 'Florenz', 'Monaco'],
                'activities': ['Premium-Restaurants', 'exklusive Touren', 'Luxus-Shopping'],
                'accommodation': ['5-Sterne Hotel', 'Boutique Hotel', 'Resort']
            },
            'adventure': {
                'keywords': ['abenteuer', 'wanderung', 'aktiv', 'outdoor', 'natur'],
                'destinations': ['Norwegen', 'Island', 'Schweiz', 'Österreich', 'Neuseeland'],
                'activities': ['Wanderungen', 'Klettern', 'Rafting', 'Skifahren'],
                'accommodation': ['Berghütte', 'Camping', 'Eco-Lodge']
            },
            'culture': {
                'keywords': ['kultur', 'museum', 'geschichte', 'kunst', 'architektur'],
                'destinations': ['Florenz', 'Wien', 'Athen', 'Istanbul', 'Prag'],
                'activities': ['Museen besuchen', 'historische Sehenswürdigkeiten', 'Kulturveranstaltungen'],
                'accommodation': ['Kultur-Hotel', 'historisches Hotel', 'Boutique Hotel']
            },
            'relaxation': {
                'keywords': ['entspannung', 'wellness', 'ruhig', 'erholung', 'spa'],
                'destinations': ['Bali', 'Malediven', 'Seychellen', 'Griechenland', 'Italien'],
                'activities': ['Wellness-Angebote', 'entspannende Spaziergänge', 'ruhige Cafés'],
                'accommodation': ['Wellness-Hotel', 'Spa-Resort', 'ruhiges Hotel']
            }
        }
        
        self.seasonal_recommendations = {
            'winter': ['Skifahren', 'Weihnachtsmärkte', 'Thermalbäder', 'Winterwanderungen'],
            'spring': ['Blütenfeste', 'Frühlingswanderungen', 'Gartenbesuche', 'Outdoor-Aktivitäten'],
            'summer': ['Strandurlaub', 'Wassersport', 'Festivals', 'Sommeraktivitäten'],
            'autumn': ['Weinlese', 'Herbstwanderungen', 'Kulturfestivals', 'Gemütlichkeit']
        }
    
    def analyze_user_preferences(self, message: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Analysiert Benutzerpräferenzen aus Nachrichten und Konversationshistorie"""
        preferences = {
            'travel_style': None,
            'budget_range': None,
            'group_type': 'solo',
            'preferred_activities': [],
            'seasonal_preferences': [],
            'interaction_style': 'direct'
        }
        
        message_lower = message.lower()
        
        # Reiseart erkennen
        for style, pattern in self.travel_patterns.items():
            if any(keyword in message_lower for keyword in pattern['keywords']):
                preferences['travel_style'] = style
                break
        
        # Budget-Präferenzen
        if any(word in message_lower for word in ['günstig', 'billig', 'sparen']):
            preferences['budget_range'] = 'low'
        elif any(word in message_lower for word in ['teuer', 'luxus', 'premium']):
            preferences['budget_range'] = 'high'
        else:
            preferences['budget_range'] = 'medium'
        
        # Gruppentyp erkennen
        if any(word in message_lower for word in ['familie', 'kinder', 'kind']):
            preferences['group_type'] = 'family'
        elif any(word in message_lower for word in ['paar', 'zusammen', 'romantisch']):
            preferences['group_type'] = 'couple'
        elif any(word in message_lower for word in ['geschäft', 'business', 'arbeit']):
            preferences['group_type'] = 'business'
        
        # Interaktionsstil basierend auf Nachrichtenlänge
        message_length = len(message.split())
        if message_length > 20:
            preferences['interaction_style'] = 'detailed'
        elif message_length > 10:
            preferences['interaction_style'] = 'exploratory'
        else:
            preferences['interaction_style'] = 'direct'
        
        return preferences
    
    def generate_personalized_destinations(self, preferences: Dict[str, Any], 
                                         last_searches: List[str] = None) -> List[str]:
        """Generiert personalisierte Reiseziele basierend auf Präferenzen"""
        destinations = []
        
        # Basierend auf Reiseart
        if preferences.get('travel_style'):
            style_destinations = self.travel_patterns[preferences['travel_style']]['destinations']
            destinations.extend(style_destinations[:3])
        
        # Basierend auf Suchhistorie
        if last_searches:
            for search in last_searches[-2:]:
                destinations.append(f"Weitere Optionen in {search.title()}")
        
        # Basierend auf Gruppentyp
        if preferences.get('group_type') == 'family':
            family_destinations = ['Disneyland Paris', 'Legoland', 'Familienparks']
            destinations.extend(family_destinations[:2])
        elif preferences.get('group_type') == 'couple':
            romantic_destinations = ['Venedig', 'Paris', 'Santorini', 'Bruges']
            destinations.extend(romantic_destinations[:2])
        
        return list(set(destinations))[:5]  # Entferne Duplikate und begrenze auf 5
    
    def generate_contextual_suggestions(self, context: str, preferences: Dict[str, Any], 
                                      current_destination: str = None) -> List[str]:
        """Generiert kontextuelle Vorschläge basierend auf aktueller Situation"""
        suggestions = []
        
        if context == 'greeting':
            if preferences.get('travel_style') == 'budget':
                suggestions = [
                    'Günstige Hotels in Barcelona',
                    'Budget-Reise nach Prag',
                    'Preiswerte Flüge nach Budapest'
                ]
            elif preferences.get('travel_style') == 'luxury':
                suggestions = [
                    'Luxus-Hotels in Paris',
                    'Premium-Flüge nach London',
                    '5-Sterne Hotels in Rom'
                ]
            else:
                suggestions = [
                    'Hotels in Paris finden',
                    'Flüge nach London',
                    'Wetter in Rom abfragen'
                ]
        
        elif context == 'post_search':
            if current_destination:
                suggestions = [
                    f'Wetter in {current_destination.title()} abfragen',
                    f'Flüge nach {current_destination.title()}',
                    f'Weitere Hotels in {current_destination.title()}',
                    'Reiseplan erstellen'
                ]
        
        elif context == 'incomplete_plan':
            if preferences.get('travel_style') == 'budget':
                suggestions.extend(['Günstige Hotels in Prag', 'Budget-Reise nach Budapest'])
            elif preferences.get('travel_style') == 'luxury':
                suggestions.extend(['Luxus-Hotels in Paris', 'Premium-Reise nach London'])
            else:
                suggestions.extend(['Hotels in Paris', 'Flüge nach Rom'])
        
        # Immer "Alles zurücksetzen" hinzufügen
        if 'Alles zurücksetzen' not in suggestions:
            suggestions.append('Alles zurücksetzen')
        
        return suggestions[:5]
    
    def create_intelligent_response(self, intent: str, preferences: Dict[str, Any], 
                                  session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt intelligente Antworten basierend auf Benutzerprofil"""
        response = {
            'personalized_message': '',
            'suggestions': [],
            'ai_insights': []
        }
        
        # Personalisierte Nachrichten basierend auf Reiseart
        if preferences.get('travel_style') == 'budget':
            response['personalized_message'] = "Ich helfe Ihnen dabei, eine günstige Reise zu finden!"
        elif preferences.get('travel_style') == 'luxury':
            response['personalized_message'] = "Ich suche nach Premium-Optionen für Ihre Reise!"
        elif preferences.get('travel_style') == 'adventure':
            response['personalized_message'] = "Lassen Sie uns ein Abenteuer planen!"
        elif preferences.get('travel_style') == 'culture':
            response['personalized_message'] = "Ich helfe Ihnen dabei, die Kultur zu erleben!"
        elif preferences.get('travel_style') == 'relaxation':
            response['personalized_message'] = "Lassen Sie uns eine entspannende Reise planen!"
        
        # KI-Insights basierend auf Suchhistorie
        if session_data.get('last_searches'):
            recent_searches = session_data['last_searches'][-2:]
            response['ai_insights'].append(
                f"Basierend auf Ihren vorherigen Reisen nach {', '.join(recent_searches)}"
            )
        
        # Personalisierte Empfehlungen basierend auf Gruppentyp
        if preferences.get('group_type') == 'family':
            response['ai_insights'].append("Familienfreundliche Optionen empfohlen")
        elif preferences.get('group_type') == 'couple':
            response['ai_insights'].append("Romantische Aktivitäten empfohlen")
        elif preferences.get('group_type') == 'business':
            response['ai_insights'].append("Business-freundliche Optionen empfohlen")
        
        return response
    
    def estimate_travel_budget(self, preferences: Dict[str, Any], 
                             destination: str = None, duration: int = 7) -> Dict[str, Any]:
        """Schätzt das Reisebudget basierend auf Präferenzen"""
        base_budget = 500  # Basis-Budget pro Person pro Woche
        
        # Anpassung basierend auf Reiseart
        if preferences.get('travel_style') == 'budget':
            base_budget *= 0.6
        elif preferences.get('travel_style') == 'luxury':
            base_budget *= 2.5
        elif preferences.get('travel_style') == 'adventure':
            base_budget *= 1.2
        elif preferences.get('travel_style') == 'culture':
            base_budget *= 0.9
        elif preferences.get('travel_style') == 'relaxation':
            base_budget *= 1.1
        
        # Anpassung basierend auf Gruppentyp
        travelers = 1
        if preferences.get('group_type') == 'family':
            travelers = 4
            base_budget *= 1.5
        elif preferences.get('group_type') == 'couple':
            travelers = 2
            base_budget *= 1.3
        elif preferences.get('group_type') == 'business':
            base_budget *= 1.4
        
        # Anpassung basierend auf Dauer
        total_budget = base_budget * (duration / 7) * travelers
        
        return {
            'min_budget': int(total_budget * 0.8),
            'max_budget': int(total_budget * 1.3),
            'currency': 'EUR',
            'per_person': int(total_budget / travelers),
            'breakdown': {
                'accommodation': int(total_budget * 0.4),
                'transportation': int(total_budget * 0.3),
                'activities': int(total_budget * 0.2),
                'food': int(total_budget * 0.1)
            }
        }
    
    def generate_seasonal_recommendations(self, current_month: int = None) -> List[str]:
        """Generiert saisonale Empfehlungen"""
        if current_month is None:
            current_month = datetime.now().month
        
        if current_month in [12, 1, 2]:
            season = 'winter'
        elif current_month in [3, 4, 5]:
            season = 'spring'
        elif current_month in [6, 7, 8]:
            season = 'summer'
        else:
            season = 'autumn'
        
        return self.seasonal_recommendations.get(season, [])
    
    def analyze_conversation_context(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Analysiert den Konversationskontext für bessere Empfehlungen"""
        context = {
            'conversation_length': len(conversation_history),
            'user_experience_level': 'beginner',
            'preferred_topics': [],
            'interaction_frequency': 'low',
            'satisfaction_indicators': []
        }
        
        if len(conversation_history) > 10:
            context['user_experience_level'] = 'expert'
        elif len(conversation_history) > 5:
            context['user_experience_level'] = 'intermediate'
        
        # Analysiere bevorzugte Themen
        topics = []
        for entry in conversation_history:
            message = entry.get('message', '').lower()
            if 'hotel' in message:
                topics.append('accommodation')
            elif 'flug' in message:
                topics.append('transportation')
            elif 'wetter' in message:
                topics.append('weather')
            elif 'aktivität' in message:
                topics.append('activities')
        
        context['preferred_topics'] = list(set(topics))
        
        return context 