'use client';
import React, { useState } from 'react';

const CardStack = () => {
  const [activeCard, setActiveCard] = useState(0);

  const cards = [
    {
      id: 0,
      title: 'What is Navis?',
      gradient: 'from-slate-800/95 via-black/95 to-slate-900/95',
      content: (
        <>
          <span className="text-white font-bold text-xl">Navis</span> is
          developed to make large-scale open-source autonomous driving datasets,
          such as KITTI, BDD100K, and Argoverse - effortless to explore. Instead
          of manually searching through thousands of frames, you can simply
          describe what you want to find, like
          <em className="text-white"> "pedestrians at night" </em> or{' '}
          <em className="text-white"> "cars at an intersection" </em> and
          instantly retrieve the most relevant matches. The goal is to turn
          tedious data discovery into a seamless, natural-language-driven
          experience for researchers and engineers working with vision data.
        </>
      ),
    },
    {
      id: 1,
      title: 'Under The Hood',
      gradient: 'from-slate-900/95 via-black/95 to-slate-800/95',
      content: (
        <>
          Under the hood, this system combines multiple state-of-the-art AI
          components.
          <span className="text-white font-semibold"> CLIP ViT-B/32 </span>
          encodes both visual frames and textual queries into a shared embedding
          space with L2 normalization for cosine similarity matching.
          <span className="text-white font-semibold"> BLIP-large </span>{' '}
          generates rich, context-aware captions for each frame, providing
          natural language descriptions of the driving scene.
          <span className="text-white font-semibold"> YOLOv8 </span> detects
          objects like cars, pedestrians, and traffic lights for precise
          filtering. These embeddings are indexed using
          <span className="text-white font-semibold"> FAISS </span> to enable
          millisecond-level similarity search across 2,794 frames.
        </>
      ),
    },
    {
      id: 2,
      title: 'The Tech Stack',
      gradient: 'from-black/95 via-slate-900/95 to-slate-800/95',
      content: (
        <>
          Built with a modern full-stack architecture:
          <span className="text-white font-semibold"> Next.js </span> and
          <span className="text-white font-semibold"> React </span> power the
          responsive frontend with Tailwind CSS for styling.
          <span className="text-white font-semibold"> FastAPI </span> handles
          the backend API with
          <span className="text-white font-semibold"> PostgreSQL </span> and
          <span className="text-white font-semibold"> Supabase </span> managing
          the database and authentication. Google Drive API serves as the media
          storage layer. The result interleaving algorithm ensures diverse
          results across all three datasets, while duplicate detection prevents
          showing the same frame twice.
        </>
      ),
    },
    {
      id: 3,
      title: 'The Impact',
      gradient: 'from-slate-800/95 via-black/95 to-slate-900/95',
      content: (
        <>
          By unifying these components, Navis dramatically reduces the manual
          overhead that researchers typically face when studying open-source
          driving datasets. Whether you're investigating rare edge cases like
          night-time jaywalking or curating balanced test sets for perception
          models, the system helps you pinpoint exactly what you need within
          seconds. It bridges the gap between raw visual data and human intent,
          creating a more intuitive, language-driven interface for exploring
          complex multimodal datasets.
        </>
      ),
    },
  ];

  const getResponsiveValues = () => {
    if (typeof window !== 'undefined') {
      return {
        offset: window.innerWidth < 640 ? 8 : 20,
        rotation: window.innerWidth < 640 ? 2 : 4,
        scale: window.innerWidth < 640 ? 0.96 : 0.92,
      };
    }
    return { offset: 20, rotation: 4, scale: 0.92 };
  };

  return (
    <div className="max-w-3xl mx-auto px-4">
      <div
        className="relative h-[500px] sm:h-[420px] md:h-[380px]"
        style={{ perspective: '1000px' }}
      >
        {cards.map((card, index) => {
          const { offset, rotation, scale } = getResponsiveValues();
          const cardOffset = (index - activeCard) * offset;
          const cardRotation = (index - activeCard) * rotation;
          const cardScale = index === activeCard ? 1 : scale;
          const zIndex = cards.length - Math.abs(index - activeCard);
          const opacity = Math.abs(index - activeCard) > 1 ? 0 : 1;

          return (
            <div
              key={card.id}
              className={`absolute inset-0 transition-all duration-500 ${
                index !== activeCard ? 'cursor-pointer' : ''
              }`}
              style={{
                transform: `translateX(${cardOffset}px) translateY(${cardOffset}px) rotateZ(${cardRotation}deg) scale(${cardScale})`,
                zIndex,
                opacity,
              }}
              onClick={() => index !== activeCard && setActiveCard(index)}
            >
              <div
                className={`h-full bg-gradient-to-br ${card.gradient} backdrop-blur-sm rounded-2xl shadow-2xl p-5 sm:p-8 border border-slate-700/50 hover:border-slate-600/70 transition-all duration-300 overflow-auto`}
              >
                <h3 className="text-xl sm:text-2xl font-bold mb-4 sm:mb-5 text-white">
                  {card.title}
                </h3>
                <p className="text-base sm:text-lg text-slate-300 leading-relaxed">
                  {card.content}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Navigation Dots */}
      <div className="flex justify-center gap-3 mt-10">
        {cards.map((card, index) => (
          <button
            key={card.id}
            onClick={() => setActiveCard(index)}
            className={`transition-all duration-300 rounded-full ${
              index === activeCard
                ? 'w-10 h-3 bg-slate-400'
                : 'w-3 h-3 bg-slate-700 hover:bg-slate-600'
            }`}
            aria-label={`Go to card ${index + 1}`}
          />
        ))}
      </div>

      {/* Navigation Arrows */}
      <div className="flex justify-center gap-4 mt-6">
        <button
          onClick={() =>
            setActiveCard((prev) => (prev > 0 ? prev - 1 : cards.length - 1))
          }
          className="group px-3 py-2 sm:px-4 bg-slate-800/50 border border-slate-700/50 rounded-lg hover:border-slate-600/70 transition-all duration-300 cursor-pointer"
          aria-label="Previous card"
        >
          <svg
            className="w-5 h-5 text-slate-400 group-hover:text-slate-300 transition-colors"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>
        <button
          onClick={() =>
            setActiveCard((prev) => (prev < cards.length - 1 ? prev + 1 : 0))
          }
          className="group px-3 py-2 sm:px-4 bg-slate-800/50 border border-slate-700/50 rounded-lg hover:border-slate-600/70 transition-all duration-300 cursor-pointer"
          aria-label="Next card"
        >
          <svg
            className="w-5 h-5 text-slate-400 group-hover:text-slate-300 transition-colors"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default CardStack;
