Here's a full updated README for the repo root:

```markdown
# NAVIS-Extended — CISC 4900 Capstone

**Husnain Khaliq · Brooklyn College · CISC 4900 Spring 2026**  
**Supervisor:** Taimoor Hafeez
**Based on:** NAVIS (Break Through Tech AI Studio, Fall 2025 · Latitude AI)

---

## What is NAVIS?

NAVIS is a semantic search engine for autonomous driving datasets. Instead of manually browsing thousands of camera frames, engineers type a natural language query — like _"pedestrian crossing at night"_ or _"rainy intersection with traffic"_ — and the system returns the most visually relevant frames across multiple datasets in seconds.

The original system was built by a 7-person team during the Break Through Tech AI Studio challenge (Fall 2025), placing **Top 3 out of 120+ teams nationally**. It uses:

- **CLIP** (ViT-B/32) for vision-language embeddings
- **FAISS** for fast vector similarity search
- **PostgreSQL** for frame metadata and structured filtering
- **FastAPI** backend + **Next.js** frontend
- **YOLOv8** for object detection and filtering
- **Google Drive** for image storage

The system indexes frames from four autonomous driving datasets: **KITTI**, **BDD10K**, **Argoverse**, and **NuScenes** (5,218 frames total).

---

## What is NAVIS-Extended?

NAVIS-Extended is my independent CISC 4900 capstone project, extending the original proof-of-concept into a more precise, measurable, and architecturally sound system.

The original system had no formal evaluation framework — there was no way to know if changes made things better or worse. My capstone introduces exactly that: a before/after measurement system with three targeted improvements.

**The core question this project answers:**  
_Can we improve retrieval precision and dataset diversity in a VLM-powered semantic search system through hybrid ranking and better indexing — and can we prove it with numbers?_

---

## Goals and Improvements

### 1. Precision@K Evaluation Framework

Built a formal benchmarking system to measure retrieval quality before and after any changes. Runs 20 test queries and computes:

- **Precision@5, @10, @20** — what fraction of top results are relevant
- **Mean Reciprocal Rank (MRR)** — how high the first relevant result appears
- **Dataset Diversity Score** — how evenly results span across datasets

This is the foundation everything else is measured against.

### 2. Hybrid Retrieval Re-ranking

Added a metadata-aware re-ranking layer on top of CLIP semantic similarity. The system now detects contextual signals in the query (night, rain, urban, highway, surround view) and boosts frames from datasets that match those conditions:

- _"rainy night city"_ → boosts BDD10K (has weather/night variety)
- _"rural highway open road"_ → boosts KITTI (German suburban roads)
- _"urban intersection"_ → boosts Argoverse + BDD10K (city driving)

Final score: `hybrid_score = CLIP_distance - (metadata_boost × 0.3)`

### 3. Minimum Quota Diversity

Replaced the round-robin interleaving with a minimum quota system — every dataset with candidates is guaranteed at least 2 results before remaining slots are filled by score. This ensures underrepresented datasets (like Argoverse with only 235 frames) always appear in results.

### 4. FAISS Index Reconstruction _(Bug Fix)_

During the codebase audit, discovered the committed `combined.index` file had only **1,775 vectors** despite the database containing **2,794 embeddings**. The index was built before all datasets were embedded and never rebuilt — silently missing 36% of the data. Fixed by rebuilding from all available embeddings.

---

## Benchmark Results

All results measured using `backendd/scripts/benchmark_precision.py` — 20 queries, k=20.

| Metric            | Baseline | Post-Hybrid | Post-Quota | Delta  |
| ----------------- | -------- | ----------- | ---------- | ------ |
| Mean Precision@5  | 84.0%    | 88.0%       | **88.0%**  | +4.0%  |
| Mean Precision@10 | 85.5%    | 85.5%       | **87.5%**  | +2.0%  |
| Mean Precision@20 | 86.1%    | 86.6%       | **88.8%**  | +2.7%  |
| Mean MRR          | 0.975    | 1.000       | **1.000**  | +0.025 |
| Dataset Diversity | 66.7%    | 66.7%       | **66.7%**  | 0%     |

**Key finding:** Precision improved across all K values. Diversity is structurally limited — with only 235 Argoverse frames vs 1,639 KITTI frames, many queries simply don't surface Argoverse candidates from FAISS regardless of re-ranking. This is a data coverage problem, not a code problem, and is documented as a finding.

---

## Repository Structure
```

extend-navis/
├── backend/ # Original team's backend (unchanged)
├── backendd/ # Capstone extension (all new work lives here)
│ ├── app/ # FastAPI entrypoint
│ ├── routes/
│ │ └── search.py # Modified: hybrid re-ranking + quota diversity
│ ├── services/
│ │ ├── text_embed.py # CLIP text encoder
│ │ ├── drive.py # Google Drive integration
│ │ └── hybrid_rerank.py # NEW: metadata signal detection + re-ranking
│ ├── scripts/
│ │ ├── build_faiss_index.py # Rebuild FAISS index from Postgres
│ │ ├── benchmark_precision.py # NEW: Precision@K evaluation framework
│ │ └── results/ # Benchmark result JSON files
│ ├── db/ # Postgres connection
│ ├── workers/ # Embedding workers
│ └── CAPSTONE.md # Detailed progress log
├── frontend/ # Original Next.js frontend (unchanged)
└── README.md # This file

````

---

## Running the Extended Backend

```bash
# From project root
cd /path/to/extend-navis
source .venv/bin/activate
uvicorn backendd.app.main:app --reload
````

**Important:** Always run from the project root, not from inside `backendd/`, so Python resolves `backendd.*` imports correctly.

---

## Running the Benchmark

```bash
# Make sure backend is running in another terminal first
python backendd/scripts/benchmark_precision.py

# Save to specific path for comparison
python backendd/scripts/benchmark_precision.py --output backendd/scripts/results/my_run.json
```

---

## Dataset Coverage

| Dataset   | Frames    | Embeddings | Notes                                            |
| --------- | --------- | ---------- | ------------------------------------------------ |
| KITTI     | 1,639     | 1,639      | German suburban/highway roads                    |
| NuScenes  | 2,424     | 0          | Frames exist, never embedded                     |
| BDD10K    | 920       | 920        | Dashcam, diverse conditions including night/rain |
| Argoverse | 235       | 235        | Pittsburgh urban driving, 5 ring cameras         |
| **Total** | **5,218** | **2,794**  |                                                  |

---

## Original Project Attribution

NAVIS was originally built by a 7-person team at Break Through Tech AI Studio (Fall 2025) in collaboration with Latitude AI:

Husnain Khaliq, Gagan Chandra Charagondla, Keerthana Venkatesan, Lissette Solano, Manasvi, Yesun Ang, Erica Li

Original repository: [github.com/huscse/Navis-vlm-dataset-navigator](https://github.com/huscse/Navis-vlm-dataset-navigator)

---

## Capstone Progress

| Week  | Milestone                                                   | Status     |
| ----- | ----------------------------------------------------------- | ---------- |
| 3–4   | Codebase audit, schema mapping, DB verification             | ✅ Done    |
| 5     | Fixed FAISS index (1,775 → 2,794 vectors)                   | ✅ Done    |
| 5     | Established Precision@K baseline (P@5=84%, Diversity=66.7%) | ✅ Done    |
| 6–7   | Hybrid retrieval + metadata signal detection                | ✅ Done    |
| 7     | Minimum quota diversity system                              | ✅ Done    |
| 8–9   | FAISS HNSW parameter sweep                                  | 📋 Planned |
| 10–11 | Final benchmark + analysis                                  | 📋 Planned |
| 12–14 | Final report + presentation                                 | 📋 Planned |
