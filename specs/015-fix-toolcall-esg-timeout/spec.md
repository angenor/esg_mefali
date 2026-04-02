# Feature Specification: Correction des 3 anomalies bloquant les tests d'intégration

**Feature Branch**: `015-fix-toolcall-esg-timeout`
**Created**: 2026-04-02
**Status**: Draft
**Input**: Correction des anomalies 3 (application tool calling), 4 (crédit tool calling), 5 (ESG timeout batch scoring)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Génération de dossier de candidature via le chat (Priority: P1)

L'utilisateur demande au chatbot de créer un dossier de candidature pour un fonds vert (ex: SUNREF). Le système appelle les tools appropriés pour créer le dossier et générer les sections, au lieu de simplement afficher du texte dans le chat. Le dossier apparait sur la page /applications.

**Why this priority**: Sans tool calling, le module candidature est inutilisable -- les dossiers ne sont jamais persistés en base. C'est un test FAIL bloquant (test 6.1).

**Independent Test**: Envoyer "Crée-moi un dossier SUNREF via la SIB" dans le chat et vérifier que le dossier apparait sur /applications en statut "draft".

**Acceptance Scenarios**:

1. **Given** un utilisateur avec un profil entreprise complété, **When** il dit "Crée-moi un dossier SUNREF via la SIB", **Then** le tool `create_fund_application` est appelé et le dossier apparait sur /applications en statut "draft".
2. **Given** un dossier de candidature existant, **When** l'utilisateur dit "Génère la section Présentation de l'entreprise", **Then** le tool `generate_application_section` est appelé et la section est sauvegardée et visible sur /applications.
3. **Given** un dossier en cours, **When** l'utilisateur dit "Quels documents il me faut ?", **Then** le tool `get_application_checklist` est appelé et la checklist est affichée.

---

### User Story 2 - Calcul du score de crédit vert via le chat (Priority: P1)

L'utilisateur demande son score de crédit vert. Le système appelle le tool `generate_credit_score` pour calculer et sauvegarder le score, au lieu de donner une estimation textuelle. Le score apparait sur /credit-score.

**Why this priority**: Sans tool calling, le module crédit est inutilisable -- aucun score n'est persisté. C'est un test FAIL bloquant (test 7.1).

**Independent Test**: Envoyer "Calcule mon score de crédit vert" et vérifier que le score apparait sur /credit-score.

**Acceptance Scenarios**:

1. **Given** un utilisateur avec des données en base (profil, ESG, carbone), **When** il dit "Calcule mon score de crédit vert", **Then** le tool `generate_credit_score` est appelé et le score apparait sur /credit-score.
2. **Given** un score de crédit existant, **When** l'utilisateur dit "Quel est mon score actuel ?", **Then** le tool `get_credit_score` est appelé et le score existant est retourné.
3. **Given** un score de crédit calculé, **When** l'utilisateur dit "Génère mon attestation", **Then** le tool `generate_credit_certificate` est appelé et un PDF est généré avec un lien de téléchargement.

---

### User Story 3 - Évaluation ESG complète sans timeout (Priority: P2)

L'utilisateur complète une évaluation ESG de 30 critères. Le système sauvegarde les critères par lot (batch) au lieu de faire 30 allers-retours séquentiels, évitant ainsi le timeout SSE/HTTP.

**Why this priority**: Le timeout empêche la finalisation des évaluations complètes. C'est un test partiellement FAIL (test 3.5). Priorité P2 car le scoring fonctionne critère par critère -- seul le batch/finalisation pose problème.

**Independent Test**: Évaluer les 30 critères ESG et finaliser l'évaluation -- le processus doit se terminer en moins de 15 secondes sans timeout.

**Acceptance Scenarios**:

1. **Given** une évaluation ESG en cours avec 10 critères Environnement évalués, **When** le système sauvegarde les critères du pilier E, **Then** un seul appel batch sauvegarde les 10 critères et tous apparaissent sur /esg.
2. **Given** une évaluation ESG avec les 30 critères évalués, **When** l'utilisateur dit "Finalise mon évaluation ESG", **Then** les scores agrégés (E, S, G, global) sont calculés et affichés en moins de 15 secondes.
3. **Given** une évaluation ESG partielle, **When** l'utilisateur répond à plusieurs questions d'un coup, **Then** les critères correspondants sont sauvegardés en batch sans timeout.

---

### User Story 4 - Non-régression des 29 tests existants (Priority: P1)

Les corrections apportées ne doivent casser aucun des 29 tests qui passaient déjà. Les modules profiling, carbone, financement, plan d'action, blocs visuels et non-régression doivent continuer à fonctionner.

**Why this priority**: La non-régression est critique -- casser des fonctionnalités existantes annulerait le bénéfice des corrections.

**Independent Test**: Relancer la suite complète des 36 tests et vérifier que les 29 précédemment passants continuent à passer, plus les 3 corrigés.

**Acceptance Scenarios**:

1. **Given** les corrections des anomalies 3, 4 et 5 appliquées, **When** on exécute les tests 8.1-8.2 (plan d'action), **Then** ils passent toujours.
2. **Given** les corrections appliquées, **When** on exécute les tests 1.1-1.5 (profiling), 4.1-4.4 (carbone), 5.1-5.3 (financement), **Then** ils passent toujours.
3. **Given** les corrections appliquées, **When** on exécute les tests 11.1-11.4 (blocs visuels) et 12.1-12.3 (non-régression), **Then** ils passent toujours.

---

### Edge Cases

- Que se passe-t-il si le tool call échoue (ex: base de données indisponible) ? Le chat doit afficher un message d'erreur explicite, pas un timeout silencieux.
- Que se passe-t-il si l'utilisateur demande un dossier pour un fonds qui n'existe pas en base ? Le système doit informer l'utilisateur et proposer les fonds disponibles.
- Que se passe-t-il si le batch ESG contient des critères avec des codes invalides ? Le tool doit valider les codes et rejeter les invalides avec un message clair.
- Que se passe-t-il si l'évaluation ESG est finalisée alors que certains critères n'ont pas été évalués ? Le système doit calculer les scores sur les critères disponibles et indiquer le taux de couverture.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le module candidature DOIT appeler les tools (`create_fund_application`, `generate_application_section`, etc.) pour persister les dossiers en base, et ne DOIT JAMAIS se contenter de texte dans le chat.
- **FR-002**: Le module crédit DOIT appeler les tools (`generate_credit_score`, `get_credit_score`, `generate_credit_certificate`) pour persister les scores en base, et ne DOIT JAMAIS donner une estimation textuelle sans appel tool.
- **FR-003**: Le système DOIT fournir un tool de sauvegarde par lot (`batch_save_esg_criteria`) pour sauvegarder plusieurs critères ESG en une seule opération.
- **FR-004**: La finalisation d'une évaluation ESG DOIT se terminer en moins de 15 secondes, en lisant les critères déjà sauvegardés et en calculant les agrégats en une seule opération.
- **FR-005**: Les prompts des modules candidature et crédit DOIVENT instruire explicitement l'utilisation des tools disponibles et interdire les réponses purement textuelles quand une action de persistance est requise.
- **FR-006**: Les prompts DOIVENT inclure des instructions sur les blocs visuels à utiliser après les appels tools (mermaid, progress, timeline, table, gauge, chart).
- **FR-007**: Le tool `finalize_esg_assessment` NE DOIT PAS re-sauvegarder les critères individuellement -- il DOIT seulement calculer les agrégats et sauvegarder le statut final.
- **FR-008**: Les timeouts SSE et LLM DOIVENT être augmentés comme sécurité supplémentaire (SSE: 120s, LLM: 60s par appel).
- **FR-009**: Les 29 tests d'intégration existants DOIVENT continuer à passer après les corrections (zéro régression).

### Key Entities

- **FundApplication**: Dossier de candidature à un fonds vert, avec sections, statut, et lien vers le fonds et l'entreprise.
- **CreditScore**: Score de crédit vert combinant solvabilité et impact, avec détail des facteurs et attestation PDF.
- **EsgAssessment**: Évaluation ESG avec 30 critères (10 E, 10 S, 10 G), scores individuels et agrégés.
- **EsgCriterionScore**: Score individuel d'un critère ESG (code, score 0-10, justification).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Le test 6.1 (dossier candidature) passe -- un dossier créé via le chat apparait sur /applications.
- **SC-002**: Le test 7.1 (crédit vert) passe -- un score calculé via le chat apparait sur /credit-score.
- **SC-003**: Le test 3.5 (ESG 30 critères) passe -- la finalisation complète se termine en moins de 15 secondes sans timeout.
- **SC-004**: Les 29 tests précédemment passants continuent à passer (taux de réussite global: 32/36 minimum, objectif 36/36).
- **SC-005**: Le nombre d'allers-retours pour sauvegarder un pilier ESG complet (10 critères) passe de 10 à 1.

## Assumptions

- Les bugs 1 et 2 (plan d'action) sont déjà corrigés et ne nécessitent pas de retouche.
- Le pattern de correction est identique aux bugs 1 et 2 : réécriture du prompt pour instruire le tool calling au lieu de forcer la sortie JSON.
- L'architecture LangGraph avec ToolNode conditionnel et boucle max 5 itérations est déjà en place (feature 012).
- Les tools LangChain pour application et crédit existent déjà dans `graph/tools/` -- seuls les prompts empêchent leur utilisation.
- Le timeout actuel SSE/HTTP est entre 30-60 secondes.
- La latence moyenne d'un tool call est de 1-2 secondes.
