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

// Convert L2 distance to match percentage
const getMatchPercent = (score) => {
  const MIN_SCORE = 1.2;
  const MAX_SCORE = 1.6;
  const clamped = Math.min(Math.max(score, MIN_SCORE), MAX_SCORE);
  const percent = ((MAX_SCORE - clamped) / (MAX_SCORE - MIN_SCORE)) * 100;
  return Math.round(percent);
};

// Dataset color config
const DATASET_COLORS = {
  KITTI: {
    bg: 'bg-blue-500/20',
    text: 'text-blue-300',
    border: 'border-blue-500/30',
  },
  BDD10K: {
    bg: 'bg-green-500/20',
    text: 'text-green-300',
    border: 'border-green-500/30',
  },
  Argoverse: {
    bg: 'bg-purple-500/20',
    text: 'text-purple-300',
    border: 'border-purple-500/30',
  },
  NuScenes: {
    bg: 'bg-orange-500/20',
    text: 'text-orange-300',
    border: 'border-orange-500/30',
  },
};

const getDatasetColors = (dataset) => {
  return (
    DATASET_COLORS[dataset] || {
      bg: 'bg-gray-500/20',
      text: 'text-gray-300',
      border: 'border-gray-500/30',
    }
  );
};

export default function ResultCard({ result, index, allResults = [] }) {
  const [shouldLoad, setShouldLoad] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [imgError, setImgError] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [bookmarked, setBookmarked] = useState(false);
  const [bookmarkLoading, setBookmarkLoading] = useState(false);

  const { session } = useAuthSession();

  const isDuplicate = useMemo(() => {
    if (!result.media_key) return false;
    const currentMediaKey = result.media_key;
    for (let i = 0; i < index; i++) {
      if (allResults[i]?.media_key === currentMediaKey) return true;
    }
    return false;
  }, [result.media_key, index, allResults]);

  useEffect(() => {
    const delay = index * 2000;
    const timer = setTimeout(() => setShouldLoad(true), delay);
    return () => clearTimeout(timer);
  }, [index]);

  useEffect(() => {
    if (session && result.frame_id) {
      isBookmarked(result.frame_id).then(setBookmarked);
    }
  }, [session, result.frame_id]);

  if (isDuplicate) return null;

  const rawSrc = result.imageUrl || result.thumbnailUrl;
  const imgSrc = rawSrc ? encodeURI(rawSrc) : null;

  const dataset = result.dataset || 'Unknown';
  const sequence = result.sequence || 'N/A';
  const sensorDisplay = result.sensor
    ? result.sensor.replace('image_', 'Camera ').replace(/_/g, ' ')
    : 'N/A';
  const frameNumber = result.frame_number || result.frame_id || 'N/A';
  const caption = result.caption || '';
  const matchPercent = result.score ? getMatchPercent(result.score) : null;
  const datasetColors = getDatasetColors(dataset);
  const rank = index + 1;

  const handleImageError = () => {
    if (retryCount < 2) {
      const retryDelay = Math.pow(2, retryCount) * 1000;
      setTimeout(() => {
        setRetryCount((prev) => prev + 1);
        setImgError(false);
      }, retryDelay);
    } else {
      setImgError(true);
    }
  };

  const handleBookmarkToggle = async (e) => {
    e.stopPropagation();
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
                key={`${imgSrc}-${retryCount}`}
                src={imgSrc}
                alt={`Result #${rank}`}
                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                loading="lazy"
                onError={handleImageError}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

              {/* Zoom icon */}
              <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <div className="bg-black/70 text-white p-3 rounded-full backdrop-blur-sm">
                  <ZoomIn className="w-6 h-6" />
                </div>
              </div>

              {/* Bookmark Button */}
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

              {/* Rank + Match Score Badge — top left */}
              <div className="absolute top-2 left-2 flex items-center gap-1.5">
                <div className="bg-black/80 text-white text-xs font-bold px-2 py-1 rounded-md backdrop-blur-sm">
                  #{rank}
                </div>
                {matchPercent !== null && (
                  <div
                    className={`text-xs font-semibold px-2 py-1 rounded-md backdrop-blur-sm border
                      ${
                        matchPercent >= 55
                          ? 'bg-green-600/80 text-white border-green-500/60'
                          : matchPercent >= 35
                          ? 'bg-gray-700/90 text-white border-gray-500/60'
                          : 'bg-red-600/80 text-white border-red-500/60'
                      }`}
                  >
                    {matchPercent}% match
                  </div>
                )}
              </div>

              {retryCount > 0 && (
                <div className="absolute bottom-2 right-2 bg-yellow-500/80 text-xs px-2 py-1 rounded">
                  Retrying...
                </div>
              )}
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

        {/* Card Content */}
        <div className="p-5">
          {/* Title row with dataset badge */}
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-base font-semibold text-white group-hover:text-gray-300 transition-colors">
              Result #{rank}
            </h3>
            <span
              className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${datasetColors.bg} ${datasetColors.text} ${datasetColors.border}`}
            >
              {dataset}
            </span>
          </div>

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

          {/* Metadata */}
          <div className="space-y-2">
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

      {/* Modal */}
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
              alt={`Result #${rank}`}
              className="max-h-[70vh] w-auto object-contain rounded-lg"
              onClick={(e) => e.stopPropagation()}
            />

            <div className="w-full max-w-4xl bg-black/80 text-white p-4 rounded-lg backdrop-blur-sm border border-white/10">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold">Result #{rank}</h3>
                <span
                  className={`text-sm font-semibold px-3 py-1 rounded-full border ${datasetColors.bg} ${datasetColors.text} ${datasetColors.border}`}
                >
                  {dataset}
                </span>
              </div>

              {caption && (
                <p className="text-sm text-gray-300 mb-3 pb-3 border-b border-white/10 italic">
                  "{caption}"
                </p>
              )}

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div>
                  <span className="text-gray-400">Match:</span>{' '}
                  <span
                    className={
                      matchPercent >= 70
                        ? 'text-green-300'
                        : matchPercent >= 45
                        ? 'text-yellow-300'
                        : 'text-red-300'
                    }
                  >
                    {matchPercent}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Sequence:</span>
                  <span className="block truncate">{sequence}</span>
                </div>
                <div>
                  <span className="text-gray-400">Sensor:</span> {sensorDisplay}
                </div>
                <div>
                  <span className="text-gray-400">Frame:</span>
                  <span className="block truncate">{frameNumber}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
