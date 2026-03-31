# Feature Specification: Scoring de Credit Vert Alternatif

**Feature Branch**: `010-green-credit-scoring`
**Created**: 2026-03-31
**Status**: Draft
**Input**: Module 5 - Scoring de credit vert alternatif avec integration des interactions intermediaires financiers comme signal de serieux

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generation du score de credit vert (Priority: P1)

En tant que dirigeant de PME africaine, je veux obtenir un score de credit vert alternatif base sur l'ensemble de mes donnees (profil, ESG, carbone, candidatures, interactions intermediaires) pour evaluer ma credibilite aupres des bailleurs de fonds verts.

**Why this priority**: Le score combine est la valeur centrale du module. Sans lui, aucune autre fonctionnalite n'a de sens. Il permet aux PME qui n'ont pas d'historique bancaire classique d'obtenir une evaluation de credit basee sur des donnees alternatives.

**Independent Test**: Peut etre teste en generant un score pour un utilisateur ayant complete son profil, une evaluation ESG, un bilan carbone et des candidatures. Le score combine, les sous-scores solvabilite et impact vert, et le niveau de confiance doivent etre retournes.

**Acceptance Scenarios**:

1. **Given** un utilisateur avec un profil complet, un score ESG de 72/100, un bilan carbone et 2 candidatures aux fonds, **When** il demande la generation de son score de credit vert, **Then** le systeme calcule un score combine sur 100 avec un sous-score solvabilite et un sous-score impact vert, chacun detaille par facteur.
2. **Given** un utilisateur avec peu de donnees (profil incomplet, pas d'ESG), **When** il demande la generation de son score, **Then** le systeme genere un score avec un niveau de confiance "faible" et indique les donnees manquantes pour ameliorer la fiabilite.
3. **Given** un utilisateur qui a contacte un intermediaire SUNREF et soumis un dossier via cet intermediaire, **When** son score est calcule, **Then** son sous-facteur "Engagement et serieux" est significativement plus eleve que celui d'un utilisateur n'ayant aucune interaction intermediaire.

---

### User Story 2 - Consultation du detail et des facteurs du score (Priority: P1)

En tant que dirigeant de PME, je veux consulter le detail de mon score de credit vert avec la decomposition par facteur pour comprendre mes forces et faiblesses et savoir comment ameliorer mon profil.

**Why this priority**: La transparence du score est essentielle pour la confiance et l'adoption. Les utilisateurs doivent comprendre pourquoi ils ont tel score et quelles actions entreprendre.

**Independent Test**: Apres generation d'un score, l'utilisateur accede a la page de detail qui affiche les jauges, le radar des facteurs, les sources de donnees et les recommandations d'amelioration.

**Acceptance Scenarios**:

1. **Given** un score de credit vert genere, **When** l'utilisateur consulte la page de detail, **Then** il voit une jauge circulaire du score combine, deux jauges secondaires (solvabilite, impact vert), le niveau de confiance, et un graphique radar des facteurs.
2. **Given** un score avec des interactions intermediaires, **When** l'utilisateur consulte le detail des facteurs, **Then** le facteur "Engagement et serieux" mentionne explicitement les intermediaires contactes et les dossiers soumis.
3. **Given** un score perfectible, **When** l'utilisateur consulte les recommandations, **Then** il voit des actions concretes d'amelioration incluant "Contactez un intermediaire pour ameliorer votre score" si pertinent.

---

### User Story 3 - Affichage conversationnel du score dans le chat (Priority: P2)

En tant qu'utilisateur du chatbot ESG, je veux pouvoir demander mon score de credit vert dans la conversation et voir des visualisations (jauges, radar) directement dans le chat pour une experience integree.

**Why this priority**: L'integration conversationnelle est le mode d'interaction principal de la plateforme. Le score doit etre accessible via le chat comme tous les autres modules.

**Independent Test**: L'utilisateur demande "Quel est mon score de credit vert ?" dans le chat et recoit une reponse avec des blocs visuels (jauge, radar, progression, parcours).

**Acceptance Scenarios**:

1. **Given** un utilisateur dans le chat ayant des donnees suffisantes, **When** il demande son score de credit vert, **Then** le chatbot affiche le score global via un bloc jauge, le detail via un radar, la couverture des sources via un bloc progression, et un parcours d'amelioration via un diagramme.
2. **Given** un utilisateur sans score genere, **When** il demande son score dans le chat, **Then** le chatbot propose de lancer la generation et explique les donnees necessaires.

---

### User Story 4 - Historique et evolution du score (Priority: P2)

En tant que dirigeant de PME, je veux suivre l'evolution de mon score de credit vert dans le temps pour mesurer l'impact de mes actions d'amelioration ESG et de mes demarches aupres des bailleurs.

**Why this priority**: Le suivi temporel motive l'amelioration continue et montre la valeur des actions entreprises par l'utilisateur.

**Independent Test**: Un utilisateur ayant genere plusieurs versions de son score voit un graphique d'evolution temporelle et peut comparer les versions.

**Acceptance Scenarios**:

1. **Given** un utilisateur avec 3 versions de score sur 6 mois, **When** il consulte l'historique, **Then** il voit un graphique lineaire montrant l'evolution du score combine et des sous-scores.
2. **Given** un utilisateur avec un seul score, **When** il consulte l'historique, **Then** le systeme affiche le score actuel et indique qu'un historique sera disponible apres la prochaine generation.

---

### User Story 5 - Attestation PDF du score (Priority: P3)

En tant que dirigeant de PME, je veux telecharger une attestation PDF de mon score de credit vert pour la presenter aux bailleurs de fonds et intermediaires financiers comme preuve de ma credibilite verte.

**Why this priority**: Le document PDF est utile pour les demarches externes mais n'est pas bloquant pour l'utilisation quotidienne de la plateforme.

**Independent Test**: L'utilisateur clique sur "Telecharger l'attestation" et recoit un PDF contenant le score, les sous-scores, le niveau de confiance, la date de validite et un resume des facteurs.

**Acceptance Scenarios**:

1. **Given** un score de credit vert genere et valide, **When** l'utilisateur demande l'attestation PDF, **Then** un document PDF est genere avec le score combine, les sous-scores, le niveau de confiance, la date de generation, la date de validite, et le detail des principaux facteurs.
2. **Given** un score expire ou inexistant, **When** l'utilisateur demande l'attestation, **Then** le systeme l'invite a regenerer son score avant de pouvoir telecharger l'attestation.

---

### Edge Cases

- Que se passe-t-il si l'utilisateur n'a aucune donnee (profil vide, pas d'ESG, pas de carbone) ? Le systeme genere un score minimal avec confiance "tres faible" et liste les etapes pour commencer.
- Que se passe-t-il si le score ESG est en cours d'evaluation (non finalise) ? Le systeme utilise les donnees partielles disponibles et ajuste le niveau de confiance a la baisse.
- Que se passe-t-il si un utilisateur a contacte un intermediaire mais que le dossier est rejete ? Le signal "engagement" reste positif (la demarche compte), mais le facteur "projets verts en cours" n'est pas bonifie.
- Que se passe-t-il si deux generations de score sont demandees simultanement ? Le systeme traite la premiere et bloque la seconde avec un message d'attente.
- Que se passe-t-il si les donnees ont change depuis la derniere generation ? Le systeme notifie l'utilisateur qu'une mise a jour du score est recommandee.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le systeme DOIT calculer un score de solvabilite sur 100 base sur 5 facteurs : regularite d'activite (20%), coherence des informations (20%), gouvernance (20%), transparence financiere (20%), engagement et serieux (20%).
- **FR-002**: Le sous-facteur "Engagement et serieux" DOIT integrer les interactions avec les intermediaires financiers : nombre d'intermediaires contactes, rendez-vous pris, dossiers soumis via intermediaire. Un utilisateur ayant soumis un dossier via intermediaire DOIT avoir un score d'engagement superieur a un utilisateur sans interaction.
- **FR-003**: Le systeme DOIT calculer un score d'impact vert sur 100 base sur 4 facteurs : score ESG global (40%), tendance ESG (20%), engagement carbone (20%), projets verts en cours (20%).
- **FR-004**: Le sous-facteur "Projets verts en cours" DOIT prendre en compte le statut des candidatures via intermediaire. Un dossier "soumis a l'intermediaire" DOIT peser plus qu'un simple statut "interesse".
- **FR-005**: Le score combine DOIT etre calcule comme : (solvabilite x 0.5) + (impact_vert x 0.5), ajuste par un coefficient de confiance.
- **FR-006**: Le niveau de confiance DOIT refleter la couverture et la qualite des donnees disponibles (nombre de sources, completude du profil, anciennete des donnees).
- **FR-007**: Le systeme DOIT conserver l'historique des scores avec versioning pour permettre le suivi de l'evolution temporelle.
- **FR-008**: Le systeme DOIT generer une attestation PDF du score contenant : score combine, sous-scores, niveau de confiance, date de generation, date de validite, et resume des facteurs principaux.
- **FR-009**: Le chatbot DOIT afficher le score via des blocs visuels dans la conversation : jauge (score global + sous-scores), radar (facteurs), progression (couverture sources), diagramme (parcours amelioration), graphique lineaire (historique).
- **FR-010**: Le systeme DOIT fournir des recommandations d'amelioration personnalisees, incluant la suggestion de contacter un intermediaire financier quand pertinent.
- **FR-011**: Le systeme DOIT empecher la generation simultanee de deux scores pour le meme utilisateur.
- **FR-012**: Le detail des facteurs DOIT mentionner explicitement les interactions intermediaires de l'utilisateur (intermediaires contactes, rendez-vous, dossiers soumis).

### Key Entities

- **Score de Credit Vert**: Evaluation globale d'un utilisateur combinant solvabilite et impact vert. Attributs principaux : score combine, score solvabilite, score impact vert, decomposition par facteur, sources de donnees utilisees, niveau de confiance, date de generation, date de validite. Versionne pour historique.
- **Point de Donnees Credit**: Donnee unitaire alimentant le calcul du score. Attributs : categorie (solvabilite/impact), valeur, poids dans le calcul, statut de verification, source d'origine. Lie a un utilisateur.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Le score de credit vert est genere en moins de 10 secondes pour un utilisateur ayant des donnees completes.
- **SC-002**: Un utilisateur ayant contacte un intermediaire et soumis un dossier obtient un score "Engagement et serieux" au moins 30% superieur a un utilisateur sans aucune interaction intermediaire, toutes autres donnees etant egales.
- **SC-003**: Le detail des facteurs affiche les interactions intermediaires de facon explicite et comprehensible pour l'utilisateur.
- **SC-004**: L'attestation PDF se genere en moins de 5 secondes et contient toutes les informations requises.
- **SC-005**: Les visualisations conversationnelles (jauges, radar) s'affichent correctement dans le chat en reponse a une demande de score.
- **SC-006**: Un utilisateur peut consulter l'evolution de son score sur au moins 3 versions historiques.
- **SC-007**: 90% des utilisateurs comprennent comment ameliorer leur score grace aux recommandations affichees (mesure par les actions entreprises suite aux recommandations).

## Assumptions

- Les features 001 a 009 sont implementees et fonctionnelles, fournissant les donnees necessaires au calcul (profil entreprise, score ESG, bilan carbone, candidatures aux fonds, interactions intermediaires).
- Le state LangGraph contient toutes les donnees necessaires, y compris les intermediaires contactes, les rendez-vous pris et les dossiers soumis via intermediaire.
- Le score de credit vert est un indicateur interne a la plateforme, non reglemente. Il ne constitue pas un score de credit officiel au sens bancaire.
- La validite du score est de 6 mois par defaut, apres quoi une regeneration est recommandee.
- Le coefficient de confiance varie de 0.5 (donnees tres partielles) a 1.0 (couverture complete) et module le score final.
- L'attestation PDF est un document informatif, pas un certificat officiel.
- Le systeme de generation PDF existant (WeasyPrint) est reutilise pour l'attestation.
