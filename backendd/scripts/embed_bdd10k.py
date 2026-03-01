import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from db.postgres import get_conn
from sentence_transformers import SentenceTransformer
from services.drive import resolve_path, download_bytes
from PIL import Image
import io
import numpy as np

# Load model
model = SentenceTransformer('clip-ViT-B-32')
MODEL_ID = 4  # Use existing model_id

# Get BDD10K frames without embeddings
conn = get_conn()
cur = conn.cursor()

cur.execute("""
    SELECT f.id, f.media_key, d.media_base_uri
    FROM navis.frames f
    JOIN navis.sequences s ON f.sequence_id = s.id
    JOIN navis.datasets d ON s.dataset_id = d.id
    WHERE d.name = 'BDD10K'
    AND NOT EXISTS (SELECT 1 FROM navis.embeddings e WHERE e.frame_id = f.id)
""")

frames = cur.fetchall()
print(f"Found {len(frames)} BDD10K frames to embed\n")

for i, row in enumerate(frames):
    try:
        # Access by column name (dict-like)
        frame_id = row['id']
        media_key = row['media_key']
        base_uri = row['media_base_uri']
        
        # DEBUG: Print what we're working with
        if i == 0:
            print(f"DEBUG: base_uri = {base_uri}")
            print(f"DEBUG: media_key = {media_key}\n")
        
        # Extract root folder ID from gdrive://...
        root_id = base_uri.replace('gdrive://', '')
        
        # Resolve path and download
        file_id = resolve_path(root_id, media_key)
        if not file_id:
            print(f"[{i+1}/{len(frames)}] ❌ Could not resolve: {media_key}")
            continue
            
        img_bytes = download_bytes(file_id)
        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        
        # Generate embedding
        embedding = model.encode(img, convert_to_numpy=True)
        
        # ✅ L2 NORMALIZE - CRITICAL FOR COSINE SIMILARITY!
        # This makes embeddings compatible with text_embed.py normalization
        embedding = embedding / np.linalg.norm(embedding)
        
        # Insert into database
        cur.execute("""
            INSERT INTO navis.embeddings (frame_id, model_id, emb)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (frame_id, MODEL_ID, embedding.tolist()))
        
        conn.commit()
        print(f"[{i+1}/{len(frames)}] ✅ Embedded frame {frame_id}")
        
    except Exception as e:
        print(f"[{i+1}/{len(frames)}] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        continue

cur.close()
conn.close()
print(f"\n✅ Done! Run build_faiss_index.py to update search index")