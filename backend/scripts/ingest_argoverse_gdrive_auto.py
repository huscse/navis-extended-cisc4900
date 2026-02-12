import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # add /backend to sys.path

from db.postgres import get_conn
from services.drive import _drive, _list_children


ARGOVERSE_GDRIVE_FOLDER_ID = "1RQvwxeWESbtd3pO0hyUi1dzMeVI3Fnbr"


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


def ingest_argoverse_from_gdrive_auto():
    """
    Automatically ingest Argoverse from Google Drive by discovering the folder structure.
    
    Argoverse structure:
    Argoverse/
      └── scenes/
          └── c6911883-1843-3727-8.../
              ├── ring_front_center/*.jpg
              ├── ring_front_right/*.jpg
              ├── ring_rear_right/*.jpg
              ├── ring_side_left/*.jpg
              └── ring_side_right/*.jpg
    """
    
    if ARGOVERSE_GDRIVE_FOLDER_ID == "YOUR_ARGOVERSE_FOLDER_ID_HERE":
        print("❌ Please set ARGOVERSE_GDRIVE_FOLDER_ID in the script first!")
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
        "argoverse",
        "Argoverse",
        "gdrive",
        f"gdrive://{ARGOVERSE_GDRIVE_FOLDER_ID}",
    ))
    dataset_id = cur.fetchone()["id"]
    print(f"✅ Dataset 'argoverse' id = {dataset_id}")
    print(f"   Provider: gdrive")
    print(f"   Base URI: gdrive://{ARGOVERSE_GDRIVE_FOLDER_ID}\n")

    # 2) Recursively discover folder structure
    print("Scanning Google Drive folder structure...")
    all_files = list_folder_recursive(ARGOVERSE_GDRIVE_FOLDER_ID)
    
    print(f"Found {len(all_files)} total files\n")
    
    # 3) Organize files by sequence (scene_id) and sensor (camera name)
    # Expected path format: scenes/c6911883-1843-3727-8.../ring_front_center/frame_000001.jpg
    sequences_data = {}  # {(scene_id, camera): [files]}
    
    for file_info in all_files:
        file_path = file_info['path']
        file_name = file_info['name']
        
        # Skip non-image files
        if not file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        
        # Parse path structure
        parts = file_path.split('/')
        
        # Expected: ['scenes', 'c6911883-1843-3727-8...', 'ring_front_center', 'frame_000001.jpg']
        # Or could be: ['argoverse-tracking', 'scenes', 'c6911883...', 'ring_front_center', 'frame_000001.jpg']
        
        # Find 'scenes' in the path
        try:
            if 'scenes' not in parts:
                continue
            
            scenes_idx = parts.index('scenes')
            
            # Scene ID is right after 'scenes'
            if len(parts) <= scenes_idx + 1:
                continue
            
            scene_id = parts[scenes_idx + 1]
            
            # Camera name is after scene_id
            if len(parts) <= scenes_idx + 2:
                continue
                
            camera = parts[scenes_idx + 2]
            
            # Only process ring cameras
            if not camera.startswith('ring_'):
                continue
            
            # Build full media_key (relative path from Argoverse root)
            media_key = file_path
            
            key = (scene_id, camera)
            if key not in sequences_data:
                sequences_data[key] = []
            
            sequences_data[key].append({
                'sample_token': file_name,
                'media_key': media_key
            })
            
        except (ValueError, IndexError) as e:
            print(f"⚠️  Skipping malformed path: {file_path}")
            continue
    
    print(f"Organized into {len(sequences_data)} sequences × cameras\n")
    
    # 4) Insert sequences and frames
    total_frames = 0
    
    for (scene_id, camera), frames in sorted(sequences_data.items()):
        # Upsert sequence
        cur.execute("""
            INSERT INTO navis.sequences (dataset_id, scene_token, sensor)
            VALUES (%s, %s, %s)
            ON CONFLICT (dataset_id, scene_token, sensor) DO UPDATE
                SET sensor = EXCLUDED.sensor
            RETURNING id;
        """, (dataset_id, scene_id, camera))
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
        print(f"✓ {scene_id[:20]:20s} / {camera:20s} → {rows_inserted:4d} frames")

    conn.commit()
    cur.close()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✅ Argoverse ingestion completed!")
    print(f"   Total sequences: {len(sequences_data)}")
    print(f"   Total frames: {total_frames}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Argoverse Google Drive Auto-Discovery Ingestion")
    print("=" * 60)
    print("\n⚠️  Before running, make sure:")
    print("   1. ARGOVERSE_GDRIVE_FOLDER_ID is set correctly")
    print("   2. Google Drive credentials are configured")
    print("   3. The Argoverse folder is shared with your service account\n")
    
    response = input("Continue with ingestion? (y/n): ")
    if response.lower() == 'y':
        ingest_argoverse_from_gdrive_auto()
    else:
        print("Aborted.")