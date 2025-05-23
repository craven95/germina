'use client';

import { createClient } from '@/utils/supabase/client';
import { Rocket } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export default function QuestionnairesDeployHome({ questionnaires }: { questionnaires: any[] }) {
  const router = useRouter();
  const supabase = createClient();
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const handleDelete = async (id: string) => {
    if (!confirm('Supprimer ce questionnaire ?')) return;
    setLoadingId(id);
    const { error } = await supabase.from('questionnaires').delete().eq('id', id);
    if (error) {
      console.error(error);
      setLoadingId(null);
    } else {
      router.refresh();
    }
  };

  const handleDownload = (q: any) => {
    const blob = new Blob([JSON.stringify(q.schema_json, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${q.title || 'questionnaire'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="container mx-auto px-6 py-16 text-center">
      <div className="flex justify-between items-center max-w-2xl mx-auto mb-10">
        <h1 className="text-4xl font-extrabold text-gray-900 dark:text-gray-100">
          Prêt à déployer ?
        </h1>
      </div>

      <ul className="space-y-4 text-left max-w-2xl mx-auto">
        {questionnaires.map((q) => (
          <li
            key={q.id}
            className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow hover:shadow-md transition relative"
          >
            <div className="flex justify-between items-start">
              <div>
                <a
                  href={`/protected/deploiement/${q.id}`}
                  className="text-indigo-600 dark:text-indigo-400 text-lg font-semibold hover:underline"
                >
                  {q.title}
                </a>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  Créé le : {new Date(q.created_at).toLocaleString()}
                </div>
              </div>

              <div className="flex gap-3 items-center">
                <button
                    onClick={() => router.push(`/protected/deploiement/${q.id}`)}
                    className="text-green-500 hover:text-green-700"
                    title="Déployer"
                  >
                  <Rocket size={18} />
                </button>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
