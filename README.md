# NAVIS-Extended -- CISC 4900 Capstone

**Husnain Khaliq · Brooklyn College · CISC 4900 Spring 2026**  
**Supervisor:** Taimoor Hafeez  
**Based on:** NAVIS (Break Through Tech AI Studio, Fall 2025 · Latitude AI)

---

## What is NAVIS?

NAVIS is a semantic search engine for autonomous driving datasets. Instead of manually browsing thousands of camera frames, engineers type a natural language query -- like _"pedestrian crossing at night"_ or _"rainy intersection with traffic"_ -- and the system returns the most visually relevant frames across multiple datasets in seconds.

The original system was built by a 7-person team during the Break Through Tech AI Studio challenge (Fall 2025), placing **Top 3 out of 120+ teams nationally**. It uses:

- **CLIP** (ViT-B/32) for vision-language embeddings
- **FAISS** for fast vector similarity search
- **PostgreSQL** for frame metadata and structured filtering
- **FastAPI** backend + **Next.js** frontend
- **YOLOv8** for object detection and filtering
- **Google Drive** for image storage

The system indexes frames from three embedded autonomous driving datasets: **KITTI**, **BDD10K**, and **Argoverse** (3,663 embedded frames).

---

## What is NAVIS-Extended?

NAVIS-Extended is my independent CISC 4900 capstone project, extending the original proof-of-concept into a more precise, measurable, and architecturally sound system.

The original system had no formal evaluation framework -- there was no way to know if changes made things better or worse. My capstone introduces exactly that: a before/after measurement system with five targeted improvements.

**The core question this project answers:**  
_Can we improve retrieval precision and dataset diversity in a VLM-powered semantic search system through hybrid ranking and better indexing -- and can we prove it with numbers?_

---

## Goals and Improvements

### 1. FAISS Index Reconstruction (Bug Fix)

During the codebase audit, discovered the committed `combined.index` file had only **1,775 vectors** despite the database containing **2,794 embeddings**. The index was built before all datasets were embedded and never rebuilt -- silently missing 36% of the data. Fixed by rebuilding from all available embeddings. Final index: **3,663 vectors** after full BDD10K re-ingestion.

### 2. Precision@K Evaluation Framework

Built a formal benchmarking system to measure retrieval quality before and after any changes. Runs 20 test queries and computes:

- **Precision@5, @10, @20** -- what fraction of top results are relevant
- **Mean Reciprocal Rank (MRR)** -- how high the first relevant result appears
- **Dataset Diversity Score** -- how evenly results span across datasets

This is the foundation everything else is measured against.

### 3. Hybrid Retrieval Re-ranking

Added a metadata-aware re-ranking layer on top of CLIP semantic similarity. The system now detects contextual signals in the query (night, rain, urban, highway, surround view, pedestrian, vehicle) and boosts frames from datasets that match those conditions:

- _"rainy night city"_ -> boosts BDD10K (has weather/night variety)
- _"rural highway open road"_ -> boosts KITTI (German suburban roads)
- _"urban intersection"_ -> boosts Argoverse + BDD10K (city driving)

Final score: `hybrid_score = CLIP_distance - (metadata_boost x 0.3)`

### 4. Minimum Quota Diversity

Replaced the round-robin interleaving with a minimum quota system -- every dataset with candidates is guaranteed at least 2 results before remaining slots are filled by score. This ensures underrepresented datasets (like Argoverse with only 235 frames) always appear in results.

### 5. UI Enhancements

- **Dataset color badges** -- KITTI=blue, BDD10K=green, Argoverse=purple for instant visual provenance
- **Rank numbers** -- Result #1, #2 instead of generic Frame labels
- **Match percentage** -- L2 distance converted to human-readable %, color coded green/gray/red
- **Dataset filter buttons** -- styled pill buttons for filtering by dataset

### 6. FAISS HNSW Parameter Sweep (Empirical Study)

Ran a full parameter sweep across M=[8,16,32] x efSearch=[32,64,128]. Best config M=32, efSearch=32 achieved 100% recall at 6x speed improvement over FlatL2 in isolation. However, the full benchmark showed missing results and recall degradation at our dataset size.

**Finding:** FlatL2 retained as the optimal index at 3,663 vectors. HNSW requires larger datasets to outperform brute force search. Negative result, documented as a valid engineering finding.

---

## Benchmark Results

All results measured using `backendd/scripts/benchmark_precision.py` -- 20 queries, k=20.

| Metric            | Baseline | Post-Hybrid | Post-Quota | Final (May 2026) | Delta  |
| ----------------- | -------- | ----------- | ---------- | ---------------- | ------ |
| Mean Precision@5  | 84.0%    | 88.0%       | 88.0%      | **91.8%**        | +7.8%  |
| Mean Precision@10 | 85.5%    | 85.5%       | 87.5%      | **90.0%**        | +4.5%  |
| Mean Precision@20 | 86.1%    | 86.6%       | 88.8%      | **89.1%**        | +3.0%  |
| Mean MRR          | 0.975    | 1.000       | 1.000      | **1.000**        | +0.025 |
| Dataset Diversity | 66.7%    | 66.7%       | 66.7%      | **56.9%**        | -9.8%  |

**Key finding:** Precision improved across all K values. MRR reached a perfect 1.000 -- every query returns a relevant result as the first hit. Diversity decreased in the final run because BDD10K now has 1,380 frames (vs 920 previously), dominating more queries by volume. This is a data composition effect, not an algorithm regression. Diversity ceiling is a structural data coverage problem -- documented as a finding, with NuScenes embedding identified as the clearest path forward.

---

## Repository Structure

```
extend-navis/
├── backend/                        # Original team's backend (unchanged)
├── backendd/                       # Capstone extension (all new work lives here)
│   ├── app/                        # FastAPI entrypoint
│   ├── routes/
│   │   └── search.py               # Modified: hybrid re-ranking + quota diversity
│   ├── services/
│   │   ├── text_embed.py           # CLIP text encoder
│   │   ├── drive.py                # Google Drive integration
│   │   └── hybrid_rerank.py        # NEW: metadata signal detection + re-ranking
│   ├── scripts/
│   │   ├── build_faiss_index.py    # Rebuild FAISS index from Postgres
│   │   ├── benchmark_precision.py  # NEW: Precision@K evaluation framework
│   │   ├── tune_hnsw.py            # NEW: HNSW parameter sweep
│   │   ├── embed_bdd10k.py         # BDD10K embedding pipeline
│   │   ├── ingest_bdd10k_gdrive_auto.py  # BDD10K ingestion from Drive
│   │   └── results/                # Benchmark result JSON files
│   ├── db/                         # Postgres connection
│   ├── faiss_indexes/              # Serialized FAISS index + frame ID mapping
│   ├── workers/                    # Embedding workers
│   └── CAPSTONE.md                 # Detailed progress log
├── frontend/                       # Next.js frontend (UI improvements added)
└── README.md                       # This file
```

---

## Running the Extended Backend

```bash
# Start Postgres container
/Applications/Docker.app/Contents/Resources/bin/docker start navis-postgres

# From project root
cd /path/to/extend-navis
source .venv/bin/activate
.venv/bin/uvicorn backendd.app.main:app --reload
```

**Important:** Always run from the project root, not from inside `backendd/`, so Python resolves `backendd.*` imports correctly. Use `.venv/bin/uvicorn` explicitly to avoid picking up the system Anaconda uvicorn.

---

## Running the Benchmark

```bash
# Make sure backend is running in another terminal first
python backendd/scripts/benchmark_precision.py

# Save to specific path for comparison
python backendd/scripts/benchmark_precision.py --output backendd/scripts/results/my_run.json
```

---

## Rebuilding the FAISS Index

```bash
# Rebuild combined FlatL2 index from all embeddings in Postgres
python3 -m backendd.scripts.build_faiss_index --combined

# Build HNSW index (experimental -- see findings above)
python3 -m backendd.scripts.build_faiss_index --hnsw
```

---

## Dataset Coverage

| Dataset   | Frames    | Embeddings | Notes                                            |
| --------- | --------- | ---------- | ------------------------------------------------ |
| KITTI     | 2,048     | 2,048      | German suburban/highway roads                    |
| BDD10K    | 1,380     | 1,380      | Dashcam, diverse conditions including night/rain |
| Argoverse | 235       | 235        | Pittsburgh urban driving, 5 ring cameras         |
| NuScenes  | 2,424     | 0          | Frames exist in DB, not yet embedded             |
| **Total** | **6,087** | **3,663**  |                                                  |

**Next step:** Embedding NuScenes (2,424 frames) would increase the searchable index from 3,663 to 6,087 frames and directly address the diversity ceiling.

---

## Original Project Attribution

NAVIS was originally built by a 7-person team at Break Through Tech AI Studio (Fall 2025) in collaboration with Latitude AI:

Husnain Khaliq, Gagan Chandra Charagondla, Keerthana Venkatesan, Lissette Solano, Manasvi, Yesun Ang, Erica Li

Original repository: [github.com/huscse/Navis-vlm-dataset-navigator](https://github.com/huscse/Navis-vlm-dataset-navigator)

---

## Capstone Progress

| Week  | Milestone                                                   | Status |
| ----- | ----------------------------------------------------------- | ------ |
| 3-4   | Codebase audit, schema mapping, DB verification             | Done   |
| 5     | Fixed FAISS index (1,775 -> 3,663 vectors)                  | Done   |
| 5     | Established Precision@K baseline (P@5=84%, MRR=0.975)       | Done   |
| 6-7   | Hybrid retrieval + metadata signal detection                | Done   |
| 7     | Minimum quota diversity system                              | Done   |
| 8-9   | FAISS HNSW parameter sweep (reverted to FlatL2)             | Done   |
| 9-10  | UI improvements: badges, rank numbers, match %, filter btns | Done   |
| 11    | BDD10K re-ingestion + full index rebuild (3,663 vectors)    | Done   |
| 12    | Final benchmark run -- P@5=91.8%, MRR=1.000                 | Done   |
| 13-15 | Final slide deck + presentation video                       | Done   |
