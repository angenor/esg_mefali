# Audit Discordance Tasks ↔ Code — Specs 007 à 018

**Date** : 2026-04-16
**Auteur** : Amelia (Developer assistant)
**Méthode** : extraction regex des paths mentionnés dans les tâches `[X]` des 12 `tasks.md`, vérification d'existence par `ls`/`find`/`grep`.

## Méthodologie

1. Pour chaque spec (007-018), parcours de `specs/{spec}/tasks.md`.
2. Extraction des lignes commençant par `- [x]` ou `- [X]`.
3. Capture regex des paths `(backend|frontend)/[…]\.(py|ts|vue|tsx|js|sql|html|css|yaml|yml|md|json)`.
4. Pour chaque path extrait, vérification `test -e <path>`.
5. Pour chaque absent, recherche d'un équivalent probable (renommage, déplacement, typo).

**Limite de la méthode** : seules les tâches qui citent un path avec extension sont vérifiées (pattern le plus courant dans les tasks.md speckit de ce projet). Les tâches décrites en prose sans path explicite ne sont pas auditables par ce biais — cf. audits individuels des specs pour couvrir ces cas (ex: T030/T031 de spec 006, FR-019 chat notification).

## Synthèse

| Statistique | Valeur |
|-------------|--------|
| Paths extraits (unique, specs 007-018) | 253 |
| Paths présents | 228 (90,1 %) |
| Paths absents | 13 (5,1 %) |
| &nbsp;&nbsp;• Vrais manquants (pas d'équivalent) | **6** |
| &nbsp;&nbsp;• Typo / renommage (fichier équivalent existe) | 6 |
| &nbsp;&nbsp;• Supprimé intentionnellement (spec 019) | 1 |

**Verdict global** : 6 vrais manquants sur 253 chemins audités (2,4 %). Faible taux mais 2 specs concernées (008 et 010). Aucune spec 011-018 ne présente de vrai manquant.

Ce taux est à considérer en complément des **2 discordances déjà identifiées dans les audits individuels** (qui n'ont pas été détectées par cette méthode car les tâches étaient décrites en prose) :
- **Spec 002 / T038** : `frontend/tests/e2e/chat.spec.ts` non trouvé (mentionné en prose)
- **Spec 006 / T030, T031** : FR-019 notification chat (tâches décrites en prose, ne citent pas de path)

---

## Détail par spec

### Spec 007-carbon-footprint-calculator — ✅ AUCUN MANQUANT

22 paths vérifiés, tous présents.

### Spec 008-green-financing-matching — 🔴 5 VRAIS MANQUANTS + 4 TYPOS

Tasks.md utilise le chemin **`backend/test_financing/`** qui n'existe pas. Les tests réels sont dans **`backend/tests/`**.

#### Vrais manquants (pas d'équivalent trouvé)

| Chemin dans tasks.md | Équivalent existant ? |
|----------------------|-----------------------|
| `backend/test_financing/test_matching.py` | ❌ Aucun fichier `test_matching*` dans tout `backend/` |
| `backend/test_financing/test_models.py` | ❌ Pas de test dédié aux modèles financing |
| `backend/test_financing/test_router_funds.py` | ❌ Pas de test dédié aux routes `/funds` |
| `backend/test_financing/test_router_matches.py` | ❌ Pas de test dédié aux routes `/matches` |
| `backend/test_financing/test_service_pathway.py` | ❌ Pas de test `pathway*` trouvé |

**Impact** : 5 tests annoncés comme livrés dans tasks.md n'existent pas. La logique de matching projet-financement, les modèles, les routes funds/matches et la logique de pathway direct/intermédiaire **ne sont pas couvertes par des tests dédiés**.

#### Typos (fichier existe ailleurs)

| Chemin dans tasks.md | Chemin réel |
|----------------------|-------------|
| `backend/test_financing/test_financing_node.py` | `backend/tests/test_financing_node.py` |
| `backend/test_financing/test_preparation_sheet.py` | `backend/tests/test_financing_preparation.py` |
| `backend/test_financing/test_router_intermediaries.py` | `backend/tests/test_financing_intermediaries.py` |
| `backend/test_financing/test_router_status.py` | `backend/tests/test_financing_status.py` |

**Impact typo seul** : aucun manque fonctionnel, mais cherche-remplace navigable cassé.

### Spec 009-fund-application-generator — ✅ AUCUN MANQUANT

Tous les paths présents.

### Spec 010-green-credit-scoring — 🟠 1 VRAI MANQUANT

| Chemin dans tasks.md | Équivalent existant ? |
|----------------------|-----------------------|
| `frontend/tests/credit-score.test.ts` | ❌ Aucun test frontend pour credit-score (`find frontend -name '*credit*' -name '*.test.*'` → vide) |

**Impact** : la page `frontend/app/pages/credit-score/index.vue` et le store `frontend/app/stores/creditScore.ts` **ne sont pas couverts par des tests unitaires/composant**.

### Spec 011-dashboard-action-plan — ✅ AUCUN MANQUANT

### Spec 012-langgraph-tool-calling — 🟡 1 SUPPRESSION INTENTIONNELLE

| Chemin dans tasks.md | Statut |
|----------------------|--------|
| `frontend/app/pages/chat.vue` | ⚠️ Supprimé volontairement par spec 019 story 2-1 ("suppression-de-la-page-chat-et-de-chatpanel") |

**Impact** : aucun — c'est une évolution postérieure à spec 012. À noter dans tasks.md historique : ne pas compter comme bug.

### Spec 013-fix-multiturn-routing-timeline — ✅ AUCUN MANQUANT

### Spec 014-concise-chat-style — ✅ AUCUN MANQUANT

### Spec 015-fix-toolcall-esg-timeout — 🟠 2 DÉPLACEMENTS/RENOMMAGES

| Chemin dans tasks.md | Chemin réel |
|----------------------|-------------|
| `backend/tests/test_prompts/test_application_tools.py` | `backend/tests/test_tools/test_application_tools.py` (déplacé) |
| `backend/tests/test_prompts/test_esg_prompt.py` | `backend/tests/test_prompts/test_esg_scoring_prompt.py` (renommé) |

**Impact** : aucun manque fonctionnel, les tests existent bien. Documentation obsolète.

### Spec 016-fix-tool-persistence-bugs — ✅ AUCUN MANQUANT

### Spec 017-fix-failing-tests — ✅ AUCUN MANQUANT

### Spec 018-interactive-chat-widgets — ✅ AUCUN MANQUANT

---

## Actions recommandées

### P1 — Créer les tests manquants réels (6 fichiers)

1. **Spec 008 — Financing** (5 tests absents)
   - `backend/tests/test_financing_matching.py` — logique de matching multi-critères (sector/ESG/taille/localisation/documents)
   - `backend/tests/test_financing_models.py` — modèles Fund + Intermediary + relations
   - `backend/tests/test_financing_router_funds.py` — endpoints catalogue fonds
   - `backend/tests/test_financing_router_matches.py` — endpoints matching
   - `backend/tests/test_financing_pathway.py` — parcours direct vs intermédiaire
   
   **Cible** : couverture >= 80 % sur `backend/app/modules/financing/service.py`

2. **Spec 010 — Credit Score Frontend** (1 test absent)
   - `frontend/tests/unit/CreditScore.test.ts` ou `frontend/tests/pages/credit-score.spec.ts`
   - Couvrir : rendu page, store `creditScore.ts`, composables

### P3 — Nettoyer les chemins obsolètes dans tasks.md

Mettre à jour les 6 paths obsolètes dans les tasks.md pour refléter l'état réel du repo (quoique tasks.md est une doc historique immuable — débat). Alternative : simplement documenter dans les audits individuels (déjà fait).

---

## Annexe : paths extraits absents — liste brute

```
backend/test_financing/test_financing_node.py       (typo → tests/)
backend/test_financing/test_matching.py             (MANQUANT)
backend/test_financing/test_models.py               (MANQUANT)
backend/test_financing/test_preparation_sheet.py    (typo + rename → tests/test_financing_preparation.py)
backend/test_financing/test_router_funds.py         (MANQUANT)
backend/test_financing/test_router_intermediaries.py (typo → tests/test_financing_intermediaries.py)
backend/test_financing/test_router_matches.py       (MANQUANT)
backend/test_financing/test_router_status.py        (typo → tests/test_financing_status.py)
backend/test_financing/test_service_pathway.py      (MANQUANT)
frontend/tests/credit-score.test.ts                  (MANQUANT)
frontend/app/pages/chat.vue                          (supprimé par spec 019)
backend/tests/test_prompts/test_application_tools.py (déplacé → test_tools/)
backend/tests/test_prompts/test_esg_prompt.py        (renommé → test_esg_scoring_prompt.py)
```

## Annexe : tâches décrites en prose — hors périmètre de cette méthode

Les tâches suivantes sont marquées `[X]` mais décrites en prose sans path explicite, non vérifiables par ce script. Cf. audits individuels :

- **Spec 002 / T038** : "E2E flux chat complet" → `frontend/tests/e2e/chat.spec.ts` absent (détecté dans audit 002)
- **Spec 006 / T030** : "Ajouter un noeud ou intégration dans le graph LangGraph" → aucun `REPORT_TOOLS`, aucune référence `report` dans `graph.py` (détecté dans audit 006)
- **Spec 006 / T031** : "Rendre le lien de téléchargement cliquable dans le composant chat frontend" → pas d'event SSE `report_ready` dans `chat.py` (détecté dans audit 006)

Pour détecter ces discordances en prose, un audit plus approfondi par grep de mots-clés ou relecture manuelle est nécessaire — non couvert ici.
