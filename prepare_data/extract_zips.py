import os
import zipfile

from tqdm import tqdm

DOWNLOAD_DIR = "data/downloads"
EXTRACT_DIR = "data/extracted"

def extract_all_zips():
    if not os.path.exists(DOWNLOAD_DIR):
        print(f"Error: '{DOWNLOAD_DIR}' directory not found.")
        return

    if not os.path.exists(EXTRACT_DIR):
        os.makedirs(EXTRACT_DIR)

    zip_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.lower().endswith('.zip')]
    
    if not zip_files:
        print("No zip files found in downloads directory.")
        return

    print(f"Found {len(zip_files)} zip files. Extracting...")

    for zip_filename in tqdm(zip_files, unit="file"):
        zip_path = os.path.join(DOWNLOAD_DIR, zip_filename)
        folder_name = os.path.splitext(zip_filename)[0]
        target_folder = os.path.join(EXTRACT_DIR, folder_name)
        
        if os.path.exists(target_folder):
            # print(f"Skipping {zip_filename}, folder exists.") # Optional: uncomment for verbose output
            continue

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_folder)
        except zipfile.BadZipFile:
            print(f"Warning: '{zip_filename}' is not a valid zip file. Skipped.")
        except Exception as e:
            print(f"Error extracting '{zip_filename}': {e}")

    print(f"Extraction complete. Files are in '{EXTRACT_DIR}'.")

if __name__ == "__main__":
    extract_all_zips()
