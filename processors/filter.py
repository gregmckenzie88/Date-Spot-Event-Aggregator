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
            logger.info(f"   📅 Filtering {len(events)} events for {date}")
            total_original += len(events)
            
            # Filter out events with excluded categories
            filtered_events = []
            excluded_count = 0
            uncategorized_count = 0
            
            for event in events:
                event_category = event.get('event_category')
                
                if event_category in self.excluded_categories:
                    # Skip events in excluded categories
                    excluded_count += 1
                    logger.debug(f"Excluding event {event.get('id')} with category: {event_category}")
                elif event_category is None:
                    # Keep events without categories (they'll be handled later)
                    uncategorized_count += 1
                    filtered_events.append(event)
                else:
                    # Keep events with valid categories
                    filtered_events.append(event)
            
            # Always include the date if there are any events (don't drop dates entirely)
            if filtered_events:
                filtered_results[date] = filtered_events
                total_filtered += len(filtered_events)
                logger.info(f"   ✓ Kept {len(filtered_events)} events for {date} after filtering")
                if excluded_count > 0:
                    logger.info(f"      {excluded_count} events excluded due to category")
                if uncategorized_count > 0:
                    logger.info(f"      {uncategorized_count} events kept without categories")
            else:
                logger.warning(f"   ⚠️ No events remaining for {date} after filtering ({excluded_count} excluded)")
                # Still include the date but with empty events list to preserve date structure
                filtered_results[date] = []
        
        logger.info(f"Event filtering complete: {total_filtered}/{total_original} events passed filter")
        
        return {
            'weather_report_by_date': weather_data,
            'results_by_date': filtered_results
        }
