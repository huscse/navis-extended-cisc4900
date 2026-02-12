# backend/workers/embedder.py
from __future__ import annotations
import argparse
import io
import sys
import time
import traceback
from pathlib import Path
from urllib.parse import urlparse
from functools import lru_cache

import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer

# --- Make "backend" imports work whether you run from repo root or /backend ---
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

from db.postgres import get_conn
from services.drive import resolve_path, download_bytes

# -------------------------- CLI args -----------------------------------------
parser = argparse.ArgumentParser(description="Embed frames and store vectors in Postgres.")
parser.add_argument("--limit", type=int, default=32, help="Max frames per batch (default: 32)")
parser.add_argument("--once", action="store_true", help="Process one batch and exit")
parser.add_argument("--dataset", type=str, default=None, help="Filter by dataset slug (e.g., kitti, nuscenes)")
parser.add_argument("--scene", type=str, default=None, help="Filter by scene_token")
parser.add_argument("--sensor", type=str, default=None, help="Filter by sensor (e.g., image_00, CAM_FRONT)")

ARGS = parser.parse_args()

# -------------------------- Model --------------------------------------------
@lru_cache(maxsize=1)
def _get_model():
    """Load CLIP model using sentence-transformers (cached)."""
    return SentenceTransformer('clip-ViT-B-32')

MODEL_NAME = "openai/clip-vit-b-32"
MODEL_DIMS = 512

# -------------------------- Helpers ------------------------------------------
def get_col(row, key_or_idx):
    """Return a column from a row (works for dict-like or tuple rows)."""
    if isinstance(row, dict):
        return row[key_or_idx]
    return row[key_or_idx]  # index for tuple rows

def get_or_create_model_id(cur) -> int:
    cur.execute("SELECT id FROM navis.models WHERE name=%s", (MODEL_NAME,))
    r = cur.fetchone()
    if r:
        return get_col(r, "id") if isinstance(r, dict) else r[0]
    cur.execute(
        "INSERT INTO navis.models(name, dims) VALUES (%s,%s) RETURNING id",
        (MODEL_NAME, MODEL_DIMS),
    )
    r = cur.fetchone()
    return get_col(r, "id") if isinstance(r, dict) else r[0]

def load_image_for_frame(conn, frame_id: int, media_key: str) -> Image.Image:
    """Use dataset media_base_uri to decide how to fetch (gdrive vs local)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT d.media_base_uri AS media_base_uri
            FROM navis.frames f
            JOIN navis.sequences s ON s.id = f.sequence_id
            JOIN navis.datasets  d ON d.id = s.dataset_id
            WHERE f.id = %s
            LIMIT 1
            """,
            (frame_id,),
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError(f"No dataset root for frame_id={frame_id}")
        media_base_uri = row["media_base_uri"] if isinstance(row, dict) else row[0]

    parsed = urlparse(media_base_uri or "")
    if parsed.scheme == "gdrive":
        root_id = parsed.netloc  # folder id after gdrive://
        file_id = resolve_path(root_id, media_key)
        if not file_id:
            raise FileNotFoundError(f"GDrive path not found: {media_key}")
        data = download_bytes(file_id)
        return Image.open(io.BytesIO(data)).convert("RGB")

    # local fallback (adjust base as needed)
    base = BACKEND_ROOT / "data" / "kitti"
    img_path = (base / media_key).resolve()
    if not img_path.exists():
        raise FileNotFoundError(f"Local file not found: {img_path}")
    return Image.open(img_path).convert("RGB")

def embed_image(img: Image.Image) -> np.ndarray:
    """Encode image using sentence-transformers CLIP model."""
    model = _get_model()
    
    # Convert PIL image to embedding
    embedding = model.encode(img, convert_to_numpy=True)
    
    # L2 normalize for cosine similarity
    embedding = embedding / np.linalg.norm(embedding)
    
    return embedding.astype(np.float32)

# -------------------------- Main loop ----------------------------------------
def main():
    while True:
        with get_conn() as conn, conn.cursor() as cur:
            model_id = get_or_create_model_id(cur)
            conn.commit()

            # Build dynamic WHERE with optional filters
            where_clauses = [
                "NOT EXISTS (SELECT 1 FROM navis.embeddings e WHERE e.frame_id = f.id AND e.model_id = %s)"
            ]
            params = [model_id]

            if ARGS.dataset:
                where_clauses.append("d.slug = %s")
                params.append(ARGS.dataset)

            if ARGS.scene:
                where_clauses.append("s.scene_token = %s")
                params.append(ARGS.scene)

            if ARGS.sensor:
                where_clauses.append("s.sensor = %s")
                params.append(ARGS.sensor)

            where_sql = " AND ".join(where_clauses)

            sql = f"""
                SELECT f.id, f.media_key
                FROM navis.frames f
                JOIN navis.sequences s ON s.id = f.sequence_id
                JOIN navis.datasets d ON d.id = s.dataset_id
                WHERE {where_sql}
                ORDER BY f.id
                LIMIT %s
            """
            params.append(ARGS.limit)

            batch = cur.fetchall()
            # psycopg might return dict or tuple rows
            if batch and isinstance(batch[0], dict):
                batch = [(r["id"], r["media_key"]) for r in batch]

        if not batch:
            print("✅ No pending frames for this model/filter. Sleeping 10s…")
            if ARGS.once:
                return
            time.sleep(10)
            continue

        # Process embeddings
        to_insert = []
        for frame_id, media_key in batch:
            print(f"Embedding frame {frame_id} — {media_key}")
            try:
                img = load_image_for_frame(conn, frame_id, media_key)
                emb_vec = embed_image(img)
                emb_json = emb_vec.tolist()
                to_insert.append((frame_id, model_id, emb_json))
                print(f"✅ Embedded frame_id={frame_id}")
            except Exception as e:
                print(f"⚠️ Skipping frame_id={frame_id}: {e}")
                traceback.print_exc()
                continue

        # Bulk insert embeddings
        if to_insert:
            import json
            with get_conn() as conn, conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO navis.embeddings (frame_id, model_id, emb)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    [(fid, mid, json.dumps(emb)) for fid, mid, emb in to_insert],
                )
            conn.commit()

        if ARGS.once:
            print("Done one batch (--once). Exiting.")
            return

if __name__ == "__main__":
    main()
