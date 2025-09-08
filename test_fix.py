#!/usr/bin/env python3
"""Test script to verify that all 7 days are preserved in the final schema"""

import asyncio
from main import DateSpotAggregator
from utils.logger import setup_logger

# Set up logging
logger = setup_logger(__name__)

async def test_seven_day_fix():
    """Test that all 7 days are preserved through the workflow"""
    
    try:
        logger.info("🧪 TESTING SEVEN-DAY FIX")
        logger.info("=" * 60)
        
        aggregator = DateSpotAggregator()
        
        # Run the full workflow
        result = await aggregator.run_workflow()
        
        # Check results
        if result and 'results_by_date' in result:
            final_dates = list(result['results_by_date'].keys())
            logger.info(f"\n📊 FINAL RESULT:")
            logger.info(f"   Dates in final schema: {len(final_dates)}")
            
            for date in sorted(final_dates):
                events = result['results_by_date'][date]
                categorized = sum(1 for e in events if e.get('event_category'))
                logger.info(f"   📅 {date}: {len(events)} events ({categorized} categorized)")
            
            if len(final_dates) == 7:
                logger.info("✅ SUCCESS: All 7 days preserved!")
            else:
                logger.error(f"❌ FAILURE: Only {len(final_dates)}/7 days in final schema")
                logger.error(f"   Missing dates might be due to no events or filtering issues")
        else:
            logger.error("❌ No results returned from workflow")
            
    except Exception as error:
        logger.error(f"💥 Test failed: {error}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_seven_day_fix())
