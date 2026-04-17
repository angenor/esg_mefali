# Audit Rétrospectif — Spec 008 : Financements Verts — BDD, Matching & Parcours d'Accès

**Date d'audit** : 2026-04-16
**Auditeur** : Angenor (Project Lead) + assistant Amelia
**Spec** : [specs/008-green-financing-matching/](../../../specs/008-green-financing-matching/)
**Méthode** : rétrospective post-hoc + audit-tasks-discordance
**Statut rétro** : 🔴 **Rework nécessaire** (5 tests critiques absents)

---

## 1. Portée de la spec

Base de données de 12 fonds verts réels (GCF, FEM, BOAD, BAD, SUNREF, FNDE, etc.) + 14 intermédiaires avec coordonnées réelles + ~50 liaisons fund-intermediary. Matching projet-financement par scoring multi-critères. Parcours direct vs via intermédiaire. Fiche de préparation PDF. RAG pgvector. Intégration chat.

| Dimension | Livré |
|-----------|-------|
| Tâches | 60 / 60 `[X]` (100 %) — **mais cf. §3.1** |
| Discordance tasks↔code | **5 tests absents** (détecté par audit forensique) |
| User Stories | 6 (US1-US2 P1, US3-US5 P2, US6 P3) |
| Fonds seedés | 12 |
| Intermédiaires seedés | 14 |
| Liaisons fund-intermediary | ~50 |
| service.py | 690 lignes, 23 fonctions |
| seed.py | 889 lignes (données réelles volumineuses) |
| CLAUDE.md mentionne | "dark mode complet, gestion états vides/erreurs" |

---

## 2. Ce qui a bien fonctionné

### 2.1 Architecture saine et dense

- `financing_node` + `FINANCING_TOOLS` coexistent proprement (graph.py:139)
- 23 fonctions dans service.py → module substantiel mais découpé
- 5 fichiers bien séparés : seed, service, router, schemas, preparation_sheet + template

### 2.2 Données réelles et soignées

- 12 fonds réels avec coordonnées concrètes (GCF, FEM, BOAD Ligne Verte, SUNREF, FNDE, IFC Green Bond, BCEAO refinancement vert, etc.)
- 14 intermédiaires avec adresses Abidjan, contacts téléphone/email
- ~50 liaisons fund-intermediary avec rôles, is_primary, geographic_coverage
- **C'est la plus grosse value proposition différenciante du produit** — d'où viennent ces données d'intermédiaires à jour pour le CI ?

### 2.3 Scoring multi-critères documenté

- FR-004 : pondération explicite secteur 30% / ESG 25% / taille 15% / localisation 10% / documents 20%
- `compute_compatibility_score` (service.py:300) implémenté selon la formule
- Critères remplis / manquants remontés → UX transparente

### 2.4 Parcours d'accès enrichi par LLM

- `generate_access_pathway` (service.py:609) : 5 étapes contextualisées par Claude
- `recommend_intermediaries` (service.py:563) : tri par proximité géographique
- Distingue les 3 modes d'accès : direct, intermédiaire requis, mixte

### 2.5 RAG financing séparé des documents

- Table `financing_chunks` dédiée avec embeddings des fonds + intermédiaires
- `search_financing_chunks` (service.py:153) → recherche sémantique par source_type
- Architecture propre : **deux RAG différents** (documents utilisateur vs catalogue financing), pas de mélange

### 2.6 Fiche de préparation PDF

- WeasyPrint + template Jinja2 (même pattern que spec 006) — cohérence architecturale
- Réutilisation intelligente du pattern PDF

---

## 3. Ce qui a posé problème

### 3.1 🔴 DETTE CRITIQUE — 5 tests backend absents sur le cœur de la value proposition

**Détecté par audit forensique 2026-04-16** ([docs/audit-tasks-discordance.md](../../../docs/audit-tasks-discordance.md)).

Tasks.md mentionne `tests/backend/test_financing/test_X.py` (chemin qui n'existe nulle part). Les tests réels sont dans `backend/tests/test_financing_*.py` (fichiers plats). Sur les 9 tests annoncés, **5 sont totalement absents** :

| Test annoncé | Statut | Criticité |
|--------------|--------|-----------|
| `test_matching.py` (T022) | ❌ **ABSENT** | 🔴 Couvre `compute_compatibility_score` + `get_fund_matches` — l'algorithme cœur |
| `test_router_matches.py` (T023) | ❌ **ABSENT** | 🔴 Couvre GET /matches (endpoint principal) |
| `test_service_pathway.py` (T032) | ❌ **ABSENT** | 🔴 Couvre `generate_access_pathway` + `recommend_intermediaries` |
| `test_router_funds.py` (T033) | ❌ **ABSENT** | 🟠 Couvre CRUD fonds |
| `test_models.py` (T020) | ❌ **ABSENT** | 🟠 Couvre contraintes BDD (unique, enums) |
| `test_financing_node.py` (T050) | ✅ Présent à `backend/tests/test_financing_node.py` | — |
| `test_preparation_sheet.py` (T044) | ✅ Présent à `backend/tests/test_financing_preparation.py` | — |
| `test_router_intermediaries.py` (T040) | ✅ Présent à `backend/tests/test_financing_intermediaries.py` | — |
| `test_router_status.py` (T043) | ✅ Présent à `backend/tests/test_financing_status.py` | — |

**Impact métier** :
- L'algorithme de matching (formule 30/25/15/10/20 %) est **non testé** → un changement de pondération passe en production sans détection
- Le parcours d'accès (direct vs intermédiaire) est **non testé** → une régression fait partir un user à SUNREF sans mentionner les banques partenaires
- L'endpoint `/matches` est **non testé** → une régression sur la redirection ESG manquant ou le tri par compatibilité est invisible

**Cause racine** :
- Confusion de chemin dans tasks.md (`tests/backend/test_financing/` vs `backend/tests/test_financing_*.py`)
- Marquage `[X]` auto-déclaratif — aucune vérification que le fichier existe réellement
- Les 4 tests livrés (node, preparation, intermediaries, status) ont pu masquer visuellement l'absence des 5 autres

**Leçon** : pour une feature qui est la **plus différenciante du produit** (accès aux fonds verts), livrer sans tests de la logique métier centrale = parier. Confirme le pattern speckit "ratifier `[X]` sans vérification" observé sur spec 002 et 006.

### 3.2 🟠 12 fonds hard-codés dans `seed.py` (889 lignes)

- Les données des 12 fonds sont dans un script Python de seed
- Assumption explicite dans la spec : *"Les donnees des fonds sont relativement stables (mises a jour manuelles par un admin, pas de synchronisation automatique avec des sources externes)"*
- Mais :
  - Aucune interface admin pour CRUD les fonds (les endpoints POST /funds existent mais pas d'UI)
  - Une mise à jour des critères d'éligibilité nécessite modification du seed + re-run du seed
  - Aucune trace de mise à jour dans le modèle (pas de `last_verified_at`, `source`, `verification_status`)
- **Impact** : les coordonnées des intermédiaires (téléphones, emails) vont devenir obsolètes — impossible à mettre à jour sans développeur
- **Leçon** : les données "stables mais vivantes" (fonds, intermédiaires, taxonomies) ont besoin d'une interface admin + champs de traçabilité dès le départ

### 3.3 🟠 Pas de versioning des coordonnées intermédiaires

- Une banque peut déménager, changer de numéro, disparaître
- Aucun champ `last_verified_at`, `verified_by`, `deprecated` sur `Intermediary`
- Si un user appelle SIB et tombe sur un numéro obsolète → perte de crédibilité produit
- **Leçon** : pour des données tierces critiques (coordonnées d'acteurs externes), versioning + cycle de vérification périodique

### 3.4 🟠 Fiche PDF : aucun test de contenu

- T044 / `test_preparation_sheet.py` existe ✅, mais que teste-t-il ?
- Le PDF doit contenir : résumé entreprise, score ESG, score carbone, raison de compatibilité, documents disponibles, coordonnées intermédiaire
- Sans inspection du contenu (parse PDF + assertions), on teste seulement "le PDF est généré sans erreur"
- Même pattern de faiblesse que spec 006 (guards sur résumé exécutif IA) — dette déjà P1
- **Leçon** : tests de contenu PDF = parse + assertions sur sections, pas juste "réponse 200"

### 3.5 🟡 Recommandation géographique basée uniquement sur la ville

- `recommend_intermediaries` trie par ville (service.py:563)
- Mais un utilisateur à Bouaké doit-il voir en priorité les intermédiaires d'Abidjan (pour peu qu'ils couvrent la CI) ?
- Pas de logique "distance" ou "couverture régionale" — juste string match sur la ville
- Edge case documenté dans spec : *"afficher les intermediaires les plus proches geographiquement avec une mention de la distance"* — mention de distance non implémentée
- **Leçon** : "proximité géographique" doit être calculée (coordonnées lat/lon + haversine) ou modélisée (zone/région), pas déduit du string ville

### 3.6 🟡 Edge case "aucun match < 20%" non tracé

- Spec edge case : *"quand aucun fonds ne correspond au profil (score < 20 pour tous) → message explicatif avec suggestions"*
- Pas de trace dans le code d'un seuil "aucun match" ni d'un message dédié
- **Leçon** : même pattern que spec 005 (edge cases documentés sans tâche) et spec 007 (bornes supérieures manquantes)

### 3.7 🟡 FundMatch sans snapshot du profil à l'instant T

- `FundMatch` stocke le score de compatibilité, mais **pas le snapshot** du profil utilisé
- Si le profil change (nouveau secteur, nouveau score ESG), les matches existants affichent un score obsolète
- Pas de `computed_at` ni de re-calcul automatique
- **Leçon** : données dérivées (scores, recommandations) doivent soit se recalculer en lecture, soit stocker un snapshot horodaté

---

## 4. Leçons transversales

1. **Tests de logique métier = non négociable** quand la feature est différenciante — speckit a laissé passer 5 tests critiques.
2. **Interface admin dès le départ** pour les données tierces critiques (fonds, intermédiaires, référentiels).
3. **Versioning + last_verified_at** pour les coordonnées externes.
4. **Tests de contenu PDF** = parse + assertions, pas juste "200 OK".
5. **Proximité géographique** = calcul (haversine) ou modélisation (zone), pas string match.
6. **Edge cases documentés = tâche explicite** (pattern récurrent avec spec 005, 007).
7. **Données dérivées = snapshot horodaté** ou re-calcul à la lecture.

---

## 5. Actions résiduelles retenues

| # | Action | Priorité | Source |
|---|--------|----------|--------|
| 1 | **Créer 5 tests backend absents** : test_matching, test_models, test_router_funds, test_router_matches, test_service_pathway | **P1** | §3.1 (déjà dans l'index P1 #11) |
| 2 | Ajouter champs `last_verified_at`, `verified_by`, `deprecated` sur `Intermediary` + `Fund` | P2 | §3.2, §3.3 |
| 3 | Interface admin `/admin/financing/` (CRUD fonds + intermédiaires) | P2 | §3.2 |
| 4 | Tests de contenu PDF avec parse + assertions sur sections | P2 | §3.4 |
| 5 | Calcul géographique par coordonnées lat/lon (ou zone régionale modélisée) + affichage distance | P3 | §3.5 |
| 6 | Message + suggestions pour edge case "aucun match < 20%" | P3 | §3.6 |
| 7 | Snapshot du profil dans `FundMatch` + champ `computed_at` + trigger de re-calcul sur changement de profil | P3 | §3.7 |

**Actions déjà en place** :
- ✅ Architecture saine (`financing_node` + `FINANCING_TOOLS`, RAG séparé, pattern WeasyPrint réutilisé)
- ✅ 12 fonds + 14 intermédiaires seedés avec coordonnées réelles
- ✅ Scoring multi-critères documenté et implémenté

---

## 6. Verdict

**Spec 008 livrée à 93 % fonctionnellement, mais avec une dette de tests critique (5/9 tests absents sur la logique métier cœur).**

Le module **fonctionne** : les 12 fonds sont seedés, le matching calcule, les parcours s'affichent, les PDFs se génèrent. Mais **sans tests sur la formule 30/25/15/10/20 % ni sur le parcours d'accès**, toute modification future est un pari. C'est précisément le type de régression qui ne produit pas d'erreur visible mais dégrade silencieusement la qualité des recommandations.

**§3.1 est déjà P1 dans l'index consolidé**. Les autres dettes sont opérationnelles (interface admin, versioning des coordonnées) et peuvent attendre la validation du marché.

**Recommandation Amelia** : avant toute nouvelle feature qui s'appuie sur le matching financing (ex: dashboard, action_plan), **créer les 5 tests manquants**. C'est le fondement sur lequel construit spec 011 (dashboard) et spec 009 (fund application generator).
