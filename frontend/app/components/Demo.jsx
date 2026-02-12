'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, Play } from 'lucide-react';

const Demo = () => {
  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#111827_0%,#000000_45%,#1F2937_95%)] text-white">
      {/* Back Button */}
      <div className="px-4 sm:px-6 lg:px-8 pt-8">
        <Link href="/land">
          <button className="group relative inline-flex items-center gap-1 px-5 py-2.5 overflow-hidden rounded-full bg-gradient-to-r from-slate-800/50 to-slate-900/50 border border-slate-700/50 text-slate-300 hover:text-white transition-all duration-500 cursor-pointer hover:shadow-lg hover:shadow-slate-900/50">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600/0 via-slate-600/0 to-blue-600/0 group-hover:from-blue-600/20 group-hover:via-slate-600/20 group-hover:to-gray-800/20 transition-all duration-500"></div>
            <svg
              className="relative w-5 h-5 transform group-hover:-translate-x-1.5 transition-transform duration-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              strokeWidth={2.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15 19l-7-7 7-7"
              />
            </svg>
            <span className="relative font-semibold text-sm tracking-wide">
              BACK
            </span>
          </button>
        </Link>
      </div>

      {/* Demo Section */}
      <section className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-2 mb-6">
              <Play className="w-4 h-4 text-blue-400" />
              <span className="text-sm text-blue-400 font-medium">
                Product Demo
              </span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              See Navis in Action
            </h1>
            <p className="text-lg text-slate-300 max-w-2xl mx-auto">
              Watch how Navis makes autonomous driving dataset navigation
              effortless with natural language search and AI-powered insights.
            </p>
          </div>

          {/* Video Container */}
          <div className="relative">
            {/* Decorative glow effect */}
            <div className="absolute -inset-4 bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-cyan-500/20 rounded-2xl blur-2xl opacity-50" />

            {/* Video wrapper */}
            <div className="relative bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10 rounded-xl overflow-hidden shadow-2xl backdrop-blur-sm">
              {/* Video embed */}
              <div
                className="relative w-full"
                style={{ paddingBottom: '56.25%', height: 0 }}
              >
                <iframe
                  src="https://www.loom.com/embed/92e6fc755536415cb7a8e09d797c40a0?autoplay=1"
                  frameBorder="0"
                  webkitallowfullscreen="true"
                  mozallowfullscreen="true"
                  allowFullScreen
                  allow="autoplay"
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                  }}
                  className="rounded-lg"
                />
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Demo;
