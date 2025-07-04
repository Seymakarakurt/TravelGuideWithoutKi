import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from decision_logic import TravelGuideDecisionLogic
from api_services.hotel_service import HotelService
from api_services.weather_service import WeatherService
from api_services.openrouter_service import OpenRouterService
from rasa_bot.rasa_handler import RasaHandler

load_dotenv('config.env')

logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('travelguide.log')
    ]
)

logger = logging.getLogger(__name__)

class TravelGuideApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'travelguide-secret-key-2024')
        
        self._initialize_services()
        self._setup_routes()
        
        logger.info("TravelGuide application initialized successfully")
    
    def _initialize_services(self):
        try:
            self.hotel_service = HotelService()
            self.weather_service = WeatherService()
            self.openrouter_service = OpenRouterService()
            self.rasa_handler = RasaHandler()
            
            self.decision_logic = TravelGuideDecisionLogic(
                hotel_service=self.hotel_service,
                weather_service=self.weather_service,
                openrouter_service=self.openrouter_service,
                rasa_handler=self.rasa_handler
            )
            
            logger.info("All services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
    
    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.app.route('/api/chat', methods=['POST'])
        def chat_endpoint():
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        'success': False,
                        'error': 'No data provided'
                    }), 400
                
                message = data.get('message', '').strip()
                user_id = data.get('user_id', 'anonymous')
                
                if not message:
                    return jsonify({
                        'success': False,
                        'error': 'Empty message'
                    }), 400
                
                logger.info(f"Nachricht von Benutzer {user_id}: {message}")
                
                response = self.decision_logic.process_user_message(message, user_id)
                
                return jsonify({
                    'success': True,
                    'response': response
                })
                
            except Exception as e:
                logger.error(f"Error processing chat message: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Internal server error'
                }), 500
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            })
        

        
        @self.app.route('/api/test/hotels', methods=['GET'])
        def test_hotels():
            try:
                # Teste Hotel-Webscraping
                location = request.args.get('location', 'Berlin')
                hotels = self.hotel_service.search_hotels(location=location)
                
                return jsonify({
                    'success': True,
                    'location': location,
                    'hotels_found': len(hotels),
                    'hotels': hotels[:3],  # Nur die ersten 3 Hotels
                    'cache_info': {
                        'cached_entries': len(self.hotel_service.price_cache),
                        'cache_file': self.hotel_service.cache_file
                    },
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error testing hotel API: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/test/hotels/scraping', methods=['GET'])
        def test_hotel_scraping():
            try:
                # Teste direktes Webscraping ohne Cache
                location = request.args.get('location', 'Berlin')
                
                # Cache löschen für Test
                self.hotel_service.clear_cache()
                
                # Direktes Webscraping testen
                hotels = self.hotel_service.search_hotels(location=location)
                
                return jsonify({
                    'success': True,
                    'location': location,
                    'hotels_found': len(hotels),
                    'hotels': hotels[:5],  # Zeige alle gefundenen Hotels
                    'scraping_test': True,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error testing hotel scraping: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/test/hotels/debug', methods=['GET'])
        def test_hotel_debug():
            try:
                # Teste Debug-Funktionalität
                location = request.args.get('location', 'Berlin')
                
                # Cache löschen für Test
                self.hotel_service.clear_cache()
                
                # Debug-Webscraping testen
                hotels = self.hotel_service.search_hotels(location=location)
                
                return jsonify({
                    'success': True,
                    'location': location,
                    'hotels_found': len(hotels),
                    'hotels': hotels[:3],  # Zeige die ersten 3 Hotels
                    'debug_mode': True,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error testing hotel debug: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/hotels/cache', methods=['GET'])
        def get_hotel_cache():
            try:
                location = request.args.get('location', '')
                
                if location:
                    # Zeige gecachte Hotels für einen spezifischen Ort
                    cached_hotels = self.hotel_service.get_cached_prices(location)
                    return jsonify({
                        'success': True,
                        'location': location,
                        'cached_hotels': cached_hotels,
                        'count': len(cached_hotels)
                    })
                else:
                    # Zeige alle Cache-Einträge
                    return jsonify({
                        'success': True,
                        'cache_entries': len(self.hotel_service.price_cache),
                        'cache_keys': list(self.hotel_service.price_cache.keys()),
                        'cache_file': self.hotel_service.cache_file
                    })
                
            except Exception as e:
                logger.error(f"Error getting hotel cache: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/hotels/cache/clear', methods=['POST'])
        def clear_hotel_cache():
            try:
                self.hotel_service.clear_cache()
                return jsonify({
                    'success': True,
                    'message': 'Hotel-Cache erfolgreich gelöscht'
                })
                
            except Exception as e:
                logger.error(f"Error clearing hotel cache: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # OpenRouter API Endpunkte
        @self.app.route('/api/openrouter/test', methods=['GET'])
        def test_openrouter():
            try:
                test_result = self.openrouter_service.test_connection()
                return jsonify({
                    'success': True,
                    'test_result': test_result,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error testing OpenRouter: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/openrouter/models', methods=['GET'])
        def get_openrouter_models():
            try:
                models = self.openrouter_service.get_available_models()
                return jsonify({
                    'success': True,
                    'models': models,
                    'count': len(models),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error getting OpenRouter models: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/openrouter/generate', methods=['POST'])
        def generate_ai_response():
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        'success': False,
                        'error': 'No data provided'
                    }), 400
                
                message = data.get('message', '').strip()
                context = data.get('context', '')
                model = data.get('model', None)
                max_tokens = data.get('max_tokens', 1000)
                temperature = data.get('temperature', 0.7)
                
                if not message:
                    return jsonify({
                        'success': False,
                        'error': 'Empty message'
                    }), 400
                
                logger.info(f"OpenRouter Anfrage: {message[:50]}...")
                
                response = self.openrouter_service.generate_response(
                    message=message,
                    context=context,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                return jsonify({
                    'success': True,
                    'response': response
                })
                
            except Exception as e:
                logger.error(f"Error generating AI response: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Internal server error'
                }), 500
    
    def run(self, host='0.0.0.0', port=5001, debug=False):
        logger.info("TravelGuide wird gestartet...")
        logger.info(f"Web-Interface verfügbar unter: http://localhost:{port}")
        self.app.run(
            host=host,
            port=port,
            debug=debug
        )

def main():
    try:
        app = TravelGuideApp()
        app.run(port=5001, debug=os.getenv('DEBUG', 'False').lower() == 'true')
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        raise

if __name__ == '__main__':
    main() 