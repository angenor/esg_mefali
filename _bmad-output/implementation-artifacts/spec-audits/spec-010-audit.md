# Audit Rétrospectif — Spec 010 : Scoring de Crédit Vert Alternatif

**Date d'audit** : 2026-04-16
**Auditeur** : Angenor (Project Lead) + assistant Amelia
**Spec** : [specs/010-green-credit-scoring/](../../../specs/010-green-credit-scoring/)
**Méthode** : rétrospective post-hoc + audit-tasks-discordance
**Statut rétro** : ✅ Audité (1 discordance front test, module backend robuste)

---

## 1. Portée de la spec

Score de crédit vert alternatif combinant solvabilité (5 facteurs) + impact vert (4 facteurs) + confiance. Intégration des interactions intermédiaires financiers comme signal de sérieux (innovation produit). Attestation PDF. Historique versionné.

| Dimension | Livré |
|-----------|-------|
| Tâches | 54 / 54 `[x]` (100 %) — **mais T023/T024 faussement marquées** |
| Discordance tasks↔code | **1 test frontend absent** (audit forensique) |
| User Stories | 5 (US1-US2 P1, US3-US4 P2, US5 P3) |
| Facteurs solvabilité | 5 (régularité 20%, cohérence 20%, gouvernance 20%, transparence 20%, engagement 20%) |
| Facteurs impact vert | 4 (ESG 40%, tendance 20%, engagement carbone 20%, projets verts 20%) |
| Tools LangChain | 3 (`CREDIT_TOOLS`) |
| Tests backend | 4 fichiers (test_service, test_router, test_node, test_certificate) |
| Composants frontend | 7 (ScoreGauge, SubScoreGauges, FactorsRadar, DataCoverage, Recommendations, ScoreHistory, CertificateButton) |

---

## 2. Ce qui a bien fonctionné

### 2.1 Architecture complète et cohérente

- `credit_node` + `CREDIT_TOOLS` + `INTERACTIVE_TOOLS` + `GUIDED_TOUR_TOOLS` (graph.py:141) — pattern le plus complet de tous les nœuds métier
- Contraste avec `application_node` (spec 009) qui exclut `GUIDED_TOUR_TOOLS`
- Module backend dense : service.py, router.py, schemas.py, certificate.py, certificate_template.html

### 2.2 Innovation produit : interactions intermédiaires dans le scoring

- FR-002 + FR-004 : les interactions intermédiaires **bonifient** le score de crédit
- `calculate_engagement_score` (service.py:194) : barème transparent
  - contacting: +15 par intermédiaire (max 30)
  - submitted: +30
  - accepted: bonus
- C'est **différenciant** : un user qui a soumis un dossier via SIB (SUNREF) a un meilleur score qu'un user sans démarche
- SC-002 mesurable : >= 30% supérieur — testable

### 2.3 Couverture backend solide

- 4 fichiers de test (service, router, node, certificate)
- Tests d'intégration US1 (T013-T015) explicites sur le cas intermédiaires
- Pattern cohérent avec spec 009

### 2.4 7 composants frontend spécialisés

- ScoreGauge + SubScoreGauges : visualisation hiérarchique
- FactorsRadar : analyse multi-dimensionnelle
- DataCoverage : transparence sur la fiabilité
- Recommendations : actions concrètes
- ScoreHistory : évolution temporelle
- CertificateButton : matérialisation PDF

### 2.5 Coefficient de confiance

- FR-006 : le score est **modulé** par un coefficient 0.5-1.0 selon la couverture des données
- Évite les scores élevés peu fiables pour les users avec données partielles
- Pattern rare et mature — rend le score honnête

### 2.6 Attestation PDF avec validité temporelle

- FR-008 : attestation avec date de génération + date de validité (6 mois)
- Pas de "score éternel" → incite à la mise à jour régulière
- Réutilisation WeasyPrint + Jinja2 (certificate_template.html)

---

## 3. Ce qui a posé problème

### 3.1 🔴 Test frontend `credit-score.test.ts` absent — T023/T024 faussement `[x]`

- **Détecté par audit forensique 2026-04-16** ([docs/audit-tasks-discordance.md](../../../docs/audit-tasks-discordance.md))
- T023 : *"Ecrire les tests du composable useCreditScore dans frontend/tests/credit-score.test.ts"*
- T024 : *"Ecrire les tests du store creditScore dans frontend/tests/credit-score.test.ts"*
- **Vérification** : `find frontend -name "*credit*test*" -o -name "*credit*.spec.*"` → **aucun résultat**
- Les fichiers `useCreditScore.ts` + `creditScore.ts` existent mais **aucun test frontend** ne les couvre
- **Impact** :
  - Le composable `useCreditScore.ts` gère 5 fonctions (generateScore, fetchScore, fetchBreakdown, fetchHistory, downloadCertificate) sans filet de sécurité
  - Le store Pinia gère state mutable sans assertion de comportement
  - Une régression (ex: mauvais parsing breakdown, erreur de type sur history) passe en silence
- **Cause racine** : même pattern speckit "`[X]` auto-déclaratif sans vérification" que spec 002/006/008
- **Leçon** : **4ème cas confirmé** de discordance speckit. À ce stade, c'est systémique.

### 3.2 🟠 Facteurs de scoring hard-codés

- `FACTOR_WEIGHTS` (service.py:23) : dict Python
- Barème intermédiaires (service.py:36-38) : magic numbers (`+15`, `+20`, `+30`)
- **Impact** :
  - Impossible de recalibrer le scoring avec des données réelles sans redéploiement
  - Pas de traçabilité "quelle version du scoring a été utilisée" sur les scores historiques
  - Un changement de pondération invalide les comparaisons temporelles (SC-006 historique)
- **Dette transverse** avec spec 005 (SECTOR_WEIGHTS), spec 007 (SECTOR_BENCHMARKS), spec 008 (fonds hard-codés), spec 009 (templates)
- **Leçon** : tout paramètre qui module un score doit être **versionné** avec l'instance du score calculé (pour reproductibilité)

### 3.3 🟠 Attestation PDF : pas de protection contre l'altération

- Même problématique que spec 006 (rapports ESG)
- L'attestation est remise aux bailleurs comme "preuve de crédibilité"
- Pas de signature cryptographique, pas de QR de vérification, pas de hash unique
- Un PDF altéré (score augmenté, date modifiée) passe inaperçu
- **Leçon** : dette déjà dans l'index (P2 #12 "signature/watermark PDF") — ajouter spec 010 comme source

### 3.4 🟠 Pas de snapshot des données utilisées

- `CreditScore` stocke le score mais **pas le snapshot** des données qui l'ont produit
- Si l'utilisateur change son profil (nouveau secteur, nouvelle taille), les scores historiques sont comparés à un profil différent
- SC-006 "évolution sur 3 versions" devient trompeur si les règles ont changé
- **Leçon** : même pattern que `FundMatch` spec 008 §3.7 — données dérivées → snapshot horodaté

### 3.5 🟡 Pas de validation des transitions d'état du score

- Statuts implicites : `active` / `expired` / `superseded`
- Pas de machine à états explicite (contrairement à spec 009 avec `VALID_TRANSITIONS`)
- Que se passe-t-il si un score "expired" est lu via `get_credit_score` tool ? Le tool retourne-t-il une erreur ou le score périmé ?
- **Leçon** : les cycles de vie temporels méritent une machine à états, même simple

### 3.6 🟡 Bonus `accepted` ambigu

- service.py:38 mentionne `"accepted": 20` en "bonus"
- Pas clair si ça s'ajoute au score engagement ou au score impact vert
- Spec FR-004 dit : *"un dossier soumis à l'intermediaire DOIT peser plus qu'un simple statut interesse"* — mais rien sur l'effet d'un dossier accepté
- **Leçon** : les modificateurs de score (bonus, malus) doivent être documentés dans la spec avec leur composant cible

### 3.7 🟡 Pas de détection d'anomalies / fraude

- Un user pourrait marquer "soumis" artificiellement pour gonfler son score
- Pas de vérification que le statut "submitted_to_intermediary" correspond à une action réelle (timestamp, document, contact intermédiaire)
- SC-007 "90% des utilisateurs comprennent comment améliorer" mais pas de garde-fou contre le gaming
- **Leçon** : un score auto-déclaratif a besoin de signaux de validation (document, timestamp, contact réel)

---

## 4. Leçons transversales

1. **4ème cas de discordance speckit `[X]` faux** — à ce stade, c'est un pattern systémique (specs 002, 006, 008, 010).
2. **Paramètres de scoring = versionnés avec l'instance calculée** (pour reproductibilité).
3. **Signature/protection des PDFs institutionnels** — dette transverse (specs 006, 008, 010).
4. **Snapshot des données dans les entités dérivées** — même pattern que `FundMatch`.
5. **Cycles de vie temporels → machine à états** (active/expired/superseded).
6. **Scores auto-déclaratifs → signaux de validation** (anti-gaming).
7. **Modificateurs de score documentés avec cible** (engagement vs impact vert).

---

## 5. Actions résiduelles retenues

| # | Action | Priorité | Source |
|---|--------|----------|--------|
| 1 | **Créer `frontend/tests/credit-score.test.ts`** (ou splitté en 2 fichiers : useCreditScore + creditScore store) | **P2** (déjà dans l'index #15) | §3.1 |
| 2 | Versionner `FACTOR_WEIGHTS` + barème intermédiaires dans `CreditScore.weights_version: str` | P2 | §3.2 |
| 3 | Snapshot des données source dans `CreditScore.source_snapshot: JSONB` | P3 | §3.4 |
| 4 | Machine à états explicite pour cycle de vie (active/expired/superseded) | P3 | §3.5 |
| 5 | Vérification anti-gaming sur les statuts `submitted_to_intermediary` (timestamp + référence contact) | P3 | §3.7 |
| 6 | Documenter explicitement cible du bonus `accepted` (engagement vs impact vert) | P3 | §3.6 |

**Actions déjà en place** :
- ✅ Architecture complète (3 tools, 4 tests backend, 7 composants frontend)
- ✅ Intégration intermédiaires innovante
- ✅ Coefficient de confiance
- ✅ Attestation PDF avec validité

**Consolidation avec autres audits** :
- §3.3 signature PDF → déjà P2 #12 (consolidation : ajouter spec 010 comme source)
- §3.2 hard-coded → dette transverse référentiels en BDD

---

## 6. Verdict

**Spec 010 livrée à 98 % (54/54 tâches mais 2 tâches `[x]` faussement déclarées sur les tests frontend), architecture la plus complète de tous les modules métier, innovation produit réussie sur l'intégration des intermédiaires.**

La découverte saillante est l'**innovation "intermédiaires = signal de sérieux"** (FR-002/FR-004) — c'est ce qui différencie structurellement Mefali d'un score de crédit classique. L'implémentation est solide (barème +15/+20/+30 documenté).

Les dettes sont opérationnelles (hard-coding, protection PDF, snapshot) et **cohérentes avec les patterns transverses** déjà identifiés. Le seul point noir est le 4ᵉ cas de discordance speckit (tests frontend absents malgré `[x]`).

**Recommandation** : spec 010 peut servir de **référence architecturale** pour les futurs modules de scoring. Le pattern `*_node + *_TOOLS + INTERACTIVE_TOOLS + GUIDED_TOUR_TOOLS + frontend composants + store + page + tests backend` est le plus mature du projet.
