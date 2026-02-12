// For Header component
import React from 'react';
import SearchBar from './SearchBar';
import DynamicGreeting from './DynamicGreeting';

export default function HeroSection({ onSearch, loading }) {
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
    </header>
  );
}
