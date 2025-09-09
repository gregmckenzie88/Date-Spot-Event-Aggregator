"""Configuration module for DateSpot Aggregator"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ConfigError(Exception):
    """Custom exception for configuration errors"""
    pass

class Config:
    """Configuration class to hold all API keys and settings"""
    
    # API Keys - Must be provided via environment variables
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    @classmethod
    def validate_required_env_vars(cls):
        """Validate that all required environment variables are set"""
        required_vars = {
            'GOOGLE_MAPS_API_KEY': cls.GOOGLE_MAPS_API_KEY,
            'WEATHER_API_KEY': cls.WEATHER_API_KEY,
            'ANTHROPIC_API_KEY': cls.ANTHROPIC_API_KEY,
            'GITHUB_TOKEN': cls.GITHUB_TOKEN,
            'SUPABASE_URL': cls.SUPABASE_URL,
            'SUPABASE_KEY': cls.SUPABASE_KEY
        }
        
        missing_vars = [var_name for var_name, var_value in required_vars.items() if not var_value]
        
        if missing_vars:
            error_msg = f"""
Missing required environment variables: {', '.join(missing_vars)}

Please set these environment variables by:

1. Creating a .env file in the project root with:
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key
   WEATHER_API_KEY=your_weather_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   GITHUB_TOKEN=your_github_token
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key

2. Or setting them as system environment variables:
   export GOOGLE_MAPS_API_KEY=your_google_maps_api_key
   export WEATHER_API_KEY=your_weather_api_key
   export ANTHROPIC_API_KEY=your_anthropic_api_key
   export GITHUB_TOKEN=your_github_token
   export SUPABASE_URL=your_supabase_url
   export SUPABASE_KEY=your_supabase_key

3. Or in Docker, ensure your docker-compose.yml has them set in the environment section.
"""
            raise ConfigError(error_msg)
    
    # GitHub Configuration
    GITHUB_REPO = 'gregmckenzie88/DateSpot-Schema'
    GITHUB_FILE_PATH = 'api/schema.js'
    
    # API Endpoints
    BLOGTO_API_BASE = 'https://www.blogto.com/api/v2/events/'
    GOOGLE_MAPS_API_BASE = 'https://maps.googleapis.com/maps/api/geocode/json'
    WEATHER_API_BASE = 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline'
    ANTHROPIC_API_BASE = 'https://api.anthropic.com/v1/messages'
    GITHUB_API_BASE = 'https://api.github.com/repos'
    
    # Rate limiting settings (in seconds)
    BLOGTO_REQUEST_DELAY = 5
    GEOCODING_REQUEST_DELAY = 0.01  # 10ms as per n8n workflow
    
    # Event filtering
    EXCLUDED_CATEGORIES = [
        "Camps & Kids Programs",
        "Seniors Programs"
    ]
    
    # Required fields for event validation
    REQUIRED_FIELDS = [
        'id',
        'venue_name', 
        'start_time',
        'end_time',
        'description_stripped',
        'title',
        'share_url',
        'hub_page_image_url'
    ]
    
    # Number of days to fetch events for
    FETCH_DAYS = 7
    
    # AI Model Configuration
    ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
    ANTHROPIC_MAX_TOKENS = 64000
    ANTHROPIC_TEMPERATURE = 0.1
    
    # Cache Configuration
    GEOCODING_CACHE_TTL_DAYS = 90
    CATEGORIZATION_CACHE_TTL_DAYS = 30
