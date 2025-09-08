"""Google Maps Geocoding service"""
import asyncio
from typing import Dict, List, Any, Optional, Tuple
import requests
from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class GeocodingService:
    """Service for geocoding venue names using Google Maps API"""
    
    def __init__(self):
        self.api_key = Config.GOOGLE_MAPS_API_KEY
        self.base_url = Config.GOOGLE_MAPS_API_BASE
        self.request_delay = Config.GEOCODING_REQUEST_DELAY
    
    async def geocode_venue(self, venue_name: str) -> Optional[Dict[str, float]]:
        """
        Geocode a venue using Google Maps API.
        
        Args:
            venue_name: Name of the venue to geocode
            
        Returns:
            Dictionary with 'lat' and 'lng' keys, or None if geocoding fails
        """
        if not venue_name:
            logger.warning("No venue name provided for geocoding")
            return None
        
        try:
            search_query = f"{venue_name}, Toronto Canada"
            logger.info(f"Geocoding venue: \"{venue_name}\"")
            
            # Prepare request parameters
            params = {
                'address': search_query,
                'key': self.api_key
            }
            
            headers = {
                'Accept': 'application/json'
            }
            
            # Make HTTP request
            response = requests.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Check response status
            if data.get('status') == 'OK' and data.get('results'):
                first_result = data['results'][0]
                if 'geometry' in first_result and 'location' in first_result['geometry']:
                    location = first_result['geometry']['location']
                    coordinates = {
                        'lat': location['lat'],
                        'lng': location['lng']
                    }
                    logger.info(f"Successfully geocoded {venue_name}: {coordinates}")
                    return coordinates
                else:
                    logger.warning(f"No geometry.location in result for {venue_name}")
                    return None
            else:
                logger.warning(f"Geocoding failed for {venue_name}: {data.get('status', 'Unknown error')}")
                if data.get('error_message'):
                    logger.warning(f"Error message: {data['error_message']}")
                return None
        
        except Exception as error:
            logger.error(f"Geocoding error for {venue_name}: {error}")
            return None
    
    async def add_coordinates_to_events(self, results_by_date: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Add location coordinates to all events.
        
        Args:
            results_by_date: Events data by date
            
        Returns:
            Events data with location_coordinates added to each event
        """
        logger.info("Starting geocoding process...")
        
        total_venues = 0
        geocoded_venues = 0
        
        # Process each date
        for date, events in results_by_date.items():
            logger.info(f"   📅 Processing {len(events)} venues for {date}")
            total_venues += len(events)
            
            # Process each venue for this date
            for i, event in enumerate(events):
                venue_name = event.get('venue_name')
                
                if not venue_name:
                    logger.warning(f"   ⚠️ No venue_name found in event {event.get('id', 'unknown')}")
                    event['location_coordinates'] = None
                    continue
                
                logger.info(f"   🏢 Geocoding venue {i + 1}/{len(events)}: \"{venue_name}\"")
                
                # Get coordinates from Google Maps
                coordinates = await self.geocode_venue(venue_name)
                event['location_coordinates'] = coordinates
                
                if coordinates:
                    geocoded_venues += 1
                    logger.info(f"   ✓ Success: {venue_name} → {coordinates['lat']:.4f}, {coordinates['lng']:.4f}")
                else:
                    logger.warning(f"   ✗ Failed: {venue_name}")
                
                # Wait between requests to avoid rate limiting
                if i < len(events) - 1:
                    await asyncio.sleep(self.request_delay)
            
            logger.info(f"   ✓ Completed {date}: {sum(1 for e in events if e.get('location_coordinates'))}/{len(events)} venues geocoded")
            # Add a small delay between dates as well
            await asyncio.sleep(self.request_delay)
        
        logger.info(f"Geocoding complete: {geocoded_venues}/{total_venues} venues geocoded successfully")
        return results_by_date
