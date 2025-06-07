import SurveyEditor from '@/components/surveyeditor';
import { use } from 'react';


export default function EditorPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  return (
      <SurveyEditor id={id} />
  );
}
