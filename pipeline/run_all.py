from loguru import logger

from main_bgh import run_bgh_pipeline
from main_states import run_states_pipeline

def main():
    logger.info("Starting one-shot ingest run...")
    
    logger.info("Step 1/2: BGH")
    run_bgh_pipeline()
    
    logger.info("Step 2/2: States")
    run_states_pipeline()

    logger.info("Done. Exiting.")

if __name__ == "__main__":
    main()