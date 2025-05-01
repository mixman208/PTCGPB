import os
import mmh3
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

def get_file_hash(file_path):
    """Find MurmurHash3 hash of a file's content."""
    with open(file_path, 'rb') as file:
        content = file.read()
        return mmh3.hash_bytes(content)

def find_xml_files(root_dir):
    """Find all XML files in the directory."""
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith('.xml'):
                yield os.path.join(dirpath, filename)

def get_file_info(file_path):
    """Get file hash and modification time."""
    return {
        'hash': get_file_hash(file_path),
        'mtime': os.path.getmtime(file_path),
        'path': file_path
    }

def scan_for_duplicates(root_dir, max_threads=8):
    """Scan for duplicate XML files and return a list of duplicates."""
    seen_files = {}
    duplicates = []
    lock = threading.Lock()

    def process_file(xml_file):
        file_info = get_file_info(xml_file)
        with lock:
            if file_info['hash'] in seen_files:
                # Compare modification times and order files by date
                existing = seen_files[file_info['hash']]
                older = existing if existing['mtime'] < file_info['mtime'] else file_info
                newer = existing if existing['mtime'] >= file_info['mtime'] else file_info
                duplicates.append((older, newer))
            else:
                seen_files[file_info['hash']] = file_info

    print(f"\nScanning '{root_dir}' for duplicate XML files...\n")
    with ThreadPoolExecutor(max_threads) as executor:
        executor.map(process_file, find_xml_files(root_dir))

    return duplicates

def format_date(timestamp):
    """Convert timestamp to readable date."""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def delete_file(file_path):
    """Delete the picked file."""
    try:
        os.remove(file_path)
        print(f"[DELETED] {file_path}")
    except Exception as e:
        print(f"Error deleting {file_path}: {e}")

if __name__ == "__main__":
    while True:
        directory_to_search = input("Enter the directory path to search for XML files: ").strip()
        if os.path.isdir(directory_to_search):
            break
        else:
            print(" Invalid directory. Please enter a valid folder path.\n")

    duplicate_files = scan_for_duplicates(directory_to_search)

    if duplicate_files:
        num_duplicates = len(duplicate_files)
        deleted_count = 0
        
        for older, newer in duplicate_files:
            delete_file(older['path'])
            deleted_count += 1

        print(f"\nSuccessfully deleted {deleted_count} older duplicate{'s' if deleted_count > 1 else ''}.")
    else:
        print("\nNo duplicate XML files found.")

    input("\nPress Enter to close...")
