# CONTRIBUTING.md

Merci de votre intérêt pour contribuer à **Germina** ! 😊 Votre aide est la bienvenue, que ce soit pour corriger un bug, ajouter une nouvelle fonctionnalité, améliorer la documentation ou proposer des idées. Ce guide présente les étapes à suivre pour cloner, configurer et proposer vos changements.

---

## 1. Avant de commencer

1. **Lisez la licence**  
   Ce projet est sous licence [MIT](../LICENSE). En contribuant, vous acceptez les termes de cette licence.

2. **Évitez de committer des données sensibles**  
   - Ne publiez jamais vos clés API, secrets ou mots de passe.  
   - Vérifiez que votre code ne contient aucune information confidentielle (ex. `.env`).  

3. **Choisissez un sujet**  
   - Parcourez les [Issues](https://github.com/votre-utilisateur/germina/issues) pour voir si quelqu’un a déjà signalé un problème ou suggéré une amélioration.  
   - Si votre idée n’est pas encore documentée, ouvrez d’abord une **issue** pour en discuter avant de commencer à coder.

---

## 2. Bonnes pratiques Git

1. **Fork & Clone**  
   # Forkez le dépôt sur GitHub via l’interface.
   git clone https://github.com/votre-utilisateur/germina.git
   cd germina


2. **Créer un remote pour le dépôt officiel**

git remote add upstream https://github.com/original-owner/germina.git
git fetch upstream

3. **Travailler sur une branche dédiée**

    Ne travaillez jamais directement sur main.

    Créez une branche descriptive pour votre fonctionnalité ou correction de bug :

    git checkout -b feature/ajout-nouvelle-question
    # ou
    git checkout -b bugfix/correction-validation-schema

4. **Commits atomiques et messages clairs**

    Un commit = une seule idée (petite fonctionnalité, correction d’un bug, amélioration d’une doc).

    Format recommandé pour le message de commit :

    type(scope): description courte

    Description plus détaillée si nécessaire.

    type ∈ {feat, fix, docs, style, refactor, test, chore}

    scope (facultatif) indique la partie du projet par ex. (frontend), (backend), (ci).

    Exemple :

        feat(frontend): ajouter le champ "age" dans le schéma de questionnaire

        Le ChatAssistant prend maintenant en charge l’ajout automatique d’une question "Quel est votre âge ?" de type "number".

5. **Mettre à jour depuis upstream/main régulièrement**

Avant de créer une Pull Request, assurez-vous que votre branche est à jour :

    git fetch upstream
    git checkout main
    git pull upstream main
    git checkout feature/ma-branche
    git rebase main

---

## 3. Installer et configurer le projet en local

Pour l'installation vous pouvez suivre : 

- **Interface (Next.js)**  
  - [README détaillé](interface/README.md)

- **API Builder (FastAPI)**  
  - [README détaillé](builder/README.md)

---

## 4. Processus de Pull Request

Créez une Pull Request (PR) vers la branche main du dépôt officiel

    Votre branche doit être à jour (git rebase main ou git merge main).

    Ne forcez jamais git push --force sur la branche main.

Titre et description de la PR

    Choisissez un titre explicite, par ex. feat: add statistics for local deployements.

    Dans la description, détaillez :

        Quel problème vous résolvez ou quelle fonctionnalité vous ajoutez.

        Comment tester/localiser les changements.

        Screenshots ou extraits de code si pertinente.

Vérifications avant la PR

    Lint sans erreur :

        Backend : flake8 . ou black --check .

        Frontend : npm run lint

    Tests : assurez-vous que toute la suite (backend + frontend) passe.

    Documentez : si vous ajoutez une nouvelle fonctionnalité, mettez à jour les README appropriés (backend ou interface).

Révisions & feedback

    Les mainteneurs pourront commenter votre PR et demander des modifications si besoin.

Merge

    Une fois validée, votre PR sera fusionnée par un mainteneur.

    Le déploiement CI/CD s’exécutera automatiquement (tests, build, déploiement).

---

## 5. Style guide & bonnes pratiques
5.1 Code Python (Backend)

    Respectez PEP 8 (utilisez flake8, black, isort).

    Annotations de type (mypy compatible si possible).

    Docstrings pour les fonctions publiques (ex. endpoint FastAPI).

5.2 Code TypeScript / React (Frontend)

    Pas de any si possible (privilégiez un typage strict).

    Composants fonctionnels avec hooks React.

5.3 Commit Messages

    Courts, descriptifs, en anglais pour etre cohérent avec l’ensemble du project :D

    Format recommandé :

    <type>(<scope>): <courte description>

    avec type ∈ {feat, fix, docs, style, refactor, test, chore}

    Exemples :

        fix(backend): good path for docker envs

        feat(frontend): add new delete icon

---

## 6. Reporting de bugs & suggestions d’amélioration

    Ouvrir une issue

        Utilisez le template “Bug report” ou “Feature request” dans GitHub.

        Décrivez le plus précisément possible (étapes pour reproduire, captures d’écran, logs d’erreur).

    Participer aux discussions

        Donnez votre avis sur les issues existantes.

        Proposez des idées, votez pour les fonctionnalités prioritaires !

---

## 7 . Contact

Si vous avez des questions, n’hésitez pas à ouvrir une issue ou à nous contacter via germina.general@gmail.com.

Merci encore pour votre contribution ! 🎉