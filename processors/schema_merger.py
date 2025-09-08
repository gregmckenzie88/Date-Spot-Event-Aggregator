"""Schema merger for combining events with categories"""
from typing import Dict, List, Any
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SchemaMerger:
    """Merges event data with AI-generated categories"""
    
    def merge_events_with_categories(
        self, 
        events_data: Dict[str, Any],
        categories_data: Dict[str, Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Merge events data with categorization data.
        
        Args:
            events_data: Schema with weather_report_by_date and results_by_date
            categories_data: Categorization data by date and event ID
            
        Returns:
            Merged schema with event_category added to each event
        """
        logger.info("Starting schema merge process...")
        
        events_results = events_data.get('results_by_date', {})
        weather_data = events_data.get('weather_report_by_date', {})
        
        if not events_results:
            logger.error("Events results_by_date is missing")
            raise ValueError("Events results_by_date is missing")
        
        if not categories_data:
            logger.error("Categories results_by_date is missing")
            raise ValueError("Categories results_by_date is missing")
        
        merged_results = {}
        total_events = 0
        categorized_events = 0
        
        # Iterate through each date in the events data
        for date, events in events_results.items():
            merged_results[date] = []
            total_events += len(events)
            
            logger.info(f"Processing {len(events)} events for {date}")
            
            # Process each event for this date
            for event in events:
                # Create a copy of the event
                merged_event = event.copy()
                event_id = str(event.get('id', ''))
                
                logger.debug(f"Looking for category for event ID: {event_id}")
                
                # Look for the category using the event ID
                event_category = None
                
                # Check if we have categories data for this date
                if date in categories_data:
                    date_categories = categories_data[date]
                    
                    # Handle different data structures
                    if isinstance(date_categories, dict):
                        # Direct mapping: {event_id: category}
                        event_category = date_categories.get(event_id)
                    elif isinstance(date_categories, list):
                        # Array of objects: [{event_id: category}, ...]
                        for category_item in date_categories:
                            if isinstance(category_item, dict) and event_id in category_item:
                                event_category = category_item[event_id]
                                break
                
                if event_category:
                    merged_event['event_category'] = event_category
                    categorized_events += 1
                    logger.debug(f"Found category for {event_id}: {event_category}")
                else:
                    merged_event['event_category'] = None
                    logger.debug(f"No category found for event ID {event_id}")
                
                merged_results[date].append(merged_event)
        
        logger.info(f"Schema merge complete: {categorized_events}/{total_events} events categorized")
        
        # Return the merged result
        return {
            'weather_report_by_date': weather_data,
            'results_by_date': merged_results
        }
