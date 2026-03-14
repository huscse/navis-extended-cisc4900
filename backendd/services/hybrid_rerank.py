"""
Hybrid Re-ranking for NAVIS-Extended
=====================================
Takes FAISS candidates and re-ranks them using a combination of:
  1. CLIP semantic similarity (the original FAISS L2 distance)
  2. Metadata boost (dataset, scene conditions inferred from query)

The final score is:
  hybrid_score = clip_distance - (metadata_boost * BOOST_WEIGHT)

Lower is better (L2 distance convention).
Metadata boost pulls relevant frames up by reducing their effective distance.
"""

# ── Tunable weight ──────────────────────────────────────────
# How much metadata signals influence the final ranking.
# 0.0 = pure CLIP, 1.0 = metadata dominates
# Start at 0.3 and tune based on benchmark results
BOOST_WEIGHT = 0.3

# ── Dataset slugs ───────────────────────────────────────────
BDD10K    = "BDD10K"
KITTI     = "KITTI"
ARGOVERSE = "Argoverse"


# ── Signal detection ────────────────────────────────────────

def detect_signals(query: str) -> dict:
    """
    Parse the query for metadata signals.
    Returns a dict of detected conditions.
    """
    q = query.lower()

    signals = {
        "night":     any(w in q for w in ["night", "dark", "darkness", "nighttime", "evening"]),
        "rain":      any(w in q for w in ["rain", "rainy", "wet", "drizzle", "storm", "stormy"]),
        "highway":   any(w in q for w in ["highway", "rural", "countryside", "freeway", "motorway", "open road"]),
        "urban":     any(w in q for w in ["city", "urban", "intersection", "downtown", "street", "building", "sidewalk"]),
        "surround":  any(w in q for w in ["surround", "360", "multiple angle", "side camera", "rear camera"]),
        "clear":     any(w in q for w in ["sunny", "clear", "daytime", "bright", "day"]),
        "pedestrian":any(w in q for w in ["pedestrian", "person", "people", "walking", "cyclist", "bicycle"]),
        "vehicle":   any(w in q for w in ["car", "truck", "vehicle", "bus", "traffic"]),
    }

    return signals


# ── Per-frame boost calculation ──────────────────────────────

def compute_boost(frame: dict, signals: dict) -> float:
    """
    Compute a metadata boost score for a single frame.
    Higher boost = more relevant to detected signals.
    Range: 0.0 to 1.0
    """
    boost = 0.0
    dataset = frame.get("dataset", "")
    sequence = frame.get("sequence", "").lower()
    sensor   = frame.get("sensor", "").lower()

    # ── Night scenes ──
    # BDD10K has dashcam footage including night driving
    if signals["night"]:
        if dataset == BDD10K:
            boost += 0.4
        # KITTI is mostly daytime — slight penalty
        if dataset == KITTI:
            boost -= 0.1

    # ── Rain / weather ──
    # BDD10K has diverse weather including rain
    if signals["rain"]:
        if dataset == BDD10K:
            boost += 0.4
        if dataset == KITTI:
            boost -= 0.1

    # ── Highway / rural ──
    # KITTI is German suburban/highway roads
    if signals["highway"]:
        if dataset == KITTI:
            boost += 0.4
        if dataset == ARGOVERSE:
            boost -= 0.1

    # ── Urban / city ──
    # Argoverse is Pittsburgh urban, BDD10K is mixed urban
    if signals["urban"]:
        if dataset == ARGOVERSE:
            boost += 0.4
        if dataset == BDD10K:
            boost += 0.2
        if dataset == KITTI:
            boost -= 0.1

    # ── Surround view / multiple angles ──
    # Argoverse has 5 ring cameras per scene
    if signals["surround"]:
        if dataset == ARGOVERSE:
            boost += 0.5
        if "side" in sensor or "rear" in sensor or "right" in sensor or "left" in sensor:
            boost += 0.2

    # ── Clear / daytime ──
    # KITTI is mostly clear daytime
    if signals["clear"]:
        if dataset == KITTI:
            boost += 0.2
        if dataset == BDD10K:
            boost += 0.1

    # ── Pedestrian heavy scenes ──
    # BDD10K and Argoverse urban areas have more pedestrians
    if signals["pedestrian"]:
        if dataset == BDD10K:
            boost += 0.2
        if dataset == ARGOVERSE:
            boost += 0.2

    # ── Vehicle heavy scenes ──
    # All datasets have vehicles but KITTI highway has dense traffic
    if signals["vehicle"]:
        if dataset == KITTI:
            boost += 0.15
        if dataset == BDD10K:
            boost += 0.15

    # Clamp to [0, 1]
    return max(0.0, min(1.0, boost))


# ── Main re-ranking function ─────────────────────────────────

def hybrid_rerank(candidates: list, query: str) -> list:
    """
    Re-rank a list of candidate frames using hybrid scoring.

    Args:
        candidates: list of dicts, each with keys:
                    frame_id, score (L2 distance), dataset,
                    sequence, sensor, media_key, media_url, frame_number
        query:      the original search query string

    Returns:
        Re-ranked list of candidates, sorted by hybrid_score ascending
        (lower = better, consistent with L2 distance convention)
    """
    if not candidates:
        return candidates

    signals = detect_signals(query)

    # Log which signals were detected
    active = [k for k, v in signals.items() if v]
    if active:
        print(f"🎯 Hybrid signals detected: {active}")
    else:
        print(f"🎯 No metadata signals detected — returning CLIP ranking")
        return candidates

    # Compute hybrid score for each candidate
    for frame in candidates:
        boost = compute_boost(frame, signals)
        clip_distance = frame["score"]
        frame["hybrid_score"] = clip_distance - (boost * BOOST_WEIGHT)
        frame["metadata_boost"] = round(boost, 4)

    # Sort by hybrid score (ascending — lower is better)
    reranked = sorted(candidates, key=lambda x: x["hybrid_score"])

    # Replace score with hybrid score for downstream use
    for frame in reranked:
        frame["score"] = round(frame["hybrid_score"], 6)

    return reranked