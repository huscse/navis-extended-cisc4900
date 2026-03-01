from __future__ import annotations
from pathlib import Path, PurePosixPath
from functools import lru_cache
from typing import Optional, List, Dict
import os
import time
import io
import base64
import tempfile
import hashlib
import httplib2
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Cache directory for downloaded files
CACHE_DIR = Path("/tmp/drive_cache")
CACHE_DIR.mkdir(exist_ok=True)

# Handle credentials from environment variable (base64 encoded) or file
_env_key_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
_env_key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

if _env_key_json:
    try:
        key_data = base64.b64decode(_env_key_json)
        tmp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        tmp_file.write(key_data.decode('utf-8'))
        tmp_file.close()
        KEY_PATH = Path(tmp_file.name)
    except Exception as e:
        raise RuntimeError(f"Failed to decode GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}")
elif _env_key_path:
    KEY_PATH = Path(_env_key_path).expanduser().resolve()
else:
    KEY_PATH = (Path(__file__).resolve().parents[1] / "secrets" / "drive-key.json")

if not KEY_PATH.exists():
    raise FileNotFoundError(
        f"Google Drive key not found at: {KEY_PATH}\n"
        "Place your service account JSON at backend/secrets/drive-key.json, "
        "set GOOGLE_APPLICATION_CREDENTIALS to a file path, "
        "or set GOOGLE_APPLICATION_CREDENTIALS_JSON to base64 encoded JSON."
    )


@lru_cache(maxsize=1)
def _get_service():
    """Build and cache the Google Drive service."""
    creds = service_account.Credentials.from_service_account_file(
        str(KEY_PATH), scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)

def list_files(folder_id: str, query: Optional[str] = None) -> List[Dict]:
    """List files in a Google Drive folder."""
    service = _get_service()
    
    q = f"'{folder_id}' in parents and trashed=false"
    if query:
        q += f" and {query}"
    
    results = service.files().list(
        q=q,
        fields="files(id, name, mimeType, parents)",
        pageSize=1000
    ).execute()
    
    return results.get("files", [])

def resolve_path(root_folder_id: str, path: str) -> Optional[str]:
    """
    Resolve a path like 'Residential/2011_09_26/...' to a file ID.
    Returns the file ID or None if not found.
    """
    parts = PurePosixPath(path).parts
    current_id = root_folder_id
    
    for part in parts:
        files = list_files(current_id, query=f"name='{part}'")
        if not files:
            return None
        current_id = files[0]["id"]
    
    return current_id

def download_bytes(file_id: str, max_retries=5):
    """
    Download file from Google Drive with caching and retry logic.
    Option 2: Local file caching - reduces API calls dramatically
    """
    # Check cache first (Option 2)
    cache_key = hashlib.md5(file_id.encode()).hexdigest()
    cache_path = CACHE_DIR / f"{cache_key}.bin"
    
    if cache_path.exists():
        print(f"[CACHE HIT] {file_id}")
        return cache_path.read_bytes()
    
    print(f"[CACHE MISS] Downloading {file_id}")
    service = _get_service()
    
    for attempt in range(max_retries):
        try:
            request = service.files().get_media(fileId=file_id)
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            buffer.seek(0)
            data = buffer.read()
            
            # Save to cache (Option 2)
            try:
                cache_path.write_bytes(data)
                print(f"[CACHED] {file_id}")
            except Exception as cache_error:
                print(f"[CACHE WARNING] Failed to cache {file_id}: {cache_error}")
            
            return data
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 1.0
                print(f"[RETRY] Attempt {attempt + 1}/{max_retries}, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise