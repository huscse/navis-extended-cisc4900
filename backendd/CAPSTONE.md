---

## CISC 4900 Capstone Extensions (Spring 2026)

> **Author**: Husnain Khaliq — Brooklyn College, CISC 4900
> **Supervisor**: Taimoor Hafeez
> **Project**: NAVIS-Extended — Improving Retrieval Precision in VLM-Powered Autonomous Driving Search

This section documents all changes and additions made to the original NAVIS system as part of the CISC 4900 capstone project. The original `backend/` folder is unchanged. All capstone work lives in `backendd/`.

---

### What Changed and Why

The original team's `combined.index` FAISS file contained only **1,775 vectors** covering a partial frame subset (IDs 2425–4707, BDD10K range only). This caused search results to be heavily biased toward Argoverse frames despite the round-robin diversity logic in `search.py`.

**Root cause**: The index was built and committed at a point in time when only a subset of embeddings existed in Postgres. The actual embedding counts are:

| Dataset   | Frames in DB | Embeddings         |
| --------- | ------------ | ------------------ |
| KITTI     | 1,639        | 1,639              |
| BDD10K    | 920          | 920                |
| Argoverse | 235          | 235                |
| NuScenes  | 2,424        | 0 (never embedded) |
| **Total** | **5,218**    | **2,794**          |

**Fix applied**: Rebuilt `combined.index` from all 2,794 available embeddings using `scripts/build_faiss_index.py --combined`. The index now correctly spans all three embedded datasets.

---

### Capstone Improvement Goals

Three targeted improvements are being implemented and measured:

1. **Hybrid Retrieval** — Combine CLIP semantic similarity with structured metadata filters (weather, time-of-day, dataset) to improve precision on condition-specific queries.

2. **FAISS HNSW Parameter Tuning** — Replace `IndexFlatL2` with `IndexHNSWFlat` and tune `M` and `efSearch` parameters to improve search speed while maintaining accuracy.

3. **Precision@K Evaluation Framework** — A formal benchmarking system to measure before/after improvement with P@5, P@10, P@20, MRR, and Dataset Diversity Score.

---

### Baseline Benchmark Results

Established **2026-02-28** using `scripts/benchmark_precision.py` against the rebuilt 2,794-vector index.

| Metric            | Baseline Score |
| ----------------- | -------------- |
| Mean Precision@5  | **84.0%**      |
| Mean Precision@10 | **85.5%**      |
| Mean Precision@20 | **86.1%**      |
| Mean MRR          | **0.975**      |
| Dataset Diversity | **66.7%**      |

**Key observations**:

- Precision is high overall but diversity is the main weakness — 9 of 20 queries return results from only 1 dataset
- Weakest queries: Q10 "rural road countryside" (P@5=40%), Q03/Q05/Q06 (P@5=60%)
- MRR near-perfect (0.975) — system almost always surfaces a relevant result first
- Dataset bias exists: BDD10K dashcam imagery scores higher for common driving queries due to CLIP's visual similarity preference

These scores serve as the **before** baseline. Target after improvements: Diversity ≥ 85%, P@5 ≥ 90%.

---

### Running the Benchmark

```bash
# Make sure backend is running in another terminal:
uvicorn backendd.app.main:app --reload

# Run benchmark
python backendd/scripts/benchmark_precision.py

# Save to specific path
python backendd/scripts/benchmark_precision.py --output results/improved.json
```

Results are saved as timestamped JSON files. Compare baseline vs. improved:

```
benchmark_baseline_20260228_210637.json   ← baseline (before)
benchmark_improved_YYYYMMDD_HHMMSS.json  ← after improvements
```

---

### Running the Extended Backend

The `backendd/` module is a self-contained copy of the backend with capstone modifications applied. Run it from the project root:

```bash
cd /path/to/extend-navis
source .venv/bin/activate
uvicorn backendd.app.main:app --reload
```

**Important**: Always run from the project root (not from inside `backendd/`) so Python can resolve the `backendd.*` imports correctly.

---

### Capstone Progress Log

| Week  | Task                                                                 | Status         |
| ----- | -------------------------------------------------------------------- | -------------- |
| 3–4   | Codebase audit, schema mapping, DB verification                      | ✅ Done        |
| 5     | Discovered index discrepancy (1,775 vs 2,794 vectors), rebuilt index | ✅ Done        |
| 5     | Established Precision@K baseline benchmark                           | ✅ Done        |
| 6–7   | Hybrid retrieval implementation                                      | 🔄 In Progress |
| 8–9   | FAISS HNSW parameter sweep                                           | 📋 Planned     |
| 10–11 | Post-improvement benchmark + analysis                                | 📋 Planned     |
| 12–14 | Final report + presentation                                          | 📋 Planned     |
