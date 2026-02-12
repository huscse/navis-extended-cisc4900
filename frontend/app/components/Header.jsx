'use client';
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '../lib/supabaseClient';
import { useAuthSession } from '../lib/useAuthSession';
import SearchResults from './SearchResults';
import { semanticSearch } from '../lib/api';
import TopNavBar from './TopNavBarHeader';
import HeroSection from './HeroSection';
import ProfileModal from './ProfileModal';
import Footer from './Footer';

export default function Header({ initialQuery }) {
  const router = useRouter();
  const session = useAuthSession();

  const [profileOpen, setProfileOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  const [objectFilter, setObjectFilter] = useState(''); // NEW

  // Run search on mount if URL has query
  useEffect(() => {
    if (initialQuery) {
      handleSearch(initialQuery, false); // false = don't update URL
    }
  }, [initialQuery]);

  const handleSignOut = async () => {
    try {
      await supabase.auth.signOut();
      router.push('/land');
    } catch (e) {
      console.error('Sign out failed:', e);
    }
  };

  const handleSearch = async (
    query,
    updateUrl = true,
    filterObjects = objectFilter,
  ) => {
    // UPDATED
    setError(null);
    setLoading(true);

    if (updateUrl) {
      const url = new URL(window.location.href);
      url.searchParams.set('q', query);
      if (filterObjects) {
        url.searchParams.set('objects', filterObjects);
      } else {
        url.searchParams.delete('objects');
      }
      window.history.pushState({}, '', url);
    }

    try {
      // Add objects filter to search
      const data = await semanticSearch({
        text: query,
        k: 8,
        objects: filterObjects || undefined, // UPDATED
      });
      const hits = data.hits || [];

      // Show results immediately with placeholder captions
      const hitsWithPlaceholders = hits.map((h) => ({
        ...h,
        caption: 'Generating summaries...',
      }));
      setResults(hitsWithPlaceholders);
      setLoading(false);

      // Fetch captions in background (non-blocking)
      if (hits.length > 0) {
        const frameIds = hits.map((h) => h.frame_id);
        const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL;

        fetch(`${BACKEND}/caption/batch`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ frame_ids: frameIds }),
        })
          .then((res) => res.json())
          .then((captionData) => {
            const hitsWithCaptions = hits.map((h) => {
              const captionObj = captionData.captions.find(
                (c) => c.frame_id === h.frame_id,
              );
              return {
                ...h,
                caption: captionObj?.caption || 'No description available',
                captionError: captionObj?.error || null,
              };
            });
            setResults(hitsWithCaptions);
          })
          .catch((err) => {
            console.error('Caption generation failed:', err);
          });
      }
    } catch (err) {
      console.error('Search failed', err);
      setError(err.message || 'Search failed. Please try again.');
      setResults([]);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#111827_0%,#000000_45%,#1F2937_95%)] text-white">
      <TopNavBar
        session={session}
        onSignOut={handleSignOut}
        onProfileClick={() => setProfileOpen(true)}
      />

      <ProfileModal
        isOpen={profileOpen}
        onClose={() => setProfileOpen(false)}
      />

      <HeroSection
        onSearch={(q) => handleSearch(q, true)}
        loading={loading}
        objectFilter={objectFilter} // NEW
        onObjectFilterChange={setObjectFilter} // NEW
      />

      <SearchResults
        results={results}
        loading={loading}
        error={error}
        className="bg-[linear-gradient(180deg,#111827_0%,#000000_45%,#1F2937_95%)]"
      />

      <Footer />
    </div>
  );
}
