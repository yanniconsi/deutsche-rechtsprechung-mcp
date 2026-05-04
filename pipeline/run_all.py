from loguru import logger

# Importiere deine Ausführungsfunktionen (wie oben besprochen)
from main_bgh import run_bgh_pipeline
from main_states import run_states_pipeline

def main():
    logger.info("Starte manuellen Datendownload- und Ingest-Lauf...")
    
    logger.info("1. Bearbeite BGH")
    run_bgh_pipeline()
    
    logger.info("2. Bearbeite Bundesländer")
    run_states_pipeline()

    logger.info("Verarbeitung komplett! Skript beendet sich.")

if __name__ == "__main__":
    main()