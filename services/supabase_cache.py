"""Supabase caching service for DateSpot Aggregator"""
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from supabase import create_client, Client
from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SupabaseCache:
    """Service for caching API responses in Supabase with in-memory optimization"""
    
    def __init__(self):
        self.supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        self.geocoding_ttl_days = Config.GEOCODING_CACHE_TTL_DAYS
        self.categorization_ttl_days = Config.CATEGORIZATION_CACHE_TTL_DAYS
        
        # In-memory caches
        self._geocoding_cache: Dict[str, Dict[str, Any]] = {}
        self._categorization_cache: Dict[str, str] = {}
        self._cache_loaded = False
    
    def _normalize_venue_name(self, venue_name: str) -> str:
        """
        Normalize venue name for consistent caching.
        
        Args:
            venue_name: Raw venue name
            
        Returns:
            Normalized venue name (lowercase, trimmed)
        """
        if not venue_name:
            return ""
        return venue_name.strip().lower()
    
    async def _load_cache_if_needed(self) -> None:
        """Load cache data from Supabase into memory if not already loaded"""
        if self._cache_loaded:
            return
            
        try:
            current_time = datetime.now().isoformat()
            
            # Load geocoding cache
            geocoding_response = self.supabase.table('geocoding_cache').select('venue_name, lat, lng, expires_at').gte('expires_at', current_time).execute()
            for row in geocoding_response.data:
                self._geocoding_cache[row['venue_name']] = {
                    'lat': row['lat'],
                    'lng': row['lng'],
                    'expires_at': row['expires_at']
                }
            
            # Load categorization cache
            categorization_response = self.supabase.table('categorization_cache').select('event_id, category, expires_at').gte('expires_at', current_time).execute()
            for row in categorization_response.data:
                self._categorization_cache[row['event_id']] = row['category']
            
            self._cache_loaded = True
            logger.info(f"   📥 Loaded cache: {len(self._geocoding_cache)} geocoding entries, {len(self._categorization_cache)} categorization entries")
            
        except Exception as error:
            logger.warning(f"   ⚠️ Error loading cache into memory: {error}")
            self._cache_loaded = True  # Prevent retry loops
    
    async def get_geocoding_cache(self, venue_name: str) -> Optional[Dict[str, float]]:
        """
        Get cached geocoding data for a venue.
        
        Args:
            venue_name: Name of the venue
            
        Returns:
            Dictionary with 'lat' and 'lng' keys, or None if not cached/expired
        """
        try:
            await self._load_cache_if_needed()
            
            normalized_name = self._normalize_venue_name(venue_name)
            if not normalized_name:
                return None
            
            # Check in-memory cache
            if normalized_name in self._geocoding_cache:
                cache_data = self._geocoding_cache[normalized_name]
                
                # Check if expired
                expires_at_str = cache_data['expires_at']
                if expires_at_str.endswith('Z'):
                    expires_at_str = expires_at_str[:-1] + '+00:00'
                expires_at = datetime.fromisoformat(expires_at_str)
                if expires_at > datetime.now(expires_at.tzinfo):
                    coordinates = {
                        'lat': cache_data['lat'],
                        'lng': cache_data['lng']
                    }
                    logger.info(f"   ✓ Cache HIT: Retrieved geocoding from cache for \"{venue_name}\" → {coordinates['lat']:.4f}, {coordinates['lng']:.4f}")
                    return coordinates
                else:
                    # Remove expired entry
                    del self._geocoding_cache[normalized_name]
            
            logger.info(f"   ○ Cache MISS: No cached geocoding for \"{venue_name}\"")
            return None
                
        except Exception as error:
            logger.warning(f"   ⚠️ Cache error for geocoding \"{venue_name}\": {error}")
            return None
    
    async def set_geocoding_cache(self, venue_name: str, coordinates: Dict[str, float]) -> bool:
        """
        Store geocoding data in cache.
        
        Args:
            venue_name: Name of the venue
            coordinates: Dictionary with 'lat' and 'lng' keys
            
        Returns:
            True if successfully cached, False otherwise
        """
        try:
            await self._load_cache_if_needed()
            
            normalized_name = self._normalize_venue_name(venue_name)
            if not normalized_name or not coordinates:
                return False
            
            expires_at = datetime.now() + timedelta(days=self.geocoding_ttl_days)
            expires_at_iso = expires_at.isoformat()
            
            # Store in Supabase - try insert first, then update if exists
            try:
                response = self.supabase.table('geocoding_cache').insert({
                    'venue_name': normalized_name,
                    'lat': coordinates['lat'],
                    'lng': coordinates['lng'],
                    'expires_at': expires_at_iso
                }).execute()
            except Exception as insert_error:
                if '23505' in str(insert_error):  # Unique constraint violation
                    # Update existing record
                    response = self.supabase.table('geocoding_cache').update({
                        'lat': coordinates['lat'],
                        'lng': coordinates['lng'],
                        'expires_at': expires_at_iso
                    }).eq('venue_name', normalized_name).execute()
                else:
                    raise insert_error
            
            if response.data:
                # Also store in memory cache
                self._geocoding_cache[normalized_name] = {
                    'lat': coordinates['lat'],
                    'lng': coordinates['lng'],
                    'expires_at': expires_at_iso
                }
                logger.info(f"   💾 Cache STORE: Saved geocoding for \"{venue_name}\" (expires in {self.geocoding_ttl_days} days)")
                return True
            else:
                logger.warning(f"   ⚠️ Failed to cache geocoding for \"{venue_name}\"")
                return False
                
        except Exception as error:
            logger.warning(f"   ⚠️ Cache store error for geocoding \"{venue_name}\": {error}")
            return False
    
    async def get_categorization_cache(self, event_id: str) -> Optional[str]:
        """
        Get cached categorization data for an event.
        
        Args:
            event_id: ID of the event
            
        Returns:
            Category string, or None if not cached/expired
        """
        try:
            await self._load_cache_if_needed()
            
            if not event_id:
                return None
            
            event_id = str(event_id)  # Ensure string
            
            # Check in-memory cache
            if event_id in self._categorization_cache:
                category = self._categorization_cache[event_id]
                logger.info(f"   ✓ Cache HIT: Retrieved categorization from cache for event {event_id} → \"{category}\"")
                return category
            
            logger.info(f"   ○ Cache MISS: No cached categorization for event {event_id}")
            return None
                
        except Exception as error:
            logger.warning(f"   ⚠️ Cache error for categorization event {event_id}: {error}")
            return None
    
    async def set_categorization_cache(self, event_id: str, category: str) -> bool:
        """
        Store categorization data in cache.
        
        Args:
            event_id: ID of the event
            category: AI-generated category
            
        Returns:
            True if successfully cached, False otherwise
        """
        try:
            await self._load_cache_if_needed()
            
            if not event_id or not category:
                return False
            
            event_id = str(event_id)  # Ensure string
            expires_at = datetime.now() + timedelta(days=self.categorization_ttl_days)
            
            # Store in Supabase - try insert first, then update if exists
            try:
                response = self.supabase.table('categorization_cache').insert({
                    'event_id': event_id,
                    'category': category,
                    'expires_at': expires_at.isoformat()
                }).execute()
            except Exception as insert_error:
                if '23505' in str(insert_error):  # Unique constraint violation
                    # Update existing record
                    response = self.supabase.table('categorization_cache').update({
                        'category': category,
                        'expires_at': expires_at.isoformat()
                    }).eq('event_id', event_id).execute()
                else:
                    raise insert_error
            
            if response.data:
                # Also store in memory cache
                self._categorization_cache[event_id] = category
                logger.info(f"   💾 Cache STORE: Saved categorization for event {event_id} → \"{category}\" (expires in {self.categorization_ttl_days} days)")
                return True
            else:
                logger.warning(f"   ⚠️ Failed to cache categorization for event {event_id}")
                return False
                
        except Exception as error:
            logger.warning(f"   ⚠️ Cache store error for categorization event {event_id}: {error}")
            return False
    
    async def cleanup_expired_cache(self) -> Dict[str, int]:
        """
        Remove expired cache entries.
        
        Returns:
            Dictionary with count of cleaned up entries
        """
        try:
            current_time = datetime.now().isoformat()
            
            # Clean up expired geocoding cache
            geocoding_response = self.supabase.table('geocoding_cache').delete().lt('expires_at', current_time).execute()
            geocoding_cleaned = len(geocoding_response.data) if geocoding_response.data else 0
            
            # Clean up expired categorization cache
            categorization_response = self.supabase.table('categorization_cache').delete().lt('expires_at', current_time).execute()
            categorization_cleaned = len(categorization_response.data) if categorization_response.data else 0
            
            cleanup_stats = {
                'geocoding_cleaned': geocoding_cleaned,
                'categorization_cleaned': categorization_cleaned,
                'total_cleaned': geocoding_cleaned + categorization_cleaned
            }
            
            if cleanup_stats['total_cleaned'] > 0:
                logger.info(f"   🧹 Cache cleanup: Removed {cleanup_stats['total_cleaned']} expired entries (geocoding: {geocoding_cleaned}, categorization: {categorization_cleaned})")
            
            return cleanup_stats
            
        except Exception as error:
            logger.warning(f"   ⚠️ Cache cleanup error: {error}")
            return {'geocoding_cleaned': 0, 'categorization_cleaned': 0, 'total_cleaned': 0}
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            current_time = datetime.now().isoformat()
            
            # Count active geocoding cache entries
            geocoding_count_response = self.supabase.table('geocoding_cache').select('id', count='exact').gte('expires_at', current_time).execute()
            active_geocoding = geocoding_count_response.count if geocoding_count_response.count is not None else 0
            
            # Count active categorization cache entries
            categorization_count_response = self.supabase.table('categorization_cache').select('id', count='exact').gte('expires_at', current_time).execute()
            active_categorization = categorization_count_response.count if categorization_count_response.count is not None else 0
            
            stats = {
                'active_geocoding_entries': active_geocoding,
                'active_categorization_entries': active_categorization,
                'total_active_entries': active_geocoding + active_categorization
            }
            
            return stats
            
        except Exception as error:
            logger.warning(f"   ⚠️ Error getting cache stats: {error}")
            return {'active_geocoding_entries': 0, 'active_categorization_entries': 0, 'total_active_entries': 0}
