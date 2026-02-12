import Header from '../components/Header';

export default async function HeaderPage({ searchParams }) {
  // Ensure we await before using its properties
  const params = await searchParams;

  const rawQ = params?.q;
  const initialQuery =
    typeof rawQ === 'string'
      ? rawQ
      : Array.isArray(rawQ)
      ? rawQ[0]
      : '';

  return <Header initialQuery={initialQuery} />;
}
