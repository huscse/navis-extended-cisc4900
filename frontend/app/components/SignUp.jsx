'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { supabase } from '../lib/supabaseClient';
import GitHubButton from './GithubButton';
import { User } from 'lucide-react';
import { UserRound } from 'lucide-react';

export default function SignUp() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const router = useRouter();

  const handleSubmit = async (e) => {
    e?.preventDefault();
    setErrorMsg('');

    if (
      !name.trim() ||
      !email.trim() ||
      !password.trim() ||
      !confirmPassword.trim()
    ) {
      return setErrorMsg('Please fill in all fields.');
    }
    if (password !== confirmPassword) {
      return setErrorMsg('Passwords do not match.');
    }

    setLoading(true);
    // store "name" as user metadata so we can show it later
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { full_name: name },
      },
    });

    setLoading(false);

    if (error) {
      return setErrorMsg(error.message);
    }
    // If successful, redirect to sign in page
    router.push('/signin');
  };

  const disabled =
    loading ||
    !name.trim() ||
    !email.trim() ||
    !password.trim() ||
    !confirmPassword.trim();

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#111827_0%,#000000_45%,#1F2937_95%)] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-4xl font-bold text-white mb-4">
            Navis.
          </h1>
          <p className="text-slate-300 text-xl">Create your account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Full name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-6 py-4 bg-slate-800 bg-opacity-50 text-white placeholder-slate-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-600 transition-all"
          />

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

          <input
            type="password"
            placeholder="Confirm password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="w-full px-6 py-4 bg-slate-800 bg-opacity-50 text-white placeholder-slate-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-600 transition-all"
          />

          {errorMsg && (
            <p className="text-red-400 text-sm pt-2" role="alert">
              {errorMsg}
            </p>
          )}

          <button
            type="submit"
            disabled={disabled}
            className="w-full py-4 bg-slate-800 bg-opacity-70 text-white font-medium rounded-lg hover:bg-opacity-90 focus:outline-none focus:ring-2 focus:ring-slate-600 transition-all mt-4 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating account…' : 'Sign up'}
          </button>
        </form>

        <div className="text-center mt-8">
          <span className="text-slate-300">
            Already have an account?{' '}
            <Link
              href="/signin"
              className="text-white hover:underline font-medium"
            >
              Sign in
            </Link>
          </span>
        </div>

        <GitHubButton />
      </div>
    </div>
  );
}
