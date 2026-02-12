import { supabase } from './supabaseClient';

/**
 * Add a bookmark for the current user
 */
export async function addBookmark(frameData) {
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    throw new Error('Must be signed in to bookmark');
  }

  const { data, error } = await supabase
    .from('bookmarks')
    .insert([
      {
        user_id: user.id,
        frame_id: frameData.frame_id,
        dataset: frameData.dataset,
        sequence: frameData.sequence,
        sensor: frameData.sensor,
        frame_number: frameData.frame_number,
        caption: frameData.caption,
        image_url: frameData.imageUrl || frameData.thumbnailUrl,
        score: frameData.score,
      },
    ])
    .select();

  if (error) throw error;
  return data;
}

/**
 * Remove a bookmark
 */
export async function removeBookmark(frameId) {
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    throw new Error('Must be signed in');
  }

  const { error } = await supabase
    .from('bookmarks')
    .delete()
    .eq('user_id', user.id)
    .eq('frame_id', frameId);

  if (error) throw error;
}

/**
 * Check if a frame is bookmarked
 */
export async function isBookmarked(frameId) {
  try {
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) return false;

    const { data, error } = await supabase
      .from('bookmarks')
      .select('id')
      .eq('user_id', user.id)
      .eq('frame_id', frameId)
      .maybeSingle(); // Changed from .single() to .maybeSingle()

    // Only throw on actual errors, not "not found"
    if (error && error.code !== 'PGRST116') {
      console.warn('Bookmark check failed:', error);
      return false;
    }

    return !!data;
  } catch (error) {
    console.warn('Bookmark check error:', error);
    return false; // Fail gracefully
  }
}

/**
 * Get all bookmarks for current user
 */
export async function getBookmarks() {
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    throw new Error('Must be signed in');
  }

  const { data, error } = await supabase
    .from('bookmarks')
    .select('*')
    .eq('user_id', user.id)
    .order('created_at', { ascending: false });

  if (error) throw error;
  return data;
}
