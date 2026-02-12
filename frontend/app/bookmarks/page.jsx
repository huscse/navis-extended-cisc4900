'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '../lib/supabaseClient';
import { useAuthSession } from '../lib/useAuthSession';
import { getBookmarks } from '../lib/bookmarks';
import TopNavBar from '../components/TopNavBarHeader';
import Footer from '../components/Footer';
import ResultCard from '../components/ResultCard';
import ProfileModal from '../components/ProfileModal';
import { Bookmark } from 'lucide-react';

export default function BookmarksPage() {
  const router = useRouter();
  const { session, loading: authLoading } = useAuthSession();

  const [bookmarks, setBookmarks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [profileOpen, setProfileOpen] = useState(false);

  useEffect(() => {
    // Redirect if not signed in
    if (!authLoading && !session) {
      router.push('/signin');
      return;
    }

    // Load bookmarks
    if (session) {
      loadBookmarks();
    }
  }, [session, authLoading, router]);

  const loadBookmarks = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getBookmarks();

      // Transform bookmarks to match ResultCard format
      const transformedBookmarks = data.map((bookmark, index) => ({
        frame_id: bookmark.frame_id,
        dataset: bookmark.dataset,
        sequence: bookmark.sequence,
        sensor: bookmark.sensor,
        frame_number: bookmark.frame_number,
        caption: bookmark.caption,
        imageUrl: bookmark.image_url,
        thumbnailUrl: bookmark.image_url,
        score: bookmark.score,
        // Add index for ResultCard
        _bookmarkId: bookmark.id,
      }));

      setBookmarks(transformedBookmarks);
    } catch (err) {
      console.error('Failed to load bookmarks:', err);
      setError('Failed to load bookmarks');
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = async () => {
    try {
      await supabase.auth.signOut();
      router.push('/land');
    } catch (e) {
      console.error('Sign out failed:', e);
    }
  };

  // Show loading while checking auth
  if (authLoading) {
    return (
      <div className="min-h-screen bg-[linear-gradient(180deg,#111827_0%,#000000_45%,#1F2937_95%)] flex items-center justify-center">
        <div className="text-white text-lg">Loading...</div>
      </div>
    );
  }

  // Don't render if not signed in (redirecting)
  if (!session) {
    return null;
  }

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

      {/* Header Section */}
      <div className="container mx-auto px-4 py-12">
        <div className="flex items-center gap-3 mb-8">
          <Bookmark className="w-8 h-8 text-gray-400" />
          <h1 className="text-4xl font-bold">My Bookmarks</h1>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center py-20">
            <div className="w-12 h-12 border-4 border-slate-700 border-t-slate-400 rounded-full animate-spin" />
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 mb-8">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && bookmarks.length === 0 && (
          <div className="text-center py-20">
            <Bookmark className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h2 className="text-2xl font-semibold text-gray-400 mb-2">
              No bookmarks yet
            </h2>
            <p className="text-gray-500 mb-6">
              Start bookmarking frames from search results to see them here
            </p>
            <button
              onClick={() => router.push('/')}
              className="bg-slate-800 hover:bg-slate-700 text-white px-6 py-3 rounded-lg transition-colors cursor-pointer"
            >
              Go to Search
            </button>
          </div>
        )}

        {/* Bookmarks Grid */}
        {!loading && !error && bookmarks.length > 0 && (
          <>
            <p className="text-gray-400 mb-6">
              {bookmarks.length} bookmark{bookmarks.length !== 1 ? 's' : ''}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {bookmarks.map((bookmark, index) => (
                <ResultCard
                  key={bookmark._bookmarkId}
                  result={bookmark}
                  index={index}
                  onBookmarkChange={loadBookmarks} // Refresh when unbookmarked
                />
              ))}
            </div>
          </>
        )}
      </div>

      <Footer />
    </div>
  );
}
