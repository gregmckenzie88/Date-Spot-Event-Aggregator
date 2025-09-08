"""Data validation and cleaning processor"""
from typing import Dict, List, Any, Optional
from config import Config
from utils.time_utils import convert_to_numerical_time
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DataValidator:
    """Validates and cleans event data from BlogTO API"""
    
    def __init__(self):
        self.required_fields = Config.REQUIRED_FIELDS
    
    def is_valid_entry(self, entry: Dict[str, Any]) -> bool:
        """
        Validate if an entry has all required fields with non-empty values.
        
        Args:
            entry: Event dictionary to validate
            
        Returns:
            True if entry is valid, False otherwise
        """
        return all(
            field in entry and 
            entry[field] is not None and 
            entry[field] != ''
            for field in self.required_fields
        )
    
    def extract_required_fields(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract only the required fields from an entry and add numerical time.
        
        Args:
            entry: Original event dictionary
            
        Returns:
            Cleaned event dictionary with only required fields
        """
        cleaned_entry = {}
        
        # Extract required fields
        for field in self.required_fields:
            if field == 'id':
                # Convert id to string
                cleaned_entry[field] = str(entry[field])
            else:
                cleaned_entry[field] = entry[field]
        
        # Add numerical_time field
        start_numerical = convert_to_numerical_time(entry.get('start_time'))
        end_numerical = convert_to_numerical_time(entry.get('end_time'))
        
        cleaned_entry['numerical_time'] = {
            'start': start_numerical,
            'end': end_numerical
        }
        
        return cleaned_entry
    
    def validate_and_clean_data(self, results_by_date: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Process and validate all events data.
        
        Args:
            results_by_date: Raw events data by date
            
        Returns:
            Validated and cleaned events data
        """
        logger.info("Starting data validation and cleaning...")
        
        validated_results = {}
        total_original = 0
        total_valid = 0
        
        # Process each date
        for date, events in results_by_date.items():
            logger.info(f"   📅 Validating {len(events)} events for {date}")
            total_original += len(events)
            
            # Filter valid entries and extract required fields
            valid_events = []
            invalid_count = 0
            for event in events:
                if self.is_valid_entry(event):
                    cleaned_event = self.extract_required_fields(event)
                    valid_events.append(cleaned_event)
                else:
                    invalid_count += 1
                    # Log which fields are missing for debugging
                    missing_fields = [field for field in self.required_fields 
                                    if field not in event or not event[field]]
                    logger.debug(f"   ⚠️ Event {event.get('id', 'unknown')} missing: {missing_fields}")
            
            # Only include the date if there are valid entries
            if valid_events:
                validated_results[date] = valid_events
                total_valid += len(valid_events)
                logger.info(f"   ✓ {date}: {len(valid_events)} valid, {invalid_count} invalid events")
            else:
                logger.warning(f"   ✗ {date}: No valid events found ({invalid_count} invalid)")
        
        logger.info(f"Data validation complete: {total_valid}/{total_original} events passed validation")
        return validated_results
