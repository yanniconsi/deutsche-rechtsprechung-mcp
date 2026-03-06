import re
import csv
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Liste der Dateinamen
filenames = """
Finanzgericht_Baden-Württemberg_3_V_2781-13_NJRE001200892.pdf
Landesarbeitsgericht_Baden-Württemberg_10_Sa_32-13_NJRE001180375.pdf
Landessozialgericht_Baden-Württemberg_L_11_R_2182-11_NJRE001131859.pdf
VG_Stuttgart_A_17_K_3378-24_NJRE001590735.pdf
Verwaltungsgerichtshof_Baden-Württemberg_2_S_1610-15_NJRE001291957.pdf
OLG_Stuttgart_9_U_108-12_NJRE001158006.pdf
Landessozialgericht_Baden-Württemberg_L_7_R_1192-12_NJRE001145626.pdf
Landessozialgericht_Baden-Württemberg_L_4_P_5153-12_NJRE001169339.pdf
OLG_Stuttgart_12_U_530-19_NJRE001450826.pdf
OLG_Karlsruhe_25_U_35-22_NJRE001578217.pdf
LG_Ravensburg_2_O_421-19_NJRE001419674.pdf
OLG_Stuttgart_9_U_168-19_NJRE001444346.pdf
VG_Stuttgart_8_K_11401-18_NJRE001416190.pdf
OLG_Karlsruhe_13_U_37-19_NJRE001402973.pdf

""".strip()

# Zusätzliche URLs
additional_urls = """
0018b891-9f5c-4b68-9365-73401026d053    https://www.landesrecht-bw.de/bsbw/document/NJRE001619542
99d48f5c-91aa-41a7-89dd-e0c99b54b097    https://www.landesrecht-bw.de/bsbw/document/NJRE001618880
0cffcc51-2ecd-4d1f-a7c9-e3c32150afb2    https://www.landesrecht-bw.de/bsbw/document/NJRE001618980
15c97dd4-53cb-43ad-8675-f19884011cd3    https://www.landesrecht-bw.de/bsbw/document/NJRE001619000
3c0ff730-7b72-4144-95b7-cff36ad0cb0e    https://www.landesrecht-bw.de/bsbw/document/NJRE001619545
48573b60-32fe-4fbd-b509-1cd07ee53546    https://www.landesrecht-bw.de/bsbw/document/NJRE001619954
""".strip()

# Zielordner
output_dir = Path("testdata")
output_dir.mkdir(exist_ok=True)

# Regex-Pattern für Dokument-IDs (NJRE oder andere Formate)
pattern = r'd=([^&\s]+)'

# Sammle alle URLs
urls_to_process = set()

# Extrahiere NJRE-Nummern aus filenames und erstelle URLs
njre_pattern = r'(NJRE\d+)'
for line in filenames.split('\n'):
    match = re.search(njre_pattern, line)
    if match:
        njre = match.group(1)
        urls_to_process.add((f"https://www.landesrecht-bw.de/bsbw/document/{njre}", njre))

# Extrahiere aus additional_urls
for line in additional_urls.split('\n'):
    if 'bsbw/document/' in line:
        url = line.split()[-1]
        doc_id = url.split('/')[-1]
        urls_to_process.add((url, doc_id))

# Lese URLs aus permalinks.csv
csv_path = Path("permalinks.csv")
if csv_path.exists():
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            permalink = row['permalink']
            # Extrahiere die Dokument-ID aus dem d= Parameter
            match = re.search(pattern, permalink)
            if match:
                doc_id = match.group(1)
                urls_to_process.add((permalink, doc_id))
else:
    print(f"Warnung: {csv_path} nicht gefunden")

print(f"Gefundene {len(urls_to_process)} eindeutige URLs zum Laden")

# Selenium Setup
chrome_options = Options()
chrome_options.add_argument('--headless')  # Im Hintergrund ausführen
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=chrome_options)

try:
    for url, doc_id in sorted(urls_to_process):
        # Erstelle sicheren Dateinamen
        safe_filename = re.sub(r'[<>:"/\\|?*%]', '_', doc_id)
        filename = f"{safe_filename}.html"
        filepath = output_dir / filename
        
        # Überspringe bereits heruntergeladene Dateien
        if filepath.exists():
            print(f"Überspringe {doc_id} (bereits vorhanden)")
            continue
        
        try:
            print(f"Lade {url} ...")
            driver.get(url)
            
            # Warte bis der Inhalt geladen ist
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
            
            # Zusätzliche Wartezeit für dynamische Inhalte
            time.sleep(2)
            
            # Hole das gerenderte HTML
            html_content = driver.page_source
            
            # Speichere HTML
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"  → Gespeichert als {filename}")
        
        except Exception as e:
            print(f"  → Fehler beim Laden: {e}")

finally:
    driver.quit()

print(f"\nFertig! {len(list(output_dir.glob('*.html')))} HTML-Dateien im Ordner 'testdata' gespeichert.")