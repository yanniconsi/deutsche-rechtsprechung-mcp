#!/bin/bash

# Ensure output directories exist if scripts expect them or just let scripts handle it.
# The scripts seem to create dirs if missing.

while true; do
    echo "Starting data preparation pipeline at $(date)..."
    
    echo "1. Extracting links..."
    # Force re-download of Table of Contents to get updates
    rm -f data/rii-toc.xml
    python extract_links.py
    
    echo "2. Downloading files..."
    python download_files.py
    
    echo "3. Extracting ZIPs..."
    python extract_zips.py
    
    echo "4. Converting to Markdown..."
    python convert_all_to_md.py
    
    echo "Pipeline finished at $(date). Sleeping for 24 hours..."
    sleep 86400
done
