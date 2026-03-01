import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # add /backend to sys.path

from db.postgres import get_conn
from services.drive import _drive, _list_children


KITTI_GDRIVE_FOLDER_ID = "12YLFl9odK4LyyFAVjDXwIoMVkmUlUlud"


def list_folder_recursive(folder_id: str, current_path: str = "") -> list:
    """
    Recursively list all files in a Google Drive folder and its subfolders.
    
    Args:
        folder_id: Google Drive folder ID to scan
        current_path: Current relative path (used for recursion)
    
    Returns:
        List of dicts with 'name', 'path', and 'id' for each file
    """
    results = []
    
    try:
        children = _list_children(folder_id)
        
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


def ingest_kitti_from_gdrive_auto():
    """
    Automatically ingest KITTI from Google Drive by discovering the folder structure.
    
    This script:
    1. Connects to Google Drive API
    2. Recursively scans your KITTI folder structure
    3. Finds all image files in image_00, image_01, image_02, image_03
    4. Creates database entries with proper media_keys
    """
    
    if KITTI_GDRIVE_FOLDER_ID == "YOUR_KITTI_FOLDER_ID_HERE":
        print("❌ Please set KITTI_GDRIVE_FOLDER_ID in the script first!")
        return
    
    conn = get_conn()
    cur = conn.cursor()

    # 1) Upsert dataset with Google Drive configuration
    cur.execute("""
        INSERT INTO navis.datasets (slug, name, provider, media_base_uri)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (slug) DO UPDATE
            SET name = EXCLUDED.name,
                provider = EXCLUDED.provider,
                media_base_uri = EXCLUDED.media_base_uri
        RETURNING id;
    """, (
        "kitti",
        "KITTI",
        "gdrive",
        f"gdrive://{KITTI_GDRIVE_FOLDER_ID}",
    ))
    dataset_id = cur.fetchone()["id"]
    print(f"✅ Dataset 'kitti' id = {dataset_id}")
    print(f"   Provider: gdrive")
    print(f"   Base URI: gdrive://{KITTI_GDRIVE_FOLDER_ID}\n")

    # 2) Recursively discover folder structure
    print("Scanning Google Drive folder structure...")
    all_files = list_folder_recursive(KITTI_GDRIVE_FOLDER_ID)
    
    print(f"Found {len(all_files)} total files\n")
    
    # 3) Organize files by sequence and sensor
    # Expected path format: City/2011_09_26/2011_09_26_drive_0001_sync/image_00/data/0000000001.png
    sequences_data = {}  # {(sequence_token, sensor): [files]}
    
    for file_info in all_files:
        file_path = file_info['path']
        file_name = file_info['name']
        
        # Skip non-image files
        if not file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        
        # Parse path structure
        parts = file_path.split('/')
        
        # Expected: [scene_type, date, sequence_sync, sensor, 'data', filename]
        if len(parts) < 5:
            continue
        
        # Check if this is in a valid sensor folder (image_00, image_01, image_02, image_03)
        if not any(sensor in parts for sensor in ['image_00', 'image_01', 'image_02', 'image_03']):
            continue
        
        # Find indices of key components
        try:
            sensor_idx = next(i for i, p in enumerate(parts) if p.startswith('image_'))
            sensor = parts[sensor_idx]
            
            # Sequence is the folder right before sensor
            sequence_folder = parts[sensor_idx - 1]
            
            # Must end with _sync
            if not sequence_folder.endswith('_sync'):
                continue
            
            # Build full media_key (relative path from KITTI root)
            media_key = file_path
            
            key = (sequence_folder, sensor)
            if key not in sequences_data:
                sequences_data[key] = []
            
            sequences_data[key].append({
                'sample_token': file_name,
                'media_key': media_key
            })
            
        except (StopIteration, IndexError):
            continue
    
    print(f"Organized into {len(sequences_data)} sequences × sensors\n")
    
    # 4) Insert sequences and frames
    total_frames = 0
    
    for (sequence_token, sensor), frames in sorted(sequences_data.items()):
        # Upsert sequence
        cur.execute("""
            INSERT INTO navis.sequences (dataset_id, scene_token, sensor)
            VALUES (%s, %s, %s)
            ON CONFLICT (dataset_id, scene_token, sensor) DO UPDATE
                SET sensor = EXCLUDED.sensor
            RETURNING id;
        """, (dataset_id, sequence_token, sensor))
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
        print(f"✓ {sequence_token:40s} / {sensor:9s} → {rows_inserted:4d} frames")

    conn.commit()
    cur.close()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✅ KITTI ingestion completed!")
    print(f"   Total sequences: {len(sequences_data)}")
    print(f"   Total frames: {total_frames}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    print("=" * 60)
    print("KITTI Google Drive Auto-Discovery Ingestion")
    print("=" * 60)
    print("\n⚠️  Before running, make sure:")
    print("   1. Set KITTI_GDRIVE_FOLDER_ID in this script")
    print("   2. Google Drive credentials are configured")
    print("   3. The KITTI folder is shared with your service account\n")
    
    response = input("Continue with ingestion? (y/n): ")
    if response.lower() == 'y':
        ingest_kitti_from_gdrive_auto()
    else:
        print("Aborted.")