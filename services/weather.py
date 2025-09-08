"""Weather service using Visual Crossing API"""
import asyncio
from typing import Dict, List, Any, Optional
import requests
from config import Config
from utils.time_utils import convert_sunset_to_number
from utils.logger import setup_logger

logger = setup_logger(__name__)


class WeatherService:
    """Service for fetching weather data from Visual Crossing API"""
    
    def __init__(self):
        self.api_key = Config.WEATHER_API_KEY
        self.base_url = Config.WEATHER_API_BASE
    
    async def fetch_weather_for_date(self, date: str) -> Optional[Dict[str, Any]]:
        """
        Fetch weather data for a specific date.
        
        Args:
            date: Date string in YYYY-MM-DD format
            
        Returns:
            Weather data dictionary or None if request fails
        """
        try:
            url = f"{self.base_url}/Toronto,ON,Canada/{date}"
            logger.info(f"Fetching weather data for {date}")
            
            params = {
                'key': self.api_key,
                'elements': 'tempmax,tempmin,conditions,sunset',
                'include': 'days',
                'unitGroup': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract weather data
            if data.get('days') and len(data['days']) > 0:
                day_data = data['days'][0]
                weather_info = {
                    'tempmax': day_data.get('tempmax'),
                    'tempmin': day_data.get('tempmin'),
                    'conditions': day_data.get('conditions'),
                    'sunset': convert_sunset_to_number(day_data.get('sunset'))
                }
                logger.info(f"Successfully fetched weather for {date}")
                return weather_info
            else:
                logger.warning(f"No weather data found for {date}")
                return None
        
        except Exception as error:
            logger.error(f"Error fetching weather for {date}: {error}")
            return {
                'error': f"Failed to fetch weather data: {str(error)}"
            }
    
    async def add_weather_data(self, results_by_date: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Add weather data to the events schema.
        
        Args:
            results_by_date: Events data by date
            
        Returns:
            Schema with weather_report_by_date and results_by_date
        """
        logger.info("Starting weather data enrichment...")
        
        dates = list(results_by_date.keys())
        
        # Fetch weather data for all dates concurrently
        logger.info(f"   🌐 Fetching weather data for {len(dates)} dates concurrently...")
        weather_tasks = [self.fetch_weather_for_date(date) for date in dates]
        weather_results = await asyncio.gather(*weather_tasks)
        
        # Build weather report by date
        weather_report_by_date = {}
        successful_weather = 0
        for date, weather_data in zip(dates, weather_results):
            weather_report_by_date[date] = weather_data
            if weather_data and not weather_data.get('error'):
                successful_weather += 1
                logger.info(f"   ✓ Weather for {date}: {weather_data.get('tempmax', 'N/A')}°C max, {weather_data.get('conditions', 'N/A')}")
            else:
                logger.warning(f"   ✗ Weather failed for {date}: {weather_data.get('error', 'Unknown error') if weather_data else 'No data'}")
        
        logger.info(f"   📊 Weather summary: {successful_weather}/{len(dates)} dates successful")
        
        # Create enriched schema
        enriched_schema = {
            'weather_report_by_date': weather_report_by_date,
            'results_by_date': results_by_date
        }
        
        logger.info("Weather data enrichment complete")
        return enriched_schema
