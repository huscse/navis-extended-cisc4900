from fastapi import APIRouter, HTTPException, Response
from urllib.parse import urlparse
from psycopg.rows import dict_row

from functools import lru_cache
import asyncio
from concurrent.futures import ThreadPoolExecutor

from backend.db.postgres import get_conn
from backend.services.drive import resolve_path, download_bytes

router = APIRouter(prefix="/media", tags=["media"])

# Thread pool for non-blocking Drive downloads
executor = ThreadPoolExecutor(max_workers=1)

@lru_cache(maxsize=1)
def get_gdrive_root():
    """Cache the gdrive root URI to avoid repeated DB queries"""
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT media_base_uri
                FROM navis.datasets
                WHERE slug = 'kitti'  -- Changed from provider = 'gdrive'
                LIMIT 1
            """)
            row = cur.fetchone()
            return row['media_base_uri'] if row else None

async def _serve_gdrive_async(path: str):
    """Async wrapper to prevent blocking"""
    print(f"[DEBUG] Requested path: {path}")
    
    # try to find dataset root by media_key join
    media_base_uri = None
    try:
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT d.media_base_uri
                    FROM navis.frames f
                    JOIN navis.sequences s ON f.sequence_id = s.id
                    JOIN navis.datasets d ON s.dataset_id = d.id
                    WHERE f.media_key = %s
                    LIMIT 1
                """, (path,))
                row = cur.fetchone()
                if row:
                    media_base_uri = row['media_base_uri']
                    print(f"[DEBUG] Found media_base_uri from frames: {media_base_uri}")

                # fallback to cached gdrive dataset root
                if not media_base_uri:
                    print("[DEBUG] No media_base_uri found, using cached fallback...")
                    media_base_uri = get_gdrive_root()
                    if media_base_uri:
                        print(f"[DEBUG] Found media_base_uri from cache: {media_base_uri}")
    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if not media_base_uri:
        print("[ERROR] No gdrive dataset root configured")
        raise HTTPException(status_code=500, detail="No gdrive dataset root configured")

    parsed = urlparse(media_base_uri)
    if parsed.scheme != "gdrive" or not parsed.netloc:
        print(f"[ERROR] Bad media_base_uri: {media_base_uri}")
        raise HTTPException(status_code=500, detail=f"Bad media_base_uri: {media_base_uri}")

    root_id = parsed.netloc
    print(f"[DEBUG] Resolving path with root_id={root_id}, path={path}")
    
    try:
        # Run blocking operations in thread pool
        loop = asyncio.get_event_loop()
        file_id = await loop.run_in_executor(executor, resolve_path, root_id, path)
        
        if not file_id:
            print(f"[ERROR] Drive file not found at: {path}")
            raise HTTPException(status_code=404, detail=f"Drive file not found at: {path}")
        
        print(f"[DEBUG] Resolved to file_id: {file_id}, downloading...")
        data = await loop.run_in_executor(executor, download_bytes, file_id)
        print(f"[DEBUG] Downloaded {len(data)} bytes")
        
        return Response(
            content=data,
            media_type="image/png" if path.lower().endswith(".png") else "application/octet-stream",
            headers={
                "Cache-Control": "public, max-age=31536000",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Drive error: {e}")
        raise HTTPException(status_code=500, detail=f"Drive error: {str(e)}")

@router.get("/gdrive/{path:path}")
async def serve_gdrive(path: str):
    """Serve files from Google Drive with timeout"""
    try:
        return await asyncio.wait_for(_serve_gdrive_async(path), timeout=120.0)  # Changed from 30 to 60 seconds
    except asyncio.TimeoutError:
        print(f"[ERROR] Timeout downloading {path}")
        raise HTTPException(status_code=504, detail="Request timeout - file download took too long")