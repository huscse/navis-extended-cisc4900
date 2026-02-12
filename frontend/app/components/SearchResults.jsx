'use client';

import React from 'react';
import { AlertCircle, Sparkles } from 'lucide-react';
import ResultCard from './ResultCard';

export default function SearchResults({ results, loading, error }) {
  // Loading state
  if (loading) {
    return (
      <div className="mt-12 max-w-5xl mx-auto text-center">
        <div className="inline-flex items-center gap-3 text-gray-300">
          <div className="w-5 h-5 border-2 border-gray-500 border-t-white rounded-full animate-spin" />
          <p className="text-lg">Searching datasets...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="mt-12 max-w-3xl mx-auto px-4">
        <div className="flex items-start gap-3 text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl p-5 backdrop-blur-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold mb-1">Search Error</h3>
            <p className="text-sm text-red-300">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  // Empty state
  if (!results || results.length === 0) {
    return (
      <div className="mt-9 max-w-3xl mx-auto text-center px-4">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-gray-500/10 to-slate-500/10 border border-white/10 mb-4">
          <Sparkles className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="text-xl font-semibold text-white mb-2">
          Start Your Search
        </h3>
        <p className="text-slate-300 leading-relaxed">
          Try searching for scenes like{' '}
          <span className="text-white font-medium">"pedestrian crossing"</span>,{' '}
          <span className="text-white font-medium">"red light"</span>, or{' '}
          <span className="text-white font-medium">"cyclist overtaking"</span>
        </p>
      </div>
    );
  }

  // Create formatted results array with media_key for deduplication
  const formattedResults = results.map((r, index) => ({
    // Pass all metadata fields directly
    imageUrl: r.media_absolute_url,
    thumbnailUrl: r.absUrl || r.media_url,
    title: r.media_key,
    dataset: r.dataset,
    sequence: r.sequence,
    sensor: r.sensor,
    frame_number: r.frame_number,
    frame_id: r.frame_id,
    score: r.score,
    caption: r.caption,
    media_key: r.media_key, // Important for deduplication!
    raw: r,
  }));

  // Results grid
  return (
    <div className="mt-12 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
      {/* Results header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-1 h-6 bg-gradient-to-b from-gray-400 to-slate-700 rounded-full" />
          <h2 className="text-lg font-semibold text-white">Search Results</h2>
          <span className="text-sm text-gray-200">
            ({formattedResults.length}{' '}
            {formattedResults.length === 1 ? 'result' : 'results'})
          </span>
        </div>
      </div>

      {/* Results grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {formattedResults.map((result, index) => (
          <ResultCard
            key={result.frame_id ?? result.id ?? `${result.media_key}-${index}`}
            result={result}
            index={index}
            allResults={formattedResults} // Pass full array for duplicate checking
          />
        ))}
      </div>
    </div>
  );
}
