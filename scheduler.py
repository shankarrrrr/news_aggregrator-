"""
Automated Scheduler for NewsNexus Pipeline
Runs the pipeline every 4 hours automatically
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8000"


def trigger_pipeline():
    """Trigger the pipeline via API"""
    try:
        logger.info("Triggering automated pipeline run...")
        response = requests.post(f"{API_URL}/admin/trigger-pipeline")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Pipeline triggered successfully. Session ID: {data['session_id']}")
            logger.info(f"Dashboard Token: {data['dashboard_token']}")
        else:
            logger.error(f"Failed to trigger pipeline. Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            
    except Exception as e:
        logger.error(f"Error triggering pipeline: {e}")


def start_scheduler():
    """Start the scheduler"""
    scheduler = BackgroundScheduler()
    
    # Run every 4 hours
    scheduler.add_job(
        trigger_pipeline,
        'interval',
        hours=4,
        id='pipeline_job',
        name='Run NewsNexus Pipeline',
        replace_existing=True
    )
    
    # Also run once at startup (optional)
    scheduler.add_job(
        trigger_pipeline,
        'date',
        run_date=datetime.now(),
        id='startup_job',
        name='Initial Pipeline Run'
    )
    
    scheduler.start()
    logger.info("Scheduler started. Pipeline will run every 4 hours.")
    
    return scheduler


if __name__ == "__main__":
    import time
    
    logger.info("Starting NewsNexus Automated Scheduler...")
    scheduler = start_scheduler()
    
    try:
        # Keep the script running
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()
        logger.info("Scheduler stopped.")
