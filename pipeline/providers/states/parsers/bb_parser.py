from bs4 import BeautifulSoup
from markdownify import markdownify as md
import json
import re
from pathlib import Path
from pipeline.common.config import get_state_data_dir



def extract_metadata_bb(html_content, md_text, filename):
    soup = BeautifulSoup(html_content, 'html.parser')
    metadata = {'doknr': Path(filename).stem}
    
    # Title (stored in <h1 id="header">)
    header = soup.find('h1', id='header')
    if header:
        metadata['title'] = header.get_text(strip=True)
        
    # Metadata table (court, date, docket, ...)
    table = soup.find('table', class_='bb-table-stripes')
    if table:
        for row in table.find_all('tr'):
            ths = row.find_all('th')
            tds = row.find_all('td')
            
            # Typical row: <th>Gericht</th><td>...</td><th>Datum</th><td>...</td>
            if len(ths) == 2 and len(tds) == 2:
                key1 = ths[0].get_text(strip=True)
                val1 = tds[0].get_text(strip=True)
                key2 = ths[1].get_text(strip=True)
                val2 = tds[1].get_text(strip=True)
                
                assign_metadata_bb(metadata, key1, val1)
                assign_metadata_bb(metadata, key2, val2)
                
            # Single key/value row (e.g. norms).
            elif len(ths) == 1 and len(tds) == 1:
                key = ths[0].get_text(strip=True)
                val = tds[0].get_text(strip=True)
                assign_metadata_bb(metadata, key, val)

    # Sections extracted from Markdownified HTML.
    sections = {
        'leitsatz': r'####\s*Leitsatz\s*:?\s*(.*?)(?=####|\Z)', 
        'tenor': r'####\s*Tenor\s*:?\s*(.*?)(?=####|\Z)',
        'gruende': r'####\s*Gründe\s*:?\s*(.*?)(?=####|\Z)',
        'tatbestand': r'####\s*Tatbestand\s*:?\s*(.*?)(?=####|\Z)',
        'entscheidungsgruende': r'####\s*Entscheidungsgründe\s*:?\s*(.*?)(?=####|\Z)',
    }
    
    for section_name, pattern in sections.items():
        match = re.search(pattern, md_text, re.DOTALL | re.IGNORECASE)
        if match:
            # Clean up residual HTML comments that markdownify couldn't parse
            content = match.group(1).replace('<!--hlIgnoreOn-->', '').replace('<!--hlIgnoreOff-->', '').strip()
            if content:
                metadata[section_name] = content[:500]  # First 500 chars preview
                
    return metadata

def assign_metadata_bb(metadata_dict, key, val):
    key = key.lower()
    if 'gericht' in key and 'ecli' not in key and 'dokumententyp' not in key and 'normen' not in key:
        metadata_dict['gericht'] = val
    elif 'datum' in key:
        # 29.07.2025 -> 20250729
        try:
            day, month, year = val.split('.')
            metadata_dict['datum'] = f"{year}{month}{day}"
        except:
            metadata_dict['datum'] = val
    elif 'aktenzeichen' in key:
        metadata_dict['aktenzeichen'] = val
    elif 'ecli' in key:
        metadata_dict['ecli'] = val
    elif 'dokumententyp' in key:
        metadata_dict['dokumenttyp'] = val
    elif 'normen' in key:
        metadata_dict['norm'] = val


# --- Run ---
base_output_dir = get_state_data_dir("bb", "markdown")
testdata_dir = get_state_data_dir("bb", "raw")

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
    
    metadata = extract_metadata_bb(html_content, markdown_text, doc_name)
    metadata['source_file'] = html_file.name
    metadata['markdown_file'] = output_file.name
    
    json_file = doc_folder / f"{doc_name}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f'Converted: {html_file.name} -> {doc_folder.name}/')

print(f'\nComplete!')