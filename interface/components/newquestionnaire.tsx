'use client';

import { createClient } from '@/utils/supabase/client';
import {
  ArrowLeft,
  ArrowRight,
  X,
  ImageIcon,
  CloudUpload,
  CheckCircle,
  AlertTriangle,
  Loader2,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useCallback, useRef, useState } from 'react';

export default function NewQuestionnaireModern() {
  const router = useRouter();
  const supabase = createClient();

  const [title, setTitle] = useState('');
  const [saving, setSaving] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const inputRef = useRef<HTMLInputElement | null>(null);

  const QUESTIONNAIRE_LIMIT = 5;
  const builderApiUrl = process.env.NEXT_PUBLIC_BUILDER_API_URL || 'http://localhost:8000';

  const getToken = async (): Promise<string> => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session?.access_token) throw new Error('No access token available');
    return session.access_token;
  };

  const handlePickedFile = useCallback((f: File | null) => {
    setErrorMsg(null);
    if (!f) {
      setFile(null);
      setPreviewUrl(null);
      return;
    }

    const allowedTypes = ["image/png", "image/jpeg", "application/pdf"];
    if (!allowedTypes.includes(f.type)) {
      setErrorMsg('Seules les images sont acceptées.');
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      setErrorMsg('Fichier trop volumineuse (max 10MB).');
      return;
    }

    setFile(f);
    const url = URL.createObjectURL(f);
    setPreviewUrl(url);
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] || null;
    handlePickedFile(f);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0] || null;
    handlePickedFile(f);
  };

  const removeFile = () => {
    if (previewUrl && previewUrl.startsWith('blob:')) URL.revokeObjectURL(previewUrl);
    setFile(null);
    setPreviewUrl(null);
    setErrorMsg(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  const uploadSurveyFileToBackend = async (fileToUpload: File, token: string, questionnaireId: string) => {
    const form = new FormData();
    form.append('file', fileToUpload);
    form.append('questionnaire_id', questionnaireId);

    const res = await fetch(`${builderApiUrl}/upload_file`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`
      },
      body: form
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || 'Erreur upload fichier');
    }

    const json = await res.json();
    return json.path;
  };

  const handleCreate = async () => {
    setErrorMsg(null);
    if (!title.trim()) {
      setErrorMsg('Merci de saisir un titre');
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
        setErrorMsg('Impossible de vérifier le nombre de questionnaires.');
        setSaving(false);
        return;
      }

      if ((count ?? 0) >= QUESTIONNAIRE_LIMIT) {
        setErrorMsg(`Vous ne pouvez pas créer plus de ${QUESTIONNAIRE_LIMIT} questionnaires.`);
        setSaving(false);
        return;
      }

      const { data, error } = await supabase.from('questionnaires').insert({
        user_id: user.id,
        title,
        schema_json: {},
        ui_schema_json: {},
        image_path: null
      }).select('id').single();

      if (error || !data) {
        console.error('Erreur lors de la création :', error);
        setErrorMsg('Erreur lors de la création du questionnaire.');
        setSaving(false);
        return;
      }

      const questionnaireId = data.id;

      if (file) {
        try {
          setUploadingFile(true);
          const token = await getToken();
          const path = await uploadSurveyFileToBackend(file, token, questionnaireId);

          const { error: updateErr } = await supabase
            .from('questionnaires')
            .update({ image_path: path })
            .eq('id', questionnaireId);

          if (updateErr) {
            console.error('Erreur lors de la mise à jour du chemin fichier :', updateErr);
            // Non blocking
          }
        } catch (e: any) {
          console.error('Erreur upload fichier:', e);
          const keep = confirm('La sauvegarde du fichier a échoué. Créer le questionnaire manuellement sans modèle ?');
          if (!keep) {
            try { await supabase.from('questionnaires').delete().eq('id', questionnaireId); } catch (delErr) { console.error('Suppression échouée', delErr); }
            setSaving(false);
            setUploadingFile(false);
            return;
          }
        } finally {
          setUploadingFile(false);
        }
      }

      router.push(`/protected/questionnaire/${questionnaireId}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="container mx-auto px-6 py-8 max-w-3xl">
      {/* Top bar (sticky on scroll) */}
      <div className="sticky top-4 z-20 bg-transparent mb-6">
        <div className="flex items-center justify-between bg-white/80 backdrop-blur-md border border-gray-100 rounded-lg px-4 py-3 shadow-sm">
          <div className="flex items-center gap-3">
            <button onClick={() => router.back()} className="flex items-center gap-2 text-gray-600 hover:text-blue-600">
              <ArrowLeft size={18} /> Retour
            </button>
            {file ? (
              <span className="ml-3 inline-flex items-center gap-2 text-green-700 bg-green-50 px-2 py-1 rounded text-xs">
                <CheckCircle size={14} /> Fichier sélectionnée
              </span>
            ) : (
              <span className="ml-3 inline-flex items-center gap-2 text-yellow-800 bg-yellow-50 px-2 py-1 rounded text-xs">
                <AlertTriangle size={14} /> Fichier recommandée
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            {uploadingFile && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Loader2 className="animate-spin" size={16} /> Upload…
              </div>
            )}

            <button
              onClick={handleCreate}
              disabled={saving || uploadingFile}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
            >
              <ArrowRight size={16} />
              {saving ? 'Création...' : file ? 'Créer (avec fichier)' : 'Créer'}
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-start gap-6">
          <div className="flex-1">
            <label className="block mb-2 text-sm font-medium text-gray-700">Titre du questionnaire</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ex. : Questionnaire RH 2025"
              className="w-full p-3 border border-gray-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
            />

            <div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              className={`mt-6 rounded-lg p-5 flex items-center gap-6 transition-all ${
                dragOver ? 'border-2 border-blue-400 bg-blue-50' : 'border border-dashed border-gray-200 bg-white'
              }`}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-gradient-to-br from-gray-50 to-gray-100 rounded-md shadow-sm">
                    <CloudUpload size={28} />
                  </div>
                  <div className="min-w-0">
                    <p className="font-semibold text-gray-800 truncate">Déposer le modèle de votre questionnaire</p>
                    <p className="text-sm text-gray-500">ou <button className="text-blue-600 underline" onClick={() => inputRef.current?.click()}>parcourir</button> votre ordinateur</p>
                    <input ref={inputRef} type="file" accept="image/*,application/pdf" onChange={handleFileChange} className="hidden" />
                  </div>
                </div>

                <p className="mt-3 text-xs text-gray-500">Formats supportés: PDF, JPG, PNG — Taille max: 10 MB.</p>

                {errorMsg && <div className="mt-3 text-sm text-red-600">{errorMsg}</div>}
              </div>

              <div className="w-44 h-32 bg-gray-50 rounded-md border flex items-center justify-center overflow-hidden relative">
              {previewUrl ? (
                  <>
                    {file?.type === "application/pdf" ? (
                      // Aperçu simple d'un PDF : première page ou viewer natif
                      <embed src={previewUrl} type="application/pdf" className="object-cover w-full h-full" />
                    ) : (
                      <img src={previewUrl} alt="Aperçu" className="object-cover w-full h-full" />
                    )}
                    <button onClick={removeFile} title="Retirer le fichier" className="absolute top-2 right-2 bg-white rounded-full p-1 shadow">
                      <X size={14} />
                    </button>
                  </>
                ) : (
                  <div className="flex flex-col items-center gap-2 text-gray-400">
                    <ImageIcon size={36} />
                    <div className="text-xs">Aperçu</div>
                  </div>
                )}
              </div>
            </div>

            {!file && (
              <div className="mt-4 p-3 rounded border-l-4 border-yellow-400 bg-yellow-50 text-yellow-800">
                <strong>Conseil :</strong> Vous pourrez créer et remplir le questionnaire manuellement plus tard mais une photo du modèle facilitera grandement la création automatique !
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
