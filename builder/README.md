# Germina – API Builder (FastAPI)

Cette partie contient le backend “builder” (FastAPI) qui gère la création, la liste et la suppression d’images Docker pour chaque questionnaire. Elle est déployée sur **Google Cloud Run** et se connecte à **Supabase** pour l’authentification et la gestion des quotas.

---

## Table des matières

1. [Vue d’ensemble](#vue-densemble)
2. [Prérequis](#prérequis)
3. [Installation & exécution en local](#installation--exécution-en-local)
4. [Création du docker](#création-du-docker)
5. [Structure du dossier](#structure-du-dossier)
6. [CI/CD (GitHub Actions → Cloud Run)](#déploiement-automatique-github-actions--gcp-cloud-run)
7. [Licence](#licence)

---

## Vue d’ensemble

Le dossier **`builder/`** contient un service **FastAPI** qui :

- Vérifie le JWT Supabase pour chaque requête.
- Implemente un compteur de quotas (`api_usage`) dans Supabase pour limiter l’usage.
- Expose 5 endpoints principaux :
  1. **`POST /build/{questionnaire_id}`**
     - Lance, en tâche de fond, la création d’une image Docker via **Cloud Build**.
     - Pousse l’image dans **Artifact Registry** (`germina-backend/builder`).
  2. **`GET /build_status?questionnaire_id=<id>`**
     - Liste les builds (images Docker) déjà créées pour ce questionnaire.
  3. **`GET /list?questionnaire_id=<id>`**
     - Renvoie la liste des images (méta : `name`, `tag`, `updated_at`).
  4. **`DELETE /delete_image?questionnaire_id=<id>`**
     - Supprime un package (toutes versions/tous tags) dans Artifact Registry.
  5. **`POST /generate_deploy_script`**
     - Fournit un script shell (ou `.ps1`) pour déployer une image Docker sur un hôte Linux/Mac/Windows.

- Utilise Supabase pour :
  - Authentifier l’utilisateur (`get_current_user`).
  - Vérifier/incrémenter son quota (`api_usage.count`).
  - Mettre à jour la table `questionnaires` (statut `pending`, `ready`, etc.).

- Est conçu pour être conteneurisé (`Dockerfile`) et déployé sur **Google Cloud Run**.

---

## Prérequis

1. **Python 3.10+**
2. **pip** pour gérer les dépendances
3. **Google Cloud SDK** (pour déploiement manuel)
4. Un compte **Supabase** (URL/clé)
5. Un projet **GCP** avec :
   - **Cloud Build** activé
   - **Artifact Registry** (repo `germina-backend/builder`)
   - **IAM** : Service Account ayant `"Cloud Run Admin"`, `"Cloud Build Editor"`, `"Artifact Registry Writer"`, etc.

---

## Installation & exécution en local

1. Clonez le repo principal si ce n’est pas déjà fait, puis placez‐vous dans le dossier `builder/` :
   ```bash
   cd builder

2. Installation des dépendances
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

3. Complétez avec vos variables d'environnements
SUPABASE_URL=https://<votre-supabase-url>
SUPABASE_KEY=<votre-supabase-service-key>
GCP_PROJECT=<votre-gcp-project-id>
GCR_LOCATION=europe-west1
GCR_REPOSITORY=germina-backend
GOOGLE_APPLICATION_CREDENTIALS=/<chemin-absolu>/sa-key.json

4. Tester en local
uvicorn main:app --reload --host 0.0.0.0 --port 8000

---

## Création du docker

Le fichier Dockerfile à la racine de builder/ permet de :

    Copier le code Python (FastAPI) dans /app.

    Installer les dépendances via requirements.txt.

    Exposer le port 8000 et démarrer Uvicorn.

Pour construire l’image localement avant de la pousser sur GCP :
# Depuis le dossier builder/
docker build -t germina-backend-builder:local .

docker run -it --rm \
  -e SUPABASE_URL=https://<votre-supabase-url> \
  -e SUPABASE_KEY=<votre-supabase-service-key> \
  -e GCP_PROJECT=<votre-gcp-project-id> \
  -e GCR_LOCATION=europe-west1 \
  -e GCR_REPOSITORY=germina-backend \
  -e GOOGLE_APPLICATION_CREDENTIALS="/run/secrets/sa-key.json" \
  -p 8000:8000 \
  germina-backend-builder:local

---

## Structure du dossier

builder/
├── Dockerfile               # Image FastAPI principale
├── gcp.py                   # Fonctions utilitaires pour GCP (Cloud Build / Artifact Registry)
├── main.py                  # Point d’entrée FastAPI (routes, CORS, etc.)
├── requirements.txt         # Dépendances Python pour la FastAPI
├── users.py                 # get_current_user(), gestion du quota dans Supabase
├── survey_template/         # Code du micro‐service qui sera embarqué dans l’image Docker générée
│   ├── app.py               # Application Flask ou équivalent pour le template de survey
│   ├── Dockerfile           # Dockerfile de l’image “survey” embarquée
│   ├── requirements.txt     # Dépendances Python pour le service de template
│   ├── schema.json          # JSON Schema exemple pour tester
│   ├── ui_schema.json       # UI Schema JSON exemple pour tester
│   ├── static/              # Fichiers statiques pour le survey
│   │   ├── form-entry.js
│   │   └── js/              # (1)
│   │       └── form.bundle.js
│   └── templates/           # Templates HTML pour le survey
│       └── form.html
└── README.md                # Ce fichier

(1) to create js bundle for survey render, run following command :
npx esbuild static/form-entry.js   --bundle   --outfile=static/js/form.bundle.js   --minify   --target=es2019   --format=esm   --global-name=SurveyForm

---

## Déploiement automatique (GitHub Actions → GCP Cloud run)

Dans .github/workflows/deploy-backend_gcp.yml, le workflow est déclenché à chaque push sur main dans le dossier builder/.

---

## LICENCE

Ce projet est sous licence **MIT**. Voir le fichier [LICENSE](../LICENSE) pour le texte complet.

---
