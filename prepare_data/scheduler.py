import logging
import os
import subprocess
import sys
import time

import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("DataPipelineScheduler")

def run_pipeline():
    logger.info("Starting scheduled data preparation pipeline...")
    start_time = time.time()
    
    steps = [
        ("Extracting links", ["python", "extract_links.py"]),
        ("Downloading files", ["python", "download_files.py"]),
        ("Extracting ZIPs", ["python", "extract_zips.py"]),
        ("Converting to Markdown", ["python", "convert_all_to_md.py"]),
        ("Ingesting to OpenSearch", ["python", "ingest.py"])
    ]

    # Special handling: Remove TOC to force update
    toc_path = "data/rii-toc.xml"
    if os.path.exists(toc_path):
        logger.info(f"Removing {toc_path} to force Table of Contents update.")
        try:
            os.remove(toc_path)
        except OSError as e:
            logger.error(f"Error removing {toc_path}: {e}")

    for step_name, command in steps:
        logger.info(f"Step: {step_name}")
        try:
            # Run command and wait for it to complete. 
            # stdout/stderr are piped to the container logs.
            subprocess.run(
                command, 
                check=True, 
                text=True,
                capture_output=False  # Let output flow to stdout
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Pipeline failed at step '{step_name}'. Exit code: {e.returncode}")
            return # Stop pipeline on error
        except Exception as e:
            logger.error(f"Unexpected error at step '{step_name}': {e}")
            return

    duration = time.time() - start_time
    logger.info(f"Pipeline finished successfully in {duration:.2f} seconds.")
    logger.info("Next run scheduled for tomorrow at 03:00.")

def main():

    run_on_startup = os.getenv("RUN_ON_STARTUP", "false").lower() == "true"

    # Schedule the job
    schedule_time = "03:00"
    schedule.every().day.at(schedule_time).do(run_pipeline)
    
    logger.info(f"Scheduler started. Pipeline will run daily at {schedule_time}.")
    
    # Run immediately on startup for the first time?
    # Usually desirable in dev/testing, maybe configurable.
    # For now, let's run it once on startup so we don't wait 24h for the first data.
    logger.info(f"Scheduler started. Pipeline will run daily at {schedule_time}.")
    
    # Only run on startup if explicitly enabled
    if run_on_startup:
        logger.info("RUN_ON_STARTUP is enabled. Performing initial startup run...")
        run_pipeline()
    else:
        logger.info("RUN_ON_STARTUP is disabled. Waiting for scheduled run at {schedule_time}.")

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
