import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from dataclasses import asdict

from enhanced_decision_logic import EnhancedDecisionLogic
from api_services.flight_service import FlightService
from api_services.hotel_service import HotelService
from api_services.weather_service import WeatherService
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
            self.flight_service = FlightService()
            self.hotel_service = HotelService()
            self.weather_service = WeatherService()
            self.rasa_handler = RasaHandler()
            
            self.decision_logic = EnhancedDecisionLogic(
                flight_service=self.flight_service,
                hotel_service=self.hotel_service,
                weather_service=self.weather_service,
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
        
        @self.app.route('/api/test/flights', methods=['GET'])
        def test_flights():
            try:
                # Teste API-Verbindung
                api_status = self.flight_service.test_api_connection()
                
                return jsonify({
                    'success': True,
                    'api_status': api_status,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error testing flight API: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
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
        
        @self.app.route('/api/ai/recommendations', methods=['POST'])
        def get_ai_recommendations():
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        'success': False,
                        'error': 'No data provided'
                    }), 400
                
                user_id = data.get('user_id', 'anonymous')
                preferences = data.get('preferences', {})
                num_recommendations = data.get('num_recommendations', 3)
                
                recommendations = self.decision_logic.ai_recommendation_engine.generate_personalized_recommendations(
                    user_id, 
                    current_preferences=preferences,
                    num_recommendations=num_recommendations
                )
                
                return jsonify({
                    'success': True,
                    'recommendations': [asdict(rec) for rec in recommendations],
                    'user_id': user_id,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error generating AI recommendations: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/ai/user-profile/<user_id>', methods=['GET'])
        def get_user_profile(user_id):
            try:
                profile = self.decision_logic.ai_recommendation_engine.user_profiles.get(user_id)
                if profile:
                    return jsonify({
                        'success': True,
                        'profile': asdict(profile),
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'User profile not found',
                        'timestamp': datetime.now().isoformat()
                    }), 404
                    
            except Exception as e:
                logger.error(f"Error getting user profile: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/ai/update-preferences', methods=['POST'])
        def update_user_preferences():
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        'success': False,
                        'error': 'No data provided'
                    }), 400
                
                user_id = data.get('user_id', 'anonymous')
                preferences = data.get('preferences', {})
                
                self.decision_logic.ai_recommendation_engine.update_user_preferences(user_id, preferences)
                
                return jsonify({
                    'success': True,
                    'message': 'User preferences updated successfully',
                    'user_id': user_id,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error updating user preferences: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
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
        app.run(debug=os.getenv('DEBUG', 'False').lower() == 'true')
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        raise

if __name__ == '__main__':
    main() 