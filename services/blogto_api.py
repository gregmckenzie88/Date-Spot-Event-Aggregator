"""BlogTO API service for fetching events"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import requests
from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BlogTOAPI:
    """Service for fetching events from BlogTO API"""
    
    def __init__(self):
        self.base_url = Config.BLOGTO_API_BASE
        self.request_delay = Config.BLOGTO_REQUEST_DELAY
    
    def generate_dates(self, number_of_days: int) -> List[str]:
        """
        Generate dynamic dates starting from today.
        
        Args:
            number_of_days: Number of days to generate
            
        Returns:
            List of date strings in YYYY-MM-DD format
        """
        dates = []
        today = datetime.now()
        
        for i in range(number_of_days):
            current_date = today + timedelta(days=i)
            date_str = current_date.strftime('%Y-%m-%d')
            dates.append(date_str)
        
        return dates
    
    async def fetch_events_for_date(self, date: str) -> List[Dict[str, Any]]:
        """
        Fetch events for a specific date.
        
        Args:
            date: Date string in YYYY-MM-DD format
            
        Returns:
            List of event dictionaries
        """
        try:
            logger.info(f"Fetching events for date: {date}")
            
            # Prepare request parameters
            params = {
                'bundle_type': 'medium',
                'date': date,
                'limit': 9999,
                'offset': 0,
                'status': 'ongoing'
            }
            
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'en-US,en;q=0.9'
            }
            
            # Make HTTP request
            response = requests.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            events = data.get('results', [])
            
            logger.info(f"Successfully fetched {len(events)} events for {date}")
            return events
            
        except Exception as error:
            logger.error(f"Error fetching events for {date}: {error}")
            return []
    
    async def fetch_all_events(self, number_of_days: int = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch events for multiple days with rate limiting.
        
        Args:
            number_of_days: Number of days to fetch (defaults to Config.FETCH_DAYS)
            
        Returns:
            Dictionary mapping dates to lists of events
        """
        if number_of_days is None:
            number_of_days = Config.FETCH_DAYS
        
        dates = self.generate_dates(number_of_days)
        results_by_date = {}
        
        logger.info(f"Starting to fetch events for {len(dates)} dates...")
        
        for i, date in enumerate(dates):
            logger.info(f"   📅 Processing date {i + 1}/{len(dates)}: {date}")
            
            # Wait between requests (skip delay for first request)
            if i > 0:
                logger.info(f'   ⏳ Waiting {self.request_delay} seconds for rate limiting...')
                await asyncio.sleep(self.request_delay)
            
            # Fetch events for this date
            events = await self.fetch_events_for_date(date)
            results_by_date[date] = events
            logger.info(f"   ✓ Completed {date}: {len(events)} events fetched")
        
        logger.info('All BlogTO API requests completed!')
        return results_by_date
