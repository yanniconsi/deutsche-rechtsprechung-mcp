import os
import urllib.parse
from pathlib import Path
import pandas as pd
from pipeline.common.config import MCP_DATA_DIR, STATES_DATA_DIR

df = pd.read_csv(STATES_DATA_DIR / "states_pages_filtered.csv")
base_data_path = MCP_DATA_DIR

saved_count = 0

for _, row in df.iterrows():
    source = str(row['source_name']).strip().lower()
    url = str(row['url_url']).strip()
    html_content = str(row['page_contentHtml'])
    
    if not html_content or html_content.lower() == 'nan':
         continue

    parsed_url = urllib.parse.urlparse(url)
    doc_id = os.path.basename(parsed_url.path) or parsed_url.path.split('/')[-2]

    target_dir = None
    if 'baden-württemberg' in source:
        target_dir = base_data_path / "bw" / "raw"
    elif 'bayern' in source:
        target_dir = base_data_path / "by" / "raw"
    elif 'brandenburg' in source:
        target_dir = base_data_path / "bb" / "raw"

    if target_dir:
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / f"{doc_id}.html"
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            saved_count += 1
        except Exception as e:
            print(f"Failed for {doc_id}: {e}")

print(f"Wrote {saved_count} HTML files under {base_data_path.resolve()}.")