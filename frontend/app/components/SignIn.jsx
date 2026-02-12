'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { supabase } from '../lib/supabaseClient';
import GitHubButton from './GithubButton';

export default function SignIn() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const router = useRouter();

  const handleSubmit = async (e) => {
    e?.preventDefault();
    setErrorMsg('');

    if (!email.trim() || !password.trim()) {
      return setErrorMsg('Please fill in all fields.');
    }

    setLoading(true);
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    setLoading(false);

    if (error) {
      return setErrorMsg(error.message);
    }

    // If successful, redirect to header page (main app)
    router.push('/header');
  };

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#111827_0%,#000000_45%,#1F2937_95%)] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-12">
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Navis.
          </h1>
          <p className="text-slate-300 text-xl">Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            placeholder="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-6 py-4 bg-slate-800 bg-opacity-50 text-white placeholder-slate-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-600 transition-all"
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-6 py-4 bg-slate-800 bg-opacity-50 text-white placeholder-slate-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-600 transition-all"
          />

          {errorMsg && <p className="text-red-400 text-sm">{errorMsg}</p>}

          <div className="text-right">
            <button
              type="button"
              className="text-slate-400 hover:text-slate-300 text-sm transition-colors bg-transparent border-0 cursor-pointer"
              onClick={() => {
                alert('Password reset is not implemented yet.');
              }}
            >
              Forgot password?
            </button>
          </div>

          <button
            type="submit"
            disabled={loading || !email.trim() || !password.trim()}
            className="w-full py-4 bg-slate-800 bg-opacity-70 text-white font-medium rounded-lg hover:bg-opacity-90 focus:outline-none focus:ring-2 focus:ring-slate-600 transition-all mt-6 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <div className="text-center mt-8">
          <span className="text-slate-300">
            Don&apos;t have an account?{' '}
            <Link
              href="/signup"
              className="text-white hover:underline font-medium"
            >
              Sign up
            </Link>
          </span>
        </div>
        <GitHubButton />
      </div>
    </div>
  );
}
