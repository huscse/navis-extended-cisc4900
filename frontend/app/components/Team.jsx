'use client';
import React, { useState, useEffect, useRef } from 'react';

const Team = () => {
  const [searchText, setSearchText] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [hasAnimated, setHasAnimated] = useState(false);
  const sectionRef = useRef(null);

  const teamMembers = [
    {
      name: 'Gagan Charagondla',
      github: 'gagan12334',
      role: 'VLM / Backend',
    },
    {
      name: 'Husnain Khaliq',
      github: 'huscse',
      role: 'UI / Backend - Model Integration',
    },
    {
      name: 'Keerthana Venkatesan',
      github: 'keerthanavenkatesan415',
      role: 'VLM / Data Processing',
    },
    {
      name: 'Lissette Solano',
      github: 'Lissette31',
      role: 'Data Processing / Exploration',
    },
    {
      name: 'Manasvi Perisetty',
      github: 'ManuPer4',
      role: 'Data Processing / Exploration',
    },
    { name: 'Yesun Ang', github: 'yesun-ang', role: 'VLM / Data Processing' },
    { name: 'Erica Li', github: 'erica-1i', role: 'UI/UX - Frontend' },
  ];

  // Intersection Observer to trigger animation when section is visible
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasAnimated) {
            setHasAnimated(true);
            startTyping();
          }
        });
      },
      { threshold: 0.3 },
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => {
      if (sectionRef.current) {
        observer.unobserve(sectionRef.current);
      }
    };
  }, [hasAnimated]);

  const startTyping = () => {
    const targetText = 'Latitude AI 2A Team';
    let currentIndex = 0;

    const typeInterval = setInterval(() => {
      if (currentIndex <= targetText.length) {
        setSearchText(targetText.slice(0, currentIndex));
        currentIndex++;
      } else {
        clearInterval(typeInterval);
        setTimeout(() => setShowResults(true), 400);
      }
    }, 80);
  };

  return (
    <div ref={sectionRef}>
      {/* Divider */}
      <div className="border-t border-slate-700/50 mb-16"></div>

      {/* Search Bar */}
      <div className="mb-10">
        <div className="max-w-xl mx-auto">
          <div className="relative">
            <input
              type="text"
              value={searchText}
              readOnly
              className="w-full px-5 py-3.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-white text-base focus:outline-none transition-all duration-300"
              placeholder="Search team members..."
            />
            <div className="absolute right-4 top-1/2 -translate-y-1/2">
              <svg
                className="w-5 h-5 text-slate-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Results */}
      {showResults && (
        <div className="animate-in fade-in duration-700">
          {/* Results Header */}
          <div className="mb-6 flex items-center gap-2">
            <div className="w-1 h-6 bg-gradient-to-b from-slate-400 to-slate-700 rounded-full" />
            <h2 className="text-lg font-semibold text-white">Team Members</h2>
            <span className="text-sm text-slate-400">
              ({teamMembers.length} results)
            </span>
          </div>

          {/* Team Grid - Simple List Style */}
          <div className="space-y-3 mb-8">
            {teamMembers.map((member, index) => (
              <a
                key={member.name}
                href={`https://github.com/${member.github}`}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-4 p-4 bg-slate-800/30 border border-slate-700/50 rounded-lg hover:bg-slate-800/50 hover:border-slate-600/70 transition-all duration-300 group"
                style={{
                  animationDelay: `${index * 100}ms`,
                  animation: 'slideIn 0.5s ease-out forwards',
                  opacity: 0,
                }}
              >
                {/* Avatar */}
                <div className="w-14 h-14 rounded-lg bg-slate-700 border border-slate-600 overflow-hidden flex-shrink-0 group-hover:scale-105 transition-transform duration-300">
                  <img
                    src={`https://github.com/${member.github}.png`}
                    alt={member.name}
                    className="w-full h-full object-cover"
                  />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <h3 className="text-white font-medium text-base mb-0.5">
                    {member.name}
                  </h3>
                  <p className="text-slate-400 text-sm">{member.role}</p>
                </div>

                {/* GitHub Link */}
                <div className="flex items-center gap-2 text-slate-500 text-sm group-hover:text-slate-400 transition-colors">
                  <svg
                    className="w-4 h-4"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      fillRule="evenodd"
                      d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span className="hidden sm:inline">@{member.github}</span>
                </div>

                {/* Arrow */}
                <svg
                  className="w-5 h-5 text-slate-600 group-hover:text-slate-400 group-hover:translate-x-1 transition-all duration-300"
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
              </a>
            ))}
          </div>

          {/* Challenge Badge */}
          <div className="text-center">
            <div className="inline-block bg-slate-800/30 border border-slate-700/50 rounded-lg px-5 py-2.5">
              <p className="text-sm text-slate-400">
                Fall 2025 Break Through Tech AI Studio Challenge
              </p>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(15px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
};

export default Team;
