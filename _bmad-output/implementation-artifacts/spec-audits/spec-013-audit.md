# Audit Rétrospectif — Spec 013 : Correction Multi-turn Routing + Timeline Format

**Date d'audit** : 2026-04-16
**Auditeur** : Angenor (Project Lead) + assistant Amelia
**Spec** : [specs/013-fix-multiturn-routing-timeline/](../../../specs/013-fix-multiturn-routing-timeline/)
**Méthode** : rétrospective post-hoc sur spec-correctif
**Statut rétro** : ✅ Audité — correctif bien exécuté, 1 dette UX résiduelle

---

## 1. Portée de la spec

**Spec-correctif** qui adresse 2 bugs révélés par les specs précédentes :
- **BUG-1** : Routing multi-tour cassé (héritage du router heuristique regex de spec 003 §3.2)
- **BUG-2** : TimelineBlock rigide (héritage du schema strict de spec 002 §3.2)

| Dimension | Livré |
|-----------|-------|
| Tâches | 56 / 57 `[X]` — **T056 non marquée** (vérif manuelle quickstart) |
| Discordance tasks↔code | 0 (tous les fichiers cités existent et sont fonctionnels) |
| User Stories | 6 (US1-US2 P1 ESG+carbon, US3-US5 P2 changement/reprise/financement, US6 P3 timeline) |
| Nouveaux champs state | 2 (`active_module: str \| None`, `active_module_data: dict \| None`) |
| Nouvelle fonction | `_is_topic_continuation()` (nodes.py:176) |
| Nouveau helper frontend | `normalizeTimeline.ts` (frontend/app/utils/) |
| Prompts standardisés | 3 (action_plan.py, carbon.py, financing.py) |
| Tests backend | 806 lignes (`test_active_module.py`) |
| Tests frontend | 218 lignes (`TimelineBlock.test.ts`) |
| CLAUDE.md mentionne | "34 tests backend + 21 tests frontend, zero regression" |

---

## 2. Ce qui a bien fonctionné

### 2.1 Spec-correctif parfaitement cadrée

- 2 bugs distincts mais regroupés pertinemment (impact simultané sur l'expérience conversationnelle)
- 6 user stories explicites avec priorités claires (US1-US2 P1 = bug core, US6 P3 = bug affichage)
- Edge cases documentés (ex: "message vide/emojis pendant module actif → reste dans le module", "LLM classification timeout → défaut continuation")
- **Pattern exemplaire de spec-correctif** : diagnostic précis + fix ciblé + tests non-régression

### 2.2 Approche TDD rigoureuse

- **806 lignes de tests backend** sur `test_active_module.py` (fichier dédié unique)
- Tests écrits AVANT implémentation (Phase 2 Foundational : 5 tests avant 3 implémentations)
- Couverture exhaustive : continuation, changement de sujet, défaut sécuritaire, reprise, transition directe
- **CLAUDE.md confirme "34 tests backend + 21 tests frontend, zero regression"**

### 2.3 Pattern `active_module` propre

- 2 champs ajoutés au state : `active_module` + `active_module_data`
- 9 nœuds spécialistes gèrent le cycle de vie (activation au démarrage, update progressif, désactivation à la finalisation)
- Défaut sécuritaire en cas d'erreur LLM : rester dans le module actif (FR-005)
- **Pattern qui corrige la dette spec 003 §3.2** (routeur heuristique regex)

### 2.4 Reprise de module après interruption (US4)

- Détection des intentions "continuons", "reprenons" dans le router
- Lecture de la session `in_progress` en base quand `active_module` est active mais `active_module_data` vide
- ESG + carbone supportent la reprise (T033-T034)

### 2.5 Transition directe entre modules (US3)

- Changement de sujet détecté + nouveau module identifié → `active_module = nouveau module` directement
- Pas de passage par l'état neutre
- Suspension propre : le module suspendu reste `in_progress` en base, pas de perte de données

### 2.6 `normalizeTimeline` : tolérance aux variantes LLM

- Accepte 4 clés racines : `events`, `phases`, `items`, `steps`
- Accepte 5 aliases de champs : `period`/`timeframe` → `date`, `name`/`label` → `title`, `state` → `status`, `details`/`content` → `description`
- Défaut `status = "todo"` si absent
- Message d'erreur explicite si ni `events` ni alias présent
- **Pattern qui corrige la dette spec 002 §3.2** (TimelineBlock rigide)

### 2.7 Standardisation des prompts

- `action_plan.py`, `carbon.py`, `financing.py` : format canonique `{"events": [...]}`
- Tests frontend valident quand même les variantes (rétrocompatibilité)
- **Double défense** : prompts canoniques (prévention) + normalizer (guérison)

---

## 3. Ce qui a posé problème

### 3.1 🟠 Classification LLM à chaque message = coût cumulé

- Chaque message reçu pendant un `active_module` déclenche `_is_topic_continuation()` qui fait un appel LLM binaire
- Pour un échange ESG de 30 critères = 30 appels LLM supplémentaires (en plus du nœud LLM principal)
- **Coût cumulé** : tokens + latence (2-5 s/appel)
- Pas de **cache** : "oui", "non", "environ 500L" génèrent chacun un appel LLM même si la réponse est évidente
- **Alternative possible** : heuristique rapide (longueur du message + mots-clés changement) + fallback LLM uniquement en cas de doute
- **Leçon** : la classification LLM systématique est **coûteuse** ; combiner avec des heuristiques rapides pour les cas évidents réduit la facture

### 3.2 🟠 `active_module` non exposé au frontend

- **Vérification** : `grep "active_module" backend/app/api/chat.py frontend/app/composables/useChat.ts` → **aucun résultat**
- Le state LangGraph contient `active_module` mais il n'est **jamais sérialisé dans les events SSE**
- **Impact UX** :
  - L'utilisateur ne sait pas quel module est actif
  - Il ne voit pas que ses réponses partent vers "ESG" vs "carbone" vs "chat général"
  - Quand le routing fait une erreur (rare mais possible), impossible à diagnostiquer côté user
- **Leçon** : les indicateurs d'état conversationnel (module actif, progression) devraient être exposés en SSE pour que le frontend puisse afficher un breadcrumb contextuel

### 3.3 🟡 Défaut "continuation" en cas d'erreur LLM = ignorer vrais changements

- FR-005 : "En cas de doute sur le changement de sujet, le système DOIT rester dans le module actif (défaut sécuritaire)"
- Pattern correct pour la plupart des cas (meilleur que retomber dans le chat général)
- **Mais** : si le LLM de classification timeout systématiquement (problème réseau), toutes les demandes de changement sont ignorées
- L'utilisateur dit "Stop, je veux parler d'autre chose" → LLM timeout → reste dans ESG → frustration
- Pas de timeout short-circuit (ex: 5 timeouts consécutifs → escape)
- **Leçon** : les défauts sécuritaires doivent avoir un **circuit breaker** en cas d'échec persistant

### 3.4 🟡 T056 manuel non validé (`[ ]`)

- T056 : "Vérification manuelle du parcours multi-tour complet selon quickstart.md" — **non marquée done**
- Les 34 tests backend + 21 frontend couvrent largement, mais la validation manuelle ajoute une garantie UX
- **Impact** : faible en pratique (couverture test solide) mais contradiction avec le statut "spec livrée"
- **Cohérent avec la dette spec 009 §3.2** (Phase Polish incomplète)

### 3.5 🟡 `active_module_data` schema non typé

- `active_module_data: dict | None` accepte n'importe quel dict
- Chaque nœud définit son propre schéma implicite :
  - ESG : `{assessment_id, criteria_remaining, criteria_evaluated}`
  - Carbon : `{assessment_id, entries_collected, current_category}`
  - Financing : structure non documentée
- Pas de `TypedDict` par module → erreur de frappe non détectée au runtime
- **Leçon** : les structures JSONB dans le state gagnent à être typées (Pydantic/TypedDict) par module

### 3.6 🟡 Pas de ré-évaluation périodique du `active_module`

- Une fois activé, `active_module` reste jusqu'à finalisation explicite ou changement détecté
- Si un module reste `in_progress` pendant des jours, `active_module` reste pointé dessus sur toutes les conversations suivantes
- **Risque** : un user inactive 1 semaine reprend et reçoit des réponses ESG alors qu'il voulait juste du chat général
- Pas de TTL sur `active_module` (ex: reset après 24h d'inactivité)
- **Leçon** : les pointeurs d'état temporels gagnent à avoir un TTL

### 3.7 🟡 Triple défense timeline (prompts + normalizer + defaults) = complexité

- Prompts canoniques + normalizer tolérant + defaults par champ
- **Effet pervers** : un bug de schéma côté LLM passe silencieusement (le normalizer l'absorbe)
- Pas de métrique sur "combien de fois le normalizer a dû appliquer un alias" → pas de feedback pour améliorer les prompts
- **Leçon** : tolérance doit être **observée** (logger les usages d'aliases) pour rétro-boucler sur les prompts

---

## 4. Leçons transversales

1. **Classification LLM + heuristiques** pour cas évidents (combiner rapidité + précision).
2. **Indicateurs d'état conversationnel exposés en SSE** pour breadcrumb frontend.
3. **Circuit breaker sur défauts sécuritaires** — éviter les verrouillages persistants.
4. **TypedDict par module** pour `active_module_data` (prévention erreurs de frappe).
5. **TTL sur pointeurs d'état temporels** — éviter les références obsolètes.
6. **Tolérance observée** (logger les aliases utilisés) pour rétro-boucler sur les prompts.

---

## 5. Actions résiduelles retenues

| # | Action | Priorité | Source |
|---|--------|----------|--------|
| 1 | Exposer `active_module` dans SSE events + breadcrumb frontend | P2 | §3.2 |
| 2 | Heuristique rapide avant appel LLM `_is_topic_continuation` (court + mots-clés → skip LLM) | P3 | §3.1 |
| 3 | Circuit breaker sur timeouts LLM de classification (reset active_module après N échecs) | P3 | §3.3 |
| 4 | TypedDict par module pour `active_module_data` | P3 | §3.5 |
| 5 | TTL sur `active_module` (ex: 24h d'inactivité) | P3 | §3.6 |
| 6 | Logger usages d'aliases `normalizeTimeline` pour détecter les prompts à corriger | P3 | §3.7 |

**Actions déjà en place** :
- ✅ `active_module` + `active_module_data` dans state
- ✅ `_is_topic_continuation` avec défaut sécuritaire
- ✅ `normalizeTimeline` avec 4 clés racines + 5 aliases
- ✅ Prompts standardisés (action_plan, carbon, financing)
- ✅ Reprise de module (ESG + carbone)
- ✅ Transition directe entre modules
- ✅ 34 tests backend + 21 frontend — zero régression

---

## 6. Verdict

**Spec 013 est un correctif exemplaire** — diagnostic précis (2 bugs), fix ciblé, 27 tests backend + 21 frontend, **zero régression** sur 796 tests existants. Elle **répare** deux dettes héritées (spec 003 routeur + spec 002 timeline) et **débloque 20+ tests d'intégration**.

La dette la plus significative est **§3.2 `active_module` non exposé au frontend** (dette UX) — l'utilisateur navigue à l'aveugle dans une conversation multi-module. P2 pour un projet en phase de polish.

Les autres dettes sont **opérationnelles et secondaires** (coût LLM cumulé, typage faible, TTL manquant). Aucune n'est P1.

**Recommandation** : spec 013 peut servir de **référence pour écrire des spec-correctifs** — diagnostic/fix/tests/zero-regression est un pattern à reproduire.
