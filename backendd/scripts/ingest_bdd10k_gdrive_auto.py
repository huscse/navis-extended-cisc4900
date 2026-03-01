import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db.postgres import get_conn
from services.drive import list_files


BDD10K_GDRIVE_FOLDER_ID = "1YnqzayO06QBSShBnOf4UufjHXm8Hi9tP"  # 10k folder


def list_folder_recursive(folder_id: str, current_path: str = "") -> list:
    """Recursively list all files in a Google Drive folder."""
    results = []
    
    try:
        children = list_files(folder_id)
        
        for item in children:
            item_name = item['name']
            item_id = item['id']
            item_type = item['mimeType']
            
            item_path = f"{current_path}/{item_name}" if current_path else item_name
            
            # If it's a folder, recurse into it
            if item_type == 'application/vnd.google-apps.folder':
                print(f"  Scanning folder: {item_path}")
                results.extend(list_folder_recursive(item_id, item_path))
            else:
                # It's a file
                results.append({
                    'name': item_name,
                    'path': item_path,
                    'id': item_id
                })
        
    except Exception as e:
        print(f"Error scanning folder {current_path}: {e}")
    
    return results


def ingest_bdd10k_from_gdrive():
    """
    Ingest BDD10K from Google Drive.
    
    Expected structure:
    10k/
    ├── test/*.jpg
    ├── train/*.jpg
    └── val/*.jpg
    """
    
    conn = get_conn()
    cur = conn.cursor()

    # 1) Upsert dataset
    cur.execute("""
        INSERT INTO navis.datasets (slug, name, provider, media_base_uri)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (slug) DO UPDATE
            SET name = EXCLUDED.name,
                provider = EXCLUDED.provider,
                media_base_uri = EXCLUDED.media_base_uri
        RETURNING id;
    """, (
        "bdd10k",
        "BDD10K",
        "gdrive",
        f"gdrive://{BDD10K_GDRIVE_FOLDER_ID}",
    ))
    dataset_id = cur.fetchone()["id"]
    print(f"✅ Dataset 'bdd10k' id = {dataset_id}")
    print(f"   Provider: gdrive")
    print(f"   Base URI: gdrive://{BDD10K_GDRIVE_FOLDER_ID}\n")

    # 2) Scan folder structure
    print("Scanning Google Drive folder structure...")
    all_files = list_folder_recursive(BDD10K_GDRIVE_FOLDER_ID)
    
    print(f"Found {len(all_files)} total files\n")
    
    # 3) Organize by split (test/train/val)
    splits = {}  # {split_name: [files]}
    
    for file_info in all_files:
        file_path = file_info['path']
        file_name = file_info['name']
        
        # Only process .jpg files
        if not file_name.lower().endswith('.jpg'):
            continue
        
        # Parse path: "test/c0a0a0b1a-7c39d841.jpg" or "train/image.jpg"
        parts = file_path.split('/')
        
        if len(parts) < 2:
            print(f"⚠️  Skipping {file_path} (unexpected structure)")
            continue
        
        split = parts[0]  # test, train, or val
        
        if split not in splits:
            splits[split] = []
        
        splits[split].append({
            'sample_token': file_name.replace('.jpg', ''),  # Remove extension for token
            'media_key': file_path
        })
    
    print(f"Found {len(splits)} splits: {list(splits.keys())}\n")
    
    # 4) Insert sequences and frames
    total_frames = 0
    
    for split_name in sorted(splits.keys()):
        frames = splits[split_name]
        
        # Create one sequence per split (test, train, val)
        cur.execute("""
            INSERT INTO navis.sequences (dataset_id, scene_token, sensor)
            VALUES (%s, %s, %s)
            ON CONFLICT (dataset_id, scene_token, sensor) DO UPDATE
                SET sensor = EXCLUDED.sensor
            RETURNING id;
        """, (dataset_id, split_name, "camera"))
        sequence_id = cur.fetchone()["id"]
        
        # Insert frames in batch
        batch = [(sequence_id, f['sample_token'], f['media_key']) for f in frames]
        
        cur.executemany("""
            INSERT INTO navis.frames (sequence_id, sample_token, media_key)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING;
        """, batch)
        
        rows_inserted = cur.rowcount
        total_frames += rows_inserted
        print(f"✓ {split_name:10s} → {rows_inserted:5d} frames")

    conn.commit()
    cur.close()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✅ BDD10K ingestion completed!")
    print(f"   Total splits: {len(splits)}")
    print(f"   Total frames: {total_frames}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    print("=" * 60)
    print("BDD10K Google Drive Ingestion")
    print("=" * 60)
    print("\n⚠️  This will ingest images from: test/, train/, val/\n")
    
    response = input("Continue with ingestion? (y/n): ")
    if response.lower() == 'y':
        ingest_bdd10k_from_gdrive()
    else:
        print("Aborted.")