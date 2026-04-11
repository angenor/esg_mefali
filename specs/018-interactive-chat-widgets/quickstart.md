# Quickstart — Interactive Chat Widgets

**Feature**: 018-interactive-chat-widgets
**Public** : développeurs backend + frontend + QA

## Objectif

Rendre les questions du LLM interactives via des widgets QCU/QCM cliquables,
avec justification optionnelle, similaire à l'extension Claude Code VS Code.

## Prérequis

- Backend ESG Mefali fonctionnel (venv activé, `uvicorn app.main:app --reload`)
- Frontend Nuxt 4 démarré (`npm run dev` dans `frontend/`)
- PostgreSQL 16 + pgvector opérationnels
- Base de données à jour : `alembic upgrade head` (inclut la migration
  `018_interactive_questions`)
- Variables d'environnement existantes valides (OPENROUTER_API_KEY, DB_URL)

## Parcours développeur : bout-en-bout

### 1. Appliquer la migration

```bash
cd backend
source venv/bin/activate
alembic upgrade head
# Vérifie la nouvelle table
psql $DATABASE_URL -c "\d interactive_questions"
```

### 2. Lancer les tests backend

```bash
# Tests unitaires du tool et des schémas
pytest tests/unit/test_ask_interactive_question_tool.py -v
pytest tests/unit/test_interactive_question_schemas.py -v

# Tests d'intégration API
pytest tests/integration/test_interactive_question_api.py -v
pytest tests/integration/test_chat_interactive_sse.py -v

# Suite complète (doit rester verte : ≥ 80% coverage)
pytest --cov=app --cov-report=term-missing
```

### 3. Lancer les tests frontend

```bash
cd frontend
npm run test:unit -- interactiveQuestion
npm run test:e2e -- interactive-widgets
```

## Parcours utilisateur : scénario démo

### Étape 1 — Connexion et nouveau chat

1. Ouvrir <http://localhost:3000>
2. Se connecter avec un compte PME existant
3. Démarrer une nouvelle conversation
4. Envoyer : « Je veux faire une évaluation ESG de mon entreprise »

### Étape 2 — Widget QCU (single choice)

**Attendu** : Le LLM ouvre le module ESG et pose une question sous forme de
widget cliquable :

```
Quel est le secteur principal de votre activité ?

[🌾 Agriculture]  [⚡ Énergie]  [♻️ Recyclage]  [🚛 Transport]  [🏭 Industrie]
```

- Un clic sur `🌾 Agriculture` → le bouton se surligne, le widget est
  soumis, le chat affiche la réponse en message utilisateur.
- L'input texte en bas est désactivé pendant l'attente (seul le bouton
  « Répondre autrement » reste cliquable).

### Étape 3 — Widget QCU + justification

**Attendu** : Une question demande un choix et une justification fun :

```
Comment gérez-vous les déchets dans votre entreprise ?

[❌ Aucune politique]  [♻️ Tri partiel]  [✅ Politique formalisée]

💬 Raconte-nous comment ça se passe au quotidien ! 🌍
[Zone de texte, 400 caractères max, compteur visible]
```

- Choisir `♻️ Tri partiel`
- Remplir : « On récupère les cartons et les bouteilles en plastique pour
  un voisin qui les revend. »
- Cliquer sur `Envoyer`
- Le message utilisateur affiche le choix + la justification en italique.

### Étape 4 — Widget QCM (multiple choice)

**Attendu** : Sur une question multi-sélection :

```
Quels objectifs de développement durable (ODD) vous concernent le plus ?
(Sélectionnez 1 à 4 options)

[☐ 🏭 ODD 9 — Innovation]
[☐ 🌍 ODD 13 — Climat]
[☐ 💸 ODD 10 — Inclusion financière]
[☐ ♻️ ODD 12 — Production responsable]
[☐ 🤝 ODD 17 — Partenariats]

[Envoyer la sélection]
```

- Cocher 3 cases
- Cliquer `Envoyer la sélection`
- Le message utilisateur liste les 3 ODD choisis.

### Étape 5 — Fallback « Répondre autrement »

**Attendu** : Sur n'importe quelle question avec widget, l'utilisateur peut
cliquer sur un bouton discret « Répondre autrement » (sous le widget).

- Le widget se grise (état `abandoned`)
- L'input texte est ré-activé
- L'utilisateur peut saisir un texte libre
- Le tour suivant du LLM voit la réponse textuelle et poursuit le flux.

### Étape 6 — Réouverture d'une conversation

**Attendu** : Si l'utilisateur quitte puis revient :

- L'historique charge les widgets déjà répondus via
  `GET /api/chat/conversations/{id}/interactive-questions`
- Chaque widget historique est affiché en mode « résumé answered » :
  options surlignées, justification en italique, non cliquable.
- Si une question était encore `pending`, le mode « expiré » s'affiche
  (grisé avec mention « Cette question n'est plus active »).

## Validation du succès

Les critères de succès de la spec doivent être observables :

- **SC-001** : ≥ 70% des questions éligibles passent par un widget (métrique
  visible via `module` + `question_type` en base).
- **SC-002** : temps de réponse utilisateur réduit (mesurable via
  `answered_at - created_at`).
- **SC-003** : justifications saisies ≥ 40% quand requises.
- **SC-004** : 0% de régression sur le flux texte classique.
- **SC-005** : rendu stable sur mobile (testé via Playwright mobile viewport).
- **SC-006** : hydratation historique fidèle (widgets re-rendus à l'identique).
- **SC-007** : aucun dépassement 400 caractères justification (validé backend).

## Dépannage

| Symptôme | Cause probable | Action |
|----------|----------------|--------|
| Le LLM répond en texte libre au lieu d'un widget | Tool `ask_interactive_question` non enregistré dans le nœud | Vérifier `backend/app/graph/tools/__init__.py` et `build_graph` |
| Event SSE `interactive_question` absent du flux | Marker `<!--SSE:-->` mal formé dans le retour du tool | Vérifier le formatage JSON du marker, tester via `curl` |
| Le widget s'affiche mais ne réagit pas au clic | Handler SSE frontend manquant | Vérifier `useChat.ts` case `interactive_question` |
| Réponse 409 `QUESTION_NOT_PENDING` | Deux questions concurrentes | Vérifier l'invariant côté tool (marquage `expired` auto) |
| Justification refusée > 400 car | Limite atteinte | Le compteur frontend doit empêcher la saisie au-delà |

## Ressources

- Spec : [spec.md](./spec.md)
- Recherche : [research.md](./research.md)
- Data model : [data-model.md](./data-model.md)
- Contrats : [contracts/](./contracts/)
