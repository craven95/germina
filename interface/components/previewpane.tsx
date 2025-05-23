'use client';

import JsonFormRenderer from './jsonformrendered';

export default function PreviewPane({ schemaJson, uiSchemaJson }: { 
  schemaJson: string;
  uiSchemaJson: string;
}) {
  try {
    const schema = JSON.parse(schemaJson);
    const uiSchema = JSON.parse(uiSchemaJson);
    
    return (
      <div className="flex-1 overflow-y-auto">
        <h3 className="text-lg font-medium mb-4">Aperçu du questionnaire</h3>
          <JsonFormRenderer schema={schema} uiSchema={uiSchema} />
      </div>
    );
  } catch (error) {
    return (
      <div className="text-red-500 p-4 border-l">
        Prévisualisation du questionnaire impossible : {(error as Error).message}
      </div>
    );
  }
}
