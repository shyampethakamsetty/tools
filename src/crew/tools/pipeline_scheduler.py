import schedule
import time
import subprocess
import sys
import os
from datetime import datetime
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline_scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def check_daily_folder_exists():
    """Check if the output folder for today exists."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    output_path = Path("outputs/youtube") / today
    
    if output_path.exists():
        logging.info(f"Output folder for today ({today}) already exists at {output_path}")
        return True
    else:
        logging.info(f"No output folder found for today ({today}) at {output_path}")
        return False

def run_script(script_name):
    """Run a Python script and log its execution."""
    try:
        logging.info(f"Starting execution of {script_name}")
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, 
                              text=True)
        
        if result.returncode == 0:
            logging.info(f"Successfully completed {script_name}")
            if result.stdout:
                logging.info(f"Output from {script_name}:\n{result.stdout}")
        else:
            logging.error(f"Error in {script_name}:\n{result.stderr}")
            
    except Exception as e:
        logging.error(f"Failed to run {script_name}: {str(e)}")

def run_pipeline():
    """Run all three scripts in sequence if today's output folder doesn't exist."""
    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    if check_daily_folder_exists():
        logging.info(f"Skipping pipeline run at {current_time} - output folder already exists")
        return
    
    logging.info(f"Starting scheduled pipeline run at {current_time}")
    
    scripts = [
        'youtube_transcript_fetcher.py',
        'chunking_pipeline.py',
        'chroma_storage.py'
    ]
    
    for script in scripts:
        script_path = os.path.join(os.path.dirname(__file__), script)
        run_script(script_path)
        # Add a small delay between scripts to ensure proper completion
        time.sleep(5)
    
    logging.info(f"Completed pipeline run at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")

def main():
    logging.info("Pipeline scheduler started")
    logging.info("This script will:")
    logging.info("1. Check for today's output folder in outputs/youtube/")
    logging.info("2. Run the pipeline if the folder doesn't exist")
    logging.info("3. Schedule checks for 00:00 UTC every day")
    logging.info("4. Continue running until manually stopped (Ctrl+C)")
    
    # Schedule the pipeline to run at 00:00 UTC every day
    schedule.every().day.at("00:00").do(run_pipeline)
    
    # Calculate time until next 00:00 UTC
    now = datetime.utcnow()
    next_run = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if now >= next_run:
        next_run = next_run.replace(day=next_run.day + 1)
    
    time_until_next = (next_run - now).total_seconds()
    logging.info(f"Next scheduled check at {next_run.strftime('%Y-%m-%d %H:%M:%S UTC')} (in {time_until_next/3600:.2f} hours)")
    
    # Run the pipeline immediately on startup if needed
    run_pipeline()
    
    # Keep the script running
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute for pending tasks
        except KeyboardInterrupt:
            logging.info("Scheduler stopped by user (Ctrl+C). You can restart it anytime to resume scheduling.")
            sys.exit(0)

if __name__ == "__main__":
    main() 