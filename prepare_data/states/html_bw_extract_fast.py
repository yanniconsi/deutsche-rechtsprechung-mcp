import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Konfiguration
NUM_WORKERS = 15       # Anzahl paralleler Browser (erhöhen auf 8-10 wenn stabil)
OUTPUT_DIR = Path("testdata")
OUTPUT_DIR.mkdir(exist_ok=True)

print_lock = Lock()

def log(msg):
    with print_lock:
        print(msg, flush=True)

def create_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')  # Keine Bilder laden
    return webdriver.Chrome(options=chrome_options)

def scrape_url(args):
    url, doc_id, i, total = args
    safe_filename = re.sub(r'[<>:"/\\|?*%]', '_', doc_id)
    filepath = OUTPUT_DIR / f"{safe_filename}.html"

    if filepath.exists():
        log(f"[{i}/{total}] ⏭️  Skip {doc_id}")
        return True

    driver = create_driver()
    try:
        log(f"[{i}/{total}] 🔄 Lade {doc_id}...")
        driver.get(url)

        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
        time.sleep(1.5)  # Reduziert von 2s auf 1.5s

        filepath.write_text(driver.page_source, encoding='utf-8')
        log(f"[{i}/{total}] ✅ {doc_id}")
        return True

    except Exception as e:
        log(f"[{i}/{total}] ❌ {doc_id}: {e}")
        return False
    finally:
        driver.quit()

# URLs laden
urls_to_process = []
ids_file = Path("urteil_ids.txt")

if ids_file.exists():
    with open(ids_file, 'r', encoding='utf-8') as f:
        for line in f:
            doc_id = line.strip()
            if doc_id:
                urls_to_process.append((
                    f"https://www.landesrecht-bw.de/bsbw/document/{doc_id}",
                    doc_id
                ))
    print(f"{len(urls_to_process)} IDs aus urteil_ids.txt geladen")
else:
    print("urteil_ids.txt nicht gefunden!")
    exit(1)

# Bereits vorhandene überspringen
remaining = [(url, doc_id) for url, doc_id in urls_to_process 
             if not (OUTPUT_DIR / f"{re.sub(r'[<>:\"/\\|?*%]', '_', doc_id)}.html").exists()]

print(f"{len(urls_to_process) - len(remaining)} bereits vorhanden")
print(f"{len(remaining)} noch zu laden mit {NUM_WORKERS} parallelen Browsern\n")

# Geschätzter Zeit
estimated_minutes = (len(remaining) * 2.5) / NUM_WORKERS / 60
print(f"Geschätzte Zeit: ~{estimated_minutes:.0f} Minuten\n")

# Paralleles Scraping
tasks = [(url, doc_id, i, len(remaining)) 
         for i, (url, doc_id) in enumerate(remaining, 1)]

success = 0
failed = []

with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
    futures = {executor.submit(scrape_url, task): task for task in tasks}
    for future in as_completed(futures):
        task = futures[future]
        if future.result():
            success += 1
        else:
            failed.append(task[1])  # doc_id merken

# Fehlgeschlagene in Datei speichern für Retry
if failed:
    with open("failed_ids.txt", 'w') as f:
        f.write('\n'.join(failed))
    print(f"\n⚠️  {len(failed)} fehlgeschlagen → gespeichert in failed_ids.txt")

total_done = len(list(OUTPUT_DIR.glob('*.html')))
print(f"\n✅ Fertig! {success} neu geladen, {total_done} gesamt im Ordner")