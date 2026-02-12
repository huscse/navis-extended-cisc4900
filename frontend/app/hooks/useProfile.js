// For Header component
import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';

export function useProfile(isOpen) {
  const [profile, setProfile] = useState(null);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Fetch profile when modal opens then populate state variables so inputs are controlled
  // and can be edited before saving back to Supabase user metadata table
  useEffect(() => {
    if (!isOpen) return;

    const fetchProfile = async () => {
      setError(null);
      setLoading(true);

      try {
        const {
          data: { user },
          error: fetchError,
        } = await supabase.auth.getUser();

        if (fetchError) throw fetchError;
        if (user) {
          setProfile(user);

          const fullName =
            (user.user_metadata &&
              (user.user_metadata.full_name || user.user_metadata.name)) ||
            '';
          setName(fullName);
          setEmail(user.email || '');
        }
      } catch (err) {
        console.error('Failed to load profile', err);
        setError(err?.message || 'Failed to load profile');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [isOpen]);

  // Update user metadata
  const handleUpdateProfile = async () => {
    setSaving(true);
    setError(null);
    try {
      const { error: updateError } = await supabase.auth.updateUser({
        data: { full_name: name },
      });
      if (updateError) throw updateError;

      // Update local profile object so UI updates immediately without refetching
      setProfile((p) =>
        p
          ? {
              ...p,
              user_metadata: { ...(p.user_metadata || {}), full_name: name },
            }
          : p,
      );
    } catch (err) {
      console.error('Update failed', err);
      setError(err?.message || 'Update failed');
      throw err; // Re-throw so caller knows it failed
    } finally {
      setSaving(false);
    }
  };

  return {
    profile,
    name,
    setName,
    email,
    loading,
    saving,
    error,
    handleUpdateProfile,
  };
}
