# Audit Rétrospectif — Spec 002 : Interface de Chat Conversationnel avec Rendu Visuel Enrichi

**Date d'audit** : 2026-04-16
**Auditeur** : Angenor (Project Lead) + assistant Amelia
**Spec** : [specs/002-chat-rich-visuals/](../../../specs/002-chat-rich-visuals/)
**Méthode** : rétrospective post-hoc
**Statut rétro** : ✅ Complet

---

## 1. Portée de la spec

Interface chat complète avec 6 types de Rich Blocks (chart, mermaid, table, gauge, progress, timeline), mode guide, responsive mobile, gestion conversations.

| Dimension | Livré |
|-----------|-------|
| Tâches | 40 / 40 `[X]` (100 %) |
| User Stories | 8 (US1-US3 P1, US4-US7 P2, US8 P3) |
| Phases | 11 |
| Rich Blocks types | 6 (+ 2 utilitaires BlockError, BlockPlaceholder) |
| Composants nouveaux | 11 (richblocks/ + MessageParser + WelcomeMessage + FullscreenModal) |
| Constitution gates | 7 / 7 passés |

---

## 2. Ce qui a bien fonctionné

### 2.1 Découpage MVP → enrichissements clair

- US1 (P1) = MVP conversationnel, livré en premier
- US2/US3 parallélisables (Chart.js ⟂ Mermaid)
- US4 (4 blocs) tous parallélisables
- Strategy d'implémentation documentée en §"Implementation Strategy"

### 2.2 Réutilisation existant + enrichissement

- 60 % du travail frontend (vs backend) → tire parti de la foundation 001
- `ChatMessage.vue`, `ChatInput.vue`, `ConversationList.vue` enrichis plutôt que réécrits
- Backend ne touche que `prompts/system.py` + génération titre

### 2.3 Regroupement composants richblocks/

- Tous les blocs dans `components/richblocks/` → cohésion haute
- `BlockError` + `BlockPlaceholder` partagés entre les 6 types → DRY
- Pattern réutilisé ensuite (spec 018 a suivi la même convention)

### 2.4 TDD partiel respecté

- Tests Vitest pour chaque bloc (T017, T019, T021-T024) écrits avant implémentation
- Couverture unitaire correcte des 6 types

---

## 3. Ce qui a posé problème (révélé a posteriori)

### 3.1 🔴 FR-013 Rate limiting jamais implémenté

- Spec exigeait **"30 messages/minute par utilisateur"** (FR-013)
- Tâche T030 mentionnait "gestion erreur 429 rate limit avec message francais" côté frontend
- **Code actuel** : `grep -n "rate|429|throttl"` dans `backend/app/api/chat.py` → **aucun résultat**
- Rate limiting absent côté backend. Le frontend a une gestion d'erreur 429 pour un endpoint qui ne la retourne jamais.
- **Cause racine** : aucune tâche backend n'implémente FR-013 — incohérence spec vs tasks non détectée à la validation
- **Leçon** : la checklist `requirements.md` a déclaré "Requirements are testable and unambiguous [x]" sans vérifier que chaque FR avait une tâche correspondante

### 3.2 🟠 TimelineBlock schema rigide → refactor en spec 013

- Spec 002 T028 a livré un `TimelineBlock` qui exigeait strictement `{events: [{date, title, status, description?}]}`
- LLM générait régulièrement des variantes : `phases`, `items`, `steps` au lieu de `events` ; `period`/`name`/`state`/`details` au lieu de `date`/`title`/`status`/`description`
- Spec 013 a dû créer `frontend/app/utils/normalizeTimeline.ts` pour tolérer 4 clés racines + 5 aliases de champs
- Prompts backend `action_plan.py`, `carbon.py`, `financing.py` ont dû être standardisés sur le format canonique
- **Cause racine** : schema défini sans observation empirique des variantes LLM + pas de test de résilience aux variantes
- **Leçon** : pour les blocs LLM-générés, prévoir dès la conception un normalizer tolérant, pas un parser strict

### 3.3 🟠 Les 6 types de Rich Blocks ne sont pas extensibles

- Spec 018 (Interactive Widgets) a voulu introduire `interactive_question` comme nouveau type de bloc
- Design choisi : **marqueur SSE séparé** `<!--SSE:{"__sse_interactive_question__":true,...}-->` + table satellite `interactive_questions` + 5 composants Vue dédiés
- **Pas** d'intégration dans le pattern Rich Blocks existant → deux systèmes de rendu parallèles dans `ChatMessage.vue`
- **Cause racine** : `MessageParser.vue` code en dur les 6 types, pas de registre extensible
- **Leçon** : un registre de blocs (`registerBlockType(name, component, parser)`) aurait évité la duplication architecturale

### 3.4 🟡 T038 E2E : un seul `.spec.ts`, fragile

- T038 listait 10 assertions dans un seul Playwright (login → chat → nouvelle conv → streaming → graphique → agrandir → télécharger → historique → recherche → mobile drawer)
- **Constat actuel** : fichier `frontend/tests/e2e/chat.spec.ts` **absent** du repo (seuls 8-1-parcours-fatou et 8-2-parcours-moussa de spec 019 existent)
- Soit T038 n'a jamais été livré, soit il a été supprimé/renommé lors d'un refactor non tracé
- **Leçon** : une tâche "E2E flux complet en 1 test" est un anti-pattern — tests fragiles, debugging pénible, couverture illusoire

### 3.5 🟡 Streaming "bloque l'envoi tant qu'une réponse est en cours" (FR-014)

- FR-014 : "Le systeme DOIT bloquer l'envoi d'un nouveau message tant qu'une reponse est en cours de streaming"
- Design rigide : si le streaming coince (réseau, LLM lent), l'utilisateur ne peut plus rien envoyer
- Edge case documenté dans spec : "Réseau interrompu pendant le streaming → message partiel conservé + message d'erreur"
- Mais pas de mécanisme de **timeout côté frontend** pour débloquer si le streaming ne se termine jamais
- Spec 015 a dû ajouter `request_timeout=60` côté backend LLM → **traitement du symptôme, pas de la cause**
- **Leçon** : les flags "en cours" doivent avoir un garde-fou temporel + bouton "annuler" côté UX

### 3.6 🟡 Génération de titre (T015) : appel LLM séparé

- Design : après le premier échange, un second appel LLM génère le titre ("Résume en 5 mots max")
- **Coût** : 2× appels LLM pour la première réponse (réponse principale + titre)
- Non mesuré dans les success criteria (SC-001 parle de "premier token < 5s" mais pas du coût)
- **Leçon** : pour les fonctionnalités "auto", mesurer le coût cumulé (tokens, latence, $) et documenter le trade-off

---

## 4. Leçons transversales

1. **Valider chaque FR a au moins une tâche dédiée** — bugfinder statique entre `spec.md` FR-xxx et `tasks.md` Txxx. FR-013 aurait été détecté.
2. **Normaliser les schemas LLM-générés dès la conception** — accepter les variantes est la norme, pas l'exception.
3. **Concevoir des systèmes extensibles par registre** — `MessageParser` hardcoded a coûté 2 architectures parallèles à la spec 018.
4. **Rompre les E2E monolithiques** — un test par scénario user-visible, pas un test "couvrant tout".
5. **Mesurer les coûts cachés** — génération de titre, retry, refresh token... tous ces "petits" appels s'additionnent.

---

## 5. Actions résiduelles retenues

| # | Action | Priorité | Source |
|---|--------|----------|--------|
| 1 | **Implémenter FR-013 rate limiting** (30 msg/min) côté backend — SlowAPI ou middleware custom | P1 | §3.1 |
| 2 | Ajouter timeout frontend sur `isStreaming` + bouton "Annuler" | P2 | §3.5 |
| 3 | Refactorer `MessageParser` vers un registre extensible de blocs | P3 | §3.3 |
| 4 | Découper `chat.spec.ts` en tests E2E par scénario (ou vérifier s'il a été absorbé ailleurs) | P3 | §3.4 |

**Actions déjà en place** :
- ✅ `normalizeTimeline` + prompts canoniques (spec 013)
- ✅ Timeout backend LLM 60s (spec 015)
- ✅ Système interactive_questions (spec 018, même si architecturalement parallèle)

---

## 6. Verdict

**Spec 002 livrée à 100 % des tâches, mais avec 2 dettes structurelles (rate limiting absent, schema Timeline rigide) et 1 dette architecturale (blocs non extensibles).**

La valeur livrée est haute (interface chat riche, 6 types de blocs fonctionnels), mais FR-013 absent est une **vulnérabilité d'abuse** à fermer rapidement. Le refactor en registre extensible peut attendre si aucune nouvelle feature ne prévoit d'ajouter un 7ᵉ type de bloc.
