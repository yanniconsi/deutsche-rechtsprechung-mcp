import os
import sys
import xml.etree.ElementTree as ET

import requests
from tqdm import tqdm


def download_toc(url, filepath):
    if os.path.exists(filepath):
        print(f"File '{filepath}' already exists. Skipping download.")
        return

    print(f"Downloading {url} to {filepath}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filepath, 'wb') as f, tqdm(
            desc=filepath,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(chunk_size=1024):
                size = f.write(chunk)
                bar.update(size)
        print(f"Successfully downloaded {filepath}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        sys.exit(1)

def extract_links(xml_file, output_file):
    if not os.path.exists(xml_file):
        print(f"Error: File '{xml_file}' not found.")
        return

    print(f"Extracting links from {xml_file} to {output_file}...")
    count = 0
    try:
        with open(output_file, 'w') as f:
            # Use iterparse for memory efficiency with large XML files
            context = ET.iterparse(xml_file, events=('end',))
            for event, elem in context:
                if elem.tag == 'link' and elem.text:
                    f.write(elem.text.strip() + '\n')
                    count += 1
                    # Clear the element to free memory
                    elem.clear()
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    print(f"Done. Extracted {count} links.")

if __name__ == "__main__":
    toc_url = "https://www.rechtsprechung-im-internet.de/rii-toc.xml"
    toc_file = "data/rii-toc.xml"
    links_file = "data/links.txt"
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    download_toc(toc_url, toc_file)
    extract_links(toc_file, links_file)

