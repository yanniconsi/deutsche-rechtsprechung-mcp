import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import requests
from tqdm import tqdm

MAX_WORKERS = 5
DOWNLOAD_DIR = "data/downloads"
LINKS_FILE = "data/links.txt"
MAX_RETRIES = 3

def download_url(url):
    if not url:
        return
    
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    if not filename:
        filename = "unknown_file_" + str(hash(url))
    
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    # Explicitly skip if the file already exists
    if os.path.exists(filepath):
        tqdm.write(f"[SKIP] {filename} already exists")
        return "skipped"

    # Rate limiting sleep
    time.sleep(random.uniform(0.5, 1.5))
    tqdm.write(f"[START] Downloading {filename}...")

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            tqdm.write(f"[SUCCESS] Downloaded {filename}")
            return True
        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                sleep_time = 2 ** attempt
                tqdm.write(f"[RETRY] {filename} failed (attempt {attempt+1}), retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                tqdm.write(f"[ERROR] Failed to download {filename} after {MAX_RETRIES} attempts: {e}")
                return False
        except Exception as e:
            tqdm.write(f"[ERROR] Critical error for {filename}: {e}")
            return False

def main():
    if not os.path.exists(LINKS_FILE):
        print(f"Error: '{LINKS_FILE}' not found. Please run extract_links.py first.")
        return

    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    with open(LINKS_FILE, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"Starting download of {len(urls)} files...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # tqdm.write allows printing while keeping the progress bar at the bottom
        list(tqdm(executor.map(download_url, urls), total=len(urls), unit="file"))

    print(f"Finished. Check the '{DOWNLOAD_DIR}' folder.")

if __name__ == "__main__":
    main()