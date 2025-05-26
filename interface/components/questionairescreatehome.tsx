'use client';

import { createClient } from '@/utils/supabase/client';
import { Edit2, PlusCircle, Trash2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

interface Questionnaire {
  id: string;
  title: string;
  created_at: string;
}

interface QuestionnairesCreateHomeProps {
  questionnaires: Questionnaire[];
}

export default function QuestionnairesCreateHome({ questionnaires }: QuestionnairesCreateHomeProps) {
  const router = useRouter();
  const supabase = createClient();
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async (id: string) => {
    if (!confirm('Supprimer ce questionnaire et son interface Docker associée ?')) return;
    setLoadingId(id);
    setError(null);

    try {
      const builderApiUrl = process.env.NEXT_PUBLIC_BUILDER_API_URL || 'http://localhost:5000';
      const token = (await supabase.auth.getSession()).data.session?.access_token;
      if (token) {
        const delImg = await fetch(
          `${builderApiUrl}/delete_image?questionnaire_id=${id}&tag=latest`,
          { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } }
        );
        if (delImg.ok || delImg.status === 404) {
        } else {
          const err = await delImg.json();
          console.error('Erreur suppression image:', err.detail);
        }
      }

      const { error: supaErr } = await supabase
        .from('questionnaires')
        .delete()
        .eq('id', id);
      if (supaErr) throw supaErr;

      router.refresh();
    } catch (e: any) {
      console.error(e);
      setError(e.message || 'Erreur lors de la suppression');
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <section className="container mx-auto px-6 py-16 text-center">
      <div className="flex justify-between items-center max-w-2xl mx-auto mb-10">
        <h1 className="text-4xl font-extrabold text-gray-900 dark:text-gray-100">
          Mes questionnaires
        </h1>
        <button
          onClick={() => router.push('/protected/questionnaire/new')}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          <PlusCircle size={20} />
          Nouveau
        </button>
      </div>

      {error && <div className="text-red-600 mb-4">⚠️ {error}</div>}

      <ul className="space-y-4 text-left max-w-2xl mx-auto">
        {questionnaires.map((q) => (
          <li
            key={q.id}
            className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow hover:shadow-md transition relative"
          >
            <div className="flex justify-between items-start">
              <div>
                <a
                  href={`/protected/questionnaire/${q.id}`}
                  className="text-indigo-600 dark:text-indigo-400 text-lg font-semibold hover:underline"
                >
                  {q.title}
                </a>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  Créé le : {new Date(q.created_at).toLocaleString('fr-FR')}
                </div>
              </div>

              <div className="flex gap-3 items-center">
                <button
                  onClick={() => router.push(`/protected/questionnaire/${q.id}`)}
                  className="text-indigo-500 hover:text-indigo-700"
                  title="Modifier"
                >
                  <Edit2 size={18} />
                </button>
                <button
                  onClick={() => handleDelete(q.id)}
                  className="text-red-600 hover:text-red-800 disabled:opacity-50"
                  disabled={loadingId === q.id}
                  title="Supprimer"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
