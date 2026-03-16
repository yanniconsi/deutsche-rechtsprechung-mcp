import glob
import json
import os
from concurrent.futures import ProcessPoolExecutor

from tqdm import tqdm
from xml_to_md import convert_xml_to_md_text

EXTRACTED_DIR = "../mcp/data/bgh/raw"
MARKDOWN_DIR = "../mcp/data/bgh/markdown"

def get_safe_worker_count():
    env_workers = os.environ.get("MAX_WORKERS")
    if env_workers and env_workers.isdigit():
        return int(env_workers)
    
    cpu_count = os.cpu_count()
    # Use half cores by default for background tasks
    return max(1, cpu_count // 2)

MAX_WORKERS = get_safe_worker_count()

def process_file(file_info):
    xml_path, md_path = file_info
    
    try:
        markdown_content, metadata = convert_xml_to_md_text(xml_path)
        
        # Ensure subdirectory exists
        os.makedirs(os.path.dirname(md_path), exist_ok=True)
        
        # Save Markdown
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
            
        # Save JSON metadata
        json_path = os.path.splitext(md_path)[0] + ".json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
            
        return True
    except Exception as e:
        return f"Error processing {xml_path}: {e}"

def main():
    if not os.path.exists(EXTRACTED_DIR):
        print(f"Error: '{EXTRACTED_DIR}' directory not found.")
        return

    print(f"Scanning '{EXTRACTED_DIR}' for XML files...")
    # Find all XML files recursively
    xml_files = glob.glob(os.path.join(EXTRACTED_DIR, "**", "*.xml"), recursive=True)
    
    if not xml_files:
        print("No XML files found.")
        return

    print(f"Found {len(xml_files)} XML files. Preparing conversion...")

    tasks = []
    for xml_path in xml_files:
        # Construct output path
        # Relies on the structure extracted/subdir/file.xml -> markdown/subdir/file.md
        rel_path = os.path.relpath(xml_path, EXTRACTED_DIR)
        md_filename = os.path.splitext(rel_path)[0] + ".md"
        md_path = os.path.join(MARKDOWN_DIR, md_filename)
        tasks.append((xml_path, md_path))

    print(f"Starting conversion with {MAX_WORKERS} processes...")
    
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(tqdm(executor.map(process_file, tasks), total=len(tasks), unit="file"))

    # Optional: Report errors
    errors = [r for r in results if r is not True]
    if errors:
        print(f"\n{len(errors)} errors occurred:")
        for err in errors[:10]: # Print first 10 errors
            print(err)
        if len(errors) > 10:
            print("...")
    else:
        print("\nAll files converted successfully.")

if __name__ == "__main__":
    main()
