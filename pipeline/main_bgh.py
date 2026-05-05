import subprocess
import time
from datetime import datetime
from loguru import logger
from pipeline.common.config import BGH_DATA_DIR, PIPELINE_DIR

def run_bgh_pipeline():
    logger.info(f"Starting BGH pipeline at {datetime.now()}")
    
    # 1. Force re-download of Table of Contents
    toc_file = BGH_DATA_DIR / "rii-toc.xml"
    if toc_file.exists():
        toc_file.unlink()
        logger.info("Deleted old rii-toc.xml")

    scripts = [
        "providers/bgh/bgh_scraper_links.py",
        "providers/bgh/bgh_scraper_download.py",
        "providers/bgh/bgh_extractor.py",
        "providers/bgh/bgh_parser.py",
        "ingest/ingest_bgh.py"
    ]

    for script in scripts:
        script_path = PIPELINE_DIR / script
        logger.info(f"Running: {script}...")
        
        try:
            subprocess.run(["python", str(script_path)], check=True)
            logger.success(f"Finished {script}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Pipeline failed at {script}. Error: {e}")
            return

    logger.info(f"Pipeline finished successfully at {datetime.now()}")

if __name__ == "__main__":
    while True:
        run_bgh_pipeline()
        logger.info("Sleeping for 24 hours...")
        time.sleep(86400) # Sleep for 24h