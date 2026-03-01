"""
Run object detection on frames and store results in the database.
Uses YOLOv8 for fast, accurate detection.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # add /backend to sys.path

from db.postgres import get_conn
from services.drive import resolve_path, download_bytes

from ultralytics import YOLO
from urllib.parse import urlparse
import io
from PIL import Image
import numpy as np
from psycopg.rows import dict_row

# Initialize YOLO model (will download on first run)
model = YOLO('yolov8n.pt')  # nano model, fastest

# COCO class names that are relevant for autonomous driving
RELEVANT_CLASSES = {
    'person', 'bicycle', 'car', 'motorcycle', 'bus', 'truck',
    'traffic light', 'stop sign', 'parking meter', 'dog', 'cat'
}

def detect_and_store(frame_id: int, image_bytes: bytes):
    """Run YOLO on image bytes and return detections"""
    # Convert bytes to PIL Image
    img = Image.open(io.BytesIO(image_bytes))
    
    # Convert grayscale to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Convert to numpy array
    img_array = np.array(img)
    
    # Run detection
    results = model(img_array, verbose=False)
    
    detections = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            cls = int(box.cls[0])
            class_name = model.names[cls]
            confidence = float(box.conf[0])
            
            # Only store relevant classes with confidence > 0.3
            if class_name in RELEVANT_CLASSES and confidence > 0.3:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append({
                    'frame_id': frame_id,
                    'object_type': class_name,
                    'confidence': confidence,
                    'bbox_x1': x1,
                    'bbox_y1': y1,
                    'bbox_x2': x2,
                    'bbox_y2': y2
                })
    
    return detections

def process_frames(limit=None):
    """Process all frames without detections"""
    # Get list of frames to process
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            # Find frames without detections - ONLY from gdrive provider
            query = """
                SELECT f.id, f.media_key, d.media_base_uri
                FROM navis.frames f
                JOIN navis.sequences s ON f.sequence_id = s.id
                JOIN navis.datasets d ON s.dataset_id = d.id
                WHERE NOT EXISTS (
                    SELECT 1 FROM navis.frame_objects fo 
                    WHERE fo.frame_id = f.id
                )
                AND d.provider = 'gdrive' AND d.name IN ('KITTI', 'Argoverse') AND s.scene_token != '2011_09_26_drive_0001_sync'
                ORDER BY f.id
            """
            if limit:
                query += f" LIMIT {limit}"
            
            cur.execute(query)
            frames = cur.fetchall()
    
    print(f"Found {len(frames)} frames to process")
    
    for i, row in enumerate(frames):
        frame_id = row['id']
        media_key = row['media_key']
        media_base_uri = row['media_base_uri']
        
        print(f"[{i+1}/{len(frames)}] Processing frame {frame_id}: {media_key}")
        
        try:
            # Download image from Google Drive
            parsed = urlparse(media_base_uri)
            root_id = parsed.netloc
            
            file_id = resolve_path(root_id, media_key)
            if not file_id:
                print(f"  ❌ Could not resolve path")
                continue
            
            image_bytes = download_bytes(file_id)
            
            # Detect objects
            detections = detect_and_store(frame_id, image_bytes)
            
            if detections:
                # Insert into database
                with get_conn() as conn:
                    with conn.cursor() as cur:
                        for det in detections:
                            cur.execute("""
                                INSERT INTO navis.frame_objects 
                                (frame_id, object_type, confidence, bbox_x1, bbox_y1, bbox_x2, bbox_y2)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (
                                det['frame_id'], det['object_type'], det['confidence'],
                                det['bbox_x1'], det['bbox_y1'], det['bbox_x2'], det['bbox_y2']
                            ))
                    conn.commit()
                
                print(f"  ✅ Found {len(detections)} objects: {[d['object_type'] for d in detections]}")
            else:
                print(f"  ⚪ No relevant objects detected")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, help='Limit number of frames to process')
    args = parser.parse_args()
    
    print("Starting object detection...")
    print("=" * 60)
    process_frames(limit=args.limit)
    print("=" * 60)
    print("Done!")
