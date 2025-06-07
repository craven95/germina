# Germina

## Description

Germina est une plateforme tout‐en‐un permettant de créer, déployer et analyser des questionnaires.
- **Frontend** : React / Next.js (déployé sur Vercel)
- **Backend “builder”** : FastAPI (déployé sur Google Cloud Run), génère des images Docker via Cloud Build & Artifact Registry.
- **Base de données & Auth** : Supabase.

## Organisation des dossiers

- `/interface/` → l’interface Next.js
- `/builder/`   → le service FastAPI pour builder / lister / supprimer des images Docker
- `.github/workflows/` → CI/CD pour déployer sur Vercel et Cloud Run

## Liens rapides

- **Interface (Next.js)**
  - [README détaillé](interface/README.md)

- **API Builder (FastAPI)**
  - [README détaillé](builder/README.md)

## Démo en ligne

- **Interface (Next.js)** :
  https://germina-cravens-projects-8d4cfd75.vercel.app

## Support

Pour toute question ou problème, contactez :
germina.general@gmail.com

## Licence

Ce projet est sous licence **MIT**. Voir le fichier [LICENSE](LICENSE) pour le texte complet.

---
