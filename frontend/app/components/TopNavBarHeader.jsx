// For Header component
import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { User, Bookmark } from 'lucide-react';

export default function TopNavBarHeader({
  session,
  onSignOut,
  onProfileClick,
}) {
  return (
    <div className="sticky top-5 bottom-2 z-10 backdrop-blur">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/">
          <Image
            src="/images/navislogodraft.png"
            alt="Navis Logo"
            width={100}
            height={40}
            priority
            className="object-contain text-white cursor-pointer"
          />
        </Link>

        {/* Right actions */}
        <div className="flex items-center gap-3">
          {/* Bookmarks link - only show when signed in */}
          {session && (
            <Link href="/bookmarks">
              <button
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-white/10 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-slate-600 cursor-pointer"
                title="View Bookmarks"
              >
                <Bookmark className="w-4 h-4" />
                <span>Bookmarks</span>
              </button>
            </Link>
          )}

          {session && (
            <button
              onClick={onSignOut}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-white/10 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-slate-600 cursor-pointer"
            >
              Sign Out
            </button>
          )}

          <button
            onClick={onProfileClick}
            className="w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 text-white transition-all duration-200 hover:scale-105 active:scale-95 focus:outline-none focus:ring-2 focus:ring-white/20 flex items-center justify-center cursor-pointer"
            title="Profile"
            aria-label="Open profile"
          >
            <User className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
