# Navis Backend (Latitude AI - 2.4)

End-to-end backend for semantic search over autonomous-driving datasets (KITTI, nuScenes, Argoverse).
Stack: **FastAPI** (query API) · **CLIP** (text/image encoders) · **FAISS** (vector index) · **Postgres + pgvector** (catalog & embeddings) · **Google Drive** (object storage) · **YOLOv8** (object detection).

> TL;DR flow:
>
> * **Workers** embed frames (images) from **Google Drive** with **CLIP** → store vectors in Postgres.
> * **Object detection worker** runs YOLOv8 inference and stores bounding boxes in `frame_objects`.
> * **FAISS indexer** builds index from Postgres embeddings for fast similarity search.
> * **FastAPI** serves `/search`: encodes the text query with CLIP → FAISS top-K → Postgres join (+ Google Drive media URLs).

---

## Table of Contents

* [Repository Layout](#repository-layout)
* [Concepts & Responsibilities](#concepts--responsibilities)
* [Installation](#installation)
* [Configuration](#configuration)
* [Running Locally](#running-locally)
* [Data Schema](#data-schema)
* [API Routes](#api-routes)
* [Workers](#workers)
* [FAISS Indexing](#faiss-indexing)
* [Google Drive Integration](#google-drive-integration)
* [Development Workflow](#development-workflow)
* [Deployment Guide](#deployment-guide)
* [Troubleshooting](#troubleshooting)

---

## Repository Layout

```
backend/
  README.md
  .env.example
  requirements.txt
  secrets/                 # (local only) service account; excluded from git
    drive-key.json
  app/
    main.py               # FastAPI entrypoint
  routes/
    search.py             # /search (FAISS-powered semantic search)
    media.py              # /media/gdrive/<path> (serve images from Drive)
  services/
    text_embed.py         # CLIP text encoder
    drive.py              # Google Drive file resolution and download
  db/
    postgres.py           # Postgres connection helper
    schema.sql            # Database schema (datasets, sequences, frames, embeddings, etc.)
  workers/
    embedder.py           # Batch embed frames with CLIP → store in Postgres
    detector.py           # YOLOv8 object detection → store in frame_objects
  scripts/
    build_faiss_index.py  # Build FAISS index from Postgres embeddings
    ingest_kitti.py       # Ingest KITTI dataset metadata
  faiss_indexes/          # FAISS index files (gitignored)
    kitti.index
    kitti_mapping.npy
```

---

## Concepts & Responsibilities

* **Google Drive (object storage)**
  All media (images) live in Drive. Each dataset has a `media_base_uri` like `gdrive://<ROOT_FOLDER_ID>`.
  Frames reference images via `media_key` (relative path like `image_00/data/0000000001.png`).

* **Postgres (catalog + embeddings)**
  Structured metadata: `datasets`, `sequences`, `frames`, `embeddings`, `frame_objects`.
  CLIP embeddings stored as JSON arrays in `embeddings` table.
  Object detections stored in `frame_objects` with bounding boxes and confidence scores.

* **FAISS (vector index)**
  In-memory index (`IndexFlatL2`) for fast similarity search.
  Built from Postgres embeddings, with frame ID mapping stored in `.npy` file.
  Loaded lazily on first search request.

* **FastAPI (query service)**
  * `/search`: text query → CLIP → FAISS → Postgres join → results
  * `/media/gdrive/<path>`: serve images directly from Google Drive

---

## Installation

### Python 3.11 Required

**CRITICAL**: Use Python 3.11 (not 3.13) to avoid FAISS/SSL memory corruption issues.

```bash
# Install Python 3.11
brew install python@3.11

# Create virtual environment
python3.11 -m venv .venv-py311
source .venv-py311/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Core dependencies**:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
psycopg[binary]==3.1.13
psycopg2-binary==2.9.9
numpy>=1.25.0,<2.0
torch==2.1.0
torchvision==0.16.0
pillow==10.1.0
ftfy==6.1.1
regex==2023.10.3
google-auth==2.23.4
google-auth-httplib2==0.1.1
google-api-python-client==2.108.0
clip @ git+https://github.com/openai/CLIP.git
faiss-cpu==1.9.0.post1
pydantic==2.5.0
ultralytics==8.0.227
```

---

## Configuration

### Environment Variables

Create `.env.local`:

```env
# Backend URL
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000

# Postgres
DATABASE_URL=postgresql://navis:password@localhost:5432/navis

# Google Drive Service Account
GOOGLE_APPLICATION_CREDENTIALS=backend/secrets/drive-key.json

# CLIP Model
CLIP_MODEL=ViT-B/32
DEVICE=cpu

# OpenMP (required for FAISS on macOS)
KMP_DUPLICATE_LIB_OK=TRUE
```

### Google Drive Setup

1. Create a service account in Google Cloud Console
2. Download JSON key → save as `backend/secrets/drive-key.json`
3. Share your Drive folders with the service account email (Viewer access)
4. Copy folder IDs from Drive URLs

### Postgres Setup

```bash
# Install PostgreSQL
brew install postgresql@14

# Start PostgreSQL
brew services start postgresql@14

# Create database
createdb navis

# Run schema
psql navis < backend/db/schema.sql
```

---

## Running Locally

### Start Backend

```bash
source .venv-py311/bin/activate
export KMP_DUPLICATE_LIB_OK=TRUE
python -m uvicorn backend.app.main:app --reload --reload-dir backend
```

Backend runs at `http://127.0.0.1:8000`

API docs at `http://127.0.0.1:8000/docs`

### Ingest Dataset

```bash
# Ingest KITTI metadata
python backend/scripts/ingest_kitti.py

# Generate embeddings
python backend/workers/embedder.py

# Build FAISS index
python backend/scripts/build_faiss_index.py
```

### Test Search

```
GET http://127.0.0.1:8000/search?text=cars+on+street&k=12
```

---

## Data Schema

### Core Tables

```sql
-- Datasets
navis.datasets (
  id SERIAL PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  name TEXT,
  provider TEXT,  -- 'gdrive'
  media_base_uri TEXT  -- 'gdrive://<FOLDER_ID>'
)

-- Sequences (scenes)
navis.sequences (
  id SERIAL PRIMARY KEY,
  dataset_id INT REFERENCES datasets(id),
  scene_token TEXT,
  name TEXT
)

-- Frames
navis.frames (
  id SERIAL PRIMARY KEY,
  sequence_id INT REFERENCES sequences(id),
  frame_idx INT,
  timestamp TIMESTAMPTZ,
  media_key TEXT  -- 'image_00/data/0000000001.png'
)

-- CLIP Embeddings
navis.embeddings (
  id SERIAL PRIMARY KEY,
  frame_id INT REFERENCES frames(id),
  model_id INT REFERENCES models(id),
  emb TEXT  -- JSON array of 512 floats
)

-- Object Detections
navis.frame_objects (
  id SERIAL PRIMARY KEY,
  frame_id INT REFERENCES frames(id),
  object_type TEXT,  -- 'car', 'person', 'bicycle', etc.
  confidence FLOAT,
  bbox_x1 FLOAT,
  bbox_y1 FLOAT,
  bbox_x2 FLOAT,
  bbox_y2 FLOAT
)
```

---

## API Routes

### `GET /search`

**Params**

* `text` (string, required): natural language query
* `k` (int, optional, default 12): number of results
* `dataset` (string, optional): filter by dataset slug (e.g., 'kitti')
* `sequence` (string, optional): filter by sequence/scene token
* `objects` (string, optional): comma-separated object types (e.g., 'car,person')

**Flow**

1. Encode query text with CLIP → 512-d vector
2. FAISS `.search()` → top-K frame IDs by L2 distance
3. Join metadata from Postgres (frames, sequences, datasets)
4. Apply optional filters (dataset, sequence, objects)
5. Build media URLs (`/media/gdrive/<media_key>`)
6. Return ranked results

**Response**

```json
{
  "query": "cars on street",
  "k": 12,
  "hits": [
    {
      "frame_id": 2437,
      "score": 1.4447,
      "media_key": "image_00/data/0000000033.png",
      "media_url": "/media/gdrive/image_00/data/0000000033.png",
      "dataset": "KITTI",
      "sequence": "2011_09_26_drive_0001_sync"
    }
  ]
}
```

### `GET /media/gdrive/<path>`

Serve images from Google Drive.

**Example**: `http://127.0.0.1:8000/media/gdrive/image_00/data/0000000001.png`

**Flow**

1. Look up dataset `media_base_uri` from frame's `media_key`
2. Resolve Drive path: `<ROOT_FOLDER_ID>` + `image_00/data/0000000001.png`
3. Download file bytes from Drive API
4. Return as PNG with caching headers

---

## Workers

### `workers/embedder.py`

Batch process frames to generate CLIP embeddings.

**Process**:
1. Query frames without embeddings
2. Download images from Google Drive (batch of 32)
3. Encode with CLIP image encoder
4. L2-normalize vectors
5. Store in `navis.embeddings` as JSON

**Usage**:
```bash
python backend/workers/embedder.py
```

### `workers/detector.py`  *(Optional)*

Run YOLOv8 object detection on frames.

**Process**:
1. Load frames from Postgres
2. Download images from Drive
3. Run YOLOv8 inference
4. Store detections in `navis.frame_objects`

**Usage**:
```bash
python backend/workers/detector.py
```

---

## FAISS Indexing

### Building the Index

```bash
python backend/scripts/build_faiss_index.py
```

**Process**:
1. Read all embeddings from Postgres for dataset
2. Convert JSON strings to numpy arrays (N × 512)
3. Build `IndexFlatL2` (L2 distance, works with normalized vectors)
4. Save index file: `backend/faiss_indexes/kitti.index`
5. Save frame ID mapping: `backend/faiss_indexes/kitti_mapping.npy`

**Output**:
```
✅ Found 540 embeddings
Embeddings shape: (540, 512)
✅ Built FAISS index with 540 vectors
✅ Saved FAISS index to: backend/faiss_indexes/kitti.index
✅ Saved frame ID mapping to: backend/faiss_indexes/kitti_mapping.npy
```

### Index Loading

FAISS index is loaded **lazily** on first search request to avoid import-time crashes.

```python
# In backend/routes/search.py
def load_faiss_index():
    global _faiss_index, _frame_id_mapping
    if _faiss_index is not None:
        return  # Already loaded
    
    import faiss  # Lazy import
    _faiss_index = faiss.read_index(str(FAISS_INDEX_PATH))
    _frame_id_mapping = np.load(str(FAISS_MAPPING_PATH))
```

---

## Google Drive Integration

### Service Account Permissions

1. Go to Google Cloud Console → IAM & Admin → Service Accounts
2. Create service account → download JSON key
3. Share Drive folders with service account email (Viewer access)

### Path Resolution

Drive paths are resolved hierarchically:

```python
# Example: image_00/data/0000000001.png
# Root: 1vHWntmgJZ7Y-GAdeqGRp3mELUJis9U5e
# 
# Resolution:
# 1. Find folder "image_00" in root
# 2. Find folder "data" in "image_00"
# 3. Find file "0000000001.png" in "data"
```

Results are cached with `@lru_cache` to avoid repeated API calls.

### Rate Limiting

Google Drive API has rate limits. Current configuration:

* `ThreadPoolExecutor(max_workers=1)` - serial downloads to avoid SSL errors
* Retry logic with exponential backoff (3 attempts)
* Cache-Control headers for browser caching

**For production**, migrate to Google Cloud Storage or CDN.

---

## Development Workflow

### Adding a New Dataset

1. **Upload to Google Drive**
   - Organize as: `<dataset>/image_XX/data/*.png`
   - Share folder with service account

2. **Ingest Metadata**
   ```python
   # Create backend/scripts/ingest_<dataset>.py
   # Insert dataset, sequences, frames
   ```

3. **Generate Embeddings**
   ```bash
   python backend/workers/embedder.py
   ```

4. **Build FAISS Index**
   ```bash
   python backend/scripts/build_faiss_index.py
   ```

5. **Test Search**
   ```
   GET /search?text=your+query
   ```

### Adding Object Detection

1. Run detector worker:
   ```bash
   python backend/workers/detector.py
   ```

2. Query with object filter:
   ```
   GET /search?text=intersection&objects=car,person
   ```

---

## Deployment Guide

### Production Checklist

- [ ] **Use Python 3.11** (not 3.13)
- [ ] **Set environment variable**: `KMP_DUPLICATE_LIB_OK=TRUE`
- [ ] **Migrate from Google Drive to GCS/S3** for image storage
- [ ] **Add CDN** (CloudFlare, CloudFront) for media serving
- [ ] **Use managed Postgres** (Supabase, RDS, Cloud SQL)
- [ ] **Increase FAISS workers** to max_workers=4+ once on GCS
- [ ] **Monitor rate limits** on Google Drive API

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ backend/
ENV KMP_DUPLICATE_LIB_OK=TRUE

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Render/Railway Deployment

```yaml
# render.yaml
services:
  - type: web
    name: navis-backend
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: KMP_DUPLICATE_LIB_OK
        value: "TRUE"
      - key: PYTHON_VERSION
        value: "3.11"
```

---

## Troubleshooting

### Memory Corruption / Segfault

**Symptom**: `malloc: Incorrect checksum for freed object`

**Cause**: Python 3.13 + FAISS + concurrent SSL connections

**Fix**: 
1. Use Python 3.11 (not 3.13)
2. Set `export KMP_DUPLICATE_LIB_OK=TRUE`
3. Reduce `max_workers=1` in media route

### Images Not Loading

**Symptom**: 404 or 500 errors on `/media/gdrive/<path>`

**Fixes**:
1. Verify service account has Viewer access to Drive folder
2. Check `media_base_uri` in database matches Drive folder ID
3. Restart backend to clear Drive path cache
4. Wait 1-2 minutes after sharing folder (permissions propagation)

### Search Returns No Results

**Fixes**:
1. Check FAISS index exists: `ls backend/faiss_indexes/`
2. Verify embeddings in database: `SELECT COUNT(*) FROM navis.embeddings;`
3. Rebuild FAISS index: `python backend/scripts/build_faiss_index.py`
4. Restart backend to reload index

### SSL/Connection Errors

**Symptom**: `[SSL] record layer failure`

**Cause**: Too many concurrent Google Drive downloads

**Fixes**:
1. Reduce `max_workers` in `backend/routes/media.py`
2. Increase frontend stagger delay (already 500ms)
3. Migrate to Google Cloud Storage for production

### FAISS Index Out of Sync

**Symptom**: Search returns wrong frames or errors

**Fix**: Rebuild index after adding/removing frames
```bash
python backend/scripts/build_faiss_index.py
# Restart backend
```

---

## Performance Notes

### Current Limitations (with Google Drive)

* **540 frames**: Search works well
* **5,000+ frames**: Drive rate limits become problematic
* **50,000+ frames**: Must migrate to GCS/S3

### Production Recommendations

1. **Image Storage**: Google Cloud Storage ($0.020/GB/month)
2. **CDN**: CloudFlare (free tier) or CloudFront
3. **FAISS**: Use IVF index for 100K+ frames
4. **Caching**: Redis for Drive path resolution
5. **Database**: Connection pooling (pgBouncer)

---

## Maintainers

* PRs: include tests for new routes/workers
* Update this README when adding new features
* Tag releases when deploying to production
