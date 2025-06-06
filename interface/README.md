# Germina – Interface (Next.js)

Cette partie contient le front‐end de Germina, basé sur Next.js et React, hébergé sur Vercel. Il permet à l’utilisateur de créer et éditer des questionnaires avec l’aide d’un chat assistant Mistral AI, de stocker les schémas dans Supabase, et de lancer le déploiement qui génère une image Docker personnalisée.

---

## Table des matières

1. [Vue d’ensemble](#vue-densemble)  
2. [Prérequis](#prérequis)  
3. [Installation & exécution en local](#installation--exécution-en-local)  
4. [Variables d’environnement](#variables-denvironnement)  
5. [Déploiement automatique (GitHub Actions → Vercel)](#déploiement-automatique-github-actions--vercel)
6. [Structure du dossier](#structure-du-dossier)  
7. [Foire aux questions (FAQ)](#foire-aux-questions-faq)  
8. [Licence](#licence)  

---

## Vue d’ensemble

La partie **Interface** (dossier `interface/`) est un projet Next.js qui permet à l’utilisateur :
- De créer et éditer des questionnaires (via Supabase).
- D’interagir avec l’API “builder” (FastAPI) pour générer, lister et supprimer les images Docker.  
- D’afficher un chat assistant (MISTRAL AI), un aperçu du questionnaire, etc.

En production, cette application est déployée sur Vercel (ex. : https://\<votre-projet-vercel\>.vercel.app).

---

## Prérequis

Avant de lancer localement l’interface, assurez‐vous d’avoir :

1. **Node.js** (v18 LTS ou supérieure)  
2. **npm** (ou `yarn` / `pnpm`)  
3. Un compte **Supabase** valide (URL et clés d’API).  
4. L’URL de votre API “builder” (FastAPI) en local (`http://localhost:8000`) ou en production (ex. lien si déployée sur le cloud).

---

## Installation & exécution en local

1. Ouvrez un terminal et placez‐vous dans le dossier `interface/` :  
   cd interface

2. Installez les dépendances :
  npm ci

3. Créez un fichier .env.local avec les variables suivantes :
  NEXT_PUBLIC_SUPABASE_URL=https://<votre-supabase-url>
  NEXT_PUBLIC_SUPABASE_ANON_KEY=<votre-supabase-anon-key>
  NEXT_PUBLIC_BUILDER_API_URL=http://localhost:8000   # ou votre API en production

4. Lancez l’application en mode développement :
  npm run dev

---

## Variables d’environnement

Ce projet lit les variables suivantes depuis votre environnement (.env.local ou Vercel) :

    NEXT_PUBLIC_SUPABASE_URL
    L’URL de votre instance Supabase, ex. https://xyz.supabase.co.

    NEXT_PUBLIC_SUPABASE_ANON_KEY
    La clé anonyme (public) pour interroger Supabase en lecture/écriture.

    NEXT_PUBLIC_BUILDER_API_URL
    L’URL de base de votre API FastAPI “builder.” En local, c’est souvent http://localhost:8000.
    En production, vous mettez la valeur fournie par Cloud Run (ex. https://germina-backend-abcde.a.run.app).

    Optionnel :

const defaultUrl = process.env.VERCEL_URL
  ? `https://${process.env.VERCEL_URL}`
  : 'http://localhost:3000';

Ici, VERCEL_URL est injecté par Vercel en production. On n’en a pas besoin en local.

---

## Déploiement automatique (GitHub Actions → Vercel)

Dans .github/workflows/deploy-interface.yml, le workflow est déclenché à chaque push sur main dans le dossier interface/.

---

## Structure du dossier

interface/
├── README.md
├── app/                       # App Router (Next.js 13+) ou pages/ si Page Router
│   ├── actions.ts
│   ├── api/
│   │   └── chat/
│   │       └── route.ts       # Route POST /api/chat → appelle Mistral AI
│   ├── auth/
│   │   └── callback/
│   │       └── route.ts
│   ├── (auth-pages)/
│   │   ├── forgot-password/
│   │   │   └── page.tsx
│   │   ├── ...
│   ├── protected/             # Pages accessibles après authentification
│   │   ├── deploiement/
│   │   │   ├── [id]/
│   │   │   │   └── page.tsx
│   │   │   ├── loading.tsx    # Page de chargement
│   │   │   └── page.tsx
│   │   ├── home/
│   │   │   ├── ...
│   └── middleware.ts
├── components/                # Composants React réutilisables
│   ├── animations/
│   │   └── cat_waiting.json
│   ├── chatassistant.tsx
│   ├── clientlayout.tsx
│   ├── ...
│   └── ui/
│       ├── badge.tsx
│       ├── ...
├── components.json            # Lockfile pour composants (par ex. Storybook)
├── lib/                       # Fonctions utilitaires, clients Supabase, etc.
├── middleware.ts              # Middleware Next.js (auth, redirections, etc.)
├── next-env.d.ts
├── next.config.ts             # Configuration Next.js (routes, image domains, etc.)
├── node_modules/
├── package-lock.json
├── package.json               # Dépendances, scripts, metadonnées
├── postcss.config.js          # Configuration PostCSS / Tailwind
├── tailwind.config.ts         # Configuration Tailwind CSS
├── tsconfig.json              # TypeScript config
└── utils/                     # Fonctions utilitaires côté client

---

## FAQ 

(à compléter !)

---

## LICENCE 

Ce projet est sous licence **MIT**. Voir le fichier [LICENSE](../LICENSE) pour le texte complet.

---