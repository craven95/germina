'use client';

import { createClient } from '@/utils/supabase/client';
import Ajv from 'ajv';
import { ArrowLeft, Save } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import ChatAssistant from './chatassistant';
import PreviewPane from './previewpane';
import SchemaInputs from './schemainputs';

export default function SurveyEditor({ id }: { id?: string }) {
  const supabase = createClient();
  const router = useRouter();
  const ajv = new Ajv();

  const [title, setTitle] = useState('');
  const [schemaJson, setSchemaJson] = useState('');
  const [uiSchemaJson, setUiSchemaJson] = useState('');
  const [saving, setSaving] = useState(false);
  const [isEditing] = useState(!!id);

  useEffect(() => {
    if (id) fetchQuestionnaire();
  }, [id]);

  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const fetchQuestionnaire = async () => {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return router.push('/sign-in');

    const { data } = await supabase
      .from('questionnaires')
      .select('*')
      .eq('id', id)
      .single();

    if (data) {
      setTitle(data.title);
      setSchemaJson(JSON.stringify(data.schema_json || {}, null, 2));
      setUiSchemaJson(JSON.stringify(data.ui_schema_json || {}, null, 2));
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const { user } = (await supabase.auth.getUser()).data;
      if (!user) return router.push('/sign-in');

      const parsedSchema = JSON.parse(schemaJson);
      const parsedUi = uiSchemaJson.trim() ? JSON.parse(uiSchemaJson) : {};

      //  TODO: Add validation with avjf ? but be coherent with preview Validation JSON Schema

      const payload = {
        title,
        schema_json: parsedSchema,
        ui_schema_json: parsedUi,
        user_id: user.id
      };

      if (isEditing && id) {
        await supabase.from('questionnaires').update(payload).eq('id', id);
      } else {
        const { data } = await supabase.from('questionnaires').insert(payload).select();
        if (data) router.push(`/protected/questionnaire/editor/${data[0].id}`);
      }

      router.refresh();
    } catch (error: any) {
      alert(`Erreur: ${error.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleSchemaModify = useCallback(
    (modifications: { title?: string; schema?: any; uiSchema?: any }) => {
      if (modifications.title) setTitle(modifications.title);
      if (modifications.schema) setSchemaJson(JSON.stringify(modifications.schema, null, 2));
      if (modifications.uiSchema) setUiSchemaJson(JSON.stringify(modifications.uiSchema, null, 2));
    },
    []
  );

  const safeJsonParse = (jsonString: string, defaultValue: any = {}) => {
    try {
      if (!jsonString.trim()) return defaultValue;
      const parsed = JSON.parse(jsonString);
      return parsed !== null ? parsed : defaultValue;
    } catch (e) {
      console.error("Erreur de parsing JSON:", e);
      return defaultValue;
    }
  };

return (
  <div className="max-w-8xl mx-auto px-1 py-10 flex flex-col h-screen w-full">
    {/* Barres d’actions en haut */}
    <div className="flex justify-between mb-6 shrink-0">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 text-gray-600 hover:text-blue-600"
      >
        <ArrowLeft size={20} /> Retour
      </button>
      <button
        onClick={handleSave}
        disabled={saving}
        className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
      >
        <Save size={18} /> {saving ? 'Enregistrement...' : 'Enregistrer'}
      </button>
    </div>

    {/* Contenu principal : 3 colonnes */}
    <div className="flex-1 grid grid-cols-3 gap-6 min-h-0">
      {/* Chat */}
      <div className="flex flex-col border rounded-lg p-4 min-h-0">
        <ChatAssistant
          initialSchema={{
            title,
            schema: safeJsonParse(schemaJson),
            uiSchema: safeJsonParse(uiSchemaJson)
          }}
          onModify={handleSchemaModify}
        />
      </div>

      {/* Édition du schéma */}
      <div className="flex flex-col border rounded-lg p-4 min-h-0">
        <SchemaInputs
          title={title}
          schemaJson={schemaJson}
          uiSchemaJson={uiSchemaJson}
          onTitleChange={setTitle}
          onSchemaChange={setSchemaJson}
          onUiSchemaChange={setUiSchemaJson}
        />
      </div>

      {/* Aperçu */}
      <div className="flex flex-col border rounded-lg p-4 min-h-0 overflow-hidden">
        {isMounted && (
          <PreviewPane
            schemaJson={schemaJson}
            uiSchemaJson={uiSchemaJson}
          />
        )}
      </div>
    </div>
  </div>
);
}
