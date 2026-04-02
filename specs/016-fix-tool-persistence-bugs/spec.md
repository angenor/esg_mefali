# Feature Specification: Correction des bugs de persistance tool calling et rendu visuel

**Feature Branch**: `016-fix-tool-persistence-bugs`
**Created**: 2026-04-02
**Status**: Draft
**Input**: Corriger les 5 bugs reportés dans le plan de test d'intégration (esg-mefali-test-plan.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sauvegarde critère par critère lors de l'évaluation ESG (Priority: P1)

L'utilisateur répond aux questions ESG posées par l'assistant. Chaque réponse doit déclencher l'appel au tool `save_esg_criterion_score` (ou `batch_save_esg_criteria`) pour persister le score du critère en base, puis l'assistant doit poser la question suivante. Actuellement, l'assistant met à jour le profil company au lieu de sauvegarder les critères d'évaluation.

**Why this priority**: Bug bloquant - sans persistance des critères, l'évaluation ESG entière ne fonctionne pas (0/4 vérifications passent au test 3.2). C'est le coeur du module ESG.

**Independent Test**: Démarrer une évaluation ESG, répondre à une question sur un critère environnemental, vérifier que `evaluated_criteria` en BDD contient le critère avec son score.

**Acceptance Scenarios**:

1. **Given** une évaluation ESG en cours (statut "draft"), **When** l'utilisateur répond à une question sur un critère (ex: gestion des déchets), **Then** l'assistant appelle `save_esg_criterion_score` ou `batch_save_esg_criteria` avec un score et une justification, et pose la question suivante
2. **Given** une évaluation ESG avec 5 critères déjà évalués, **When** l'utilisateur répond au 6e critère, **Then** l'assistant affiche "6/30 critères évalués" et la progression est visible sur la page /esg
3. **Given** une réponse de l'utilisateur couvrant plusieurs critères, **When** l'assistant traite la réponse, **Then** il sauvegarde TOUS les critères identifiés (pas seulement le premier)

---

### User Story 2 - Sauvegarde des entrées d'émission carbone (Priority: P1)

L'utilisateur fournit ses données de consommation (électricité, carburant, transport). L'assistant doit appeler `save_emission_entry` pour chaque source d'émission identifiée. Actuellement, l'assistant calcule et affiche les résultats mais ne persiste rien en base.

**Why this priority**: Bug bloquant - sans persistance, le bilan carbone reste vide (entries=[]) malgré les calculs affichés dans le chat. Même pattern systémique que le bug ESG.

**Independent Test**: Démarrer un bilan carbone, fournir une donnée d'électricité, vérifier que `entries` en BDD contient l'entrée avec les calculs.

**Acceptance Scenarios**:

1. **Given** un bilan carbone en cours, **When** l'utilisateur dit "On paye 800 000 FCFA d'électricité par mois", **Then** l'assistant appelle `save_emission_entry` avec la conversion kWh et le calcul tCO2e, et l'entrée apparaît sur /carbon
2. **Given** un message contenant plusieurs sources (électricité + gasoil), **When** l'assistant traite la réponse, **Then** il appelle `save_emission_entry` DEUX FOIS (une par source)
3. **Given** des entrées déjà sauvegardées, **When** l'utilisateur ajoute une nouvelle source, **Then** le total cumulé est mis à jour sur /carbon

---

### User Story 3 - Recherche de fonds via la BDD (Priority: P2)

Quand l'utilisateur demande les financements disponibles, l'assistant doit appeler `search_compatible_funds` pour interroger la base de données de fonds réels. Actuellement, l'assistant répond avec ses connaissances générales (cite GCF, BOAD, FENU) au lieu d'utiliser la BDD (SUNREF, FNDE, etc.).

**Why this priority**: Bug important - les recommandations de fonds sont incorrectes et ne correspondent pas à la BDD de 12 fonds réels avec leurs intermédiaires. L'utilisateur reçoit des informations non fiables.

**Independent Test**: Demander "Quels financements verts pour mon entreprise ?", vérifier que l'assistant appelle `search_compatible_funds` et que les fonds cités (SUNREF, FNDE, etc.) correspondent à la BDD.

**Acceptance Scenarios**:

1. **Given** un profil entreprise complété (recyclage, Abidjan, 150M FCFA), **When** l'utilisateur demande les financements disponibles, **Then** l'assistant appelle `search_compatible_funds` et affiche un tableau avec les fonds de la BDD (SUNREF, FNDE, etc.)
2. **Given** les résultats de `search_compatible_funds`, **When** l'assistant présente les fonds, **Then** chaque fonds affiche : nom, score de compatibilité %, type d'accès (direct/intermédiaire), montant
3. **Given** un fonds à accès indirect (ex: SUNREF), **When** l'assistant le présente, **Then** il mentionne les intermédiaires bancaires (SIB, SGBCI, Banque Atlantique)

---

### User Story 4 - Rendu du bloc gauge de complétion du profil (Priority: P3)

Quand l'utilisateur demande son pourcentage de complétion, l'assistant génère un bloc gauge. Ce bloc reste bloqué sur "Génération du graphique..." au lieu de s'afficher.

**Why this priority**: Bug visuel non bloquant - les données sont correctes (75% dans le texte), seul le rendu graphique échoue. L'information est accessible autrement.

**Independent Test**: Demander "Mon profil est complet à combien ?", vérifier que le bloc gauge se rend correctement dans le chat.

**Acceptance Scenarios**:

1. **Given** un profil à 75% de complétion, **When** l'utilisateur demande son taux de complétion, **Then** un bloc gauge circulaire coloré s'affiche dans le chat avec "75%"
2. **Given** un bloc gauge généré par l'assistant, **When** le frontend le reçoit, **Then** il rend un composant visuel interactif (pas du texte brut ni "Génération du graphique...")

---

### User Story 5 - Correction de la réponse sur données inexistantes (Priority: P3)

Quand l'utilisateur demande des données sur une entité inexistante (ex: "mon usine de Yamoussoukro"), l'assistant doit signaler l'absence de données au lieu de proposer d'ajouter un site.

**Why this priority**: Bug mineur de comportement - l'assistant ne hallucine pas de données (c'est bon) mais sa réponse est trompeuse en proposant d'ajouter un site qui n'existe pas.

**Independent Test**: Demander "Quel est le bilan carbone de mon usine de Yamoussoukro ?", vérifier que l'assistant indique clairement qu'il n'a pas de données pour Yamoussoukro.

**Acceptance Scenarios**:

1. **Given** un profil basé à Abidjan uniquement, **When** l'utilisateur mentionne une localisation inexistante (Yamoussoukro), **Then** l'assistant dit clairement "Je n'ai pas de données pour un site à Yamoussoukro. Votre profil est basé à Abidjan."
2. **Given** une question sur des données inexistantes, **When** l'assistant répond, **Then** il ne propose PAS d'ajouter/créer l'entité inexistante sans que l'utilisateur l'ait explicitement demandé

---

### Edge Cases

- Que se passe-t-il si le tool `save_esg_criterion_score` échoue (erreur réseau/BDD) ? L'assistant doit informer l'utilisateur et réessayer.
- Que se passe-t-il si `search_compatible_funds` retourne une liste vide ? L'assistant doit dire qu'aucun fonds compatible n'a été trouvé et suggérer de compléter le profil.
- Que se passe-t-il si l'utilisateur fournit des données de consommation dans des unités inhabituelles (BTU, gallons) ? L'assistant doit demander une clarification ou convertir.
- Que se passe-t-il si le bloc gauge reçoit un JSON malformé ? Un fallback textuel propre doit s'afficher.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le module ESG DOIT appeler `save_esg_criterion_score` ou `batch_save_esg_criteria` après chaque réponse de l'utilisateur contenant des informations évaluables
- **FR-002**: Le module ESG DOIT rester dans le `esg_scoring_node` pendant toute la durée de l'évaluation (pas de routing vers `profiling_node`)
- **FR-003**: Le module carbone DOIT appeler `save_emission_entry` pour chaque source d'émission identifiée dans la réponse de l'utilisateur
- **FR-004**: Le module financement DOIT appeler `search_compatible_funds` (pas de réponse basée sur les connaissances générales du LLM) quand l'utilisateur demande les financements disponibles
- **FR-005**: Les prompts des modules ESG, carbone et financement DOIVENT contenir une instruction explicite forçant l'utilisation des tools de sauvegarde/recherche
- **FR-006**: Le composant gauge du frontend DOIT rendre un visuel interactif sans rester bloqué sur "Génération du graphique..."
- **FR-007**: L'assistant DOIT signaler l'absence de données au lieu de proposer d'ajouter des entités inexistantes quand l'utilisateur référence une localisation/entité non présente dans son profil
- **FR-008**: Après chaque sauvegarde de critère ESG, l'assistant DOIT afficher la progression (X/30 critères évalués)
- **FR-009**: Après chaque sauvegarde d'entrée carbone, le total cumulé DOIT être mis à jour et visible sur la page /carbon sans refresh manuel

### Key Entities

- **ESG Assessment**: Évaluation contenant 30 critères (E, S, G) avec scores individuels et score global
- **ESG Criterion Score**: Score d'un critère individuel (0-10) avec justification textuelle
- **Carbon Assessment**: Bilan carbone annuel contenant des entrées d'émission par source
- **Emission Entry**: Entrée d'émission (source, quantité, unité, facteur d'émission, tCO2e calculé)
- **Fund**: Fonds de financement vert avec critères d'éligibilité, montants, type d'accès
- **Fund Intermediary**: Intermédiaire bancaire/institutionnel liant une PME à un fonds

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Le test 3.2 du plan de test passe à 4/4 (save_esg_criterion_score appelé, progression affichée, question suivante posée, critère visible sur /esg)
- **SC-002**: Le test 4.2 du plan de test passe à 5/5 (save_emission_entry appelé pour chaque source, calculs corrects, entrées visibles sur /carbon)
- **SC-003**: Le test 5.1 du plan de test passe à 6/6 (search_compatible_funds appelé, fonds BDD affichés avec scores/accès/montants, SUNREF et FNDE présents)
- **SC-004**: Le test 1.5 du plan de test passe à 3/3 (bloc gauge rendu correctement dans le chat)
- **SC-005**: Le test 12.1 du plan de test passe à 2/2 (l'assistant corrige au lieu de proposer d'ajouter)
- **SC-006**: Zéro régression sur les 10 tests déjà PASS (profiling 1.1-1.4, ESG 3.1, carbone 4.1, plan d'action 8.1-8.2, chat 10.1, non-régression 12.2)
- **SC-007**: Le scorecard global atteint au minimum 20/45 tests PASS (contre 10 actuellement)

## Assumptions

- Les tools `save_esg_criterion_score`, `batch_save_esg_criteria`, `save_emission_entry` et `search_compatible_funds` existent déjà et fonctionnent correctement quand ils sont appelés (le bug est dans les prompts/routing, pas dans les tools eux-mêmes)
- Le bug systémique est principalement un problème de prompts LLM insuffisamment directifs pour forcer le tool calling
- Le fix de la branche 015 (tool calling application/credit + timeout ESG) est déjà mergé et fonctionnel
- Le composant gauge frontend existe mais a un bug de rendu (pas un composant manquant)
- La correction des prompts n'impactera pas les performances de réponse du LLM (pas de latence additionnelle significative)
