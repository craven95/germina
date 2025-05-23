'use client';

export default function SchemaInputs({
  title,
  schemaJson,
  uiSchemaJson,
  onTitleChange,
  onSchemaChange,
  onUiSchemaChange
}: {
  title: string;
  schemaJson: string;
  uiSchemaJson: string;
  onTitleChange: (value: string) => void;
  onSchemaChange: (value: string) => void;
  onUiSchemaChange: (value: string) => void;
}) {
  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="shrink-0">
        <label className="block mb-2 font-medium">Titre</label>
        <input
          value={title}
          onChange={e => onTitleChange(e.target.value)}
          className="w-full p-2 border rounded"
        />
      </div>

      <div className="flex-1 flex flex-col space-y-4 mt-4 min-h-0">
        {/* Editeur du schéma JSON */}
        <div className="flex flex-col flex-1 min-h-0">
          <label className="block mb-2 font-medium">Schéma JSON</label>
          <textarea
            value={schemaJson}
            onChange={e => onSchemaChange(e.target.value)}
            className="flex-1 w-full p-2 border rounded font-mono text-sm resize-none min-h-0"
          />
        </div>

        {/* Editeur du UI Schema JSON */}
        <div className="flex flex-col flex-1 min-h-0">
          <label className="block mb-2 font-medium">UI Schema JSON</label>
          <textarea
            value={uiSchemaJson}
            onChange={e => onUiSchemaChange(e.target.value)}
            className="flex-1 w-full p-2 border rounded font-mono text-sm resize-none min-h-0"
          />
        </div>
      </div>
    </div>
  );
}
