import os
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class WeatherService:
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        self.base_url = "http://api.openweathermap.org/data/2.5"
        
        if not self.api_key:
            logger.warning("OpenWeatherMap API Key nicht gefunden")
    
    def get_weather(self, location: str, date: Optional[str] = None) -> Dict[str, Any]:
        try:
            if not self.api_key:
                return self._get_fallback_weather(location)
            

            coords = self._get_coordinates(location)
            if not coords:
                return self._get_fallback_weather(location)
            
            lat, lon = coords
            

            weather_data = self._get_current_weather(lat, lon)
            if not weather_data:
                return self._get_fallback_weather(location)
            

            if date:
                forecast = self._get_forecast(lat, lon, date)
                if forecast:
                    weather_data.update(forecast)
            
            return weather_data
            
        except Exception as e:
            logger.error(f"Fehler bei Wetterabfrage: {e}")
            return self._get_fallback_weather(location)
    
    def _get_coordinates(self, location: str) -> Optional[tuple]:
        try:
            url = f"http://api.openweathermap.org/geo/1.0/direct"
            params = {
                'q': location,
                'limit': 1,
                'appid': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data:
                return (data[0]['lat'], data[0]['lon'])
            
            return None
            
        except Exception as e:
            logger.error(f"Fehler bei Geocoding: {e}")
            return None
    
    def _get_current_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',  
                'lang': 'de'        
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'temperature': round(data['main']['temp']),
                'feels_like': round(data['main']['feels_like']),
                'humidity': data['main']['humidity'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'wind_speed': round(data['wind']['speed'] * 3.6, 1),
                'pressure': data['main']['pressure'],
                'visibility': data.get('visibility', 10000) / 1000,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Fehler bei aktueller Wetterabfrage: {e}")
            return None
    
    def _get_forecast(self, lat: float, lon: float, target_date: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'de'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            

            try:
                target_dt = datetime.strptime(target_date, "%d.%m.%Y")
            except:
                try:
                    target_dt = datetime.strptime(target_date, "%d.%m")

                    target_dt = target_dt.replace(year=datetime.now().year + 1)
                except:
                    return None
            
            for item in data['list']:
                forecast_dt = datetime.fromtimestamp(item['dt'])
                if forecast_dt.date() == target_dt.date():
                    return {
                        'forecast_temperature': round(item['main']['temp']),
                        'forecast_description': item['weather'][0]['description'],
                        'forecast_icon': item['weather'][0]['icon'],
                        'forecast_date': target_date
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Fehler bei Wettervorhersage: {e}")
            return None
    
    def _get_fallback_weather(self, location: str) -> Dict[str, Any]:
        return {
            'temperature': 20,
            'feels_like': 22,
            'humidity': 65,
            'description': 'Leicht bewölkt',
            'icon': '02d',
            'wind_speed': 12.5,
            'pressure': 1013,
            'visibility': 10.0,
            'timestamp': datetime.now().isoformat(),
            'note': f'Wetterdaten für {location} (Simulation - API nicht verfügbar)'
        }
    
    def get_weather_summary(self, location: str) -> str:
        weather = self.get_weather(location)
        
        if 'note' in weather:
            return f"Wetter in {location}: {weather['description']} bei {weather['temperature']}°C (Simulation)"
        
        summary = f"Wetter in {location}:\n"
        summary += f"• Temperatur: {weather['temperature']}°C (gefühlt {weather['feels_like']}°C)\n"
        summary += f"• Beschreibung: {weather['description'].title()}\n"
        summary += f"• Luftfeuchtigkeit: {weather['humidity']}%\n"
        summary += f"• Wind: {weather['wind_speed']} km/h\n"
        summary += f"• Sichtweite: {weather['visibility']} km"
        
        if 'forecast_temperature' in weather:
            summary += f"\n\n Vorhersage für {weather['forecast_date']}:\n"
            summary += f"• Temperatur: {weather['forecast_temperature']}°C\n"
            summary += f"• Wetter: {weather['forecast_description'].title()}"
        
        return summary 