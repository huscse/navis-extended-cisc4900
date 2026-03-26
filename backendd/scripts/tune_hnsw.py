"""
FAISS HNSW Parameter Sweep — NAVIS-Extended Capstone
=====================================================
Tests different HNSW configurations and measures:
  - Search speed (ms per query)
  - Recall vs FlatL2 baseline (what fraction of true top-K results are returned)
  - Index build time

Parameters tuned:
  M         — number of connections per node (8, 16, 32)
              higher M = better recall, more memory, slower build
  efSearch  — search beam width at query time (32, 64, 128)
              higher efSearch = better recall, slower search

Usage:
    python backendd/scripts/tune_hnsw.py
"""

import sys
import time
import json
import numpy as np
from pathlib import Path
from psycopg.rows import dict_row
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT.parent))

import faiss
from backendd.db.postgres import get_conn


def load_embeddings():
    """Load all embeddings from Postgres."""
    print("Loading embeddings from Postgres...")
    with get_conn() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("""
            SELECT e.frame_id, e.emb, d.slug
            FROM navis.embeddings e
            JOIN navis.frames f ON e.frame_id = f.id
            JOIN navis.sequences s ON f.sequence_id = s.id
            JOIN navis.datasets d ON s.dataset_id = d.id
            ORDER BY e.frame_id
        """)
        rows = cur.fetchall()

    frame_ids = []
    embeddings = []
    for row in rows:
      frame_id = row['frame_id']
      emb = row['emb']
      if isinstance(emb, str):
        
        emb = json.loads(emb)
        frame_ids.append(frame_id)
        embeddings.append(emb)

    embeddings_np = np.array(embeddings, dtype=np.float32)
    frame_ids_np = np.array(frame_ids, dtype=np.int32)

    print(f"Loaded {len(embeddings_np)} embeddings, shape: {embeddings_np.shape}")
    return embeddings_np, frame_ids_np


def build_flatl2_baseline(embeddings_np):
    """Build the baseline FlatL2 index for recall comparison."""
    d = embeddings_np.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(embeddings_np)
    return index


def build_hnsw_index(embeddings_np, M, efSearch):
    """Build an HNSW index with given parameters."""
    d = embeddings_np.shape[1]

    start = time.time()
    index = faiss.IndexHNSWFlat(d, M)
    index.hnsw.efSearch = efSearch
    index.add(embeddings_np)
    build_time = time.time() - start

    return index, build_time


def generate_test_queries(embeddings_np, n=50):
    """
    Generate test queries by sampling random embeddings
    and adding small noise — simulates real query vectors.
    """
    np.random.seed(42)
    indices = np.random.choice(len(embeddings_np), n, replace=False)
    queries = embeddings_np[indices] + np.random.normal(0, 0.01, (n, embeddings_np.shape[1])).astype(np.float32)
    # Normalize
    norms = np.linalg.norm(queries, axis=1, keepdims=True)
    queries = queries / norms
    return queries


def measure_recall(baseline_index, hnsw_index, queries, k=10):
    """
    Measure recall@K — what fraction of true top-K results
    does HNSW return compared to exact FlatL2.
    """
    total_recall = 0.0

    for query in queries:
        q = query.reshape(1, -1)

        # Ground truth from FlatL2
        _, true_indices = baseline_index.search(q, k)
        true_set = set(true_indices[0].tolist())

        # HNSW results
        _, hnsw_indices = hnsw_index.search(q, k)
        hnsw_set = set(hnsw_indices[0].tolist())

        # Recall = overlap / k
        overlap = len(true_set & hnsw_set)
        total_recall += overlap / k

    return total_recall / len(queries)


def measure_speed(index, queries, k=10, runs=3):
    """Measure average search time in milliseconds per query."""
    times = []
    for _ in range(runs):
        start = time.time()
        for query in queries:
            index.search(query.reshape(1, -1), k)
        elapsed = (time.time() - start) / len(queries) * 1000
        times.append(elapsed)
    return sum(times) / len(times)


def run_sweep():
    embeddings_np, frame_ids_np = load_embeddings()
    queries = generate_test_queries(embeddings_np, n=50)

    print("\nBuilding FlatL2 baseline...")
    baseline = build_flatl2_baseline(embeddings_np)
    baseline_speed = measure_speed(baseline, queries)
    print(f"FlatL2 baseline speed: {baseline_speed:.3f} ms/query")

    # Parameter grid
    M_values = [8, 16, 32]
    efSearch_values = [32, 64, 128]

    results = []

    print("\n" + "=" * 65)
    print(f"{'M':>4} {'efSearch':>10} {'Build(s)':>10} {'Speed(ms)':>10} {'Recall@10':>10}")
    print("=" * 65)

    best_config = None
    best_score = -1

    for M in M_values:
        for efSearch in efSearch_values:
            index, build_time = build_hnsw_index(embeddings_np, M, efSearch)
            speed = measure_speed(index, queries)
            recall = measure_recall(baseline, index, queries, k=10)

            # Score = recall weighted more than speed
            # We care more about accuracy than speed at this scale
            score = (recall * 0.7) + ((1 / speed) * 0.3)

            print(f"{M:>4} {efSearch:>10} {build_time:>10.2f} {speed:>10.3f} {recall:>10.4f}")

            result = {
                "M": M,
                "efSearch": efSearch,
                "build_time_s": round(build_time, 3),
                "speed_ms": round(speed, 4),
                "recall_at_10": round(recall, 4),
                "score": round(score, 4),
            }
            results.append(result)

            if score > best_score:
                best_score = score
                best_config = result

    print("=" * 65)
    print(f"\n✅ Best config: M={best_config['M']}, efSearch={best_config['efSearch']}")
    print(f"   Recall@10: {best_config['recall_at_10']:.4f}")
    print(f"   Speed: {best_config['speed_ms']:.3f} ms/query")
    print(f"   vs FlatL2: {baseline_speed:.3f} ms/query")

    # Save results
    output = {
        "flatl2_baseline_speed_ms": round(baseline_speed, 4),
        "sweep_results": results,
        "best_config": best_config,
    }

    results_dir = BACKEND_ROOT / "scripts" / "results"
    results_dir.mkdir(exist_ok=True)
    output_path = results_dir / "hnsw_sweep_results.json"

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Results saved to: {output_path}")
    return best_config


if __name__ == "__main__":
    best = run_sweep()
    print(f"\nNext step: rebuild combined.index using M={best['M']}, efSearch={best['efSearch']}")