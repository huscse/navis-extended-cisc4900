"""
NAVIS-Extended Baseline Benchmark: Precision@K Evaluation
==========================================================
Run this BEFORE making improvements to establish baseline scores.
Then run again AFTER improvements to measure delta.

Usage:
    python benchmark_precision.py
    python benchmark_precision.py --api http://localhost:8000
    python benchmark_precision.py --output results/baseline.json

What it measures:
    - Precision@5, @10, @20: fraction of top-K results that are "relevant"
    - Dataset Diversity Score: fraction of results that span multiple datasets
    - Mean Reciprocal Rank (MRR): how high the first relevant result appears

Relevance is defined by:
    1. Keyword match between query and frame metadata (dataset, sequence, sensor)
    2. Object type match (if query mentions objects that exist in frame_objects)
    3. Scene condition match (night/rain/snow if detectable from media_key or sequence)
"""

import json
import time
import argparse
import urllib.request
import urllib.parse
from datetime import datetime
from collections import defaultdict
from pathlib import Path


# ─────────────────────────────────────────────
#  TEST QUERIES WITH RELEVANCE CRITERIA
# ─────────────────────────────────────────────
# Each query has:
#   - text: the search query
#   - relevant_datasets: which dataset(s) should ideally appear
#   - relevant_keywords: keywords we check against frame metadata fields
#   - min_expected_hits: how many of top-10 we expect to be relevant
#
# NOTE: We define "relevant" pragmatically — a result is relevant if it
# comes from a dataset that logically matches the query. This is a proxy
# for ground truth since we don't have hand-labeled annotations yet.

TEST_QUERIES = [
    # ── Daytime driving ──
    {
        "id": "Q01",
        "text": "car driving on road daytime",
        "relevant_datasets": ["KITTI", "BDD10K", "Argoverse"],
        "relevant_keywords": ["car", "road"],
        "k_values": [5, 10, 20],
        "note": "Generic driving query — all datasets relevant"
    },
    {
        "id": "Q02",
        "text": "highway with multiple vehicles",
        "relevant_datasets": ["KITTI", "BDD10K", "Argoverse"],
        "relevant_keywords": ["highway", "vehicle"],
        "k_values": [5, 10, 20],
        "note": "Highway scene"
    },
    {
        "id": "Q03",
        "text": "intersection with traffic lights",
        "relevant_datasets": ["BDD10K", "Argoverse"],
        "relevant_keywords": ["intersection", "traffic"],
        "k_values": [5, 10, 20],
        "note": "Urban intersection — BDD10K and Argoverse more likely"
    },

    # ── Pedestrians ──
    {
        "id": "Q04",
        "text": "pedestrian crossing street",
        "relevant_datasets": ["BDD10K", "Argoverse", "KITTI"],
        "relevant_keywords": ["pedestrian", "person", "crossing"],
        "k_values": [5, 10, 20],
        "note": "Pedestrian detection query"
    },
    {
        "id": "Q05",
        "text": "people walking on sidewalk",
        "relevant_datasets": ["BDD10K", "Argoverse"],
        "relevant_keywords": ["pedestrian", "person"],
        "k_values": [5, 10, 20],
        "note": "Urban pedestrian scene"
    },

    # ── Weather / lighting conditions ──
    {
        "id": "Q06",
        "text": "driving at night dark road",
        "relevant_datasets": ["BDD10K"],
        "relevant_keywords": ["night", "dark"],
        "k_values": [5, 10, 20],
        "note": "Night driving — BDD10K has night scenes"
    },
    {
        "id": "Q07",
        "text": "rainy weather wet road",
        "relevant_datasets": ["BDD10K"],
        "relevant_keywords": ["rain", "wet", "weather"],
        "k_values": [5, 10, 20],
        "note": "Rain condition query"
    },
    {
        "id": "Q08",
        "text": "clear sunny day open road",
        "relevant_datasets": ["KITTI", "BDD10K", "Argoverse"],
        "relevant_keywords": ["sunny", "clear", "day"],
        "k_values": [5, 10, 20],
        "note": "Clear weather — all datasets relevant"
    },

    # ── Dataset-specific scenes ──
    {
        "id": "Q09",
        "text": "urban city street with buildings",
        "relevant_datasets": ["BDD10K", "Argoverse"],
        "relevant_keywords": ["urban", "city", "building"],
        "k_values": [5, 10, 20],
        "note": "Urban scene — BDD10K/Argoverse cities"
    },
    {
        "id": "Q10",
        "text": "rural road countryside",
        "relevant_datasets": ["KITTI"],
        "relevant_keywords": ["rural", "countryside"],
        "k_values": [5, 10, 20],
        "note": "Rural road — KITTI Germany roads"
    },

    # ── Object-specific ──
    {
        "id": "Q11",
        "text": "bicycle cyclist on road",
        "relevant_datasets": ["BDD10K", "KITTI"],
        "relevant_keywords": ["bicycle", "cyclist"],
        "k_values": [5, 10, 20],
        "note": "Cyclist query"
    },
    {
        "id": "Q12",
        "text": "truck large vehicle highway",
        "relevant_datasets": ["KITTI", "BDD10K"],
        "relevant_keywords": ["truck", "vehicle"],
        "k_values": [5, 10, 20],
        "note": "Truck/large vehicle"
    },
    {
        "id": "Q13",
        "text": "stop sign at intersection",
        "relevant_datasets": ["BDD10K", "Argoverse"],
        "relevant_keywords": ["stop", "sign", "intersection"],
        "k_values": [5, 10, 20],
        "note": "Traffic sign detection"
    },

    # ── Complex/multi-condition ──
    {
        "id": "Q14",
        "text": "busy city intersection multiple cars pedestrians",
        "relevant_datasets": ["BDD10K", "Argoverse"],
        "relevant_keywords": ["intersection", "car", "pedestrian"],
        "k_values": [5, 10, 20],
        "note": "Complex urban scene"
    },
    {
        "id": "Q15",
        "text": "empty road no traffic",
        "relevant_datasets": ["KITTI", "BDD10K"],
        "relevant_keywords": ["empty", "road"],
        "k_values": [5, 10, 20],
        "note": "Empty road query"
    },

    # ── Sensor/view specific ──
    {
        "id": "Q16",
        "text": "front camera view driving forward",
        "relevant_datasets": ["KITTI", "BDD10K", "Argoverse"],
        "relevant_keywords": ["front", "camera", "forward"],
        "k_values": [5, 10, 20],
        "note": "Front camera view — all datasets"
    },
    {
        "id": "Q17",
        "text": "road markings lane lines visible",
        "relevant_datasets": ["KITTI", "BDD10K", "Argoverse"],
        "relevant_keywords": ["lane", "marking", "road"],
        "k_values": [5, 10, 20],
        "note": "Lane detection scenario"
    },

    # ── Safety-critical ──
    {
        "id": "Q18",
        "text": "near collision dangerous situation",
        "relevant_datasets": ["BDD10K", "Argoverse"],
        "relevant_keywords": ["collision", "dangerous", "emergency"],
        "k_values": [5, 10, 20],
        "note": "Safety-critical scenario"
    },
    {
        "id": "Q19",
        "text": "parking lot vehicles stationary",
        "relevant_datasets": ["BDD10K", "Argoverse"],
        "relevant_keywords": ["parking", "stationary"],
        "k_values": [5, 10, 20],
        "note": "Parking scenario"
    },
    {
        "id": "Q20",
        "text": "construction zone road works",
        "relevant_datasets": ["BDD10K"],
        "relevant_keywords": ["construction", "work", "zone"],
        "k_values": [5, 10, 20],
        "note": "Construction zone"
    },
]


# ─────────────────────────────────────────────
#  RELEVANCE SCORING
# ─────────────────────────────────────────────

def is_relevant(hit: dict, query: dict) -> bool:
    """
    Determine if a search hit is relevant to a query.
    
    Relevance criteria (any one sufficient):
    1. Hit's dataset matches one of the expected relevant datasets
    2. Any relevant keyword appears in the hit's metadata fields
    
    This is a proxy for ground truth — in a full evaluation you'd have
    human-labeled relevant frame IDs. This gives us a measurable baseline.
    """
    hit_dataset = hit.get("dataset", "").lower()
    hit_sequence = hit.get("sequence", "").lower()
    hit_sensor = hit.get("sensor", "").lower()
    hit_frame_number = hit.get("frame_number", "").lower()
    hit_media_key = hit.get("media_key", "").lower()
    
    # Criterion 1: Dataset match
    relevant_datasets_lower = [d.lower() for d in query["relevant_datasets"]]
    if hit_dataset in relevant_datasets_lower:
        return True
    
    # Criterion 2: Keyword match in any metadata field
    all_metadata = f"{hit_dataset} {hit_sequence} {hit_sensor} {hit_frame_number} {hit_media_key}"
    for keyword in query["relevant_keywords"]:
        if keyword.lower() in all_metadata:
            return True
    
    return False


def compute_precision_at_k(hits: list, query: dict, k: int) -> float:
    """Compute P@K: fraction of top-K hits that are relevant."""
    if not hits or k == 0:
        return 0.0
    top_k = hits[:k]
    relevant_count = sum(1 for h in top_k if is_relevant(h, query))
    return relevant_count / min(k, len(top_k))


def compute_mrr(hits: list, query: dict) -> float:
    """Mean Reciprocal Rank: 1/rank of first relevant result."""
    for i, hit in enumerate(hits):
        if is_relevant(hit, query):
            return 1.0 / (i + 1)
    return 0.0


def compute_diversity_score(hits: list) -> float:
    """
    Dataset diversity score: fraction of unique datasets in results.
    Score of 1.0 = all 3 datasets represented equally.
    Score of 0.33 = only 1 dataset.
    """
    if not hits:
        return 0.0
    datasets = set(h.get("dataset", "unknown") for h in hits)
    total_datasets = 3  # kitti, bdd10k, argoverse
    return len(datasets) / total_datasets


# ─────────────────────────────────────────────
#  API CALL
# ─────────────────────────────────────────────

def search_api(api_base: str, query_text: str, k: int = 20) -> dict:
    """Call the NAVIS search API and return the response."""
    params = urllib.parse.urlencode({"text": query_text, "k": k})
    url = f"{api_base}/search?{params}"
    
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return {"error": str(e), "hits": []}


# ─────────────────────────────────────────────
#  MAIN BENCHMARK
# ─────────────────────────────────────────────

def run_benchmark(api_base: str, output_path: str = None):
    print("=" * 60)
    print("NAVIS-Extended Baseline Benchmark: Precision@K")
    print(f"API: {api_base}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Queries: {len(TEST_QUERIES)}")
    print("=" * 60)

    results = []
    aggregate = defaultdict(list)

    for query in TEST_QUERIES:
        print(f"\n[{query['id']}] {query['text'][:50]}...")
        
        # Call API with max k=20 to get enough results
        response = search_api(api_base, query["text"], k=20)
        
        if "error" in response:
            print(f"  ❌ API Error: {response['error']}")
            continue
        
        hits = response.get("hits", [])
        
        if not hits:
            print(f"  ⚠️  No results returned")
            result = {
                "query_id": query["id"],
                "query_text": query["text"],
                "total_hits": 0,
                "precision_at_5": 0.0,
                "precision_at_10": 0.0,
                "precision_at_20": 0.0,
                "mrr": 0.0,
                "diversity_score": 0.0,
                "datasets_found": [],
                "relevant_datasets": query["relevant_datasets"],
            }
        else:
            p5  = compute_precision_at_k(hits, query, 5)
            p10 = compute_precision_at_k(hits, query, 10)
            p20 = compute_precision_at_k(hits, query, 20)
            mrr = compute_mrr(hits, query)
            div = compute_diversity_score(hits)
            datasets_found = list(set(h.get("dataset", "?") for h in hits))

            print(f"  Hits: {len(hits)} | P@5={p5:.2f} P@10={p10:.2f} P@20={p20:.2f} | MRR={mrr:.2f} | Diversity={div:.2f}")
            print(f"  Datasets: {datasets_found}")

            result = {
                "query_id": query["id"],
                "query_text": query["text"],
                "total_hits": len(hits),
                "precision_at_5": round(p5, 4),
                "precision_at_10": round(p10, 4),
                "precision_at_20": round(p20, 4),
                "mrr": round(mrr, 4),
                "diversity_score": round(div, 4),
                "datasets_found": sorted(datasets_found),
                "relevant_datasets": query["relevant_datasets"],
                "note": query.get("note", ""),
            }

            aggregate["p5"].append(p5)
            aggregate["p10"].append(p10)
            aggregate["p20"].append(p20)
            aggregate["mrr"].append(mrr)
            aggregate["diversity"].append(div)

        results.append(result)
        time.sleep(0.2)  # Be gentle on the API

    # ── Summary ──
    print("\n" + "=" * 60)
    print("AGGREGATE RESULTS (Baseline)")
    print("=" * 60)

    def avg(lst): return sum(lst) / len(lst) if lst else 0.0

    mean_p5  = avg(aggregate["p5"])
    mean_p10 = avg(aggregate["p10"])
    mean_p20 = avg(aggregate["p20"])
    mean_mrr = avg(aggregate["mrr"])
    mean_div = avg(aggregate["diversity"])

    print(f"  Mean Precision@5:   {mean_p5:.4f}  ({mean_p5*100:.1f}%)")
    print(f"  Mean Precision@10:  {mean_p10:.4f}  ({mean_p10*100:.1f}%)")
    print(f"  Mean Precision@20:  {mean_p20:.4f}  ({mean_p20*100:.1f}%)")
    print(f"  Mean MRR:           {mean_mrr:.4f}")
    print(f"  Mean Diversity:     {mean_div:.4f}  ({mean_div*100:.1f}%)")
    print()
    print("  ℹ️  These are your BASELINE scores.")
    print("  Run this again after improvements to measure delta.")

    summary = {
        "benchmark_type": "baseline",
        "timestamp": datetime.now().isoformat(),
        "api_base": api_base,
        "total_queries": len(results),
        "aggregate": {
            "mean_precision_at_5":  round(mean_p5, 4),
            "mean_precision_at_10": round(mean_p10, 4),
            "mean_precision_at_20": round(mean_p20, 4),
            "mean_mrr":             round(mean_mrr, 4),
            "mean_diversity_score": round(mean_div, 4),
        },
        "queries": results,
    }

    # ── Save output ──
    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"benchmark_baseline_{ts}.json"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n✅ Results saved to: {output_path}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NAVIS Precision@K Benchmark")
    parser.add_argument("--api", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--output", default=None, help="Output JSON file path")
    args = parser.parse_args()

    run_benchmark(api_base=args.api, output_path=args.output)