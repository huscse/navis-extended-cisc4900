'use client';
import React, { useState, useRef } from 'react';
import { Search, X, Loader2 } from 'lucide-react';

export default function SearchBar({
  onSearch,
  placeholder = 'Describe a moment…',
  defaultValue = '',
  loading: loadingProp,
  disabled = false,
  className = '',
}) {
  const [q, setQ] = useState(defaultValue);
  const [isFocused, setIsFocused] = useState(false);
  const [internalLoading, setInternalLoading] = useState(false);
  const inputRef = useRef(null);

  const loading = loadingProp ?? internalLoading; // external > internal

  async function handleSubmit(e) {
    e.preventDefault();
    const trimmed = q.trim();
    if (!trimmed) return;

    const maybePromise = onSearch?.(trimmed);
    // If parent returns a promise, manage internal loading
    if (maybePromise && typeof maybePromise.then === 'function') {
      try {
        setInternalLoading(true);
        await maybePromise;
      } finally {
        setInternalLoading(false);
      }
    }
  }

  function handleClear() {
    setQ('');
    inputRef.current?.focus();
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') handleSubmit(e);
  }

  return (
    <div
      className={`flex items-center gap-3 w-full ${className}`}
      role="search"
      aria-label="Dataset search"
    >
      <div className="flex-1 relative group">
        <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
          <Search
            className={`w-5 h-5 transition-colors ${
              isFocused ? 'text-gray-400' : 'text-gray-500'
            }`}
          />
        </div>

        <input
          ref={inputRef}
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          onKeyDown={handleKeyDown}
          className={`w-full rounded-full border bg-white/5 backdrop-blur-sm pl-12 pr-12 py-3.5 text-white placeholder:text-gray-500 transition-all duration-200 focus:outline-none ${
            isFocused
              ? 'border-gray-600 bg-white/10 shadow-lg shadow-black/20'
              : 'border-gray-700 hover:border-gray-600'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
          placeholder={placeholder}
          aria-label="Search query"
          disabled={disabled || loading}
        />

        {/* Clear button / loading spinner appears only when there's text */}
        {q && (
          <div className="absolute inset-y-0 right-3 flex items-center">
            {loading ? (
              <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
            ) : (
              <button
                type="button"
                onClick={handleClear}
                className="p-1 rounded-full text-gray-400 hover:text-gray-200 hover:bg-white/10 transition-all"
                aria-label="Clear search"
                title="Clear"
                tabIndex={-1}
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={handleSubmit}
        disabled={disabled || loading || !q.trim()}
        className="rounded-full px-6 py-3.5 bg-white text-gray-900 font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-100 active:scale-95 transition-all duration-200 whitespace-nowrap"
        aria-busy={loading}
      >
        {loading ? (
          <span className="flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            Searching…
          </span>
        ) : (
          'Search'
        )}
      </button>
    </div>
  );
}
