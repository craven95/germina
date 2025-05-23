import { createClient } from '@/utils/supabase/server';
import { redirect } from 'next/navigation';
import NewQuestionnaire from '@/components/newquestionnaire';

export default async function NewPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return redirect('/sign-in');

  return <NewQuestionnaire />;
}
