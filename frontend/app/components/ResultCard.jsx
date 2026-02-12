'use client';

import React, { useState, useEffect, useMemo } from 'react';
import {
  Database,
  Image as ImageIcon,
  Video,
  Camera,
  Hash,
  X,
  ZoomIn,
  FileText,
  Bookmark,
  BookmarkCheck,
} from 'lucide-react';
import { useAuthSession } from '../lib/useAuthSession';
import { addBookmark, removeBookmark, isBookmarked } from '../lib/bookmarks';

export default function ResultCard({ result, index, allResults = [] }) {
  const [shouldLoad, setShouldLoad] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [imgError, setImgError] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [bookmarked, setBookmarked] = useState(false);
  const [bookmarkLoading, setBookmarkLoading] = useState(false);

  const { session } = useAuthSession();

  // Check if this is a duplicate frame (same media_key appears earlier in results)
  const isDuplicate = useMemo(() => {
    if (!result.media_key) return false;

    const currentMediaKey = result.media_key;
    for (let i = 0; i < index; i++) {
      if (allResults[i]?.media_key === currentMediaKey) {
        return true;
      }
    }
    return false;
  }, [result.media_key, index, allResults]);

  useEffect(() => {
    // Stagger loading - load 1 image every 2 seconds
    const delay = index * 2000;
    const timer = setTimeout(() => setShouldLoad(true), delay);
    return () => clearTimeout(timer);
  }, [index]);

  // Check if bookmarked on mount
  useEffect(() => {
    if (session && result.frame_id) {
      isBookmarked(result.frame_id).then(setBookmarked);
    }
  }, [session, result.frame_id]);

  // Don't render if duplicate
  if (isDuplicate) {
    return null;
  }

  const rawSrc = result.imageUrl || result.thumbnailUrl;
  const imgSrc = rawSrc ? encodeURI(rawSrc) : null;
  const title = `Frame ${index + 1}`;

  const dataset = result.dataset || 'Unknown';
  const sequence = result.sequence || 'N/A';
  const sensorDisplay = result.sensor
    ? result.sensor.replace('image_', 'Camera ').replace(/_/g, ' ')
    : 'N/A';
  const frameNumber = result.frame_number || result.frame_id || 'N/A';
  const score = result.score ? result.score.toFixed(3) : 'N/A';
  const caption = result.caption || '';

  const handleImageError = (e) => {
    if (retryCount < 2) {
      const retryDelay = Math.pow(2, retryCount) * 1000;
      setTimeout(() => {
        setRetryCount((prev) => prev + 1);
        // Don't directly set src - let React re-render
        setImgError(false); // Reset error state to trigger re-render
      }, retryDelay);
    } else {
      setImgError(true);
    }
  };

  const handleBookmarkToggle = async (e) => {
    e.stopPropagation(); // Prevent modal from opening

    if (!session) {
      alert('Please sign in to bookmark frames');
      return;
    }

    setBookmarkLoading(true);
    try {
      if (bookmarked) {
        await removeBookmark(result.frame_id);
        setBookmarked(false);
      } else {
        await addBookmark({
          frame_id: result.frame_id,
          dataset: result.dataset,
          sequence: result.sequence,
          sensor: result.sensor,
          frame_number: result.frame_number,
          caption: result.caption,
          imageUrl: result.imageUrl || result.thumbnailUrl,
          score: result.score,
        });
        setBookmarked(true);
      }
    } catch (error) {
      console.error('Bookmark error:', error);
      alert('Failed to update bookmark');
    } finally {
      setBookmarkLoading(false);
    }
  };

  return (
    <>
      <article
        className="bg-gradient-to-br from-white/5 to-white/[0.02] border border-white/10 rounded-xl overflow-hidden hover:from-white/10 hover:to-white/5 hover:border-white/20 hover:shadow-xl hover:shadow-black/20 transition-all duration-300 group cursor-pointer"
        onClick={() => setShowModal(true)}
      >
        {/* Thumbnail */}
        <div className="relative h-48 overflow-hidden bg-gray-900/50">
          {imgSrc && shouldLoad && !imgError ? (
            <>
              <img
                key={`${imgSrc}-${retryCount}`} // Force re-render on retry
                src={imgSrc}
                alt={title}
                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                loading="lazy"
                onError={handleImageError}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

              {/* Zoom icon on hover */}
              <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <div className="bg-black/70 text-white p-3 rounded-full backdrop-blur-sm">
                  <ZoomIn className="w-6 h-6" />
                </div>
              </div>

              {/* Bookmark Button - Top Right */}
              {session && (
                <button
                  onClick={handleBookmarkToggle}
                  disabled={bookmarkLoading}
                  className="absolute top-2 right-2 bg-black/70 hover:bg-black/90 text-white p-2 rounded-full backdrop-blur-sm transition-all duration-200 hover:scale-110 disabled:opacity-50"
                >
                  {bookmarked ? (
                    <BookmarkCheck className="w-5 h-5 text-yellow-400" />
                  ) : (
                    <Bookmark className="w-5 h-5" />
                  )}
                </button>
              )}

              {retryCount > 0 && (
                <div className="absolute bottom-2 right-2 bg-yellow-500/80 text-xs px-2 py-1 rounded">
                  Retrying...
                </div>
              )}

              {/* Similarity Score Badge */}
              <div className="absolute top-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded-md backdrop-blur-sm">
                Score: {score}
              </div>
            </>
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center text-gray-600">
              {!shouldLoad ? (
                <div className="w-8 h-8 border-2 border-gray-600 border-t-gray-400 rounded-full animate-spin" />
              ) : (
                <>
                  <ImageIcon className="w-12 h-12 mb-2 opacity-30" />
                  <span className="text-sm">
                    {imgError ? 'Failed to load' : 'No preview available'}
                  </span>
                </>
              )}
            </div>
          )}
        </div>

        {/* Content with Metadata */}
        <div className="p-5">
          <h3 className="text-base font-semibold text-white mb-3 line-clamp-1 group-hover:text-gray-300 transition-colors">
            {title}
          </h3>

          {/* Caption */}
          {caption && (
            <div className="mb-3 pb-3 border-b border-white/10">
              <div className="flex items-start gap-2">
                <FileText className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-gray-300 leading-relaxed line-clamp-2 italic">
                  {caption}
                </p>
              </div>
            </div>
          )}

          {/* Metadata Grid */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-blue-400 flex-shrink-0" />
              <span className="text-xs text-gray-400">Dataset:</span>
              <span className="text-sm text-white font-medium truncate">
                {dataset}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <Video className="w-4 h-4 text-green-400 flex-shrink-0" />
              <span className="text-xs text-gray-400">Sequence:</span>
              <span className="text-sm text-white truncate">{sequence}</span>
            </div>

            <div className="flex items-center gap-2">
              <Camera className="w-4 h-4 text-purple-400 flex-shrink-0" />
              <span className="text-xs text-gray-400">Sensor:</span>
              <span className="text-sm text-white truncate">
                {sensorDisplay}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <Hash className="w-4 h-4 text-orange-400 flex-shrink-0" />
              <span className="text-xs text-gray-400">Frame:</span>
              <span className="text-sm text-white truncate">{frameNumber}</span>
            </div>
          </div>
        </div>
      </article>

      {/* Modal - same as before */}
      {showModal && (
        <div
          className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4 backdrop-blur-sm"
          onClick={() => setShowModal(false)}
        >
          <button
            className="absolute top-4 right-4 text-white hover:text-gray-300 transition-colors z-10"
            onClick={() => setShowModal(false)}
          >
            <X className="w-8 h-8" />
          </button>

          <div className="max-w-7xl w-full flex flex-col items-center gap-4">
            <img
              src={imgSrc}
              alt={title}
              className="max-h-[70vh] w-auto object-contain rounded-lg"
              onClick={(e) => e.stopPropagation()}
            />

            <div className="w-full max-w-4xl bg-black/80 text-white p-4 rounded-lg backdrop-blur-sm border border-white/10">
              <h3 className="text-lg font-semibold mb-3">{title}</h3>

              {caption && (
                <p className="text-sm text-gray-300 mb-3 pb-3 border-b border-white/10 italic">
                  "{caption}"
                </p>
              )}

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div>
                  <span className="text-gray-400">Dataset:</span> {dataset}
                </div>
                <div>
                  <span className="text-gray-400">Sequence:</span>
                  <span className="block truncate">{sequence}</span>
                </div>
                <div>
                  <span className="text-gray-400">Sensor:</span> {sensorDisplay}
                </div>
                <div>
                  <span className="text-gray-400">Score:</span> {score}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
