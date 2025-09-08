"""AI categorization service using Claude API"""
import json
import re
from typing import Dict, List, Any
import requests
from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AICategorizer:
    """Service for categorizing events using Claude AI"""
    
    def __init__(self):
        self.api_key = Config.ANTHROPIC_API_KEY
        self.base_url = Config.ANTHROPIC_API_BASE
        self.model = Config.ANTHROPIC_MODEL
        self.max_tokens = Config.ANTHROPIC_MAX_TOKENS
        self.temperature = Config.ANTHROPIC_TEMPERATURE
        
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
    
    def create_reduced_payload(self, results_by_date: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, str]]]:
        """
        Create reduced payload for LLM processing.
        
        Args:
            results_by_date: Full events data
            
        Returns:
            Reduced payload with just ID and description
        """
        logger.info("Creating reduced payload for LLM processing...")
        
        reduced_payload = {"results_by_date": {}}
        
        for date, events in results_by_date.items():
            reduced_payload["results_by_date"][date] = []
            
            for event in events:
                event_summary = {
                    event['id']: f"{event['title']}: {self.cleanse_text(event['description_stripped'])}"
                }
                reduced_payload["results_by_date"][date].append(event_summary)
        
        return reduced_payload
    
    async def categorize_events(self, results_by_date: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, str]]:
        """
        Categorize events using Claude AI.
        
        Args:
            results_by_date: Events data to categorize
            
        Returns:
            Categories mapped by date and event ID
        """
        logger.info("Starting AI categorization process...")
        
        # Calculate total events to check if we need to process in batches
        total_events = sum(len(events) for events in results_by_date.values())
        logger.info(f"   📊 Total events to categorize: {total_events} across {len(results_by_date)} dates")
        
        # If we have too many events, process in smaller batches by date
        if total_events > 100:  # Arbitrary threshold to prevent token limit issues
            logger.info("   🔄 Large dataset detected, processing dates in batches...")
            return await self._categorize_in_batches(results_by_date)
        else:
            return await self._categorize_single_batch(results_by_date)
    
    async def _categorize_single_batch(self, results_by_date: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, str]]:
        """Process all events in a single AI request"""
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
        
        return await self._make_ai_request(payload, reduced_payload)
    
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
                all_categories[date] = []
        
        return all_categories
    
    async def _make_ai_request(self, payload: Dict[str, Any], reduced_payload: Dict[str, Any]) -> Dict[str, Any]:
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
