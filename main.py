"""Main workflow orchestrator for DateSpot Aggregator"""
import asyncio
import sys
from datetime import datetime
from typing import Dict, Any
import pytz

# Local imports
from config import Config, ConfigError
from utils.logger import setup_logger
from services.blogto_api import BlogTOAPI
from processors.data_validator import DataValidator
from services.geocoding import GeocodingService
from services.weather import WeatherService
from services.ai_categorizer import AICategorizer
from processors.schema_merger import SchemaMerger
from processors.filter import EventFilter
from services.github_publisher import GitHubPublisher

# Set up logging
logger = setup_logger(__name__)


class DateSpotAggregator:
    """Main workflow orchestrator"""
    
    def __init__(self):
        self.blogto_api = BlogTOAPI()
        self.data_validator = DataValidator()
        self.geocoding_service = GeocodingService()
        self.weather_service = WeatherService()
        self.ai_categorizer = AICategorizer()
        self.schema_merger = SchemaMerger()
        self.event_filter = EventFilter()
        self.github_publisher = GitHubPublisher()
    
    async def run_workflow(self) -> Dict[str, Any]:
        """
        Execute the complete DateSpot aggregation workflow.
        
        Returns:
            Final processed schema
        """
        # Use Toronto timezone for all workflow timing
        toronto_tz = pytz.timezone('America/Toronto')
        workflow_start_time = datetime.now(toronto_tz)
        logger.info("=" * 80)
        logger.info("🚀 STARTING DATESPOT AGGREGATOR WORKFLOW")
        logger.info(f"🕐 Start Time: {workflow_start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info("=" * 80)
        
        try:
            # Step 1: Fetch events from BlogTO
            step_start = datetime.now(toronto_tz)
            logger.info("🔵 STEP 1/8: FETCHING EVENTS FROM BLOGTO")
            logger.info(f"   ⏰ Step started at: {step_start.strftime('%H:%M:%S %Z')}")
            logger.info("   📋 Fetching events for the next 7 days with rate limiting...")
            
            raw_events = await self.blogto_api.fetch_all_events()
            
            step_duration = (datetime.now(toronto_tz) - step_start).total_seconds()
            if not raw_events:
                logger.error("   ❌ STEP 1 FAILED: No events fetched from BlogTO API")
                return {}
            
            total_raw_events = sum(len(events) for events in raw_events.values())
            logger.info(f"   ✅ STEP 1 COMPLETED in {step_duration:.1f}s")
            logger.info(f"   📊 Result: {total_raw_events} events across {len(raw_events)} dates")
            logger.info("-" * 60)
            
            # Step 2: Validate and clean data
            step_start = datetime.now(toronto_tz)
            logger.info("🔵 STEP 2/8: VALIDATING AND CLEANING DATA")
            logger.info(f"   ⏰ Step started at: {step_start.strftime('%H:%M:%S %Z')}")
            logger.info("   📋 Filtering events with required fields and adding numerical time...")
            
            validated_events = self.data_validator.validate_and_clean_data(raw_events)
            
            step_duration = (datetime.now(toronto_tz) - step_start).total_seconds()
            if not validated_events:
                logger.error("   ❌ STEP 2 FAILED: No valid events after validation")
                return {}
            
            total_valid_events = sum(len(events) for events in validated_events.values())
            logger.info(f"   ✅ STEP 2 COMPLETED in {step_duration:.1f}s")
            logger.info(f"   📊 Result: {total_valid_events}/{total_raw_events} events passed validation")
            logger.info("-" * 60)
            
            # Step 3: Add location coordinates
            step_start = datetime.now(toronto_tz)
            logger.info("🔵 STEP 3/8: ADDING LOCATION COORDINATES")
            logger.info(f"   ⏰ Step started at: {step_start.strftime('%H:%M:%S %Z')}")
            logger.info("   📋 Geocoding venue addresses using Google Maps API...")
            
            geocoded_events = await self.geocoding_service.add_coordinates_to_events(validated_events)
            
            step_duration = (datetime.now(toronto_tz) - step_start).total_seconds()
            # Count successful geocoding
            geocoded_count = sum(
                1 for date_events in geocoded_events.values() 
                for event in date_events 
                if event.get('location_coordinates')
            )
            logger.info(f"   ✅ STEP 3 COMPLETED in {step_duration:.1f}s")
            logger.info(f"   📊 Result: {geocoded_count}/{total_valid_events} venues geocoded successfully")
            logger.info("-" * 60)
            
            # Step 4: Enrich with weather data
            step_start = datetime.now(toronto_tz)
            logger.info("🔵 STEP 4/8: ENRICHING WITH WEATHER DATA")
            logger.info(f"   ⏰ Step started at: {step_start.strftime('%H:%M:%S %Z')}")
            logger.info("   📋 Fetching weather data from Visual Crossing API...")
            
            weather_enriched_schema = await self.weather_service.add_weather_data(geocoded_events)
            
            step_duration = (datetime.now(toronto_tz) - step_start).total_seconds()
            weather_count = len([w for w in weather_enriched_schema.get('weather_report_by_date', {}).values() if w and not w.get('error')])
            logger.info(f"   ✅ STEP 4 COMPLETED in {step_duration:.1f}s")
            logger.info(f"   📊 Result: Weather data fetched for {weather_count}/{len(geocoded_events)} dates")
            logger.info("-" * 60)
            
            # Step 5: Categorize events with AI
            step_start = datetime.now(toronto_tz)
            logger.info("🔵 STEP 5/8: CATEGORIZING EVENTS WITH AI")
            logger.info(f"   ⏰ Step started at: {step_start.strftime('%H:%M:%S %Z')}")
            logger.info("   📋 Using Claude AI to categorize events into predefined categories...")
            
            categories = await self.ai_categorizer.categorize_events(geocoded_events)
            
            step_duration = (datetime.now(toronto_tz) - step_start).total_seconds()
            categorized_count = sum(len(date_cats) for date_cats in categories.values())
            logger.info(f"   ✅ STEP 5 COMPLETED in {step_duration:.1f}s")
            logger.info(f"   📊 Result: {categorized_count} events categorized by AI")
            logger.info("-" * 60)
            
            # Step 6: Merge schemas
            step_start = datetime.now(toronto_tz)
            logger.info("🔵 STEP 6/8: MERGING EVENT DATA WITH CATEGORIES")
            logger.info(f"   ⏰ Step started at: {step_start.strftime('%H:%M:%S %Z')}")
            logger.info("   📋 Combining event data with AI-generated categories...")
            
            merged_schema = self.schema_merger.merge_events_with_categories(
                weather_enriched_schema, 
                categories
            )
            
            step_duration = (datetime.now(toronto_tz) - step_start).total_seconds()
            merged_count = sum(len(events) for events in merged_schema.get('results_by_date', {}).values())
            with_categories = sum(
                1 for date_events in merged_schema.get('results_by_date', {}).values()
                for event in date_events
                if event.get('event_category')
            )
            logger.info(f"   ✅ STEP 6 COMPLETED in {step_duration:.1f}s")
            logger.info(f"   📊 Result: {with_categories}/{merged_count} events successfully categorized")
            logger.info("-" * 60)
            
            # Step 7: Filter unwanted categories
            step_start = datetime.now(toronto_tz)
            logger.info("🔵 STEP 7/8: FILTERING UNWANTED CATEGORIES")
            logger.info(f"   ⏰ Step started at: {step_start.strftime('%H:%M:%S %Z')}")
            logger.info(f"   📋 Removing events in excluded categories: {Config.EXCLUDED_CATEGORIES}")
            
            filtered_schema = self.event_filter.filter_events_by_category(merged_schema)
            
            step_duration = (datetime.now(toronto_tz) - step_start).total_seconds()
            filtered_count = sum(len(events) for events in filtered_schema.get('results_by_date', {}).values())
            logger.info(f"   ✅ STEP 7 COMPLETED in {step_duration:.1f}s")
            logger.info(f"   📊 Result: {filtered_count}/{merged_count} events after filtering")
            logger.info("-" * 60)
            
            # Step 8: Publish to GitHub
            step_start = datetime.now(toronto_tz)
            logger.info("🔵 STEP 8/8: PUBLISHING TO GITHUB")
            logger.info(f"   ⏰ Step started at: {step_start.strftime('%H:%M:%S %Z')}")
            logger.info(f"   📋 Publishing schema to {Config.GITHUB_REPO}/{Config.GITHUB_FILE_PATH}")
            
            publish_success = await self.github_publisher.publish_to_github(filtered_schema)
            
            step_duration = (datetime.now(toronto_tz) - step_start).total_seconds()
            if publish_success:
                logger.info(f"   ✅ STEP 8 COMPLETED in {step_duration:.1f}s")
                logger.info("   📊 Result: Schema successfully published to GitHub")
            else:
                logger.warning(f"   ⚠️ STEP 8 COMPLETED WITH WARNINGS in {step_duration:.1f}s")
                logger.warning("   📊 Result: GitHub publication failed")
            
            # Final summary
            total_duration = (datetime.now(toronto_tz) - workflow_start_time).total_seconds()
            logger.info("=" * 80)
            logger.info("🎉 WORKFLOW COMPLETED SUCCESSFULLY")
            logger.info(f"🕐 Total Duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
            logger.info(f"📊 Final Result: {filtered_count} events across {len(filtered_schema.get('results_by_date', {}))} dates")
            logger.info("=" * 80)
            
            return filtered_schema
        
        except Exception as error:
            total_duration = (datetime.now(toronto_tz) - workflow_start_time).total_seconds()
            logger.error("=" * 80)
            logger.error("💥 WORKFLOW FAILED")
            logger.error(f"❌ Error: {error}")
            logger.error(f"🕐 Failed after: {total_duration:.1f} seconds")
            logger.error("=" * 80)
            raise


async def main():
    """Main entry point"""
    try:
        # Validate configuration before starting
        logger.info("🔧 Validating configuration...")
        Config.validate_required_env_vars()
        logger.info("✅ Configuration validation passed")
        
        # Initialize and run the aggregator
        aggregator = DateSpotAggregator()
        result = await aggregator.run_workflow()
        
        # Print summary
        if result:
            total_events = sum(len(events) for events in result.get('results_by_date', {}).values())
            total_dates = len(result.get('results_by_date', {}))
            logger.info(f"📊 Final result: {total_events} events across {total_dates} dates")
        
        return 0
    
    except ConfigError as error:
        logger.error("❌ Configuration Error:")
        logger.error(str(error))
        return 1
    except KeyboardInterrupt:
        logger.info("Workflow interrupted by user")
        return 1
    except Exception as error:
        logger.error(f"Unexpected error: {error}")
        return 1


if __name__ == "__main__":
    # Run the async main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
