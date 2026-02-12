'use client';

import { useState } from 'react';

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL;

export default function SearchPage() {
  const [q, setQ] = useState('a car turning left at an intersection');
  const [k, setK] = useState(12);
  const [dataset, setDataset] = useState(''); // e.g. "kitti" or "nuscenes"
  const [sequence, setSequence] = useState(''); // optional scene token/name
  const [loading, setLoading] = useState(false);
  const [hits, setHits] = useState([]);
  const [error, setError] = useState('');

  async function runSearch(e) {
    e?.preventDefault();
    setLoading(true);
    setError('');
    setHits([]);

    const params = new URLSearchParams();
    params.set('text', q);
    params.set('k', String(k));
    if (dataset.trim()) params.set('dataset', dataset.trim());
    if (sequence.trim()) params.set('sequence', sequence.trim());

    try {
      const res = await fetch(`${BACKEND}/search?` + params.toString());
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`${res.status} ${res.statusText}: ${txt}`);
      }
      const data = await res.json();
      // media_url from backend is relative (/media/...), make it absolute for the <img>
      const patched = (data.hits ?? []).map((h) => ({
        ...h,
        absUrl: `${BACKEND}${
          h.media_url.startsWith('/') ? h.media_url : `/${h.media_url}`
        }`,
      }));
      setHits(patched);
    } catch (err) {
      setError(err.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="text-3xl font-semibold mb-6">Semantic Search</h1>

      <form
        onSubmit={runSearch}
        className="grid grid-cols-1 md:grid-cols-6 gap-3 mb-6"
      >
        <input
          className="md:col-span-3 border rounded-lg px-3 py-2"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Describe what you want to see (e.g., 'people not:car')"
        />
        <input
          className="border rounded-lg px-3 py-2"
          type="number"
          min={1}
          max={50}
          value={k}
          onChange={(e) => setK(Number(e.target.value))}
          placeholder="k"
          title="Top-K results"
        />
        <input
          className="border rounded-lg px-3 py-2"
          value={dataset}
          onChange={(e) => setDataset(e.target.value)}
          placeholder="dataset (optional: kitti, nuscenes)"
        />
        <input
          className="border rounded-lg px-3 py-2"
          value={sequence}
          onChange={(e) => setSequence(e.target.value)}
          placeholder="sequence / scene (optional)"
        />
        <button
          type="submit"
          className="md:col-span-6 bg-black text-white rounded-lg px-4 py-2 hover:opacity-90"
          disabled={loading}
        >
          {loading ? 'Searching…' : 'Search'}
        </button>
      </form>

      {error && (
        <div className="mb-4 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-red-700">
          {error}
        </div>
      )}

      {!loading && hits.length === 0 && !error && (
        <p className="text-gray-500">No results yet. Try a query above.</p>
      )}

      <ul className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {hits.map((h) => (
          <li
            key={h.frame_id}
            className="border rounded-xl overflow-hidden shadow-sm"
          >
            <div className="aspect-[4/3] bg-gray-100">
              {/* Next/Image would require next.config; <img> is simplest for localhost */}
              <img
                src={h.absUrl}
                alt={h.media_key}
                className="w-full h-full object-cover"
                loading="lazy"
              />
            </div>
            <div className="p-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium">{h.dataset}</span>
                <span className="tabular-nums text-gray-500">
                  sim: {h.score.toFixed(3)}
                </span>
              </div>
              <div className="text-gray-600 truncate">{h.sequence}</div>
              <div className="text-gray-500 truncate">{h.media_key}</div>
            </div>
          </li>
        ))}
      </ul>
    </main>
  );
}
