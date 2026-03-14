from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from urllib.parse import urlparse
from psycopg.rows import dict_row
from pathlib import Path
import numpy as np
from collections import defaultdict
from backendd.services.hybrid_rerank import hybrid_rerank
# DON'T import faiss here - import it inside the function

from backendd.db.postgres import get_conn
from backendd.services.text_embed import get_text_embedding

router = APIRouter(prefix="/search", tags=["search"])

# Load FAISS index on startup
BACKEND_ROOT = Path(__file__).resolve().parents[1]
FAISS_INDEX_PATH = BACKEND_ROOT / "faiss_indexes" / "combined.index"
FAISS_MAPPING_PATH = BACKEND_ROOT / "faiss_indexes" / "combined_mapping.npy"

# Global variables for FAISS index
_faiss_index = None
_frame_id_mapping = None

def load_faiss_index():
    """Load FAISS index and frame ID mapping (lazy loading)"""
    global _faiss_index, _frame_id_mapping
    
    if _faiss_index is not None:
        return  # Already loaded
    
    if not FAISS_INDEX_PATH.exists():
        raise RuntimeError(f"FAISS index not found at {FAISS_INDEX_PATH}")
    
    import faiss  # Import here instead of top of file
    _faiss_index = faiss.read_index(str(FAISS_INDEX_PATH))
    _frame_id_mapping = np.load(str(FAISS_MAPPING_PATH))
    print(f"✅ Loaded FAISS index with {_faiss_index.ntotal} vectors")


class SearchHit(BaseModel):
    frame_id: int
    score: float
    media_key: str
    media_url: str
    dataset: str
    sequence: str
    sensor: str
    frame_number: str

class SearchResponse(BaseModel):
    query: str
    k: int
    hits: List[SearchHit]

def _media_url(media_base_uri: Optional[str], media_key: str) -> str:
    if not media_base_uri:
        return f"/media/local/{media_key}"
    parsed = urlparse(media_base_uri)
    if parsed.scheme == "gdrive":
        return f"/media/gdrive/{media_key}"
    return f"/media/local/{media_key}"

@router.get("", response_model=SearchResponse, summary="Semantic search over frames (FAISS-powered)")
def search(
    q: str = Query(..., alias="text", description="Natural language query"),
    k: int = Query(50, ge=1, le=100, description="Top-K results"),
    dataset: Optional[str] = Query(None, description="Dataset slug filter (e.g. 'kitti')"),
    sequence: Optional[str] = Query(None, description="Sequence name/scene filter"),
    objects: Optional[str] = Query(None, description="Comma-separated object types to filter (e.g., 'car,person')"),
):
    load_faiss_index()
    
    if _faiss_index is None or _frame_id_mapping is None:
        raise HTTPException(status_code=500, detail="FAISS index not loaded")
    
    # AUTO-DETECT object keywords in query
    if not objects:
        query_lower = q.lower()
        keyword_map = {
            'car': ['car', 'cars', 'vehicle', 'vehicles', 'automobile', 'automobiles'],
            'person': ['person', 'people', 'pedestrian', 'pedestrians', 'human', 'humans', 'walking', 'standing', 'man', 'woman'],
            'truck': ['truck', 'trucks', 'lorry', 'lorries'],
            'bicycle': ['bicycle', 'bicycles', 'bike', 'bikes', 'cycling', 'cyclist', 'cyclists'],
            'motorcycle': ['motorcycle', 'motorcycles', 'motorbike', 'motorbikes'],
            'traffic light': ['traffic light', 'traffic lights', 'stoplight', 'stoplights', 'signal', 'signals'],
            'bus': ['bus', 'buses'],
            'dog': ['dog', 'dogs', 'puppy', 'puppies'],
            'cat': ['cat', 'cats', 'kitten', 'kittens'],
            'stop sign': ['stop sign', 'stop signs'],
        }
        
        detected_objects = []
        for obj_type, keywords in keyword_map.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_objects.append(obj_type)
        
        if detected_objects:
            objects = ','.join(detected_objects)
            print(f"🔍 Auto-detected objects in query '{q}': {objects}")
    
    # 1) Embed the text query
    qvec = get_text_embedding(q)
    qvec_np = np.array([qvec], dtype=np.float32)
    
    # 2) Determine search multiplier based on filters
    multiplier = 3

    if objects:
        rare_objects = ['truck', 'motorcycle', 'traffic light', 'dog', 'bicycle', 'bus']
        object_list = [obj.strip() for obj in objects.split(',')]
        if any(obj in rare_objects for obj in object_list):
            multiplier = 50
        else:
            multiplier = 10
    
    search_k = min(k * multiplier, _faiss_index.ntotal)
    distances, indices = _faiss_index.search(qvec_np, search_k)
    
    # 3) Map FAISS indices back to frame IDs
    candidate_frame_ids = _frame_id_mapping[indices[0]].tolist()
    candidate_distances = distances[0].tolist()
    
    # 4) Fetch metadata from Postgres and apply filters
    placeholders = ','.join(['%s'] * len(candidate_frame_ids))
    
    sql = f"""
    WITH RankedFrames AS (
        SELECT DISTINCT ON (f.media_key)
            f.id        AS frame_id,
            f.media_key AS media_key,
            f.sample_token AS sample_token,
            d.slug      AS dataset_slug,
            d.name      AS dataset_name,
            s.scene_token AS sequence_name,
            s.sensor    AS sensor,
            d.media_base_uri AS media_base_uri,
            f.id as original_id
        FROM navis.frames f
        JOIN navis.sequences s ON s.id = f.sequence_id
        JOIN navis.datasets d  ON d.id = s.dataset_id
        WHERE f.id IN ({placeholders})
        AND s.scene_token != '2011_09_26_drive_0001_sync'
        ORDER BY f.media_key, f.id
    )
    SELECT * FROM RankedFrames
    WHERE 1=1
    """
    
    params = candidate_frame_ids
    
    if dataset:
        sql += " AND dataset_slug = %s"
        params.append(dataset)
    
    if sequence:
        sql += " AND sequence_name = %s"
        params.append(sequence)
    
    if objects:
        object_list = [obj.strip() for obj in objects.split(',')]
        placeholders_obj = ','.join(['%s'] * len(object_list))
        sql += f"""
            AND EXISTS (
                SELECT 1 FROM navis.frame_objects fo
                WHERE fo.frame_id = frame_id 
                AND fo.object_type IN ({placeholders_obj})
                AND fo.confidence > 0.5
            )
        """
        params.extend(object_list)
    
    with get_conn() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    
    # 5) Build flat candidate list for hybrid re-ranking
    frame_id_to_row = {r['frame_id']: r for r in rows}
    frame_id_to_distance = dict(zip(candidate_frame_ids, candidate_distances))

    flat_candidates = []
    seen_for_rerank = set()

    for frame_id in candidate_frame_ids:
        if frame_id in frame_id_to_row:
            r = frame_id_to_row[frame_id]
            if r['media_key'] not in seen_for_rerank:
                seen_for_rerank.add(r['media_key'])
                flat_candidates.append({
                    'frame_id': r['frame_id'],
                    'score': float(frame_id_to_distance[frame_id]),
                    'media_key': r['media_key'],
                    'media_url': _media_url(r['media_base_uri'], r['media_key']),
                    'dataset': r['dataset_name'] or r['dataset_slug'],
                    'sequence': r['sequence_name'],
                    'sensor': r['sensor'] or 'N/A',
                    'frame_number': r['sample_token'] or str(r['frame_id']),
                })

    # 6) Hybrid re-rank using metadata signals from query
    reranked_candidates = hybrid_rerank(flat_candidates, q)

    # 7) Group by dataset for diversity-aware selection
    dataset_frames = defaultdict(list)
    for frame in reranked_candidates:
        dataset_frames[frame['dataset']].append(frame)

    if not dataset_frames:
        return SearchResponse(query=q, k=k, hits=[])

    # 8) Minimum quota + score-based fill
    hits: List[SearchHit] = []
    seen_hit_keys = set()

    # Step 1: Guarantee minimum 2 results from each dataset that has candidates
    MIN_PER_DATASET = 2
    for ds, frames in dataset_frames.items():
        count = 0
        for frame in frames:
            if count >= MIN_PER_DATASET:
                break
            if frame['media_key'] not in seen_hit_keys:
                seen_hit_keys.add(frame['media_key'])
                hits.append(SearchHit(**frame))
                count += 1

    # Step 2: Fill remaining slots by hybrid score across all datasets
    remaining = []
    for ds, frames in dataset_frames.items():
        for frame in frames:
            if frame['media_key'] not in seen_hit_keys:
                remaining.append(frame)

    # Sort remaining by score ascending (lower = better)
    remaining.sort(key=lambda x: x['score'])

    for frame in remaining:
        if len(hits) >= k:
            break
        if frame['media_key'] not in seen_hit_keys:
            seen_hit_keys.add(frame['media_key'])
            hits.append(SearchHit(**frame))

    # Trim to k
    hits = hits[:k]

    return SearchResponse(query=q, k=k, hits=hits)