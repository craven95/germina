import SurveyEditor from '@/components/surveyeditor';
import { Suspense, use } from 'react';


export default function EditorPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  return (
    <Suspense fallback={<div>Chargement...</div>}>
      <SurveyEditor id={id} />
    </Suspense>
  );
}