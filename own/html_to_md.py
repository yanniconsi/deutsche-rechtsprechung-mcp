from markdownify import markdownify as md
import os
import re
import json
from pathlib import Path
from datetime import datetime

def extract_metadata_from_markdown(md_text, filename):
    """
    Extracts metadata from Markdown text converted from HTML.
    Parses table-based metadata and document sections.
    """
    metadata = {}
    
    # Extract doknr from filename
    metadata['doknr'] = Path(filename).stem
    
    # Extract table metadata (Pattern: | **Key:** | Value |)
    table_pattern = r'\|\s*\*\*([^*]+)\*\*\s*\|\s*([^|]+?)\s*\|'
    matches = re.findall(table_pattern, md_text)
    
    for key, value in matches:
        key = key.strip()
        value = value.strip()
        
        if key == 'Gericht:':
            metadata['gericht'] = value
        elif key == 'Entscheidungsdatum:':
            date_str = value
            try:
                date_obj = datetime.strptime(date_str, '%d.%m.%Y')
                metadata['datum'] = date_obj.strftime('%Y%m%d')
            except:
                metadata['datum'] = value  # Keep original if parsing fails
        elif key == 'Aktenzeichen:':
            metadata['aktenzeichen'] = value
        elif key == 'ECLI:':
            metadata['ecli'] = value
        elif key == 'Dokumenttyp:':
            metadata['dokumenttyp'] = value
        elif key == 'Normen:':
            metadata['norm'] = value
        elif key == 'Rechtskraft:':
            metadata['rechtskraft'] = value
    
    # Extract title - often after "Langtext" as :   Text
    title_pattern = r'Langtext\s*:?\s*([^\n#]+)'
    title_match = re.search(title_pattern, md_text)
    if title_match:
        metadata['title'] = title_match.group(1).strip()
    
    sections = {
        'leitsatz': r'####\s*Leitsatz\s*:?\s*(.*?)(?=####|\Z)',
        'tenor': r'####\s*Tenor\s*:?\s*(.*?)(?=####|\Z)',
        'tatbestand': r'####\s*Tatbestand\s*:?\s*(.*?)(?=####|\Z)',
        'gruende': r'####\s*Gründe\s*:?\s*(.*?)(?=####|\Z)',
        'entscheidungsgruende': r'####\s*Entscheidungsgründe\s*:?\s*(.*?)(?=####|\Z)',
    }
    
    for section_name, pattern in sections.items():
        match = re.search(pattern, md_text, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            if content:
                metadata[section_name] = content[:500]  # First 500 chars as preview
    
    return metadata

base_output_dir = Path('../mcp/markdown_bw')
base_output_dir.mkdir(exist_ok=True)

testdata_dir = Path('testdata')
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
    
    metadata = extract_metadata_from_markdown(markdown_text, doc_name)
    metadata['source_file'] = html_file.name
    metadata['markdown_file'] = output_file.name
    
    json_file = doc_folder / f"{doc_name}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f'Converted: {html_file.name} -> {doc_folder.name}/ ({output_file.name} + {json_file.name})')

print(f'\nComplete! All files saved in subdirectories of {base_output_dir}.')