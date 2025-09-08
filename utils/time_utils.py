"""Time conversion utilities"""
import re
from typing import Optional


def convert_to_numerical_time(time_string: str) -> Optional[int]:
    """
    Convert time string to 24-hour numerical format.
    
    Args:
        time_string: Time string like "9:30 PM", "11:00 AM", "9 PM", etc.
        
    Returns:
        4-digit number in HHMM format (e.g., 930 for 9:30 AM, 2130 for 9:30 PM)
        or None if parsing fails
    """
    if not time_string or not isinstance(time_string, str):
        return None
    
    # Remove any extra whitespace and convert to uppercase
    clean_time = time_string.strip().upper()
    
    # Extract time parts using regex to handle various formats
    time_match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)|(\d{1,2})\s*(AM|PM)', clean_time)
    
    if not time_match:
        return None
    
    hours = 0
    minutes = 0
    
    if time_match.group(1):
        # Format: "9:30 PM" or "11:00 AM"
        hours = int(time_match.group(1))
        minutes = int(time_match.group(2))
        period = time_match.group(3)
        
        # Convert to 24-hour format
        if period == 'PM' and hours != 12:
            hours += 12
        elif period == 'AM' and hours == 12:
            hours = 0
    elif time_match.group(4):
        # Format: "9 PM" or "11 AM"
        hours = int(time_match.group(4))
        minutes = 0
        period = time_match.group(5)
        
        # Convert to 24-hour format
        if period == 'PM' and hours != 12:
            hours += 12
        elif period == 'AM' and hours == 12:
            hours = 0
    
    # Return as 4-digit number (HHMM format)
    return hours * 100 + minutes


def convert_sunset_to_number(sunset_string: str) -> Optional[int]:
    """
    Convert sunset time string to 4-digit 24-hour format number.
    
    Args:
        sunset_string: Sunset time in format "HH:MM:SS"
        
    Returns:
        4-digit number in HHMM format or None if parsing fails
    """
    if not sunset_string:
        return None
    
    # Parse the time string (format: "HH:MM:SS")
    time_parts = sunset_string.split(':')
    if len(time_parts) < 2:
        return None
    
    try:
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        
        # Convert to 4-digit number (HHMM format)
        return hours * 100 + minutes
    except (ValueError, IndexError):
        return None
