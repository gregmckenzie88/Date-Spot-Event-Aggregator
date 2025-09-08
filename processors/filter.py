"""Event filtering processor"""
from typing import Dict, List, Any
from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EventFilter:
    """Filters events based on category exclusions"""
    
    def __init__(self):
        self.excluded_categories = Config.EXCLUDED_CATEGORIES
    
    def filter_events_by_category(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter out events with excluded categories.
        
        Args:
            schema: Schema with weather_report_by_date and results_by_date
            
        Returns:
            Filtered schema with excluded categories removed
        """
        logger.info(f"Starting event filtering. Excluding categories: {self.excluded_categories}")
        
        results_by_date = schema.get('results_by_date', {})
        weather_data = schema.get('weather_report_by_date', {})
        
        filtered_results = {}
        total_original = 0
        total_filtered = 0
        
        # Process each date
        for date, events in results_by_date.items():
            logger.info(f"Filtering {len(events)} events for {date}")
            total_original += len(events)
            
            # Filter out events with excluded categories
            filtered_events = []
            for event in events:
                event_category = event.get('event_category')
                
                if event_category not in self.excluded_categories:
                    filtered_events.append(event)
                else:
                    logger.debug(f"Excluding event {event.get('id')} with category: {event_category}")
            
            # Only include the date if there are remaining events
            if filtered_events:
                filtered_results[date] = filtered_events
                total_filtered += len(filtered_events)
                logger.info(f"Kept {len(filtered_events)} events for {date} after filtering")
            else:
                logger.info(f"No events remaining for {date} after filtering")
        
        logger.info(f"Event filtering complete: {total_filtered}/{total_original} events passed filter")
        
        return {
            'weather_report_by_date': weather_data,
            'results_by_date': filtered_results
        }
