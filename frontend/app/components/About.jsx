'use client';
import React from 'react';
import Link from 'next/link';
import Team from './Team';

const About = () => {
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

      <section id="about" className="py-20">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-5xl font-bold mb-6">About Navis</h2>
            <p className="text-xl text-slate-400 max-w-3xl mx-auto">
              A semantic search platform that makes exploring autonomous driving
              datasets as simple as describing what you're looking for
            </p>
          </div>

          {/* Main Content Sections */}
          <div className="space-y-16">
            {/* What is Navis */}
            <div>
              <h3 className="text-2xl font-bold mb-4 text-white">
                What is Navis?
              </h3>
              <p className="text-lg text-slate-300 leading-relaxed">
                <span className="text-white font-semibold">Navis</span> is
                developed to make large-scale open-source autonomous driving
                datasets, such as KITTI, BDD100K, and Argoverse - effortless to
                explore. Instead of manually searching through thousands of
                frames, you can simply describe what you want to find, like{' '}
                <em className="text-white">"pedestrians at night"</em> or{' '}
                <em className="text-white">"cars at an intersection"</em> and
                instantly retrieve the most relevant matches. The goal is to
                turn tedious data discovery into a seamless,
                natural-language-driven experience for researchers and engineers
                working with vision data.
              </p>
            </div>

            {/* Divider */}
            <div className="border-t border-slate-700/50"></div>

            {/* Under The Hood */}
            <div>
              <h3 className="text-2xl font-bold mb-4 text-white">
                Under The Hood
              </h3>
              <p className="text-lg text-slate-300 leading-relaxed mb-6">
                Under the hood, this system combines multiple state-of-the-art
                AI components.
                <span className="text-white font-semibold">
                  {' '}
                  CLIP ViT-B/32
                </span>{' '}
                encodes both visual frames and textual queries into a shared
                embedding space with L2 normalization for cosine similarity
                matching.
                <span className="text-white font-semibold">
                  {' '}
                  BLIP-large
                </span>{' '}
                generates rich, context-aware captions for each frame, providing
                natural language descriptions of the driving scene.
                <span className="text-white font-semibold"> YOLOv8</span>{' '}
                detects objects like cars, pedestrians, and traffic lights for
                precise filtering. These embeddings are indexed using{' '}
                <span className="text-white font-semibold">FAISS</span> to
                enable millisecond-level similarity search across over 3000
                frames.
              </p>

              {/* Technology Pills */}
              <div className="flex flex-wrap gap-3">
                <span className="px-4 py-2 bg-slate-700/30 border border-slate-600/50 rounded-lg text-sm text-slate-300">
                  CLIP ViT-B/32
                </span>
                <span className="px-4 py-2 bg-slate-700/30 border border-slate-600/50 rounded-lg text-sm text-slate-300">
                  BLIP-large
                </span>
                <span className="px-4 py-2 bg-slate-700/30 border border-slate-600/50 rounded-lg text-sm text-slate-300">
                  YOLOv8
                </span>
                <span className="px-4 py-2 bg-slate-700/30 border border-slate-600/50 rounded-lg text-sm text-slate-300">
                  FAISS
                </span>
              </div>
            </div>

            {/* Divider */}
            <div className="border-t border-slate-700/50"></div>

            {/* Tech Stack */}
            <div>
              <h3 className="text-2xl font-bold mb-4 text-white">
                The Tech Stack
              </h3>
              <p className="text-lg text-slate-300 leading-relaxed mb-6">
                Built with a modern full-stack architecture:{' '}
                <span className="text-white font-semibold">Next.js</span> and{' '}
                <span className="text-white font-semibold">React</span> power
                the responsive frontend with Tailwind CSS for styling.
                <span className="text-white font-semibold"> FastAPI</span>{' '}
                handles the backend API with{' '}
                <span className="text-white font-semibold">PostgreSQL</span> and{' '}
                <span className="text-white font-semibold">Supabase</span>{' '}
                managing the database and authentication.{' '}
                <span className="text-white font-semibold">
                  Google Drive API
                </span>{' '}
                serves as the media storage layer. The result interleaving
                algorithm ensures diverse results across all three datasets,
                while duplicate detection prevents showing the same frame twice.
              </p>

              {/* Tech Stack Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-4 text-center">
                  <div className="text-slate-400 text-sm mb-1">Frontend</div>
                  <div className="text-white font-semibold">Next.js</div>
                </div>
                <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-4 text-center">
                  <div className="text-slate-400 text-sm mb-1">Backend</div>
                  <div className="text-white font-semibold">FastAPI</div>
                </div>
                <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-4 text-center">
                  <div className="text-slate-400 text-sm mb-1">Database</div>
                  <div className="text-white font-semibold">PostgreSQL</div>
                </div>
                <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-4 text-center">
                  <div className="text-slate-400 text-sm mb-1">Auth</div>
                  <div className="text-white font-semibold">Supabase</div>
                </div>
              </div>
            </div>

            {/* Divider */}
            <div className="border-t border-slate-700/50"></div>

            {/* The Impact */}
            <div>
              <h3 className="text-2xl font-bold mb-4 text-white">The Impact</h3>
              <p className="text-lg text-slate-300 leading-relaxed">
                By unifying these components, Navis dramatically reduces the
                manual overhead that researchers typically face when studying
                open-source driving datasets. Whether you're investigating rare
                edge cases like night-time jaywalking or curating balanced test
                sets for perception models, the system helps you pinpoint
                exactly what you need within seconds. It bridges the gap between
                raw visual data and human intent, creating a more intuitive,
                language-driven interface for exploring complex multimodal
                datasets.
              </p>
            </div>
          </div>

          {/* Team Section */}
          <div className="mt-32">
            <Team />
          </div>
        </div>
      </section>
    </div>
  );
};

export default About;
