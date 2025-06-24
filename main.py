import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from decision_logic import TravelGuideDecisionLogic
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
            
            self.decision_logic = TravelGuideDecisionLogic(
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