'use client';

import { createClient } from '@/utils/supabase/client';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export default function NewQuestionnaire() {
  const router = useRouter();
  const supabase = createClient();
  const [title, setTitle] = useState('');
  const [saving, setSaving] = useState(false);

  const QUESTIONNAIRE_LIMIT = 5;

  const handleCreate = async () => {
    if (!title.trim()) {
      alert('Merci de saisir un titre');
      return;
    }

    setSaving(true);
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        router.push('/sign-in');
        return;
      }

      const { count, error: countError } = await supabase
        .from('questionnaires')
        .select('id', { count: 'exact', head: true })
        .eq('user_id', user.id);

      if (countError) {
        console.error('Erreur lors du comptage des questionnaires :', countError);
        alert('Impossible de vérifier le nombre de questionnaires. Veuillez réessayer.');
        setSaving(false);
        return;
      }

      if ((count ?? 0) >= QUESTIONNAIRE_LIMIT) {
        alert(`Vous ne pouvez pas créer plus de ${QUESTIONNAIRE_LIMIT} questionnaires.`);
        setSaving(false);
        return;
      }

      const { data, error } = await supabase.from('questionnaires').insert({
        user_id: user.id,
        title,
        schema_json: {},
        ui_schema_json: {},
      }).select('id').single();

      if (error) {
        console.error('Erreur lors de la création :', error);
        alert('Erreur lors de la création du questionnaire.');
        return;
      }

      router.push(`/protected/questionnaire/${data.id}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="container mx-auto px-6 py-12 max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-gray-600 hover:text-blue-600"
        >
          <ArrowLeft size={20} /> Retour
        </button>
      </div>

      <h1 className="text-2xl font-semibold mb-4">Créer un nouveau questionnaire</h1>

      <label className="block mb-6">
        <span className="text-sm font-medium text-gray-700">Titre du questionnaire</span>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Ex. : Questionnaire RH 2025"
          className="w-full mt-1 p-3 border border-gray-300 rounded"
        />
      </label>

      <button
        onClick={handleCreate}
        disabled={saving}
        className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
      >
        <ArrowRight size={18} /> {saving ? 'Création...' : 'Suivant'}
      </button>
    </section>
  );
}
