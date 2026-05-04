# pipeline/main_states.py
import subprocess
import time
from datetime import datetime
from loguru import logger
from pipeline.common.config import PIPELINE_DIR

def run_states_pipeline():
    logger.info(f"Start States Pipeline at {datetime.now()}")
    
    scripts = [
        "providers/states/api_client.py",
        "providers/states/raw_fetcher.py",
        # Da wir alle Bundesländer parsen wollen, rufen wir jeden Parser auf
        "providers/states/parsers/bw_parser.py",
        "providers/states/parsers/by_parser.py",
        "providers/states/parsers/bb_parser.py",
        "ingest/ingest_states.py" 
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

    logger.info(f"States Pipeline finished successfully at {datetime.now()}")

if __name__ == "__main__":
    while True:
        run_states_pipeline()
        logger.info("Sleeping for 24 hours...")
        time.sleep(86400)