# Audit Rétrospectif — Spec 003 : Profilage Intelligent et Mémoire Contextuelle

**Date d'audit** : 2026-04-16
**Auditeur** : Angenor (Project Lead) + assistant Amelia
**Spec** : [specs/003-company-profiling-memory/](../../../specs/003-company-profiling-memory/)
**Méthode** : rétrospective post-hoc
**Statut rétro** : ✅ Complet

---

## 1. Portée de la spec

Extraction automatique du profil entreprise via conversation + personnalisation contextuelle des réponses + mémoire inter-sessions via résumés.

| Dimension | Livré |
|-----------|-------|
| Tâches | 57 / 57 `[x]` (100 %) |
| User Stories | 5 (US1-US2 P1, US3-US4 P2, US5 P3) |
| Phases | 8 |
| Nouveau modèle | `CompanyProfile` (20 colonnes, SectorEnum de 11 valeurs) |
| Nouveau chain | `extraction.py`, `summarization.py` |
| Nouveau node | `profiling_node`, `router_node` (refactor chat_node monolithique de spec 001) |
| Clarifications | 2 (pondération completion + timing summary) |

---

## 2. Ce qui a bien fonctionné

### 2.1 Pondération completion bien pensée (clarification Q1)

- Deux pourcentages séparés : identité+localisation d'un côté, ESG de l'autre
- Seul le premier déclenche le seuil 70% (FR-008) → évite que les questions de profilage s'arrêtent quand l'ESG est vide
- **Design toujours en place**, `CompanyProfile` model n'a pas bougé depuis

### 2.2 Résumé à la création de nouveau thread (clarification Q2)

- `_summarize_previous_conversation()` dans `chat.py:373` : génère le résumé du thread précédent quand un nouveau est créé
- Stocké dans `conversation.summary: Mapped[str | None]`
- Chargement des 3 derniers via `_load_recent_summaries()` dans `context_memory` de l'état
- **Design toujours en place**, simple et efficace

### 2.3 Refactor chat_node → multi-noeuds

- Spec 001 avait livré un `chat_node` monolithique
- Spec 003 a introduit `router_node` + `profiling_node` + chat enrichi
- A ouvert la voie aux 9 noeuds spécialistes de spec 012 (bien que le routeur ait été refondu en spec 013)

### 2.4 Page profil + édition manuelle (US4)

- Alternative claire à la conversation, accessible depuis la sidebar
- Badge de completion (US5) réactif via store Pinia
- **Design toujours en place**

### 2.5 TDD complet sur US1, US2, US3, US4

- 9 fichiers de test écrits avant implémentation
- Tests d'intégration SSE (T017) particulièrement solides

---

## 3. Ce qui a posé problème (révélé a posteriori)

### 3.1 🔴 DETTE MAJEURE — Code mort : `profiling_node` + `chains/extraction.py`

- Spec 003 a livré `profiling_node` (nodes.py:1192) + `chains/extraction.py` (`extract_profile_from_message`)
- Architecture : chaque message utilisateur passait dans le routeur, qui décidait si appeler `profiling_node` en parallèle de `chat_node`
- **Spec 012 a remplacé ce mécanisme** par un tool LangChain `update_company_profile` (`PROFILING_TOOLS`)
- `CLAUDE.md` Recent Changes confirme : *"Migration evenements profil (profile_update/profile_completion) depuis l'ancien extract_and_update_profile vers le tool update_company_profile"*
- **Vérification code actuel** :
  - `graph.py` n'importe PLUS `profiling_node` → dead code confirmé
  - Seul `PROFILING_TOOLS` est wiré (`graph.py:124`)
  - `profiling_node` (240+ lignes) + `chains/extraction.py` restent dans le repo, non utilisés
- **Cause racine** : migration spec 012 sans nettoyage de l'ancien système
- **Impact** : confusion pour tout nouvel arrivant, tests fantômes, maintenance de code mort
- **Leçon** : quand une spec remplace un mécanisme d'une spec antérieure, **supprimer** l'ancien, pas l'oublier

### 3.2 🟠 Router heuristique cassé en multi-tour → refondu en spec 013

- Spec 003 T019 : routeur avec "heuristiques regex/mots-cles" pour détecter intentions
- Spec 013 : *"Classification binaire LLM continuation/changement dans router_node avec defaut securitaire"*
- **Cause racine** : heuristiques regex inadéquates pour le contexte conversationnel multi-tour
- Quand l'utilisateur dit "oui, continue" après avoir lancé un scoring ESG, les regex ne détectent pas la continuation → retour forcé à `chat_node`
- **Leçon** : les routeurs conversationnels nécessitent une classification LLM avec `active_module` maintenu en state, pas des règles figées

### 3.3 🟠 `context_memory` contaminé par hallucinations

- Bug fix du 2026-04-15 (feature 019) a dû ajouter un **paragraphe neutralisant** dans `_format_memory_section`
- Raison : les résumés générés par spec 003's `summarization.py` contenaient parfois des hallucinations du type "outil indisponible"
- Ces hallucinations se perpétuaient via `context_memory` → contamination inter-sessions
- **Nettoyage BDD one-shot** : 9 `conversations.summary` ont dû être remis à NULL
- **Cause racine** : `SUMMARY_PROMPT` initial permettait trop de latitude au LLM pour documenter des "problèmes rencontrés"
- **Correctif a posteriori** : `SUMMARY_PROMPT` renforcé (interdiction explicite de formulations "outil indisponible", "hors service", "pas accessible")
- **Leçon** : les prompts qui génèrent du contenu persistant doivent interdire explicitement la persistence des erreurs transitoires

### 3.4 🟡 `_summarize_previous_conversation` silencieux en échec

- `chat.py:411` : `summary = await generate_summary(messages_text)` ; puis `if summary:` → silent skip si échec
- Pas de retry, pas de log, pas d'observabilité
- Impact : un échec réseau ponctuel pendant la génération du résumé laisse la conversation précédente **définitivement sans résumé**
- Et comme `_summarize_previous_conversation` ne cible que la dernière conversation sans résumé, les échecs précédents ne sont jamais rattrapés
- **Leçon** : tout I/O asynchrone LLM doit avoir un retry + log warn en cas d'échec

### 3.5 🟡 `ProfileNotification.vue` : notification in-chat, pas dans le toast global

- Spec 003 a créé un composant dédié `ProfileNotification.vue` intégré dans `ChatMessage.vue`
- Le système de toast global existait déjà (spec 001 US4)
- Résultat : deux systèmes de notification parallèles dans l'app
- **Cause racine** : focus sur le UX chat-intégré au lieu de réutiliser le toast global
- **Leçon** : vérifier l'existant avant de créer un nouveau composant de notification

### 3.6 🟡 Pas de stratégie pour les conflits d'extraction

- Edge case documenté : *"contradictions entre deux conversations → la dernière prévaut"*
- Mais pas de trace de cette logique dans le code (pas de timestamp sur les sources d'extraction, pas de conflict-resolution)
- Une édition manuelle "prévaut toujours" selon la spec mais aucun flag `manually_edited` sur les champs
- **Impact** : une extraction LLM après une édition manuelle peut écraser silencieusement la valeur manuelle
- **Leçon** : les règles de priorité documentées dans la spec doivent avoir un mécanisme tangible dans le schema (flag, timestamp, audit log)

---

## 4. Leçons transversales

1. **Nettoyer le code remplacé** — une spec qui supplante une spec antérieure doit supprimer l'ancien, pas laisser coexister les deux.
2. **Éviter les routeurs regex pour le conversationnel** — les LLM classifient mieux les intentions avec contexte d'état actif.
3. **Les prompts persistant doivent interdire explicitement la persistance d'erreurs transitoires** — sinon les hallucinations se propagent.
4. **Tout I/O LLM asynchrone doit avoir retry + observabilité** — les échecs silencieux créent des dettes invisibles.
5. **Réutiliser les composants UI existants** — vérifier le toast global avant de créer un `ProfileNotification` dédié.
6. **Les règles de priorité doivent être implémentées, pas juste documentées** — flags, timestamps, audit logs.

---

## 5. Actions résiduelles retenues

| # | Action | Priorité | Source |
|---|--------|----------|--------|
| 1 | **Supprimer dead code** : `profiling_node` (nodes.py:1192+) + `chains/extraction.py` + tests associés | P1 | §3.1 |
| 2 | Ajouter retry + log warn dans `_summarize_previous_conversation` (chat.py:373) | P2 | §3.4 |
| 3 | Ajouter flag `manually_edited_fields: JSONB` sur `CompanyProfile` pour protéger les éditions manuelles | ~~P2~~ → **P1** (reclassé 2026-04-16) | §3.6 |
| 4 | Unifier `ProfileNotification.vue` avec le toast global (`useToast`) | P3 | §3.5 |

**Actions déjà en place** :
- ✅ Classification LLM dans router_node (spec 013)
- ✅ `SUMMARY_PROMPT` durci + paragraphe neutralisant (bug fix 2026-04-15)
- ✅ 9 summaries contaminés purgés (one-shot 2026-04-15)

---

## 6. Verdict

**Spec 003 livrée à 100 %, design de completion et de mémoire contextuelle bien pensé et toujours en place, mais la dette de code mort (profiling_node + extraction.py) et la fragilité des résumés (retry silencieux, hallucinations) créent une charge cognitive importante.**

Le nettoyage du code mort (§3.1) est **P1** : ~300 lignes de code non utilisées, source de confusion pour les contributeurs, et risque qu'un futur PR le réactive par erreur. Les autres dettes (retry, édition manuelle, toast) sont acceptables à court terme mais à ouvrir en stories BMAD dédiées.

---

## 7. Mise à jour 2026-04-16 — reclassements

### `manually_edited_fields` : P2 → **P1**

**Justification** : le finding §3.6 — « édition manuelle prévaut » documentée mais non implémentée — est en réalité un **risque de perte de données utilisateur silencieuse**. Un user édite son profil via `/profile`, puis envoie un message qui retrigger `update_company_profile` → le LLM écrase la correction. C'est invisible côté UX et catastrophique pour la confiance plateforme.

Mérite P1 au même titre que les failles sécurité : invisible tant que ça n'arrive pas, catastrophique quand ça arrive.

**Audit BDD suggéré** avant d'implémenter le flag : chercher en BDD les divergences entre le dernier `profile_update` SSE event et l'état actuel du profil pour chaque user — possibles écrasements passés à inventorier.
