import logging
import json
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class UserPreference:
    destination_type: str  # 'city', 'beach', 'mountain', 'cultural', 'adventure'
    budget_range: str      # 'budget', 'mid-range', 'luxury'
    travel_style: str      # 'relaxed', 'active', 'cultural', 'luxury'
    group_size: int        # 1, 2, 3-5, 6+
    season_preference: str # 'spring', 'summer', 'autumn', 'winter', 'any'
    duration_preference: str # 'weekend', 'week', 'long_weekend', 'extended'

@dataclass
class TravelRecommendation:
    destination: str
    confidence_score: float
    reasoning: str
    activities: List[str]
    best_time_to_visit: str
    estimated_budget: Dict[str, float]
    accommodation_suggestions: List[str]
    transportation_suggestions: List[str]

class AIRecommendationEngine:
    def __init__(self):
        self.destination_database = self._load_destination_database()
        self.user_profiles = {}
        self.recommendation_history = {}
        
    def _load_destination_database(self) -> Dict[str, Any]:
        """Lädt die Destination-Datenbank mit detaillierten Informationen"""
        return {
            'paris': {
                'name': 'Paris',
                'country': 'Frankreich',
                'type': 'cultural',
                'best_seasons': ['spring', 'autumn'],
                'activities': ['Museen besuchen', 'Eiffelturm', 'Louvre', 'Seine-Cruise', 'Shopping'],
                'budget_range': 'mid-range',
                'travel_style': 'cultural',
                'avg_hotel_price': 150,
                'avg_flight_price': 200,
                'daily_budget': 120,
                'keywords': ['romantisch', 'kultur', 'mode', 'kunst', 'geschichte']
            },
            'london': {
                'name': 'London',
                'country': 'Großbritannien',
                'type': 'cultural',
                'best_seasons': ['spring', 'summer'],
                'activities': ['Big Ben', 'Tower Bridge', 'British Museum', 'West End Shows', 'Shopping'],
                'budget_range': 'mid-range',
                'travel_style': 'cultural',
                'avg_hotel_price': 180,
                'avg_flight_price': 180,
                'daily_budget': 140,
                'keywords': ['geschichte', 'kultur', 'shopping', 'theater', 'royal']
            },
            'rome': {
                'name': 'Rom',
                'country': 'Italien',
                'type': 'cultural',
                'best_seasons': ['spring', 'autumn'],
                'activities': ['Kolosseum', 'Vatikan', 'Trevi-Brunnen', 'Pizza essen', 'Antike Stätten'],
                'budget_range': 'mid-range',
                'travel_style': 'cultural',
                'avg_hotel_price': 130,
                'avg_flight_price': 160,
                'daily_budget': 100,
                'keywords': ['geschichte', 'antike', 'pizza', 'vatikan', 'kunst']
            },
            'barcelona': {
                'name': 'Barcelona',
                'country': 'Spanien',
                'type': 'cultural',
                'best_seasons': ['spring', 'autumn'],
                'activities': ['Sagrada Familia', 'Park Güell', 'Las Ramblas', 'Tapas essen', 'Strand'],
                'budget_range': 'mid-range',
                'travel_style': 'cultural',
                'avg_hotel_price': 120,
                'avg_flight_price': 150,
                'daily_budget': 90,
                'keywords': ['architektur', 'strand', 'tapas', 'gaudi', 'kultur']
            },
            'amsterdam': {
                'name': 'Amsterdam',
                'country': 'Niederlande',
                'type': 'cultural',
                'best_seasons': ['spring', 'summer'],
                'activities': ['Anne Frank Haus', 'Van Gogh Museum', 'Grachtenfahrt', 'Fahrrad fahren', 'Tulpenfelder'],
                'budget_range': 'mid-range',
                'travel_style': 'cultural',
                'avg_hotel_price': 140,
                'avg_flight_price': 140,
                'daily_budget': 110,
                'keywords': ['kunst', 'geschichte', 'fahrrad', 'grachten', 'tulpen']
            },
            'berlin': {
                'name': 'Berlin',
                'country': 'Deutschland',
                'type': 'cultural',
                'best_seasons': ['spring', 'summer', 'autumn'],
                'activities': ['Brandenburger Tor', 'Mauer-Museum', 'Reichstag', 'Kreuzberg', 'Techno-Clubs'],
                'budget_range': 'budget',
                'travel_style': 'cultural',
                'avg_hotel_price': 100,
                'avg_flight_price': 120,
                'daily_budget': 80,
                'keywords': ['geschichte', 'kultur', 'party', 'streetart', 'vielfalt']
            },
            'prag': {
                'name': 'Prag',
                'country': 'Tschechien',
                'type': 'cultural',
                'best_seasons': ['spring', 'autumn'],
                'activities': ['Karlsbrücke', 'Prager Burg', 'Altstadt', 'Bier trinken', 'Golem-Legende'],
                'budget_range': 'budget',
                'travel_style': 'cultural',
                'avg_hotel_price': 80,
                'avg_flight_price': 100,
                'daily_budget': 60,
                'keywords': ['geschichte', 'bier', 'architektur', 'günstig', 'mittelalter']
            },
            'wien': {
                'name': 'Wien',
                'country': 'Österreich',
                'type': 'cultural',
                'best_seasons': ['spring', 'autumn'],
                'activities': ['Schloss Schönbrunn', 'Stephansdom', 'Kaffeehäuser', 'Wiener Walzer', 'Museen'],
                'budget_range': 'mid-range',
                'travel_style': 'cultural',
                'avg_hotel_price': 130,
                'avg_flight_price': 140,
                'daily_budget': 100,
                'keywords': ['musik', 'kaffee', 'imperial', 'kultur', 'eleganz']
            },
            'budapest': {
                'name': 'Budapest',
                'country': 'Ungarn',
                'type': 'cultural',
                'best_seasons': ['spring', 'autumn'],
                'activities': ['Parlament', 'Thermalbäder', 'Donau-Cruise', 'Gulasch essen', 'Burgberg'],
                'budget_range': 'budget',
                'travel_style': 'cultural',
                'avg_hotel_price': 70,
                'avg_flight_price': 90,
                'daily_budget': 50,
                'keywords': ['thermalbäder', 'gulasch', 'donau', 'günstig', 'geschichte']
            },
            'krakau': {
                'name': 'Krakau',
                'country': 'Polen',
                'type': 'cultural',
                'best_seasons': ['spring', 'autumn'],
                'activities': ['Marktplatz', 'Wawel-Burg', 'Auschwitz-Gedenkstätte', 'Pierogi essen', 'Jüdisches Viertel'],
                'budget_range': 'budget',
                'travel_style': 'cultural',
                'avg_hotel_price': 60,
                'avg_flight_price': 80,
                'daily_budget': 40,
                'keywords': ['geschichte', 'pierogi', 'günstig', 'kultur', 'mittelalter']
            }
        }
    
    def create_user_profile(self, user_id: str, preferences: Dict[str, Any]) -> UserPreference:
        """Erstellt ein Benutzerprofil basierend auf gesammelten Präferenzen"""
        profile = UserPreference(
            destination_type=preferences.get('destination_type', 'cultural'),
            budget_range=preferences.get('budget_range', 'mid-range'),
            travel_style=preferences.get('travel_style', 'cultural'),
            group_size=preferences.get('group_size', 2),
            season_preference=preferences.get('season_preference', 'any'),
            duration_preference=preferences.get('duration_preference', 'week')
        )
        
        self.user_profiles[user_id] = profile
        logger.info(f"Benutzerprofil für {user_id} erstellt: {asdict(profile)}")
        return profile
    
    def update_user_preferences(self, user_id: str, new_preferences: Dict[str, Any]):
        """Aktualisiert Benutzerpräferenzen basierend auf Interaktionen"""
        if user_id not in self.user_profiles:
            self.create_user_profile(user_id, new_preferences)
        else:
            profile = self.user_profiles[user_id]
            
            # Aktualisiere nur die angegebenen Präferenzen
            for key, value in new_preferences.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            
            logger.info(f"Benutzerpräferenzen für {user_id} aktualisiert")
    
    def generate_personalized_recommendations(self, user_id: str, 
                                           current_preferences: Dict[str, Any] = None,
                                           num_recommendations: int = 3) -> List[TravelRecommendation]:
        """Generiert personalisierte Reiseempfehlungen basierend auf Benutzerprofil"""
        
        # Aktualisiere Benutzerprofil falls neue Präferenzen vorhanden
        if current_preferences:
            self.update_user_preferences(user_id, current_preferences)
        
        if user_id not in self.user_profiles:
            # Fallback: Erstelle Standardprofil
            self.create_user_profile(user_id, {})
        
        profile = self.user_profiles[user_id]
        recommendations = []
        
        # Bewerte alle Destinationen basierend auf Benutzerprofil
        destination_scores = {}
        
        for dest_key, dest_data in self.destination_database.items():
            score = self._calculate_destination_score(dest_data, profile)
            destination_scores[dest_key] = score
        
        # Sortiere nach Score und wähle die besten
        sorted_destinations = sorted(destination_scores.items(), 
                                   key=lambda x: x[1], reverse=True)
        
        for i, (dest_key, score) in enumerate(sorted_destinations[:num_recommendations]):
            dest_data = self.destination_database[dest_key]
            
            recommendation = TravelRecommendation(
                destination=dest_data['name'],
                confidence_score=score,
                reasoning=self._generate_reasoning(dest_data, profile),
                activities=dest_data['activities'][:5],  # Top 5 Aktivitäten
                best_time_to_visit=self._get_best_time_to_visit(dest_data, profile),
                estimated_budget=self._calculate_budget_estimate(dest_data, profile),
                accommodation_suggestions=self._get_accommodation_suggestions(dest_data, profile),
                transportation_suggestions=self._get_transportation_suggestions(dest_data, profile)
            )
            
            recommendations.append(recommendation)
        
        # Speichere Empfehlungen in Historie
        self.recommendation_history[user_id] = {
            'timestamp': datetime.now().isoformat(),
            'recommendations': [asdict(rec) for rec in recommendations]
        }
        
        logger.info(f"Generierte {len(recommendations)} Empfehlungen für Benutzer {user_id}")
        return recommendations
    
    def _calculate_destination_score(self, dest_data: Dict[str, Any], profile: UserPreference) -> float:
        """Berechnet einen Score für eine Destination basierend auf Benutzerprofil"""
        score = 0.0
        
        # Destination Type Match (30% Gewichtung)
        if dest_data['type'] == profile.destination_type:
            score += 0.3
        
        # Budget Match (25% Gewichtung)
        if dest_data['budget_range'] == profile.budget_range:
            score += 0.25
        elif (profile.budget_range == 'budget' and dest_data['budget_range'] == 'mid-range') or \
             (profile.budget_range == 'luxury' and dest_data['budget_range'] == 'mid-range'):
            score += 0.15
        
        # Travel Style Match (20% Gewichtung)
        if dest_data['travel_style'] == profile.travel_style:
            score += 0.2
        
        # Season Match (15% Gewichtung)
        if profile.season_preference == 'any' or profile.season_preference in dest_data['best_seasons']:
            score += 0.15
        
        # Zufällige Variation für Vielfalt (10% Gewichtung)
        score += random.uniform(0, 0.1)
        
        return min(score, 1.0)  # Maximal 1.0
    
    def _generate_reasoning(self, dest_data: Dict[str, Any], profile: UserPreference) -> str:
        """Generiert eine Begründung für die Empfehlung"""
        reasons = []
        
        if dest_data['type'] == profile.destination_type:
            reasons.append(f"Perfekt für {profile.destination_type}-Liebhaber")
        
        if dest_data['budget_range'] == profile.budget_range:
            reasons.append(f"Entspricht Ihrem {profile.budget_range}-Budget")
        
        if dest_data['travel_style'] == profile.travel_style:
            reasons.append(f"Ideal für {profile.travel_style}-Reisende")
        
        if profile.season_preference in dest_data['best_seasons']:
            reasons.append(f"Beste Reisezeit in Ihrer bevorzugten Jahreszeit")
        
        # Fallback-Begründung
        if not reasons:
            reasons.append(f"Beliebte Destination mit vielfältigen Aktivitäten")
        
        return ". ".join(reasons) + "."
    
    def _get_best_time_to_visit(self, dest_data: Dict[str, Any], profile: UserPreference) -> str:
        """Bestimmt die beste Reisezeit basierend auf Profil und Destination"""
        if profile.season_preference != 'any':
            return f"Beste Zeit: {profile.season_preference.title()}"
        
        seasons = dest_data['best_seasons']
        if len(seasons) == 1:
            return f"Beste Zeit: {seasons[0].title()}"
        else:
            return f"Beste Zeit: {', '.join([s.title() for s in seasons])}"
    
    def _calculate_budget_estimate(self, dest_data: Dict[str, Any], profile: UserPreference) -> Dict[str, float]:
        """Berechnet Budget-Schätzung basierend auf Gruppengröße und Dauer"""
        base_daily = dest_data['daily_budget']
        group_size = profile.group_size
        
        # Anpassung für Gruppengröße (Rabatte für größere Gruppen)
        if group_size >= 4:
            daily_per_person = base_daily * 0.8
        elif group_size >= 2:
            daily_per_person = base_daily * 0.9
        else:
            daily_per_person = base_daily
        
        return {
            'hotel_per_night': dest_data['avg_hotel_price'] * group_size,
            'flight_per_person': dest_data['avg_flight_price'],
            'daily_per_person': daily_per_person,
            'total_weekly_per_person': (daily_per_person * 7) + dest_data['avg_flight_price']
        }
    
    def _get_accommodation_suggestions(self, dest_data: Dict[str, Any], profile: UserPreference) -> List[str]:
        """Generiert Unterkunftsvorschläge basierend auf Budget und Stil"""
        suggestions = []
        
        if profile.budget_range == 'budget':
            suggestions.extend(['Hostel', 'Pension', 'Günstiges Hotel'])
        elif profile.budget_range == 'mid-range':
            suggestions.extend(['3-4 Sterne Hotel', 'Apartment', 'Boutique Hotel'])
        else:  # luxury
            suggestions.extend(['5 Sterne Hotel', 'Luxus Apartment', 'Boutique Hotel'])
        
        return suggestions[:3]
    
    def _get_transportation_suggestions(self, dest_data: Dict[str, Any], profile: UserPreference) -> List[str]:
        """Generiert Transportvorschläge"""
        return ['Öffentliche Verkehrsmittel', 'Fahrrad', 'Zu Fuß erkunden']
    
    def get_recommendation_history(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Gibt die Empfehlungshistorie eines Benutzers zurück"""
        return self.recommendation_history.get(user_id)
    
    def analyze_user_behavior(self, user_id: str, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analysiert Benutzerverhalten für bessere Personalisierung"""
        analysis = {
            'preferred_destinations': [],
            'common_intents': {},
            'budget_preferences': {},
            'travel_patterns': {}
        }
        
        # Analysiere Interaktionen
        for interaction in interactions:
            intent = interaction.get('intent', 'unknown')
            analysis['common_intents'][intent] = analysis['common_intents'].get(intent, 0) + 1
            
            # Extrahiere Budget-Informationen
            if 'budget' in interaction.get('message', '').lower():
                # Einfache Budget-Erkennung
                pass
        
        return analysis 