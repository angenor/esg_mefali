# Feature Specification: Correction des 34 tests en échec

**Feature Branch**: `017-fix-failing-tests`
**Created**: 2026-04-02
**Status**: Draft
**Input**: User description: "Corriger les 34 tests en échec documentés dans documents_et_brouillons/failing-tests-audit.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Correction authentification tests (15 tests) (Priority: P1)

En tant que développeur, je veux que les 15 tests d'authentification (financing status, intermédiaires, préparation fiche) passent correctement en utilisant le mécanisme `dependency_overrides` de FastAPI au lieu de `@patch` pour mocker l'authentification.

**Why this priority**: Ces 15 tests représentent 44% des échecs totaux et partagent une cause racine unique. Un seul fixture partagé les corrige tous.

**Independent Test**: Exécuter les tests financing status, intermediaires et préparation — tous doivent passer avec le status HTTP attendu (200, 404, 409, 422).

**Acceptance Scenarios**:

1. **Given** un fixture auth partagé utilisant `dependency_overrides`, **When** un test financing status envoie une requête, **Then** le endpoint retourne le status HTTP attendu (pas 401)
2. **Given** le fixture auth est actif, **When** un test financing intermédiaires filtre par type/fonds, **Then** les résultats sont retournés avec status 200
3. **Given** le fixture auth est actif, **When** un test financing préparation demande une fiche inexistante, **Then** le endpoint retourne 404 (pas 401)

---

### User Story 2 - Correction state incomplet pour nodes (7 tests) (Priority: P1)

En tant que développeur, je veux que les 7 tests de nodes (financing node + credit node) passent en fournissant un state `ConversationState` complet avec toutes les clés requises.

**Why this priority**: 7 tests impactés, cause racine unique (state dict incomplet). Un fixture partagé corrige les deux catégories.

**Independent Test**: Exécuter les tests financing node et credit node — tous doivent passer sans KeyError.

**Acceptance Scenarios**:

1. **Given** un state complet avec toutes les clés de `ConversationState`, **When** le financing node génère une réponse, **Then** aucune KeyError ne survient
2. **Given** un state complet, **When** le credit node traite un score, **Then** les blocs visuels sont générés correctement
3. **Given** un state complet sans données ESG, **When** le financing node détecte une redirection, **Then** la redirection est effectuée sans erreur

---

### User Story 3 - Correction Form vs JSON dans tests chat (3 tests) (Priority: P2)

En tant que développeur, je veux que les 3 tests chat envoient les données au bon format (Form data) correspondant à ce que l'endpoint attend.

**Why this priority**: 3 tests impactés, correction simple et ciblée.

**Independent Test**: Exécuter les tests chat — les tests de validation (contenu vide, persistance, longueur max) doivent passer.

**Acceptance Scenarios**:

1. **Given** un endpoint attendant Form data, **When** le test envoie des données Form vides, **Then** le endpoint retourne 422 (validation)
2. **Given** le même endpoint, **When** le test envoie un message Form valide, **Then** le message est persisté correctement
3. **Given** le même endpoint, **When** le test envoie un contenu trop long en Form, **Then** la validation de longueur est déclenchée

---

### User Story 4 - Correction mock type dans test application node (1 test) (Priority: P2)

En tant que développeur, je veux que le test application node utilise le bon type de mock (AIMessage au lieu de MagicMock) avec une chaîne async correcte.

**Why this priority**: 1 test impacté, correction ciblée du mock chain async.

**Independent Test**: Exécuter le test application node — doit passer sans AttributeError.

**Acceptance Scenarios**:

1. **Given** un mock LLM correctement chaîné en async, **When** le node application invoque le LLM, **Then** la réponse contient le contenu attendu sans erreur

---

### User Story 5 - Correction WeasyPrint dans tests rapport (6 tests) (Priority: P3)

En tant que développeur, je veux que les 6 tests rapport passent en mockant la dépendance WeasyPrint pour éviter la nécessité de bibliothèques système C.

**Why this priority**: 6 tests impactés. Le mock est préféré pour la portabilité CI/CD.

**Independent Test**: Exécuter les tests report router et report service — tous doivent passer sans bibliothèques C installées.

**Acceptance Scenarios**:

1. **Given** la génération PDF mockée dans les tests, **When** un test génère un rapport, **Then** le mock retourne des données valides sans erreur système
2. **Given** le mock actif, **When** un test vérifie l'isolation utilisateur, **Then** le contrôle d'accès fonctionne correctement (403)

---

### Edge Cases

- Que se passe-t-il si un fixture auth est oublié dans un nouveau test ? Le test échouera avec 401, signal clair du problème.
- Que se passe-t-il si `ConversationState` ajoute de nouvelles clés ? Le fixture doit être mis à jour en conséquence.
- Que se passe-t-il si WeasyPrint est installé localement mais pas en CI ? Le mock garantit la cohérence entre environnements.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le système DOIT fournir un fixture partagé d'authentification utilisant le mécanisme d'override de dépendances pour injecter un utilisateur test
- **FR-002**: Le système DOIT fournir un fixture/helper retournant un state conversationnel complet avec toutes les clés requises à leurs valeurs par défaut
- **FR-003**: Les tests chat DOIVENT envoyer des données Form au lieu de JSON pour correspondre à la signature de l'endpoint
- **FR-004**: Le test application node DOIT utiliser le type de réponse LLM approprié au lieu d'un mock générique, avec une chaîne async correcte
- **FR-005**: Les tests rapport DOIVENT mocker la génération PDF pour éviter la dépendance aux bibliothèques système
- **FR-006**: Aucune régression ne DOIT être introduite sur les 867 tests existants qui passent déjà
- **FR-007**: Les fixtures partagés DOIVENT nettoyer leur état après chaque test

### Key Entities

- **ConversationState**: État du graphe conversationnel contenant toutes les clés de contexte (messages, profil utilisateur, données financement, module actif, etc.)
- **Fixture Auth**: Mécanisme de test qui bypass l'authentification pour permettre aux tests de se concentrer sur la logique métier

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Les 34 tests en échec passent tous (0 échecs restants)
- **SC-002**: La suite complète atteint 901/901 tests (100% pass rate)
- **SC-003**: Aucune régression sur les 867 tests existants
- **SC-004**: Les tests s'exécutent sans dépendance à des bibliothèques système externes

## Assumptions

- Les 34 tests échouent pour les 5 causes racines identifiées dans l'audit (pas d'autres causes cachées)
- La structure de l'état conversationnel est stable et documentée dans le code existant
- L'endpoint chat continuera à utiliser le format Form (pas de migration prévue)
- Les tests existants (867 pass) ne sont pas fragiles et ne casseront pas suite aux ajouts de fixtures
- Le mock de génération PDF est suffisant pour valider la logique métier des rapports
