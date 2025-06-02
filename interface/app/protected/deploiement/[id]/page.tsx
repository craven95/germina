'use client'

import { createClient } from '@/utils/supabase/client';
import { ArrowLeft, Trash, X } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { use, useEffect, useRef, useState } from 'react';
import DeployOptions from '../../../../components/deployoptions';

interface DeploiementProps { params: Promise<{ id: string }> }

type ImageInfo = { name: string; tag: string; updated_at?: string };

export default function DeploiementPage({ params }: DeploiementProps) {
  const { id } = use(params);
  const router = useRouter();
  const supabase = createClient();

  const [title, setTitle] = useState('');
  const [schemaJson, setSchemaJson] = useState<any>(null);
  const [uiSchemaJson, setUiSchemaJson] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const [currentImage, setCurrentImage] = useState<ImageInfo | null>(null);
  const [error, setError] = useState<string>();
  const [success, setSuccess] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);

  const [showDeployModal, setShowDeployModal] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const POLL_INTERVAL = 3000;
  const TIMEOUT_MS = 3 * 60 * 1000;

  const builderApiUrl = process.env.NEXT_PUBLIC_BUILDER_API_URL || 'http://localhost:5000';

  const getToken = async (): Promise<string> => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session?.access_token) {
      throw new Error('No access token available');
    }
    return session.access_token;
  };

  const fetchCurrentImage = async (token: string) => {
    const res = await fetch(
      `${builderApiUrl}/list?questionnaire_id=${id}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    const { images: imgs } = await res.json();
    const latest = imgs.find((img: ImageInfo) => img.tag === 'latest') || null;
    setCurrentImage(latest);
  };

  useEffect(() => {
    (async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return router.push('/sign-in');

      const { data, error: errQ } = await supabase
        .from('questionnaires')
        .select('title, schema_json, ui_schema_json')
        .eq('id', id).eq('user_id', user.id).single();
      if (errQ || !data) {
        setError('Impossible de récupérer le questionnaire');
        return setLoading(false);
      }
      setTitle(data.title);
      setSchemaJson(data.schema_json);
      setUiSchemaJson(data.ui_schema_json);

      const token = await getToken();
      await fetchCurrentImage(token);
      setLoading(false);
    })();

    return () => {
      if (pollingRef.current) clearTimeout(pollingRef.current);
    };
  }, [id, router, supabase]);

  const handleBuild = async () => {
    setSubmitting(true);
    setError(undefined);
    setSuccess('');

    try {
      const token = await getToken();
      const { data: { user } } = await supabase.auth.getUser();
      const resp = await fetch(
        `${builderApiUrl}/build/${id}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ user_id: user!.id, title, schema: schemaJson, ui_schema: uiSchemaJson })
        }
      );
      if (!resp.ok) {
        const errorData = await resp.json();
        throw new Error(errorData.detail || 'Erreur au démarrage du build');
      }

      const start = Date.now();
      const poll = async () => {
        const token = await getToken();
        await fetchCurrentImage(token);
        if (currentImage) {
          setSuccess(`Image créée : ${currentImage.name}`);
          setSubmitting(false);
          return;
        }
        if (Date.now() - start < TIMEOUT_MS) {
          pollingRef.current = setTimeout(poll, POLL_INTERVAL);
        } else {
          setError('Le build prend trop de temps. Réessayez plus tard.');
          setSubmitting(false);
        }
      };
      poll();

    } catch (e: any) {
      setError(e.message);
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!currentImage) return;
    if (!confirm(`Supprimer l'image ${currentImage.tag} ?`)) return;
    setSubmitting(true);
    setError(undefined);
    try {
      const token = await getToken();
      const resp = await fetch(
        `${builderApiUrl}/delete_image?questionnaire_id=${id}&tag=latest`,
        { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } }
      );
      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || 'Erreur suppression');
      }
      setSuccess('Image supprimée');
      setCurrentImage(null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  const openDeployModal = () => {
    if (currentImage) setSelectedImage(currentImage.name);
    setShowDeployModal(true);
  };

  if (loading) return <div className="p-8 text-center">Chargement…</div>;

  return (
    <section className="container mx-auto px-6 py-12 max-w-2xl relative">
      <button onClick={() => router.back()} className="flex items-center gap-2 text-gray-600 hover:text-blue-600 mb-6">
        <ArrowLeft size={20}/> Retour
      </button>

      <h1 className="text-2xl font-bold mb-4">
        {currentImage ? `Déploiement de « ${title} »` : `Déployer « ${title} »`}
      </h1>

      <div className="mb-6 text-gray-700">
        {currentImage ? (
          <><p className="text-green-600 mb-2">✅ Interface créée</p></>  
        ) : (
          <><p>Pour déployer ce questionnaire, deux étapes sont nécessaires :</p><ol className="list-decimal list-inside pl-4"><li>Création de l'interface</li><li>Déploiement sur un serveur</li></ol></>
        )}
      </div>

      {error && <div className="text-red-600 mb-4">⚠️ {error}</div>}
      {success && <div className="fixed top-4 right-4 bg-green-100 border border-green-400 text-green-800 px-4 py-3 rounded shadow-lg flex items-center"><span className="flex-1">{success}</span><button onClick={() => setSuccess('')} className="ml-4"><X size={16}/></button></div>}

      <div className="flex gap-4 mb-6">
        <button onClick={handleBuild} disabled={submitting} className={`flex-1 ${currentImage ? 'bg-orange-600 hover:bg-orange-700' : 'bg-blue-600 hover:bg-blue-700'} text-white py-2 rounded disabled:opacity-50 transition-colors`}>
          {submitting ? 'En cours…' : currentImage ? '🔄 Re-créer l’interface' : '🚀 Créer l’interface'}
        </button>
        {currentImage && (
          <button onClick={handleDelete} disabled={submitting} className="bg-red-600 hover:bg-red-700 text-white py-2 rounded disabled:opacity-50 transition-colors flex items-center justify-center gap-2">
            <Trash size={16}/>Supprimer
          </button>
        )}
      </div>

      {currentImage && (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Version actuelle</h2>
          <div className="border p-4 rounded-md bg-gray-50 dark:bg-gray-700">
            <div className="font-medium text-blue-600 dark:text-blue-300">{currentImage.name.split(':')[0]}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1"><span className="font-semibold">Tag :</span> {currentImage.tag}</div>
            {currentImage.updated_at && <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">Dernière mise à jour : {new Date(currentImage.updated_at).toLocaleDateString('fr-FR',{day:'2-digit',month:'long',year:'numeric',hour:'2-digit',minute:'2-digit'})}</div>}
            <button onClick={openDeployModal} className="mt-4 w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded">Déployer</button>
          </div>
        </div>
      )}

      {showDeployModal && selectedImage && <DeployOptions image={{ name: selectedImage }} onClose={() => setShowDeployModal(false)} />}
    </section>
  );
}
