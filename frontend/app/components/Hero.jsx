'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthSession } from '../lib/useAuthSession';

const Hero = () => {
  const router = useRouter();
  const { session, loading } = useAuthSession();
  const [isTransitioning, setIsTransitioning] = useState(false);

  const handleTransition = (path) => {
    setIsTransitioning(true);
    setTimeout(() => {
      router.push(path);
    }, 400);
  };

  const handleGetStarted = () => {
    if (session) {
      // If signed in, go to search
      handleTransition('/header');
    } else {
      // If not signed in, go to sign in
      handleTransition('/signin');
    }
  };

  return (
    <div
      className={`transition-all duration-400 ease-in-out transform ${
        isTransitioning
          ? 'opacity-0 scale-95 -translate-y-4'
          : 'opacity-100 scale-100 translate-y-0'
      }`}
    >
      <section className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 md:py-32">
          <div className="text-center">
            <h1 className="text-5xl md:text-5xl lg:text-5xl font-bold mb-6 leading-tight font-extrabold tracking-tight">
              VLM-Driven
              <span className="text-slate-300 font-extrabold">
                {' '}
                Open Dataset
              </span>
              <br />
              <span>Navigator</span>
            </h1>
            <p className="text-xl md:text-2xl text-slate-300 mb-12 max-w-3xl mx-auto">
              Explore and analyze large-scale driving datasets with the power of
              Vision-Language Models. Search, summarize, and extract insights
              effortlessly.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={handleGetStarted}
                disabled={isTransitioning || loading}
                className="px-8 py-4 bg-slate-700 hover:bg-slate-600 rounded-lg text-lg font-medium transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 active:scale-95"
              >
                {loading
                  ? 'Loading...'
                  : session
                  ? 'Go to Search'
                  : 'Get Started'}
              </button>
              <button
                onClick={() => handleTransition('/about')}
                disabled={isTransitioning}
                className="px-8 py-4 bg-slate-800 hover:bg-slate-700 rounded-lg text-lg font-medium transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 active:scale-95"
              >
                Learn More
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Hero;
