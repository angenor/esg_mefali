---
title: 'V8.1 — Régressions Vague 8 (city extraction + routing crédit déterministe)'
type: 'bugfix'
created: '2026-04-29'
status: 'done'
context:
  - '{project-root}/CLAUDE.md'
  - '{project-root}/_bmad-output/implementation-artifacts/tests-manuels-vague-8-2026-04-29.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-v8-axe1-profile-extraction-hybrid.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-v8-axe3-routing-credit-carbon-finalize.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** La Vague 8 sort ROUGE après 12/62 tests : (1) BUG-V8-001 — l'extraction profil hybride V8-AXE1 perd le champ `city` (« Dakar » non capté → `company_profiles.city = NULL`) ; (2) BUG-V8-002 — le forçage déterministe `generate_credit_score` de V8-AXE3 reste inopérant car le router ne reconnaît pas « évalue ma solvabilité » comme une demande crédit, et le `credit_node` n'est donc jamais atteint.

**Approach:** (1) Étendre `profile_extraction.py` avec un dict `CITIES_FR` (~21 villes francophones africaines) + extracteur `_extract_city` aligné sur le pattern existant `_extract_country` (normalisation NFD + word-boundary). (2) Aligner la détection router sur la regex `_FORCE_CREDIT_RE` du `credit_node` : appliquer la même heuristique dans `_detect_credit_request` pour que tout déclencheur de forçage soit aussi un déclencheur de routage.

## Boundaries & Constraints

**Always:**
- Tolérance accents/casse via la fonction `_normalize` existante (NFD + lower).
- Word-boundary stricte (`\b...\b`) pour éviter les sous-chaînes (« Lomé » dans « Loménie »).
- Le LLM reste prioritaire : la regex backend ne s'applique qu'au fallback déterministe (cf. logique existante `extract_profile_from_text`).
- `_detect_credit_request` doit rester True-strict (false negative > false positive) : ne déclencher que si verbe d'action + nom crédit/score/solvabilité dans 40 caractères.

**Ask First:**
- Aucun. Périmètre clos par les patches user.

**Never:**
- Ajouter des villes hors zone CEDEAO/UEMOA/Maghreb pertinentes pour PME africaines francophones.
- Modifier la signature de `extract_profile_from_text` ni `_detect_credit_request`.
- Toucher au `credit_node` ou à `_should_force_credit_score` (déjà corrects ; le problème est en amont).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|----------------------------|----------------|
| City matchée canonique | « AgriVert Sarl, Agriculture, 15 employés, Sénégal, Dakar » | `extract_profile_from_text` retourne `city="Dakar"` | N/A |
| City synonyme accents | « basé à Lomé » ou « base a lome » | `city="Lomé"` (canonique) | N/A |
| City absente | « entreprise au Sénégal » | clé `city` absente du dict (pas de `None` explicite) | N/A |
| Faux positif évité | « Saint-Louis du Missouri » | match « Saint-Louis » accepté (pas de désambiguïsation pays — limite assumée) | N/A |
| Détection crédit explicite | « évalue ma solvabilité » | `_detect_credit_request` → True → router pose `_route_credit=True` | N/A |
| Détection crédit insuffisante | « comment ça va ? » | False, pas de routage crédit | N/A |
| Pas de double-match | « calculer mon score crédit vert » | True (déjà couvert par patterns existants), pas de régression | N/A |

</frozen-after-approval>

## Code Map

- `backend/app/services/profile_extraction.py` -- Ajouter `CITIES_FR` + `_extract_city` + appel dans `extract_profile_from_text` (BUG-V8-001).
- `backend/app/graph/nodes.py` -- Étendre `_detect_credit_request` pour réutiliser `_FORCE_CREDIT_RE` (BUG-V8-002).
- `backend/tests/test_services/test_profile_extraction.py` -- Tests unitaires `_extract_city` (cas Dakar, Lomé, accents, absent, multi).
- `backend/tests/test_graph/test_nodes.py` (ou équivalent) -- Test unitaire `_detect_credit_request("évalue ma solvabilité")` → True.

## Tasks & Acceptance

**Execution:**
- [ ] `backend/app/services/profile_extraction.py` -- Ajouter constante `CITIES_FR` (~21 villes), fonction `_extract_city(normalized)`, et appel dans `extract_profile_from_text` après `_extract_country`. Mettre à jour le docstring (la mention « city non couvert » devient obsolète).
- [ ] `backend/app/graph/nodes.py` -- Dans `_detect_credit_request`, ajouter en plus des `_CREDIT_PATTERNS` un test `_FORCE_CREDIT_RE.search(text)`. Retourner True si l'un des deux matche. Garder l'API actuelle (signature, boolean).
- [ ] `backend/tests/test_services/test_profile_extraction.py` (créer si absent) -- Cas : Dakar canonique, Lomé accents, lome ASCII, ouaga abréviation, ville absente, texte vide.
- [ ] `backend/tests/test_graph/test_credit_routing.py` (créer si absent) -- Cas : « évalue ma solvabilité » True, « calcule mon score crédit » True, « bonjour » False, « génère un score de solvabilité » True.

**Acceptance Criteria:**
- Given un texte « AgriVert Sarl, Agriculture, 15 employés, Sénégal, Dakar », when `extract_profile_from_text(text)` est appelé, then la clé `city` vaut `"Dakar"`.
- Given un message utilisateur « évalue ma solvabilité maintenant », when `_detect_credit_request(message)` est appelé, then la fonction retourne `True`.
- Given le scénario T-V8-CREDIT-01, when l'utilisateur envoie « évalue ma solvabilité » dans le chat, then le router pose `_route_credit=True`, le `credit_node` invoque `generate_credit_score` via forçage, et une ligne apparaît dans `credit_scores`.
- Tous les tests existants `pytest backend/tests/` continuent de passer (zéro régression).

## Design Notes

Pourquoi BUG-V8-002 n'est pas un bug du `credit_node` : le forçage est déjà câblé correctement (lignes 1297-1319 `nodes.py`) et la regex `_FORCE_CREDIT_RE` matche bien « évalue ma solvabilité ». Mais le router amont (`router_node` → `_detect_credit_request`) utilise `_CREDIT_KEYWORDS` qui exigent le mot « score » à proximité (`\bscore\s+(?:de\s+)?solvabilit[ée]\b`). « évalue ma solvabilité » ne contient pas « score » → le router route vers `chat_node`, qui répond textuellement. La correction unifie les deux niveaux : si la regex de forçage matche, le router DOIT router crédit.

Pourquoi accepter `Saint-Louis` ambigu : la zone primaire est francophone Afrique ; PME américaines hors-cible ; coût/bénéfice d'un désambiguïsateur pays-ville disproportionné en V8.1.

## Verification

**Commands:**
- `cd backend && source venv/bin/activate && pytest tests/test_services/test_profile_extraction.py -v` -- expected: tests verts, ≥6 cas city.
- `cd backend && source venv/bin/activate && pytest tests/test_graph/test_credit_routing.py -v` -- expected: tests verts, ≥4 cas detection.
- `cd backend && source venv/bin/activate && pytest tests/ -x` -- expected: 935+ tests verts, zéro régression.

**Manual checks:**
- Rejouer T-V8-PROFILE-01/03 : « AgriVert Sarl, Agriculture, 15 employés, Sénégal, Dakar » → `SELECT city FROM company_profiles` → `Dakar`.
- Rejouer T-V8-CREDIT-01/02 : « évalue ma solvabilité » → backend log `Forced tool invocation: generate_credit_score in credit_node` → `SELECT * FROM credit_scores` → 1 ligne.
