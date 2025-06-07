## Description

Merci pour votre contribution !
Veuillez décrire en quelques lignes la modification apportée :
- Quel problème corrigez-vous ou quelle fonctionnalité ajoutez-vous ?
- Pourquoi ce changement est‐il nécessaire ?

## Type de changement

- [ ] Nouvel API / nouvelle fonctionnalité (« feat »)
- [ ] Correction de bug (« fix »)
- [ ] Mise à jour de la documentation (« docs »)
- [ ] Amélioration du style / refactor (« refactor », « style »)
- [ ] Tests ajoutés ou mis à jour (« test »)
- [ ] Autre (« chore »)

## Comment tester/manuellement ?

Décrivez la ou les étapes pour vérifier que tout fonctionne correctement :

1. Cloner le dépôt et basculer sur la branche de la PR :
   git checkout <votre-branche>

2.  Installer les dépendances et lancer l’application :

    - Backend
        cd builder
        python3 -m venv .venv && source .venv/bin/activate
        pip install -r requirements.txt
        uvicorn main:app --reload

    - Frontend
        cd interface
        npm ci
        npm run dev

## Reproduire le scénario lié à votre modification (page à charger, endpoint à appeler, etc.).

Checklist avant PR

Mon code suit les conventions du projet (lint / style).

J’ai ajouté/supprimé/ajusté les tests au besoin.

J’ai mis à jour la documentation (README, exemples, etc.) si nécessaire.

Je n’ai pas laissé de données sensibles ou de clés d’API dans les commits.

Mon commit contient un message clair et descriptif.

## Merci pour votre contribution ! Un·e mainteneur·se passera en revue votre PR dès que possible. 😊
