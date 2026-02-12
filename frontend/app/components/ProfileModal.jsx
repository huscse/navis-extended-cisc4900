// For Header component
import React from 'react';
import { useProfile } from '../hooks/useProfile';

export default function ProfileModal({ isOpen, onClose }) {
  const { name, setName, email, loading, saving, error, handleUpdateProfile } =
    useProfile(isOpen);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center"
      role="dialog"
      aria-modal="true"
    >
      {/* backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={() => !loading && onClose()}
      />

      {/* panel */}
      <div className="relative z-10 w-full max-w-md mx-4 rounded-xl bg-[#0b1220]/80 border border-white/10 p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-white mb-3">Your profile</h3>

        {loading ? (
          <p className="text-slate-300">Loading…</p>
        ) : (
          <>
            <label className="block text-sm text-slate-300 mb-1">Name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-2 rounded-md bg-slate-800 text-white placeholder-slate-400 border border-white/5 mb-3 focus:outline-none focus:ring-2 focus:ring-slate-600"
              placeholder="Full name"
            />

            <label className="block text-sm text-slate-300 mb-1">Email</label>
            <input
              value={email}
              readOnly
              className="w-full px-4 py-2 rounded-md bg-slate-900 text-slate-300 border border-white/5 mb-3 cursor-not-allowed"
            />

            {error && <p className="text-red-400 text-sm mb-2">{error}</p>}

            <div className="mt-3 flex items-center justify-end gap-3">
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-md bg-transparent border border-white/10 text-slate-300 hover:bg-white/5 transition"
                type="button"
                disabled={saving}
              >
                Cancel
              </button>

              <button
                onClick={async () => {
                  await handleUpdateProfile();
                  onClose();
                }}
                className="px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 transition"
                type="button"
                disabled={saving}
              >
                {saving ? 'Saving…' : 'Save'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
