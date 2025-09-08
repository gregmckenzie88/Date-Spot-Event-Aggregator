"""Scheduler for running DateSpot Aggregator at regular intervals"""
import asyncio
import schedule
import time
from datetime import datetime
import pytz
from main import DateSpotAggregator
from config import Config, ConfigError
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def run_aggregator_job():
    """Run the aggregator workflow as a scheduled job"""
    toronto_tz = pytz.timezone('America/Toronto')
    job_start_time = datetime.now(toronto_tz)
    
    try:
        logger.info("=" * 80)
        logger.info("🕐 SCHEDULED DATESPOT AGGREGATOR RUN")
        logger.info(f"🕐 Started at: {job_start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info("=" * 80)
        
        # Validate configuration before starting
        logger.info("🔧 Validating configuration...")
        Config.validate_required_env_vars()
        logger.info("✅ Configuration validation passed")
        
        aggregator = DateSpotAggregator()
        result = await aggregator.run_workflow()
        
        job_duration = (datetime.now(toronto_tz) - job_start_time).total_seconds()
        
        if result:
            total_events = sum(len(events) for events in result.get('results_by_date', {}).values())
            total_dates = len(result.get('results_by_date', {}))
            logger.info("=" * 80)
            logger.info("✅ SCHEDULED RUN COMPLETED SUCCESSFULLY")
            logger.info(f"📊 Result: {total_events} events across {total_dates} dates")
            logger.info(f"⏱️ Total time: {job_duration:.1f} seconds ({job_duration/60:.1f} minutes)")
            logger.info("=" * 80)
        else:
            logger.warning("=" * 80)
            logger.warning("⚠️ SCHEDULED RUN COMPLETED WITH NO RESULTS")
            logger.warning(f"⏱️ Total time: {job_duration:.1f} seconds")
            logger.warning("=" * 80)
    
    except ConfigError as error:
        job_duration = (datetime.now(toronto_tz) - job_start_time).total_seconds()
        logger.error("=" * 80)
        logger.error("❌ SCHEDULED RUN FAILED - CONFIGURATION ERROR")
        logger.error(str(error))
        logger.error(f"⏱️ Failed after: {job_duration:.1f} seconds")
        logger.error("=" * 80)
    except Exception as error:
        job_duration = (datetime.now(toronto_tz) - job_start_time).total_seconds()
        logger.error("=" * 80)
        logger.error("❌ SCHEDULED RUN FAILED")
        logger.error(f"💥 Error: {error}")
        logger.error(f"⏱️ Failed after: {job_duration:.1f} seconds")
        logger.error("=" * 80)


def schedule_job():
    """Wrapper to run async job in sync context"""
    asyncio.run(run_aggregator_job())


def main():
    """Main scheduler entry point"""
    logger.info("🚀 Starting DateSpot Aggregator Scheduler")
    logger.info("📅 Scheduled to run daily at 2:00 AM")
    
    # Schedule the job to run daily at 2:00 AM
    schedule.every().day.at("02:00").do(schedule_job)
    
    # Also run immediately on startup (optional)
    logger.info("🔄 Running initial execution...")
    schedule_job()
    
    # Keep the scheduler running
    logger.info("⏰ Scheduler is now running. Waiting for scheduled times...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Scheduler stopped by user")
    except Exception as error:
        logger.error(f"💥 Scheduler error: {error}")
        exit(1)
