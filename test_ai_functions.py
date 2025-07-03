#!/usr/bin/env python3
"""
Test-Skript für die KI-Funktionen des TravelGuide-Systems
Testet: Präferenz-Erkennung, KI-Empfehlungen, Entscheidungslogik
"""

import sys
import os
import json
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_decision_logic import EnhancedDecisionLogic
from ai_recommendation_engine import AIRecommendationEngine, UserPreference
from api_services.flight_service import FlightService
from api_services.hotel_service import HotelService
from api_services.weather_service import WeatherService
from rasa_bot.rasa_handler import RasaHandler

class TravelGuideTester:
    def __init__(self):
        print("🧪 TravelGuide KI-Funktionen Test")
        print("=" * 50)
        
        # Services initialisieren
        self.flight_service = FlightService()
        self.hotel_service = HotelService()
        self.weather_service = WeatherService()
        self.rasa_handler = RasaHandler()
        
        # KI-Komponenten initialisieren
        self.ai_engine = AIRecommendationEngine()
        self.decision_logic = EnhancedDecisionLogic(
            flight_service=self.flight_service,
            hotel_service=self.hotel_service,
            weather_service=self.weather_service,
            rasa_handler=self.rasa_handler
        )
        
        self.test_user_id = "test_user_123"
        self.test_results = []
    
    def run_all_tests(self):
        """Führt alle Tests aus"""
        print("\n🚀 Starte alle Tests...\n")
        
        # Test 1: Präferenz-Extraktion
        self.test_preference_extraction()
        
        # Test 2: KI-Empfehlungsmaschine
        self.test_ai_recommendation_engine()
        
        # Test 3: Intent-Erkennung
        self.test_intent_recognition()
        
        # Test 4: Vollständige Nachrichtenverarbeitung
        self.test_message_processing()
        
        # Test 5: Benutzerprofil-Management
        self.test_user_profile_management()
        
        # Ergebnisse anzeigen
        self.show_test_results()
    
    def test_preference_extraction(self):
        """Testet die Präferenz-Extraktion aus Nachrichten"""
        print("📋 Test 1: Präferenz-Extraktion")
        print("-" * 30)
        
        test_messages = [
            "Ich suche günstige Hotels für eine kulturelle Reise zu zweit im Frühling",
            "Luxus-Urlaub für die Familie im Sommer",
            "Budget: günstig, Reiseart: aktiv",
            "Gruppe: allein, Jahreszeit: Winter"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\nTest {i}: '{message}'")
            
            # Extrahiere Präferenzen
            preferences = self.decision_logic._extract_preferences_from_message(message)
            
            print(f"   Erkannte Präferenzen: {preferences}")
            
            # Bewerte Ergebnis
            if preferences:
                self.test_results.append(f"✅ Test {i}: Präferenzen erkannt")
                print(f"   ✅ Erfolgreich")
            else:
                self.test_results.append(f"❌ Test {i}: Keine Präferenzen erkannt")
                print(f"   ❌ Fehlgeschlagen")
    
    def test_ai_recommendation_engine(self):
        """Testet die KI-Empfehlungsmaschine"""
        print("\n🤖 Test 2: KI-Empfehlungsmaschine")
        print("-" * 30)
        
        # Test-Benutzerprofil erstellen
        test_preferences = {
            'budget_range': 'budget',
            'travel_style': 'cultural',
            'group_size': 2,
            'season_preference': 'spring'
        }
        
        print(f"Test-Profil: {test_preferences}")
        
        # Empfehlungen generieren
        recommendations = self.ai_engine.generate_personalized_recommendations(
            self.test_user_id,
            current_preferences=test_preferences,
            num_recommendations=3
        )
        
        print(f"\nGenerierte {len(recommendations)} Empfehlungen:")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec.destination}")
            print(f"   Confidence: {rec.confidence_score:.1%}")
            print(f"   Begründung: {rec.reasoning}")
            print(f"   Budget: €{rec.estimated_budget['total_weekly_per_person']:.0f}/Woche")
            print(f"   Aktivitäten: {', '.join(rec.activities[:3])}")
        
        if recommendations:
            self.test_results.append("✅ KI-Empfehlungsmaschine funktioniert")
        else:
            self.test_results.append("❌ KI-Empfehlungsmaschine fehlgeschlagen")
    
    def test_intent_recognition(self):
        """Testet die Intent-Erkennung"""
        print("\n🎯 Test 3: Intent-Erkennung")
        print("-" * 30)
        
        test_cases = [
            ("Meine Präferenzen ändern", "preference_collection"),
            ("Weitere Präferenzen angeben", "preference_collection"),
            ("Empfehlungen anzeigen", "recommendation_request"),
            ("Hotels in Paris finden", "search_request"),
            ("Wetter in London", "search_request"),
            ("Budget: günstig", "preference_collection")
        ]
        
        for message, expected_intent in test_cases:
            print(f"\nTest: '{message}'")
            
            # Rasa Intent
            rasa_response = self.rasa_handler.process_message(message, self.test_user_id)
            rasa_intent = rasa_response.get('intent', 'unknown')
            rasa_confidence = rasa_response.get('confidence', 0.0)
            
            # KI-gestützter Intent
            ai_intent = self.decision_logic._determine_ai_intent(message, rasa_intent, rasa_confidence)
            
            print(f"   Rasa Intent: {rasa_intent} (Confidence: {rasa_confidence:.2f})")
            print(f"   KI Intent: {ai_intent}")
            print(f"   Erwartet: {expected_intent}")
            
            if ai_intent == expected_intent:
                self.test_results.append(f"✅ Intent '{message}' korrekt erkannt")
                print(f"   ✅ Korrekt")
            else:
                self.test_results.append(f"❌ Intent '{message}' falsch erkannt")
                print(f"   ❌ Falsch")
    
    def test_message_processing(self):
        """Testet die vollständige Nachrichtenverarbeitung"""
        print("\n💬 Test 4: Vollständige Nachrichtenverarbeitung")
        print("-" * 30)
        
        test_messages = [
            "Meine Präferenzen ändern",
            "Budget: günstig",
            "Reiseart: kulturell",
            "Empfehlungen anzeigen"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\nTest {i}: '{message}'")
            
            try:
                # Vollständige Nachrichtenverarbeitung
                response = self.decision_logic.process_user_message(message, self.test_user_id)
                
                print(f"   Response Type: {response.get('type', 'unknown')}")
                print(f"   Message: {response.get('message', '')[:100]}...")
                print(f"   Suggestions: {len(response.get('suggestions', []))} Vorschläge")
                
                if response and response.get('type') != 'error':
                    self.test_results.append(f"✅ Nachrichtenverarbeitung {i} erfolgreich")
                    print(f"   ✅ Erfolgreich")
                else:
                    self.test_results.append(f"❌ Nachrichtenverarbeitung {i} fehlgeschlagen")
                    print(f"   ❌ Fehlgeschlagen")
                    
            except Exception as e:
                self.test_results.append(f"❌ Nachrichtenverarbeitung {i} Exception: {str(e)}")
                print(f"   ❌ Exception: {e}")
    
    def test_user_profile_management(self):
        """Testet das Benutzerprofil-Management"""
        print("\n👤 Test 5: Benutzerprofil-Management")
        print("-" * 30)
        
        # Profil erstellen
        initial_preferences = {
            'budget_range': 'mid-range',
            'travel_style': 'cultural'
        }
        
        print("Erstelle Benutzerprofil...")
        profile = self.ai_engine.create_user_profile(self.test_user_id, initial_preferences)
        print(f"   Erstellt: {profile}")
        
        # Profil aktualisieren
        new_preferences = {
            'budget_range': 'budget',
            'group_size': 4
        }
        
        print("\nAktualisiere Profil...")
        self.ai_engine.update_user_preferences(self.test_user_id, new_preferences)
        
        # Profil abrufen
        updated_profile = self.ai_engine.user_profiles.get(self.test_user_id)
        print(f"   Aktualisiert: {updated_profile}")
        
        # Empfehlungshistorie testen
        history = self.ai_engine.get_recommendation_history(self.test_user_id)
        print(f"   Historie vorhanden: {history is not None}")
        
        if updated_profile and history:
            self.test_results.append("✅ Benutzerprofil-Management funktioniert")
        else:
            self.test_results.append("❌ Benutzerprofil-Management fehlgeschlagen")
    
    def show_test_results(self):
        """Zeigt die Testergebnisse an"""
        print("\n" + "=" * 50)
        print("📊 TESTERGEBNISSE")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result.startswith("✅"))
        total = len(self.test_results)
        
        print(f"\nTests bestanden: {passed}/{total}")
        print(f"Erfolgsrate: {(passed/total)*100:.1f}%")
        
        print("\nDetaillierte Ergebnisse:")
        for result in self.test_results:
            print(f"  {result}")
        
        if passed == total:
            print(f"\n🎉 ALLE TESTS BESTANDEN! Die KI-Funktionen funktionieren korrekt.")
        else:
            print(f"\n⚠️  {total-passed} Test(s) fehlgeschlagen. Überprüfen Sie die Implementierung.")
        
        # Speichere Ergebnisse in Datei
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"test_results_{timestamp}.json"
        
        test_summary = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': total,
            'passed_tests': passed,
            'success_rate': (passed/total)*100,
            'results': self.test_results
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(test_summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Testergebnisse gespeichert in: {results_file}")

def main():
    """Hauptfunktion"""
    try:
        tester = TravelGuideTester()
        tester.run_all_tests()
        
    except Exception as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 