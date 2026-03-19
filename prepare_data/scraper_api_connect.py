import os
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

class ScraperDataProcessor:
    def __init__(self):
        self.base_url = os.getenv("WEBSCRAPER_URL")
        self.auth_token = os.getenv("WEBSCRAPER_AUTH")
        self.headers = {
            "Authorization": self.auth_token,
            "Content-Type": "application/json"
        }

    def fetch_to_dataframe(self, page_size=50):
        endpoint = f"{self.base_url}/api/pages/list"
        payload = {"pageSize": page_size, "page": 1}

        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            if not data:
                print("Keine Daten erhalten.")
                return pd.DataFrame()

            df = pd.json_normalize(data, sep='_')
            
            return df

        except Exception as e:
            print(f"Fehler beim Abruf: {e}")
            return pd.DataFrame()

processor = ScraperDataProcessor()
df = processor.fetch_to_dataframe(page_size=500)

if not df.empty:
    cols_to_keep = ['source_name', 'url_url', 'page_contentHtml']
    existing_cols = [c for c in cols_to_keep if c in df.columns]
    
    if not all(col in existing_cols for col in ['source_name', 'url_url']):
        print(f"Kritische Spalten fehlen: {df.columns.tolist()}")
    else:
        df = df[existing_cols]
        if 'page_contentHtml' in df.columns:
            df = df.dropna(subset=['page_contentHtml'])
            
        mask_is_bw = df['source_name'] == 'source.court.baden-württemberg'
        mask_has_re_in_url = df['url_url'].str.contains(r'[A-Z]{2,}RE\d+', na=False, regex=True)
        mask_keep = (~mask_is_bw) | (mask_is_bw & mask_has_re_in_url)
        df_filtered = df[mask_keep]

        df_filtered.to_csv("db_filtered.csv", index=False, encoding='utf-8')
        print(f"{len(df_filtered)} Datensätze in 'db_filtered.csv' gespeichert.")
else:
    print("Der DataFrame ist leer.")