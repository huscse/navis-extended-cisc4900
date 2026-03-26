import sys
from pathlib import Path
import numpy as np
import faiss
import json
import argparse

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from db.postgres import get_conn

def build_faiss_index(dataset_slug='kitti'):
    """Build FAISS index from embeddings in Postgres for a specific dataset"""
    
    with get_conn() as conn, conn.cursor() as cur:
        # Get all embeddings for this dataset
        cur.execute("""
            SELECT e.frame_id, e.emb
            FROM navis.embeddings e
            JOIN navis.frames f ON e.frame_id = f.id
            JOIN navis.sequences s ON f.sequence_id = s.id
            JOIN navis.datasets d ON s.dataset_id = d.id
            WHERE d.slug = %s
            ORDER BY e.frame_id
        """, (dataset_slug,))
        
        rows = cur.fetchall()
        
    if not rows:
        print(f"❌ No embeddings found for dataset: {dataset_slug}")
        return
    
    print(f"✅ Found {len(rows)} embeddings for {dataset_slug}")
    
    # Extract frame_ids and embeddings
    frame_ids = []
    embeddings = []
    
    for row in rows:
        frame_id = row['frame_id'] if isinstance(row, dict) else row[0]
        emb = row['emb'] if isinstance(row, dict) else row[1]
        
        # Parse embedding if it's a string
        if isinstance(emb, str):
            emb = json.loads(emb)
        elif isinstance(emb, list):
            pass  # already a list
        else:
            print(f"Unknown embedding type: {type(emb)}")
            continue
        
        frame_ids.append(frame_id)
        embeddings.append(emb)
    
    # Convert to numpy array
    embeddings_np = np.array(embeddings, dtype=np.float32)
    print(f"Embeddings shape: {embeddings_np.shape}")
    
    # Build FAISS index (L2 distance, which works with normalized vectors for cosine similarity)
    d = embeddings_np.shape[1]  # dimension (512 for CLIP)
    index = faiss.IndexFlatL2(d)
    index.add(embeddings_np)
    
    print(f"✅ Built FAISS index with {index.ntotal} vectors")
    
    # Save index and mapping
    index_dir = BACKEND_ROOT / "faiss_indexes"
    index_dir.mkdir(exist_ok=True)
    
    index_path = index_dir / f"{dataset_slug}.index"
    mapping_path = index_dir / f"{dataset_slug}_mapping.npy"
    
    faiss.write_index(index, str(index_path))
    np.save(mapping_path, np.array(frame_ids, dtype=np.int32))
    
    print(f"✅ Saved FAISS index to: {index_path}")
    print(f"✅ Saved frame ID mapping to: {mapping_path}")


def build_combined_index():
    """Build a single FAISS index from ALL datasets"""
    
    with get_conn() as conn, conn.cursor() as cur:
        # Get all embeddings from all datasets
        cur.execute("""
            SELECT e.frame_id, e.emb, d.slug
            FROM navis.embeddings e
            JOIN navis.frames f ON e.frame_id = f.id
            JOIN navis.sequences s ON f.sequence_id = s.id
            JOIN navis.datasets d ON s.dataset_id = d.id
            ORDER BY e.frame_id
        """)
        
        rows = cur.fetchall()
        
    if not rows:
        print(f"❌ No embeddings found in database")
        return
    
    print(f"✅ Found {len(rows)} embeddings across all datasets")
    
    # Extract frame_ids, embeddings, and track dataset distribution
    frame_ids = []
    embeddings = []
    dataset_counts = {}
    
    for row in rows:
        frame_id = row['frame_id'] if isinstance(row, dict) else row[0]
        emb = row['emb'] if isinstance(row, dict) else row[1]
        dataset_slug = row['slug'] if isinstance(row, dict) else row[2]
        
        # Parse embedding if it's a string
        if isinstance(emb, str):
            emb = json.loads(emb)
        elif isinstance(emb, list):
            pass  # already a list
        else:
            print(f"Unknown embedding type: {type(emb)}")
            continue
        
        frame_ids.append(frame_id)
        embeddings.append(emb)
        dataset_counts[dataset_slug] = dataset_counts.get(dataset_slug, 0) + 1
    
    # Print dataset distribution
    print("\nDataset distribution:")
    for dataset, count in sorted(dataset_counts.items()):
        print(f"  - {dataset}: {count} frames")
    
    # Convert to numpy array
    embeddings_np = np.array(embeddings, dtype=np.float32)
    print(f"\nEmbeddings shape: {embeddings_np.shape}")
    
    # Build FAISS index (L2 distance, which works with normalized vectors for cosine similarity)
    d = embeddings_np.shape[1]  # dimension (512 for CLIP)
    index = faiss.IndexFlatL2(d)
    index.add(embeddings_np)
    
    print(f"✅ Built combined FAISS index with {index.ntotal} vectors")
    
    # Save index and mapping
    index_dir = BACKEND_ROOT / "faiss_indexes"
    index_dir.mkdir(exist_ok=True)
    
    index_path = index_dir / "combined.index"
    mapping_path = index_dir / "combined_mapping.npy"
    
    faiss.write_index(index, str(index_path))
    np.save(mapping_path, np.array(frame_ids, dtype=np.int32))
    
    print(f"✅ Saved FAISS index to: {index_path}")
    print(f"✅ Saved frame ID mapping to: {mapping_path}")


def build_hnsw_index(M=32, efSearch=32):
    """Build HNSW index with tuned parameters from sweep."""
    
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT e.frame_id, e.emb, d.slug
            FROM navis.embeddings e
            JOIN navis.frames f ON e.frame_id = f.id
            JOIN navis.sequences s ON f.sequence_id = s.id
            JOIN navis.datasets d ON s.dataset_id = d.id
            ORDER BY e.frame_id
        """)
        rows = cur.fetchall()

    if not rows:
        print("❌ No embeddings found")
        return

    frame_ids = []
    embeddings = []
    dataset_counts = {}

    for row in rows:
        frame_id = row[0] if not isinstance(row, dict) else row['frame_id']
        emb = row[1] if not isinstance(row, dict) else row['emb']
        slug = row[2] if not isinstance(row, dict) else row['slug']

        if isinstance(emb, str):
            emb = json.loads(emb)

        frame_ids.append(frame_id)
        embeddings.append(emb)
        dataset_counts[slug] = dataset_counts.get(slug, 0) + 1

    print(f"✅ Found {len(embeddings)} embeddings")
    print("\nDataset distribution:")
    for dataset, count in sorted(dataset_counts.items()):
        print(f"  - {dataset}: {count} frames")

    embeddings_np = np.array(embeddings, dtype=np.float32)
    d = embeddings_np.shape[1]

    print(f"\nBuilding HNSW index (M={M}, efSearch={efSearch})...")
    index = faiss.IndexHNSWFlat(d, M)
    index.hnsw.efSearch = efSearch
    index.add(embeddings_np)

    print(f"✅ Built HNSW index with {index.ntotal} vectors")

    index_dir = BACKEND_ROOT / "faiss_indexes"
    index_dir.mkdir(exist_ok=True)

    index_path = index_dir / "combined.index"
    mapping_path = index_dir / "combined_mapping.npy"

    faiss.write_index(index, str(index_path))
    np.save(mapping_path, np.array(frame_ids, dtype=np.int32))

    print(f"✅ Saved HNSW index to: {index_path}")
    print(f"   M={M}, efSearch={efSearch}, vectors={index.ntotal}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Build FAISS index from embeddings')
    parser.add_argument('--dataset', type=str, help='Build index for specific dataset')
    parser.add_argument('--combined', action='store_true', help='Build combined FlatL2 index')
    parser.add_argument('--hnsw', action='store_true', help='Build combined HNSW index (M=32, efSearch=32)')

    args = parser.parse_args()

    if args.hnsw:
        print("=" * 60)
        print("Building HNSW index (M=32, efSearch=32)")
        print("=" * 60)
        build_hnsw_index(M=32, efSearch=32)
    elif args.combined:
        print("=" * 60)
        print("Building COMBINED FlatL2 index")
        print("=" * 60)
        build_combined_index()
    elif args.dataset:
        print("=" * 60)
        print(f"Building index for dataset: {args.dataset}")
        print("=" * 60)
        build_faiss_index(args.dataset)
    else:
        print("=" * 60)
        print("No arguments — building COMBINED FlatL2 index")
        print("=" * 60)
        build_combined_index()