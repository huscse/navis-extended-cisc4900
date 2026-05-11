'use client';
import React, { useState } from 'react';
import SearchBar from './SearchBar';
import DynamicGreeting from './DynamicGreeting';

const DATASETS = [
  { label: 'All', value: '' },
  {
    label: 'KITTI',
    value: 'kitti',
    color: 'border-blue-500 text-blue-300 bg-blue-500/20 hover:bg-blue-500/40',
  },
  {
    label: 'BDD10K',
    value: 'bdd10k',
    color:
      'border-green-500 text-green-300 bg-green-500/20 hover:bg-green-500/40',
  },
  {
    label: 'Argoverse',
    value: 'argoverse',
    color:
      'border-purple-500 text-purple-300 bg-purple-500/20 hover:bg-purple-500/40',
  },
];

export default function HeroSection({
  onSearch,
  loading,
  dataset,
  onDatasetChange,
}) {
  return (
    <header className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 pt-16 pb-8 text-center">
      <div className="text-center">
        <DynamicGreeting />
      </div>
      <div className="mt-8">
        <SearchBar
          onSearch={onSearch}
          placeholder="Describe a moment…"
          loading={loading}
          className="max-w-3xl mx-auto"
        />
      </div>
      <div className="flex items-center justify-center gap-2 mt-4">
        {DATASETS.map((ds) => {
          const isActive = dataset === ds.value;
          if (ds.value === '') {
            return (
              <button
                key="all"
                onClick={() => onDatasetChange('')}
                className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-all duration-200 ${
                  isActive
                    ? 'bg-white text-black border-white'
                    : 'border-white/30 text-white/70 hover:bg-white/10'
                }`}
              >
                All
              </button>
            );
          }
          return (
            <button
              key={ds.value}
              onClick={() => onDatasetChange(ds.value)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-all duration-200 ${
                isActive ? ds.color.replace('/20', '/60') : ds.color
              }`}
            >
              {ds.label}
            </button>
          );
        })}
      </div>
    </header>
  );
}
