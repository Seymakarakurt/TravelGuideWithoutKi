import os
import requests
import logging
from typing import Dict, Any, Optional, List
import json

logger = logging.getLogger(__name__)

class OpenRouterService:
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1"
        self.default_model = os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet')
        
        if not self.api_key:
            logger.warning("OpenRouter API Key nicht gefunden")
    
    def generate_response(self, 
                         message: str, 
                         context: str = "", 
                         model: Optional[str] = None,
                         max_tokens: int = 1000,
                         temperature: float = 0.7) -> Dict[str, Any]:
        """
        Generiert eine Antwort mit OpenRouter API
        
        Args:
            message: Die Benutzer-Nachricht
            context: Zusätzlicher Kontext für die KI
            model: Das zu verwendende Modell (optional)
            max_tokens: Maximale Anzahl Tokens
            temperature: Kreativität (0.0 = deterministisch, 1.0 = sehr kreativ)
        
        Returns:
            Dict mit der Antwort und Metadaten
        """
        try:
            if not self.api_key:
                return self._get_fallback_response(message)
            
            # Verwende Standardmodell falls keines angegeben
            model_to_use = model or self.default_model
            
            # Erstelle den vollständigen Prompt
            full_prompt = self._create_prompt(message, context)
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://travelguide-app.com',
                'X-Title': 'TravelGuide AI Assistant'
            }
            
            payload = {
                'model': model_to_use,
                'messages': [
                    {
                        'role': 'system',
                        'content': self._get_system_prompt()
                    },
                    {
                        'role': 'user',
                        'content': full_prompt
                    }
                ],
                'max_tokens': max_tokens,
                'temperature': temperature,
                'stream': False
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extrahiere die Antwort
            ai_response = data['choices'][0]['message']['content']
            usage = data.get('usage', {})
            
            return {
                'success': True,
                'response': ai_response,
                'model': model_to_use,
                'usage': {
                    'prompt_tokens': usage.get('prompt_tokens', 0),
                    'completion_tokens': usage.get('completion_tokens', 0),
                    'total_tokens': usage.get('total_tokens', 0)
                },
                'timestamp': data.get('created', None)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API Fehler: {e}")
            return self._get_fallback_response(message)
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei OpenRouter API: {e}")
            return self._get_fallback_response(message)
    
    def _create_prompt(self, message: str, context: str = "") -> str:
        """Erstellt einen strukturierten Prompt für die KI"""
        prompt_parts = []
        
        if context:
            prompt_parts.append(f"Kontext: {context}")
        
        prompt_parts.append(f"Benutzer-Nachricht: {message}")
        
        return "\n\n".join(prompt_parts)
    
    def _get_system_prompt(self) -> str:
        """Gibt den System-Prompt für die KI zurück"""
        return """Du bist ein hilfreicher Reiseassistent für die TravelGuide-Anwendung. 

Deine Hauptaufgaben:
1. Beantworte Fragen zu Reisezielen, Hotels, Wetter und Reiseplanung
2. Gib hilfreiche und präzise Antworten auf Deutsch
3. Sei freundlich und professionell
4. Wenn du keine spezifischen Informationen hast, gib allgemeine Reisetipps
5. Antworte in einem natürlichen, gesprächigen Ton

Wichtige Regeln:
- Antworte immer auf Deutsch
- Sei hilfreich und informativ
- Gib praktische Reisetipps
- Wenn du unsicher bist, sage das ehrlich
- Halte Antworten prägnant aber informativ"""
    
    def _get_fallback_response(self, message: str) -> Dict[str, Any]:
        """Fallback-Antwort wenn API nicht verfügbar ist"""
        return {
            'success': False,
            'response': f"Entschuldigung, ich kann momentan nicht auf Ihre Nachricht '{message}' antworten. Bitte versuchen Sie es später erneut.",
            'model': 'fallback',
            'usage': {
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0
            },
            'timestamp': None,
            'error': 'API nicht verfügbar'
        }
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Gibt verfügbare Modelle zurück"""
        try:
            if not self.api_key:
                return []
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            return data.get('data', [])
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der verfügbaren Modelle: {e}")
            return []
    
    def test_connection(self) -> Dict[str, Any]:
        """Testet die Verbindung zur OpenRouter API"""
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'Kein API-Key konfiguriert'
                }
            
            # Teste mit einer einfachen Anfrage
            test_response = self.generate_response(
                message="Hallo, das ist ein Test.",
                max_tokens=50,
                temperature=0.1
            )
            
            return {
                'success': test_response['success'],
                'model': test_response.get('model', 'unbekannt'),
                'response_length': len(test_response.get('response', '')),
                'error': test_response.get('error', None)
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Testen der OpenRouter-Verbindung: {e}")
            return {
                'success': False,
                'error': str(e)
            } 