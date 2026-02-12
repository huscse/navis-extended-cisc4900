import os
import sys
from pathlib import Path

# Add backend to path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from backend.db.postgres import get_conn

def main():
    dataset_id = 4  # Your KITTI dataset ID
    scene_token = "2011_09_26_drive_0001_sync"
    
    # Sensors to add
    sensors = ["image_01", "image_02", "image_03"]
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            for sensor in sensors:
                # Insert sequence
                cur.execute("""
                    INSERT INTO navis.sequences (dataset_id, scene_token, sensor)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (dataset_id, scene_token, sensor) DO UPDATE
                        SET sensor = EXCLUDED.sensor
                    RETURNING id;
                """, (dataset_id, scene_token, sensor))
                
                result = cur.fetchone()
                sequence_id = result["id"] if isinstance(result, dict) else result[0]
                print(f"✅ Created sequence {sensor} with id={sequence_id}")
                
                # Insert frames (assuming same 108 frames as image_00)
                batch = []
                for i in range(108):
                    frame_file = f"{i:010d}.png"
                    media_key = f"City/2011_09_26/2011_09_26_drive_0001_sync/{sensor}/data/{frame_file}"
                    batch.append((sequence_id, media_key))
                
                cur.executemany("""
                    INSERT INTO navis.frames (sequence_id, media_key)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, batch)
                
                print(f"   Added {len(batch)} frames for {sensor}")
            
            conn.commit()
            print("\n🎉 Done! Added image_01, image_02, image_03 sequences")

if __name__ == "__main__":
    main()