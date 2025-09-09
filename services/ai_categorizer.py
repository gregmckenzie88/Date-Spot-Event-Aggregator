"""AI categorization service using Claude API"""
import json
import re
from typing import Dict, List, Any
import requests
from config import Config
from utils.logger import setup_logger
from services.supabase_cache import SupabaseCache

logger = setup_logger(__name__)


class AICategorizer:
    """Service for categorizing events using Claude AI"""
    
    def __init__(self):
        self.api_key = Config.ANTHROPIC_API_KEY
        self.base_url = Config.ANTHROPIC_API_BASE
        self.model = Config.ANTHROPIC_MODEL
        self.max_tokens = Config.ANTHROPIC_MAX_TOKENS
        self.temperature = Config.ANTHROPIC_TEMPERATURE
        self.cache = SupabaseCache()
        
        # Event categories from the n8n workflow
        self.categories = [
            "Comedy Scene",
            "Trivia & Quiz Nights",
            "Live Music Performances", 
            "Theatre Productions",
            "Dance Classes & Socials",
            "Museum Exhibitions",
            "Camps & Kids Programs",
            "Farmers Markets & Food Markets",
            "Movie Screenings",
            "Fitness",
            "Walking & Bus Tours",
            "Interactive Dining Experiences",
            "Escape Rooms & Immersive Games",
            "Cultural Festivals",
            "Craft Workshops",
            "Sports Leagues & Activities",
            "Drag & Cabaret Shows",
            "Language & Cultural Exchange",
            "Professional Networking",
            "Seniors Programs",
            "Art Gallery Openings",
            "Patio & Rooftop Events",
            "Board Game Nights"
        ]
    
    def cleanse_text(self, text: str) -> str:
        """
        Cleanse text for LLM processing.
        
        Args:
            text: Raw text to cleanse
            
        Returns:
            Cleansed text
        """
        if not text or not isinstance(text, str):
            return ''
        
        # Remove newlines and replace with spaces
        cleaned = text.replace('\n', ' ')
        
        # Replace non-UTF8 characters (emojis, non-English characters) with spaces
        cleaned = re.sub(r'[^\x00-\x7F]', ' ', cleaned)
        
        # Replace multiple consecutive spaces with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Trim whitespace and limit to 250 characters
        cleaned = cleaned.strip()[:250]
        
        return cleaned
    
    def create_reduced_payload(self, results_by_date: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        Create reduced payload for LLM processing.
        
        Args:
            results_by_date: Full events data
            
        Returns:
            Reduced payload with just ID and description organized by date
        """
        logger.info("Creating reduced payload for LLM processing...")
        
        reduced_payload = {"results_by_date": {}}
        
        for date, events in results_by_date.items():
            reduced_payload["results_by_date"][date] = {}
            
            for event in events:
                event_id = str(event['id'])
                event_description = f"{event['title']}: {self.cleanse_text(event['description_stripped'])}"
                reduced_payload["results_by_date"][date][event_id] = event_description
        
        return reduced_payload
    
    async def categorize_events(self, results_by_date: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, str]]:
        """
        Categorize events using Claude AI with caching.
        
        Args:
            results_by_date: Events data to categorize
            
        Returns:
            Categories mapped by date and event ID
        """
        logger.info("Starting AI categorization process...")
        
        # Calculate total events and check cache
        total_events = sum(len(events) for events in results_by_date.values())
        logger.info(f"   📊 Total events to categorize: {total_events} across {len(results_by_date)} dates")
        
        # Check cache for each event and separate cached vs uncached
        cached_categories = {}
        events_to_categorize = {}
        cache_hits = 0
        
        for date, events in results_by_date.items():
            cached_categories[date] = {}
            events_to_categorize[date] = []
            
            for event in events:
                event_id = event.get('id')
                if event_id:
                    cached_category = await self.cache.get_categorization_cache(event_id)
                    if cached_category:
                        cached_categories[date][event_id] = cached_category
                        cache_hits += 1
                    else:
                        events_to_categorize[date].append(event)
        
        uncached_events = sum(len(events) for events in events_to_categorize.values())
        logger.info(f"   📊 Cache results: {cache_hits} hits, {uncached_events} events need API categorization")
        
        # If all events are cached, return cached results
        if uncached_events == 0:
            logger.info("   ✓ All events found in cache, no API calls needed!")
            return cached_categories
        
        # Process uncached events
        new_categories = {}
        if uncached_events > 100:  # Arbitrary threshold to prevent token limit issues
            logger.info("   🔄 Large uncached dataset detected, processing dates in batches...")
            new_categories = await self._categorize_in_batches(events_to_categorize)
        else:
            new_categories = await self._categorize_single_batch(events_to_categorize)
        
        # Merge cached and new categories
        final_categories = {}
        for date in results_by_date.keys():
            final_categories[date] = {}
            # Add cached categories
            if date in cached_categories and isinstance(cached_categories[date], dict):
                final_categories[date].update(cached_categories[date])
            # Add new categories
            if date in new_categories and isinstance(new_categories[date], dict):
                final_categories[date].update(new_categories[date])
        
        return final_categories
    
    async def _categorize_single_batch(self, results_by_date: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, str]]:
        """Process all events in a single AI request"""
        # Skip if no events to process
        total_uncached_events = sum(len(events) for events in results_by_date.values())
        if total_uncached_events == 0:
            return {}
        
        logger.info(f"   ○ Cache MISS: Making Claude AI API call for {total_uncached_events} events")
        
        # Create reduced payload
        reduced_payload = self.create_reduced_payload(results_by_date)
        
        # Log payload size for debugging
        payload_size = len(json.dumps(reduced_payload))
        logger.info(f"   📊 Payload size: {payload_size} characters")
        
        # Prepare system prompt
        system_prompt = f"""You are an expert event categorization system. Your task is to categorize event descriptions into exactly one of these categories:
{chr(10).join(f'- {cat}' for cat in self.categories)}

Rules:
1. Return ONLY the JSON structure maintaining the same unique ID keys from the input
2. Each value must be exactly one of the categories above
3. Maintain the exact same structure and order as the input
4. CRITICAL: Process every single entry - do not skip any entries from the input data
5. Take your time to ensure completeness - verify that your output has the same number of entries as the input
6. If uncertain, choose the most likely category based on keywords and context
7. Do not include any explanation or additional text
8. Ensure the output is stringified JSON. Do not return markdown or any other format."""
        
        user_content = f"Categorize this event data:\n\n{json.dumps(reduced_payload)}"
        
        # Prepare API request
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": user_content
                }
            ]
        }
        
        return await self._make_ai_request(payload, reduced_payload, results_by_date)
    
    async def _categorize_in_batches(self, results_by_date: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, str]]:
        """Process events in batches by date to avoid token limits"""
        all_categories = {}
        
        # Process each date separately
        for date, events in results_by_date.items():
            logger.info(f"   📅 Processing batch for {date} ({len(events)} events)")
            
            # Create payload for just this date
            single_date_data = {date: events}
            categories = await self._categorize_single_batch(single_date_data)
            
            # Merge results
            if categories and date in categories:
                all_categories[date] = categories[date]
            else:
                logger.warning(f"   ⚠️ No categories returned for {date}")
                all_categories[date] = {}
        
        return all_categories
    
    async def _make_ai_request(self, payload: Dict[str, Any], reduced_payload: Dict[str, Any], original_events: Dict[str, List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Make the actual AI request and parse response"""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        try:
            logger.info("   🤖 Sending categorization request to Claude AI...")
            logger.info(f"   📊 Request size: {len(json.dumps(payload))} characters")
            
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=120  # Increased timeout for AI processing
            )
            response.raise_for_status()
            
            response_data = response.json()
            
            # Extract the categorized data
            if 'content' in response_data and response_data['content']:
                ai_response = response_data['content'][0]['text']
                logger.info("   ✓ Successfully received categorization from Claude AI")
                logger.info(f"   📊 Response size: {len(ai_response)} characters")
                
                # Parse the JSON response
                try:
                    categorized_data = json.loads(ai_response)
                    logger.info("   ✓ Successfully parsed AI categorization response")
                    
                    # Count categorized events and validate completeness
                    ai_results = categorized_data.get('results_by_date', {})
                    total_categorized = sum(len(date_data) for date_data in ai_results.values())
                    total_input = sum(len(events) for events in reduced_payload.get('results_by_date', {}).values())
                    
                    logger.info(f"   📊 AI categorized {total_categorized}/{total_input} events")
                    
                    if total_categorized < total_input:
                        logger.warning(f"   ⚠️ AI response incomplete: {total_categorized}/{total_input} events categorized")
                    
                    # Store successful categorizations in cache
                    if original_events:
                        await self._store_categorizations_in_cache(ai_results, original_events)
                    
                    return ai_results
                except json.JSONDecodeError as e:
                    logger.error(f"   ❌ Failed to parse AI response as JSON: {e}")
                    logger.error(f"   📄 AI response: {ai_response[:500]}...")
                    return {}
            else:
                logger.error("   ❌ No content in AI response")
                return {}
        
        except Exception as error:
            logger.error(f"   ❌ Error during AI categorization: {error}")
            return {}
    
    async def _store_categorizations_in_cache(self, ai_results: Dict[str, Dict[str, str]], original_events: Dict[str, List[Dict[str, Any]]]) -> None:
        """Store AI categorization results in cache"""
        try:
            stored_count = 0
            for date, date_categories in ai_results.items():
                for event_id, category in date_categories.items():
                    success = await self.cache.set_categorization_cache(event_id, category)
                    if success:
                        stored_count += 1
            
            total_categories = sum(len(date_cats) for date_cats in ai_results.values())
            logger.info(f"   💾 Cached {stored_count}/{total_categories} new categorizations")
            
        except Exception as error:
            logger.warning(f"   ⚠️ Error storing categorizations in cache: {error}")
