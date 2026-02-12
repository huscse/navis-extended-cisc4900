// app/lib/api.js
const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, '');

function ensureBase() {
  if (!API_BASE) {
    throw new Error(
      'NEXT_PUBLIC_BACKEND_URL is not set. Add it to .env.local (e.g., http://127.0.0.1:8000).',
    );
  }
}

// ---- Semantic search over frames ----
export async function semanticSearch({
  text,
  k = 12,
  dataset,
  sequence,
  objects,
} = {}) {
  // ADDED objects
  ensureBase();
  if (!text || !text.trim()) {
    return { query: text ?? '', k, hits: [] };
  }

  const params = new URLSearchParams();
  params.set('text', text);
  params.set('k', String(k));
  if (dataset) params.set('dataset', dataset);
  if (sequence) params.set('sequence', sequence);
  if (objects) params.set('objects', objects); // NEW: Add objects filter

  const res = await fetch(`${API_BASE}/search?${params.toString()}`, {
    method: 'GET',
  });

  if (!res.ok) {
    const msg = await res.text().catch(() => '');
    throw new Error(`Search failed: ${res.status} ${res.statusText} ${msg}`);
  }

  const data = await res.json(); // { query, k, hits: [...] }
  const hits = (data.hits ?? []).map((h) => ({
    ...h,
    // make an absolute URL for <img src=...>
    media_absolute_url: `${API_BASE}${h.media_url?.startsWith('/') ? '' : '/'}${
      h.media_url
    }`,
  }));
  return { ...data, hits };
}

// ---- Convenience helpers (optional) ----
export async function listDatasets() {
  ensureBase();
  const r = await fetch(`${API_BASE}/datasets/`);
  if (!r.ok) throw new Error(`datasets failed: ${r.status}`);
  return r.json(); // [{id, slug, name, ...}]
}

export async function listSequences(datasetId) {
  ensureBase();
  const r = await fetch(`${API_BASE}/sequences/?dataset_id=${datasetId}`);
  if (!r.ok) throw new Error(`sequences failed: ${r.status}`);
  return r.json(); // [...]
}

// TEMP compatibility alias so old imports don't crash:
export { semanticSearch as searchDatasets };
