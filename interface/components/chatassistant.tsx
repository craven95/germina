'use client';

import Ajv from 'ajv';
import { applyPatch } from 'fast-json-patch';
import { useCallback, useEffect, useRef, useState } from 'react';

import Lottie from 'lottie-react';
import waveAnimation from './animations/cat_waiting.json';


interface Operation {
  op: 'add' | 'remove' | 'replace' | 'move' | 'copy' | 'test';
  path: string;
  value?: any;
  from?: string;
}


interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface SchemaState {
  title: string;
  schema: any;
  uiSchema: any;
}

export default function ChatAssistant({
  initialSchema,
  onModify
}: {
  initialSchema: SchemaState;
  onModify: (modifications: {
    title?: string;
    schema?: any;
    uiSchema?: any;
  }) => void;
}) {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const ajv = new Ajv();


  const [messages, setMessages] = useState<Message[]>([]);
  const initialized = useRef(false)


  const validatePatch = (patches: any): patches is Operation[] => {
    return Array.isArray(patches) && patches.every(op => 
      op && typeof op === 'object' &&
      ['add', 'remove', 'replace', 'move', 'copy', 'test'].includes(op.op) &&
      typeof op.path === 'string'
    );
  };

const applySafeModifications = useCallback(
  async (patches: unknown, target: 'schema' | 'uiSchema') => {
    try {
      if (!validatePatch(patches)) {
        throw new Error('Format de patch invalide');
      }

      const baseStructure = target === 'schema' ? { 
        $schema: "http://json-schema.org/draft-07/schema#",
        type: "object",
        properties: {},
        required: []
      } : {};
      
      const current = structuredClone(initialSchema[target] || baseStructure);

      if (target === 'schema' && typeof current.properties !== 'object') {
        current.properties = {};
      }

      console.log('Applying patches:', patches);
      console.log('Initial state:', JSON.stringify(current, null, 2));

      const patchResult = applyPatch(current as any, patches as Operation[], /*validate*/ true);

      const newDoc = patchResult && (patchResult.newDocument ?? patchResult);

      console.log('Patched document:', JSON.stringify(newDoc, null, 2));

      onModify({ [target]: newDoc });
      return true;
    } catch (error) {
      console.error('Erreur détaillée:', error);
      return false;
    }
  },
  [initialSchema, onModify]
);


  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    setIsLoading(true);
    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      console.log('Sending message to assistant:', userMessage);
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [
            ...messages,
            {
              role: 'system',
              content: `
              Current Schema:
              ${JSON.stringify(initialSchema.schema, null, 2)}
              
              Current UI Schema:
              ${JSON.stringify(initialSchema.uiSchema, null, 2)}
              `
            },
            userMessage
          ]
        })
      });
      
      const data = await response.json();
      console.log('Assistant response:', data);
      console.log('MAINTENANT ON VA PARSER LA REPONSE');
      const { response: textResponse, modifications } = data.content 
      ? JSON.parse(data.content.replace(/```json/g, '').replace(/```/g, '').trim())
      : data;

      console.log('PARSED REPONSE IS :', textResponse, modifications);

      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: textResponse }
      ]);

        if (modifications) {
          console.log('Applying modifications:', modifications);
          
          let success = true;
          
          if (modifications.title) {
            onModify({ title: modifications.title });
          }

          if (modifications.schemaPatch) {
            success = await applySafeModifications(
              modifications.schemaPatch,
              'schema'
            );
          }

          if (modifications.uiSchemaPatch) {
            success = await applySafeModifications(
              modifications.uiSchemaPatch,
              'uiSchema'
            ) && success;
          }

          if (!success) {
            setMessages(prev => [
              ...prev,
              {
                role: 'assistant',
                content: "⚠️ Certaines modifications n'ont pas pu être appliquées en raison d'erreurs de validation"
              }
            ]);
          }
        }
      } catch (error) {
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            content: "❌ Erreur lors de la communication avec l'assistant"
          }
        ]);
      } finally {
        setIsLoading(false);
      }
    };

    useEffect(() => {
      if (!initialized.current) {
        setMessages([{
          role: 'assistant',
          content: "Salut ! Comment ça va aujourd'hui ? Prêt·e à reprendre le questionnaire ? Je t'écoute !"
        }]);
        initialized.current = true;
      }
    }, []);


    return (
      <div className="flex flex-col h-full min-h-0">
        {/* En-tête animé + titre */}
        <div className="flex items-center gap-2 mb-4 shrink-0">
          <div className="w-10 h-10"><Lottie animationData={waveAnimation} loop /></div>
          <h2 className="text-lg font-semibold text-black dark:text-gray-100">
            GerminaBot ✨
          </h2>
        </div>
  
        {/* Messages, scrollable */}
        <div className="flex-1 overflow-y-auto space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`p-3 rounded-lg text-black ${
              msg.role === 'user' ? 'bg-blue-100 ml-6' : 'bg-gray-100 mr-6'
            }`}>
              <strong>
                {msg.role === 'user' ? 'Vous' : 'GerminaBot'} 
                {msg.role === 'assistant' && <span className="ml-1">✨</span>}
                :
              </strong>
              <p className="mt-1 whitespace-pre-wrap">{msg.content}</p>
            </div>
          ))}
        </div>
  
        {/* Input, fixe en bas */}
        <form onSubmit={handleSubmit} className="mt-2 flex items-center gap-2 shrink-0">
          {/* Wrapper pour permettre au champ de se contracter proprement */}
          <div className="flex-1 min-w-0">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Votre message…"
              className="w-full p-2 border rounded block"
              disabled={isLoading}
            />
          </div>
          <button
            type="submit"
            className="flex-shrink-0 px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
            disabled={isLoading}
          >
            {isLoading ? 'Envoi…' : 'Envoyer'}
          </button>
        </form>
      </div>
    );
  }