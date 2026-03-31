# Feature Specification: Evaluation et Scoring ESG Contextualise

**Feature Branch**: `005-esg-scoring-assessment`
**Created**: 2026-03-31
**Status**: Draft
**Input**: Modules 2.2 (Grille d'Evaluation ESG) et 2.3 (Scoring ESG Dynamique) — module metier central de la plateforme ESG Mefali.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Evaluation ESG conversationnelle (Priority: P1)

En tant que dirigeant de PME africaine, je veux repondre a des questions adaptees a mon secteur d'activite pour obtenir un score ESG detaille sur les 3 piliers (Environnement, Social, Gouvernance), afin de connaitre ma position et mes axes d'amelioration.

**Why this priority**: C'est la fonctionnalite coeur du module. Sans evaluation conversationnelle, aucun scoring ni recommandation n'est possible. C'est le MVP minimum.

**Independent Test**: Peut etre teste en demarrant une evaluation ESG via le chat, en repondant aux questions de Claude pilier par pilier, et en verifiant que les scores partiels et le score global sont calcules correctement.

**Acceptance Scenarios**:

1. **Given** un utilisateur avec un profil entreprise renseigne (secteur, taille, pays), **When** il demande "Je veux evaluer mon entreprise sur les criteres ESG", **Then** le systeme demarre une evaluation conversationnelle avec des questions adaptees a son secteur.
2. **Given** une evaluation en cours sur le pilier Environnement, **When** l'utilisateur repond aux questions E1 a E10, **Then** le systeme affiche un bloc `progress` avec les scores des 10 criteres environnementaux et passe au pilier Social.
3. **Given** les 3 piliers evalues (30 criteres), **When** l'evaluation est terminee, **Then** le systeme affiche dans le chat : un radar chart (3 piliers), une jauge du score global (0-100), et un tableau de recommandations priorisees.
4. **Given** un utilisateur dont le profil est incomplet (secteur manquant), **When** il demande une evaluation ESG, **Then** le systeme redirige vers le profilage pour completer les informations necessaires avant de commencer.

---

### User Story 2 - Page de resultats ESG persistante (Priority: P2)

En tant qu'utilisateur, je veux consulter les resultats detailles de mon evaluation ESG sur une page dediee (hors chat), avec des graphiques interactifs et mes recommandations, afin de pouvoir y revenir et les partager.

**Why this priority**: Le chat donne les resultats en temps reel, mais la page persistante permet la consultation ulterieure, la navigation dans les details, et la comparaison dans le temps.

**Independent Test**: Peut etre teste en accedant a la page /esg/results apres une evaluation completee, et en verifiant la presence de tous les elements visuels (score global, radar, barres de progression, recommandations).

**Acceptance Scenarios**:

1. **Given** une evaluation ESG completee, **When** l'utilisateur accede a la page de resultats, **Then** il voit le score global dans un cercle de progression colore (vert >70, orange 40-70, rouge <40).
2. **Given** une evaluation completee, **When** l'utilisateur consulte la page resultats, **Then** il voit un radar chart avec les 3 piliers E, S, G et des barres de progression detaillees pour chaque critere (30 criteres).
3. **Given** une evaluation completee, **When** l'utilisateur consulte la section recommandations, **Then** il voit ses points forts (badges verts) et ses axes d'amelioration classes par priorite.
4. **Given** aucune evaluation existante, **When** l'utilisateur accede a la page ESG, **Then** il voit un ecran d'invitation "Commencez votre evaluation ESG" avec un bouton pour demarrer.

---

### User Story 3 - Evaluation documentaire via RAG (Priority: P2)

En tant qu'utilisateur ayant uploade des documents (rapports RSE, politiques internes, certifications), je veux que l'evaluation ESG prenne en compte ces documents pour affiner les scores, afin d'obtenir une evaluation plus precise sans tout ressaisir manuellement.

**Why this priority**: Le RAG enrichit considerablement la qualite de l'evaluation en exploitant les documents deja analyses (feature 004). C'est un differenciateur cle de la plateforme.

**Independent Test**: Peut etre teste en uploadant un rapport RSE, puis en lancant une evaluation ESG et en verifiant que le systeme cite des elements du document dans ses questions et son scoring.

**Acceptance Scenarios**:

1. **Given** des documents analyses contenant des informations environnementales, **When** le systeme evalue le pilier Environnement, **Then** il retrouve et utilise les informations pertinentes des documents pour pre-remplir ou ajuster les scores.
2. **Given** un document certifiant une norme ISO 14001, **When** le critere "Politique environnementale" est evalue, **Then** le systeme attribue un score plus eleve en citant la certification trouvee dans les documents.

---

### User Story 4 - Benchmarking sectoriel (Priority: P3)

En tant que dirigeant de PME, je veux voir comment mon entreprise se positionne par rapport aux autres entreprises de mon secteur, afin de comprendre mes forces et faiblesses relatives.

**Why this priority**: Le benchmark ajoute du contexte aux scores mais necessite des donnees de reference. Fonctionnel meme avec des moyennes sectorielles predefinies.

**Independent Test**: Peut etre teste en consultant le benchmark apres une evaluation, et en verifiant que le graphique comparatif affiche le score de l'entreprise vs la moyenne sectorielle.

**Acceptance Scenarios**:

1. **Given** une evaluation completee pour une entreprise du secteur "agriculture", **When** l'utilisateur consulte le benchmark, **Then** il voit un graphique en barres comparant ses scores E, S, G aux moyennes du secteur agriculture.
2. **Given** une evaluation completee, **When** le benchmark est affiche dans le chat, **Then** un bloc `chart` (bar) montre la position relative de l'entreprise.

---

### User Story 5 - Historique des evaluations (Priority: P3)

En tant qu'utilisateur, je veux voir l'evolution de mon score ESG au fil du temps, afin de mesurer mes progres.

**Why this priority**: L'historique n'est utile qu'apres plusieurs evaluations. C'est une fonctionnalite de retention a long terme.

**Independent Test**: Peut etre teste en ayant au moins 2 evaluations completees et en verifiant que le graphique d'evolution affiche les scores dans le temps.

**Acceptance Scenarios**:

1. **Given** au moins 2 evaluations completees a des dates differentes, **When** l'utilisateur consulte l'historique, **Then** il voit un graphique d'evolution du score global dans le temps.
2. **Given** une seule evaluation existante, **When** l'utilisateur consulte l'historique, **Then** il voit un point unique avec un message indiquant qu'un historique sera disponible apres la prochaine evaluation.

---

### Edge Cases

- Que se passe-t-il si l'utilisateur abandonne l'evaluation en cours (ferme le navigateur, change de page) ? L'evaluation est sauvegardee en statut "draft" et peut etre reprise.
- Que se passe-t-il si l'utilisateur donne des reponses incoherentes (ex: dit "zero emission" mais travaille dans le transport diesel) ? Le systeme signale l'incoherence et demande confirmation.
- Que se passe-t-il si aucun document n'a ete uploade ? L'evaluation se base uniquement sur les reponses conversationnelles, sans composante RAG.
- Que se passe-t-il si le secteur de l'entreprise n'est pas dans les benchmarks disponibles ? Le systeme utilise une moyenne generale et indique qu'un benchmark sectoriel specifique n'est pas encore disponible.
- Que se passe-t-il si l'utilisateur modifie son profil (changement de secteur) apres une evaluation ? Les evaluations passees conservent leur contexte sectoriel d'origine. Une nouvelle evaluation utilise le nouveau secteur.

## Requirements *(mandatory)*

### Functional Requirements

**Grille d'evaluation (30 criteres)**

- **FR-001**: Le systeme DOIT evaluer les entreprises sur 30 criteres ESG repartis en 3 piliers de 10 criteres chacun (Environnement E1-E10, Social S1-S10, Gouvernance G1-G10).
- **FR-002**: Chaque critere DOIT etre note de 0 a 10, les scores par pilier de 0 a 100 (somme des criteres), et le score global de 0 a 100 (moyenne ponderee des piliers).
- **FR-003**: Les questions posees lors de l'evaluation DOIVENT etre adaptees au secteur d'activite de l'entreprise (ex: criteres energetiques differents pour agriculture vs. industrie).
- **FR-004**: Le systeme DOIT ponderer les criteres en fonction du secteur (ex: "Gestion de l'eau" pese plus pour l'agriculture que pour les services numeriques).

**Evaluation conversationnelle**

- **FR-005**: Le systeme DOIT conduire l'evaluation sous forme de conversation, pilier par pilier, en posant des questions contextualisees.
- **FR-006**: A la fin de chaque pilier, le systeme DOIT afficher un bloc `progress` dans le chat montrant les scores des criteres evalues.
- **FR-007**: A la fin de l'evaluation complete, le systeme DOIT afficher dans le chat : un bloc `chart` (radar) des 3 piliers, un bloc `gauge` du score global, et un bloc `table` des recommandations.
- **FR-008**: Le systeme DOIT pouvoir reprendre une evaluation interrompue (statut "draft") la ou elle s'etait arretee.
- **FR-009**: Le systeme DOIT rediriger vers le profilage si des informations de profil essentielles manquent (secteur, pays, taille).

**Evaluation documentaire (RAG)**

- **FR-010**: Le systeme DOIT utiliser les documents analyses pour retrouver les informations pertinentes et enrichir l'evaluation.
- **FR-011**: Le systeme DOIT citer les sources documentaires utilisees pour justifier les scores attribues.

**Scoring et resultats**

- **FR-012**: Le systeme DOIT persister les resultats d'evaluation : scores par critere, scores par pilier, score global, recommandations, points forts, lacunes.
- **FR-013**: Le systeme DOIT generer des recommandations priorisees basees sur les lacunes identifiees.
- **FR-014**: Le systeme DOIT classer le score global avec un code couleur : vert (>70), orange (40-70), rouge (<40).

**Benchmarking**

- **FR-015**: Le systeme DOIT fournir un benchmark sectoriel comparant les scores de l'entreprise aux moyennes de son secteur.
- **FR-016**: Le benchmark DOIT etre affiche dans le chat (bloc `chart` bar) et sur la page de resultats.

**Page de resultats**

- **FR-017**: La page ESG DOIT afficher un ecran d'invitation si aucune evaluation n'existe.
- **FR-018**: La page de resultats DOIT afficher : score global (cercle colore), radar chart (3 piliers), barres de progression (30 criteres), points forts, recommandations, benchmark sectoriel.
- **FR-019**: La page DOIT afficher un historique des scores sous forme de graphique d'evolution temporelle.

**Endpoints**

- **FR-020**: Le systeme DOIT exposer des endpoints pour : creation d'evaluation, liste des evaluations, detail d'une evaluation, lancement/continuation de l'evaluation conversationnelle, score detaille, benchmark sectoriel.

### Key Entities

- **ESGAssessment** : Represente une evaluation ESG complete. Attributs : identifiant, utilisateur, version, statut (brouillon/complete), scores (global, E, S, G), donnees d'evaluation detaillees, recommandations, points forts, lacunes, benchmark sectoriel, date de creation.
- **ESG Criteria (E1-E10, S1-S10, G1-G10)** : Les 30 criteres d'evaluation, chacun avec un code, un libelle, une description, une ponderation sectorielle, et un score (0-10).
- **Sector Benchmark** : Donnees de reference par secteur contenant les moyennes E, S, G pour comparaison.
- **Sector Weights** : Ponderations des criteres par secteur d'activite, determinant l'importance relative de chaque critere.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un utilisateur peut completer une evaluation ESG en moins de 20 minutes via la conversation.
- **SC-002**: Les scores calcules refletent correctement les reponses de l'utilisateur avec une ponderation sectorielle coherente (un auditeur peut verifier le calcul).
- **SC-003**: L'utilisateur voit des visuels intermediaires (barres de progression) apres chaque pilier evalue, rendant le processus engageant et transparent.
- **SC-004**: Les resultats sont accessibles a tout moment sur la page dediee, avec tous les graphiques et recommandations, dans un delai inferieur a 3 secondes.
- **SC-005**: Le systeme retrouve et utilise les informations pertinentes des documents uploades pour enrichir au moins 50% des criteres evalues (quand des documents sont disponibles).
- **SC-006**: Le benchmark sectoriel permet a l'utilisateur de comprendre sa position relative en un coup d'oeil.
- **SC-007**: 80% des recommandations generees sont actionnables et specifiques au contexte de l'entreprise (pas de conseils generiques).

## Assumptions

- Le profil entreprise (secteur, pays, taille) est deja renseigne via la feature 003 (profilage). Si incomplet, le systeme redirige vers le profilage.
- Les documents pertinents sont deja uploades et analyses via la feature 004 (upload/analyse documents). L'evaluation fonctionne aussi sans documents (mode conversationnel pur).
- Les blocs visuels du chat (`progress`, `chart`, `gauge`, `table`, `mermaid`) sont deja implementes via la feature 002 (chat rich visuals).
- Les benchmarks sectoriels sont initialises avec des donnees de reference predefinies pour les secteurs principaux de la zone UEMOA/CEDEAO (agriculture, energie, recyclage, transport, services, industrie).
- La ponderation sectorielle des criteres est definie comme donnees de configuration. Les ponderations par defaut sont fournies si aucune configuration sectorielle specifique n'existe.
- L'evaluation se fait en francais, adaptee au contexte des PME africaines francophones.
- Le systeme conversationnel existant (features 001-002) gere le routage et la gestion de l'etat.
