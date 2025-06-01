from fastapi import FastAPI, BackgroundTasks
from fastapi_utils.tasks import repeat_every
from datetime import datetime
import uvicorn
from tuna_scraper import scrape_and_notify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Show Scraper API")

@app.on_event("startup")
@repeat_every(seconds=60 * 60)  # Run every hour
async def scheduled_scrape() -> None:
    """Scheduled task to scrape shows every hour"""
    logger.info("Running scheduled scrape task")
    try:
        result = scrape_and_notify()
        logger.info(f"Scheduled scrape completed with result: {result}")
    except Exception as e:
        logger.error(f"Error in scheduled scrape: {str(e)}")

@app.get("/")
async def root():
    return {"status": "running", "message": "Show scraper service is active"}

@app.post("/trigger-scrape")
async def trigger_scrape(background_tasks: BackgroundTasks):
    """Endpoint to manually trigger a scrape"""
    background_tasks.add_task(scrape_and_notify)
    return {"status": "success", "message": "Scrape job triggered"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 