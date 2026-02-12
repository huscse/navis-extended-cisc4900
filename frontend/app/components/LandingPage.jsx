'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthSession } from '../lib/useAuthSession';
import Footer from './Footer';
import Hero from './Hero';
import Navigation from './Navigation';

export default function LandingPage() {
  const { session } = useAuthSession();
  const router = useRouter();

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#111827_0%,#000000_45%,#1F2937_95%)] text-white">
      {/* Navigation */}
      <Navigation />

      {/* Hero Section */}
      <Hero />

      {/* Footer */}
      <Footer />
    </div>
  );
}
