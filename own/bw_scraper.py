import requests
import json
import time

# --- KONFIGURATION (Hier bei Bedarf Token/Cookie erneuern) ---
CSRF_TOKEN = "5oHvVnl6U9Xz3DPQ1P3TvSpMh0GfrmkL.jp80.0303161700"
COOKIE = 'LASTACCESS="03.03.2026 17:14:59"; up={"search":{"hitsPerPage":0,"sort":"date","categorySort":null,"disableComfortSearch":false,"isSearchInAIMode":false,"extendedFieldsOpen":false},"casefile":{"sort":"standard"},"menu":{"searchFrameLeftSplitter":324,"docFrameLeftSplitter":282},"document":{"docAIQuestionExpanded":false}}; r3autologin="bsbw"; JSESSIONID=8C8C460248F2DD537210057AE0146CE7.jp80; OAuth_Token_Request_State=5208f0c7-be1c-4959-83df-6b71eef462e8'

OUTPUT_FILE = "urteil_ids.txt"
TOTAL_HITS = 18543
PAGE_SIZE = 50

def fetch_ids():
    url = "https://www.landesrecht-bw.de/jportal/wsrest/recherche3/search"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) Gecko/20100101 Firefox/148.0",
        "Accept": "*/*",
        "Accept-Language": "de,en-US;q=0.9,en;q=0.8",
        "content-type": "application/json",
        "juris-portalid": "bsbw",
        "x-csrf-token": CSRF_TOKEN,
        "Referer": "https://www.landesrecht-bw.de/bsbw/search",
        "Origin": "https://www.landesrecht-bw.de",
        "Connection": "keep-alive",
        "Cookie": COOKIE,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=4"
    }

    all_doc_ids = set()

    # Wir fangen bei 1 an, wie in deinem cURL (start: 1)
    for start in range(1, TOTAL_HITS, PAGE_SIZE):
        print(f"Lade Position {start} bis {start + PAGE_SIZE}...")
        
        payload = {
            "searchTasks": {
                "RESULT_LIST": {
                    "start": start,
                    "size": PAGE_SIZE + 1, # +1 wie im cURL (51)
                    "sort": "date",
                    "addToHistory": True,
                    "addCategory": True
                },
                "FAST_ACCESS": {},
                "SEARCH_WORD_HITS": {}
            },
            "filters": {"CATEGORY": ["Rechtsprechung"]},
            "searches": [],
            "clientID": "bsbw",
            "clientVersion": "bsbw - V08_28_00 - 27.02.2026 14:56",
            "r3ID": "2026-03-03T16:14:58.159Z"
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            
            # DEBUG: Zeige uns die Antwort, falls es leer ist
            if response.status_code != 200:
                print(f"Fehler! Status: {response.status_code}")
                print(f"Antwort vom Server: {response.text}")
                break

            data = response.json()
            
            # Wir suchen in 'resultList'
            current_ids = []
            if "resultList" in data:
                current_ids = [doc.get("docId") for doc in data["resultList"] if doc.get("docId")]
            
            if not current_ids:
                print("DEBUG: Server gab leere Liste zurück. Prüfe 'data' Struktur:")
                # Zeigt die Keys an, die der Server geschickt hat
                print(f"Verfügbare Felder in Antwort: {list(data.keys())}") 
                break

            all_doc_ids.update(current_ids)
            
            with open(OUTPUT_FILE, "a") as f:
                for doc_id in current_ids:
                    f.write(doc_id + "\n")
            
            print(f"  -> {len(current_ids)} IDs gespeichert.")
            time.sleep(1.2)

        except Exception as e:
            print(f"Abbruch: {e}")
            break

    print(f"Fertig. Datei {OUTPUT_FILE} enthält jetzt {len(all_doc_ids)} IDs.")

if __name__ == "__main__":
    # Datei leeren
    with open(OUTPUT_FILE, "w") as f: pass
    fetch_ids()