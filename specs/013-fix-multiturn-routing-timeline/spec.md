# Feature Specification: Correction du Routing Multi-tour LangGraph et du Format Timeline

**Feature Branch**: `013-fix-multiturn-routing-timeline`
**Created**: 2026-04-01
**Status**: Draft
**Input**: Correction de deux bugs : (1) le routeur LangGraph ne maintient pas le contexte du module actif entre les tours de conversation, (2) le composant timeline frontend n'accepte pas les variantes de format generees par le LLM.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Evaluation ESG multi-tour complete (Priority: P1)

Un utilisateur demarre une evaluation ESG via le chat. Le systeme pose des questions critere par critere (E1, E2, S1, etc.). L'utilisateur repond a chaque question avec des details sur ses pratiques. Chaque reponse est correctement interpretee comme une reponse au critere en cours, le score est sauvegarde, et le systeme passe au critere suivant. A la fin, l'evaluation est finalisee avec tous les criteres sauvegardes.

**Why this priority**: C'est le bug principal qui bloque 20+ tests d'integration. Sans routing multi-tour, aucun workflow conversationnel multi-etapes ne fonctionne (ESG, carbone, financement).

**Independent Test**: Peut etre teste en envoyant 5 messages successifs dans un echange ESG et en verifiant que les 5 criteres sont sauvegardes en base.

**Acceptance Scenarios**:

1. **Given** une conversation active sans module en cours, **When** l'utilisateur dit "Je veux faire mon evaluation ESG", **Then** le message est route vers le noeud ESG et une evaluation est creee.
2. **Given** une evaluation ESG en cours avec le critere E1 pose, **When** l'utilisateur repond "On collecte le plastique, on le trie par type PET, HDPE", **Then** le message reste dans le noeud ESG (pas reroute vers chat), le critere E1 est evalue et sauvegarde.
3. **Given** une evaluation ESG en cours, **When** l'utilisateur repond par un message court ("oui", "non", "environ 500L"), **Then** le message reste dans le noeud ESG.
4. **Given** une evaluation ESG avec 5 questions posees et 5 reponses donnees, **When** le dernier critere est evalue, **Then** les 5 criteres sont sauvegardes en base et visibles sur la page ESG.

---

### User Story 2 - Bilan carbone multi-tour (Priority: P1)

Un utilisateur demarre un bilan carbone conversationnel. Le systeme pose des questions par categorie (energie, transport, dechets). L'utilisateur fournit ses donnees de consommation. Chaque reponse est correctement routee vers le noeud carbone et les entrees sont sauvegardees.

**Why this priority**: Meme bug que l'ESG, affecte un autre module critique.

**Independent Test**: Envoyer 3 messages de consommation et verifier les 3 entrees en base.

**Acceptance Scenarios**:

1. **Given** une conversation active, **When** l'utilisateur dit "Je veux faire mon bilan carbone", **Then** le message est route vers le noeud carbone.
2. **Given** un bilan carbone en cours, **When** l'utilisateur repond "On consomme 300L de gasoil par mois", **Then** le message reste dans le noeud carbone et l'entree est sauvegardee.
3. **Given** un bilan carbone avec 3 entrees successives, **Then** les 3 entrees sont sauvegardees en base et visibles sur la page carbone.

---

### User Story 3 - Changement de module en cours de session (Priority: P2)

Pendant un workflow actif (ESG, carbone), l'utilisateur decide de changer de sujet. Le systeme detecte la demande de changement, suspend le module actif (sans perdre la progression), et route vers le nouveau module ou le chat general.

**Why this priority**: Essentiel pour l'experience utilisateur fluide, mais secondaire par rapport au fonctionnement de base du multi-tour.

**Independent Test**: Demarrer un bilan carbone, dire "Parlons de financement", verifier que le routing bascule vers le noeud financement.

**Acceptance Scenarios**:

1. **Given** un bilan carbone en cours, **When** l'utilisateur dit "Parlons plutot de financement", **Then** le module carbone est suspendu (reste in_progress en base), le message est route vers le noeud financement.
2. **Given** une evaluation ESG en cours, **When** l'utilisateur dit "Stop, je veux parler d'autre chose", **Then** le module ESG est suspendu et le message est route vers le chat general.
3. **Given** une evaluation ESG en cours, **When** l'utilisateur dit "Merci, au revoir", **Then** le module ESG est suspendu et le message est route vers le chat general.

---

### User Story 4 - Reprise de module apres interruption (Priority: P2)

Apres avoir quitte un module sans le finaliser, l'utilisateur peut y revenir plus tard. Le systeme retrouve la session en cours et reprend la ou elle s'etait arretee.

**Why this priority**: Ameliore significativement l'experience utilisateur pour les workflows longs.

**Independent Test**: Quitter un ESG en cours, envoyer un message general, puis dire "Continuons l'ESG" et verifier la reprise.

**Acceptance Scenarios**:

1. **Given** une evaluation ESG suspendue (in_progress en base), **When** l'utilisateur dit "Continuons l'evaluation ESG", **Then** le noeud ESG retrouve l'evaluation in_progress et reprend au prochain critere non evalue.
2. **Given** un bilan carbone suspendu, **When** l'utilisateur dit "On reprend le bilan carbone", **Then** le noeud carbone reprend avec les entrees deja collectees.

---

### User Story 5 - Recherche de financement multi-tour (Priority: P2)

Un utilisateur demande des financements compatibles. Le systeme recherche via les outils (search_compatible_funds) et pose des questions de suivi. Les reponses restent dans le noeud financement.

**Why this priority**: Meme bug multi-tour, mais le financement a moins de questions sequentielles que ESG/carbone.

**Independent Test**: Dire "Quels financements pour moi ?", verifier que search_compatible_funds est appele, puis repondre "Oui le SUNREF m'interesse" et verifier que le message reste dans le noeud financement.

**Acceptance Scenarios**:

1. **Given** une conversation active, **When** l'utilisateur dit "Quels financements pour moi ?", **Then** le noeud financement appelle search_compatible_funds (pas une reponse memorisee).
2. **Given** un module financement actif, **When** l'utilisateur dit "Oui le SUNREF m'interesse", **Then** le message reste dans le noeud financement.

---

### User Story 6 - Affichage correct des blocs timeline (Priority: P3)

Quand le systeme genere une frise chronologique (plan d'action, parcours financement), le composant frontend l'affiche correctement quel que soit le format exact genere par le LLM (events ou phases).

**Why this priority**: Bug d'affichage uniquement, n'affecte pas les donnees ni la logique metier.

**Independent Test**: Generer un bloc timeline et verifier l'affichage, puis simuler un bloc avec "phases" au lieu de "events" et verifier qu'il s'affiche aussi.

**Acceptance Scenarios**:

1. **Given** un message contenant un bloc timeline avec le format {"events": [...]}, **When** le composant le parse, **Then** la frise s'affiche correctement.
2. **Given** un message contenant un bloc timeline avec le format {"phases": [...]}, **When** le composant le parse, **Then** la frise s'affiche correctement (phases traite comme alias de events).
3. **Given** un message contenant un bloc timeline avec des variantes de noms de champs ("period" au lieu de "date", "label" au lieu de "title"), **When** le composant le parse, **Then** les champs sont correctement interpretes.
4. **Given** un message contenant un bloc timeline sans "events" ni "phases", **When** le composant le parse, **Then** un message d'erreur explicite est affiche.

---

### Edge Cases

- Que se passe-t-il si l'utilisateur envoie un message vide ou uniquement des emojis pendant un module actif ? Le message reste dans le module actif (defaut le plus sur).
- Que se passe-t-il si deux evaluations ESG in_progress existent pour la meme entreprise ? Le systeme reprend la plus recente.
- Que se passe-t-il si le LLM de classification du changement de sujet echoue (timeout, erreur) ? Le message reste dans le module actif par defaut (securite).
- Que se passe-t-il si le bloc timeline contient du JSON invalide ? Le composant affiche un message d'erreur sans crash.
- Que se passe-t-il si un noeud specialiste est appele mais qu'il n'y a pas de session active ni de demande de creation ? Le noeud cree une nouvelle session.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le systeme DOIT maintenir un indicateur de "module actif" entre les tours de conversation, representant le noeud specialiste en cours d'utilisation.
- **FR-002**: Le systeme DOIT stocker des donnees contextuelles du module actif (identifiant de session, progression) entre les tours de conversation.
- **FR-003**: Le routeur DOIT prioriser le module actif sur la classification du message : si un module est actif et que le message n'est pas un changement de sujet explicite, le message est route vers le module actif.
- **FR-004**: Le routeur DOIT detecter les demandes explicites de changement de sujet quand un module est actif, en utilisant une classification binaire (continuation vs changement).
- **FR-005**: En cas de doute sur le changement de sujet, le systeme DOIT rester dans le module actif (defaut securitaire).
- **FR-006**: Chaque noeud specialiste DOIT activer le module correspondant quand il demarre une session (evaluation ESG, bilan carbone, recherche financement, etc.).
- **FR-007**: Chaque noeud specialiste DOIT desactiver le module quand il finalise une session.
- **FR-008**: Quand l'utilisateur quitte un module sans finaliser, le systeme DOIT suspendre le module (in_progress en base) sans perte de donnees.
- **FR-009**: Quand l'utilisateur demande de reprendre un module suspendu, le systeme DOIT retrouver la session in_progress et reprendre au point d'arret.
- **FR-010**: La transition directe entre modules DOIT etre supportee (ex: carbone vers financement sans passer par l'etat neutre).
- **FR-011**: Le composant d'affichage timeline DOIT accepter "phases" comme alias de "events" dans les donnees JSON.
- **FR-012**: Le composant timeline DOIT accepter les variantes de noms de champs : "period"/"timeframe" pour "date", "name"/"label" pour "title", "state" pour "status", "details"/"content" pour "description".
- **FR-013**: Si le statut est absent dans un evenement timeline, le systeme DOIT utiliser "todo" par defaut.
- **FR-014**: Les instructions de generation du LLM DOIVENT specifier le format "events" comme format canonique pour les blocs timeline.
- **FR-015**: Aucune regression ne DOIT etre introduite sur les tests existants (profiling, plan d'action, dashboard, etc.).

### Key Entities

- **Module Actif (Active Module)**: Indicateur du noeud specialiste en cours d'utilisation dans une conversation. Valeurs possibles : null, esg_scoring, carbon, financing, application, credit, profiling, document.
- **Donnees Module Actif (Active Module Data)**: Contexte du module en cours : identifiant de session (assessment_id), progression (criteres restants, entrees collectees), derniere question posee.
- **Evenement Timeline**: Un element d'une frise chronologique avec date/periode, titre, statut (done/in_progress/todo) et description optionnelle.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un echange ESG de 5 questions-reponses successives sauvegarde les 5 criteres en base, visibles sur la page de resultats ESG.
- **SC-002**: Un echange carbone de 3 entrees successives sauvegarde les 3 entrees en base, visibles sur la page de resultats carbone.
- **SC-003**: Une demande de financement declenche une recherche active de fonds compatibles (pas une reponse de memoire).
- **SC-004**: Un changement de sujet en milieu de module est detecte et le routing bascule correctement dans 100% des cas de changement explicite.
- **SC-005**: Une reprise de module apres interruption fonctionne : le systeme retrouve la session et reprend au bon endroit.
- **SC-006**: Les blocs timeline s'affichent correctement quel que soit le format LLM (events ou phases).
- **SC-007**: Zero regression sur les 14 tests qui passaient avant cette correction.
- **SC-008**: Les messages courts ("oui", "non", "environ 500L") pendant un module actif restent dans le module actif dans 100% des cas.

## Assumptions

- Le routeur actuel fonctionne correctement pour le premier message (classification initiale). Seul le multi-tour est casse.
- L'etat de la conversation (ConversationState) est maintenu entre les appels au graphe LangGraph pour une meme conversation.
- Le LLM de classification (changement de sujet vs continuation) est suffisamment fiable pour une classification binaire simple.
- Les sessions in_progress existantes en base de donnees sont correctement requetables par entreprise et par type de module.
- Le composant TimelineBlock.vue est le seul composant qui parse les blocs timeline cote frontend.
- Les prompts systeme des noeuds specialistes sont centralises dans des fichiers ou constantes modifiables.
