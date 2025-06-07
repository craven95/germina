import { Mistral } from '@mistralai/mistralai';
import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  const { messages } = await req.json();

  const client = new Mistral({
    apiKey: process.env.MISTRAL_API_KEY ?? '',
  });

  const agentId = process.env.MISTRAL_AGENT_ID;

  try {
    const result = await client.agents.complete({
      agentId: agentId || 'mistral-agent',
      messages: [
        {
          role: 'system',
          content:
            'Vous êtes un expert en création de questionnaires. Répondez toujours en JSON valide.',
        },
        ...messages,
      ],
    });

    console.log('Réponse de Mistral:', result);

    const raw = result.choices?.[0]?.message.content;
    if (!raw) {
      throw new Error('Aucune réponse de l’agent');
    }
    const cleaned = (typeof raw === 'string' ? raw : JSON.stringify(raw))
    .replace(/```json|```/g, '')
    .trim();

    console.log('Réponse brute nettoyée:', cleaned);


    let parsed;
    try {
      parsed = JSON.parse(cleaned);
    } catch (e) {
      console.error('JSON invalide reçu de Mistral:', cleaned);
      return NextResponse.json(
        { error: 'Réponse JSON mal formée' },
        { status: 502 }
      );
    }

    console.log('Réponse JSON analysée:', parsed);

    return NextResponse.json(parsed);
  } catch (err: any) {
    console.error('Erreur Mistral SDK:', err);
    return NextResponse.json(
      { error: 'Erreur de communication avec Mistral' },
      { status: 500 }
    );
  }
}
