from bs4 import BeautifulSoup
from markdownify import markdownify as md
import json
import re
from pathlib import Path
from pipeline.common.config import get_state_data_dir

def extract_metadata_from_html(html_content, filename):
    soup = BeautifulSoup(html_content, 'html.parser')
    metadata = {'doknr': Path(filename).stem}
    
    # Header line: court, type, date, docket.
    kopf_div = soup.find('div', class_='col-sm-9', style='font-size:110%')
    if kopf_div and kopf_div.b:
        kopf_text = kopf_div.b.get_text(strip=True)
        # Example: "OLG Nürnberg, Beschluss v. 30.07.2025 – 8 W 1286/25"
        match = re.search(r'([^,]+),\s*([^v\.]+)\s*v\.\s*(\d{2}\.\d{2}\.\d{4})\s*–\s*(.*)', kopf_text)
        if match:
            metadata['gericht'] = match.group(1).strip()
            metadata['dokumenttyp'] = match.group(2).strip()
            
            day, month, year = match.group(3).strip().split('.')
            metadata['datum'] = f"{year}{month}{day}"
            
            metadata['aktenzeichen'] = match.group(4).strip()
    
    # Title
    titel = soup.find('h1', class_='titelzeile')
    if titel:
        metadata['title'] = titel.get_text(strip=True)
        
    # Norms section
    norm_ueber = soup.find('div', class_='rsprboxueber', string=re.compile('Normenkette', re.I))
    if norm_ueber:
        norm_zeile = norm_ueber.find_next_sibling('div', class_='rsprboxzeile')
        if norm_zeile:
            metadata['norm'] = norm_zeile.get_text(strip=True)
            
    # Headnotes
    leitsaetze = soup.find_all('div', class_='leitsatz')
    if leitsaetze:
        metadata['leitsatz'] = " ".join([l.get_text(strip=True) for l in leitsaetze])
        
    # ECLI (optional)
    ecli_ueber = soup.find('div', class_='rsprboxueber', string=re.compile('ECLI', re.I))
    if ecli_ueber:
        ecli_zeile = ecli_ueber.find_next_sibling('div', class_='rsprboxzeile')
        if ecli_zeile:
            metadata['ecli'] = ecli_zeile.get_text(strip=True)

    # Sections (preview only)
    tenor_divs = soup.find_all('div', class_=re.compile(r'absatz\s+tenor'))
    if tenor_divs:
        tenor_text = " ".join([t.get_text(separator=' ', strip=True) for t in tenor_divs])
        metadata['tenor'] = tenor_text[:500]
        
    gruende_divs = soup.find_all('div', class_=re.compile(r'absatz\s+gruende'))
    if gruende_divs:
        gruende_text = " ".join([g.get_text(separator=' ', strip=True) for g in gruende_divs])
        metadata['gruende'] = gruende_text[:500]
        
    return metadata

# --- Run ---
base_output_dir = get_state_data_dir("by", "markdown")
testdata_dir = get_state_data_dir("by", "raw")

for html_file in testdata_dir.glob('*.html'):
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    markdown_text = md(html_content)
    
    doc_name = html_file.stem
    doc_folder = base_output_dir / doc_name
    doc_folder.mkdir(exist_ok=True)
    
    output_file = doc_folder / f"{doc_name}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_text)
    
    metadata = extract_metadata_from_html(html_content, doc_name)
    metadata['source_file'] = html_file.name
    metadata['markdown_file'] = output_file.name
    
    json_file = doc_folder / f"{doc_name}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f'Converted: {html_file.name} -> {doc_folder.name}/')

print(f'\nComplete!')