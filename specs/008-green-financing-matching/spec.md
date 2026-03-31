# Feature Specification: Financements Verts - BDD, Matching & Parcours d'Acces

**Feature Branch**: `008-green-financing-matching`
**Created**: 2026-03-31
**Status**: Draft
**Input**: Base de donnees des financements verts, matching intelligent, et parcours d'acces via intermediaires (Modules 3.1 & 3.2)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Decouvrir les financements verts recommandes (Priority: P1)

En tant que dirigeant de PME africaine, je veux voir les fonds verts les plus compatibles avec mon profil entreprise, afin de savoir immediatement quels financements cibler.

Le systeme utilise le profil entreprise, le score ESG et les donnees carbone deja collectes pour calculer un score de compatibilite (0-100) avec chaque fonds. Les resultats sont tries par pertinence et presentes avec un badge clair indiquant si l'acces est direct ou via un intermediaire.

**Why this priority**: C'est la proposition de valeur fondamentale du module. Sans recommandations personnalisees, le reste du module n'a pas de sens.

**Independent Test**: Peut etre teste en creant un profil PME avec score ESG et donnees carbone, puis en verifiant que les fonds recommandes correspondent au secteur, a la taille et a la localisation de l'entreprise.

**Acceptance Scenarios**:

1. **Given** un utilisateur avec un profil entreprise complet (secteur agriculture, Abidjan, CA 500M FCFA, score ESG 65/100), **When** il accede a la page des financements, **Then** il voit une liste de fonds tries par compatibilite avec score, badge d'acces (direct/intermediaire), montant eligible et timeline estimee.
2. **Given** un utilisateur sans score ESG, **When** il demande des recommandations de financement, **Then** le systeme le redirige vers l'evaluation ESG avant de continuer.
3. **Given** un utilisateur avec profil complet, **When** il consulte les recommandations, **Then** chaque fonds affiche un badge colore : vert ("Acces direct"), bleu ("Via intermediaire"), ou orange ("Mixte").

---

### User Story 2 - Comprendre le parcours d'acces a un fonds via intermediaire (Priority: P1)

En tant que dirigeant de PME, je veux comprendre exactement comment acceder a un fonds qui necessite un intermediaire, avec les etapes concretes, les noms des intermediaires disponibles dans ma ville, et leurs coordonnees.

**Why this priority**: C'est la valeur differenciante critique de cette feature. La plupart des PME africaines ne savent pas que les fonds internationaux ne sont pas accessibles directement. Sans cette information, le matching est inutile.

**Independent Test**: Peut etre teste en consultant le detail du fonds SUNREF et en verifiant que les banques partenaires (SIB, SGBCI, Banque Atlantique CI, Bridge Bank CI) apparaissent avec adresses et contacts, accompagnees d'un diagramme visuel du parcours.

**Acceptance Scenarios**:

1. **Given** un utilisateur a Abidjan consultant le fonds SUNREF, **When** il ouvre le detail du fonds, **Then** il voit l'explication "Ce fonds n'accepte pas les candidatures directes", la liste des banques partenaires avec adresses/contacts, et un diagramme du parcours (PME -> Banque partenaire -> Consultant SUNREF -> Pret bonifie).
2. **Given** un utilisateur consultant le FNDE (acces direct), **When** il ouvre le detail, **Then** il voit "Vous pouvez candidater directement" avec les etapes simples et aucun intermediaire n'est affiche.
3. **Given** un utilisateur consultant un fonds a acces mixte (BOAD Ligne Verte), **When** il ouvre le detail, **Then** il voit les deux options : acces direct (grands projets) et via banque relais (PME), avec une recommandation adaptee a sa taille.

---

### User Story 3 - Consulter le catalogue complet des fonds (Priority: P2)

En tant que dirigeant de PME, je veux parcourir l'ensemble des fonds verts disponibles et les filtrer par type, secteur, montant et mode d'acces, pour explorer toutes les opportunites.

**Why this priority**: Complemente les recommandations personnalisees en offrant une vue exhaustive. Utile pour les utilisateurs qui veulent explorer au-dela des recommandations.

**Independent Test**: Peut etre teste en verifiant que les 12 fonds sont affiches et que les filtres (type, secteur, montant, mode d'acces) fonctionnent correctement.

**Acceptance Scenarios**:

1. **Given** un utilisateur sur la page financements, **When** il clique sur l'onglet "Tous les fonds", **Then** il voit les 12 fonds avec nom, organisation, type, montants, mode d'acces et statut.
2. **Given** la liste complete des fonds, **When** l'utilisateur filtre par "acces direct", **Then** seul le FNDE apparait.
3. **Given** la liste complete, **When** l'utilisateur filtre par type "regional", **Then** les fonds BOAD et BIDC apparaissent.

---

### User Story 4 - Consulter les intermediaires disponibles (Priority: P2)

En tant que dirigeant de PME, je veux voir tous les intermediaires disponibles dans ma zone geographique avec leurs services et les fonds qu'ils couvrent, pour pouvoir les contacter directement.

**Why this priority**: Offre une vue centralisee des intermediaires, utile pour les PME qui connaissent deja le type de fonds qu'elles cherchent.

**Independent Test**: Peut etre teste en verifiant que les intermediaires sont affiches avec filtres par type et que les coordonnees sont completes.

**Acceptance Scenarios**:

1. **Given** un utilisateur a Abidjan, **When** il clique sur l'onglet "Intermediaires", **Then** il voit la liste des intermediaires disponibles (SIB, SGBCI, BAD, PNUD CI, ANDE, etc.) avec type, adresse, fonds couverts et services offerts.
2. **Given** la liste des intermediaires, **When** l'utilisateur filtre par type "banque", **Then** seuls SIB, SGBCI, Banque Atlantique CI, Bridge Bank CI, Coris Bank CI, Ecobank CI apparaissent.
3. **Given** un intermediaire affiche, **When** l'utilisateur clique dessus, **Then** il voit le detail complet : description, fonds couverts, services offerts, frais estimes, criteres d'eligibilite pour les PME.

---

### User Story 5 - Exprimer son interet et preparer sa visite (Priority: P2)

En tant que dirigeant de PME interesse par un fonds, je veux pouvoir marquer mon interet, choisir un intermediaire, et generer une fiche de preparation a emporter lors de mon rendez-vous.

**Why this priority**: Transforme l'information en action concrete. La fiche de preparation donne de la credibilite a la PME lors du rendez-vous avec l'intermediaire.

**Independent Test**: Peut etre teste en cliquant "Je suis interesse" sur un fonds, en choisissant un intermediaire, puis en verifiant que la fiche generee contient le resume entreprise, score ESG, score carbone et raison de compatibilite.

**Acceptance Scenarios**:

1. **Given** un utilisateur sur le detail d'un fonds via intermediaire, **When** il clique "Je suis interesse", **Then** le statut passe a "interesse" et le systeme demande s'il souhaite contacter un intermediaire.
2. **Given** l'utilisateur confirme vouloir contacter un intermediaire, **When** il choisit un intermediaire dans la liste, **Then** le statut passe a "contact intermediaire" et un bouton "Preparer ma visite" apparait.
3. **Given** l'utilisateur clique "Preparer ma visite", **When** la fiche est generee, **Then** elle contient : resume de l'entreprise, score ESG, score carbone, raison de compatibilite avec le fonds, documents disponibles.

---

### User Story 6 - Obtenir des conseils de financement via le chat (Priority: P3)

En tant que dirigeant de PME, je veux pouvoir demander a l'assistant IA des conseils sur les financements verts directement dans le chat, et recevoir des reponses visuelles avec diagrammes de parcours et tableaux comparatifs.

**Why this priority**: Enrichit l'experience conversationnelle existante avec les donnees de financement. Exploite le noeud LangGraph pour des reponses contextuelles.

**Independent Test**: Peut etre teste en posant la question "Comment acceder au financement SUNREF ?" dans le chat et en verifiant qu'un diagramme Mermaid du parcours complet apparait.

**Acceptance Scenarios**:

1. **Given** un utilisateur dans le chat, **When** il demande "Comment acceder au financement SUNREF ?", **Then** Claude affiche un diagramme Mermaid montrant PME -> Banque partenaire -> Consultant SUNREF -> Pret bonifie, avec les noms des banques reelles en CI.
2. **Given** un utilisateur dans le chat, **When** il demande "Quels fonds sont compatibles avec mon profil ?", **Then** Claude affiche un tableau avec les fonds recommandes, scores de compatibilite, mode d'acces, montants et timelines.
3. **Given** un utilisateur sans score ESG, **When** il demande des recommandations de financement dans le chat, **Then** le financing_node redirige vers l'evaluation ESG et informe l'utilisateur.

---

### Edge Cases

- Que se passe-t-il quand un utilisateur n'a ni profil entreprise, ni score ESG, ni donnees carbone ? Le systeme doit guider vers le profilage d'abord.
- Que se passe-t-il quand aucun fonds ne correspond au profil de l'utilisateur (score de compatibilite < 20 pour tous) ? Afficher un message explicatif avec des suggestions d'amelioration (ex: "Completez votre evaluation ESG pour debloquer plus de fonds").
- Que se passe-t-il quand un fonds passe du statut "active" a "closed" ? Les recommandations existantes doivent refleter le nouveau statut, les matchs en cours ne sont pas supprimes mais marques.
- Que se passe-t-il quand aucun intermediaire n'est disponible dans la ville de l'utilisateur pour un fonds donne ? Afficher les intermediaires les plus proches geographiquement avec une mention de la distance.
- Que se passe-t-il quand l'utilisateur a un profil incomplet (ex: pas de secteur d'activite) ? Le matching ne peut pas fonctionner correctement — afficher un message invitant a completer le profil avec lien direct.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le systeme DOIT stocker et afficher 12 fonds verts avec leurs criteres d'eligibilite reels, montants, secteurs, mode d'acces (direct/intermediaire/mixte), et processus de candidature.
- **FR-002**: Le systeme DOIT stocker et afficher 14+ intermediaires avec leurs coordonnees reelles (adresse, telephone, email, site web), types, services offerts et frais estimes.
- **FR-003**: Le systeme DOIT lier chaque fonds a ses intermediaires avec le role specifique, la couverture geographique et le statut principal/secondaire.
- **FR-004**: Le systeme DOIT calculer un score de compatibilite (0-100) entre un profil PME et chaque fonds, base sur : secteur (30%), ESG (25%), taille entreprise (15%), localisation (10%), documents disponibles (20%).
- **FR-005**: Le systeme DOIT generer un parcours d'acces complet pour chaque match : etapes, intermediaire recommande, documents requis et timeline estimee.
- **FR-006**: Le systeme DOIT afficher un badge d'acces clair sur chaque fonds : "Acces direct" (vert), "Via intermediaire" (bleu), ou "Mixte" (orange).
- **FR-007**: Le systeme DOIT permettre de filtrer les fonds par type (international, regional, national, marche carbone, ligne verte bancaire), secteur, montant et mode d'acces.
- **FR-008**: Le systeme DOIT permettre de filtrer les intermediaires par type (banque, banque de developpement, agence ONU, ONG, agence gouvernementale, cabinet conseil, developpeur carbone), pays, ville et fonds couvert.
- **FR-009**: Le systeme DOIT permettre a l'utilisateur de marquer son interet pour un fonds et suivre le statut de sa demarche (interesse, contact intermediaire, en candidature, soumis, accepte, rejete).
- **FR-010**: Le systeme DOIT generer une fiche de preparation (document telechargeable) contenant le resume entreprise, score ESG, score carbone et raison de compatibilite avec le fonds.
- **FR-011**: Le systeme DOIT rediriger l'utilisateur vers l'evaluation ESG si le score ESG n'est pas disponible avant de proposer des recommandations.
- **FR-012**: Le noeud conversationnel DOIT repondre aux questions sur les financements avec des blocs visuels : tableaux, diagrammes Mermaid du parcours, graphiques comparatifs et timelines.
- **FR-013**: Le systeme DOIT retrouver les fonds et intermediaires pertinents par recherche semantique (RAG via embeddings).
- **FR-014**: Le systeme DOIT recommander les intermediaires les plus pertinents pour chaque match, tries par proximite geographique avec l'utilisateur.
- **FR-015**: Le systeme DOIT afficher le detail d'un intermediaire avec : nom, type, adresse complete, telephone, email, site web, services offerts, frais estimes et criteres d'eligibilite pour les PME.

### Key Entities

- **Fonds (Fund)** : Represente un fonds de financement vert. Attributs cles : nom, organisation, type de fonds, mode d'acces (direct/intermediaire/mixte), type d'intermediaire requis, criteres d'eligibilite, secteurs eligibles, montants min/max, documents requis, exigences ESG, processus de candidature, timeline typique, statut.
- **Intermediaire (Intermediary)** : Represente une entite qui facilite l'acces aux fonds. Attributs cles : nom, type d'intermediaire, type d'organisation, coordonnees completes (adresse, tel, email, site), accreditations, services offerts, frais typiques, criteres d'eligibilite pour les PME.
- **Liaison Fonds-Intermediaire (FundIntermediary)** : Materialise la relation entre un fonds et un intermediaire avec le role specifique, le statut principal/secondaire et la couverture geographique.
- **Match de Financement (FundMatch)** : Represente le resultat du matching entre un profil PME et un fonds. Contient le score de compatibilite, les criteres remplis/manquants, les intermediaires recommandes, le parcours d'acces complet et le statut de suivi de la demarche.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Les 12 fonds verts sont affiches avec leurs criteres d'eligibilite reels et leur mode d'acces correct (direct/intermediaire/mixte).
- **SC-002**: Les 14+ intermediaires sont affiches avec coordonnees completes et services offerts.
- **SC-003**: Le score de compatibilite classe correctement les fonds par pertinence pour un profil PME donne (le fonds le plus pertinent sectorellement et geographiquement apparait en premier).
- **SC-004**: Pour le fonds SUNREF, l'utilisateur voit clairement qu'il doit passer par SIB, SGBCI, Banque Atlantique CI ou Bridge Bank CI, avec adresses et contacts a Abidjan.
- **SC-005**: Pour le FNDE, l'utilisateur voit clairement qu'il peut candidater directement sans intermediaire.
- **SC-006**: La question "Comment acceder au financement SUNREF ?" dans le chat produit un diagramme visuel montrant le parcours complet (PME -> Banque partenaire -> Consultant SUNREF -> Pret bonifie) avec les noms des banques reelles.
- **SC-007**: La fiche de preparation generee contient le resume entreprise, scores ESG et carbone, et la raison de compatibilite avec le fonds cible.
- **SC-008**: Un utilisateur sans score ESG est redirige vers l'evaluation ESG avant de recevoir des recommandations de financement.
- **SC-009**: La recherche semantique retrouve les fonds et intermediaires pertinents quand l'utilisateur pose une question en langage naturel dans le chat.
- **SC-010**: L'utilisateur peut suivre l'evolution de sa demarche a travers au moins 6 statuts (interesse, contact intermediaire, en candidature, soumis, accepte, rejete).

## Assumptions

- Les features 001-007 sont implementees et fonctionnelles. Le state LangGraph contient deja le profil entreprise, le score ESG et les donnees carbone.
- Les coordonnees des intermediaires (adresses, telephones, emails) sont des donnees publiques representant les informations reelles disponibles au moment du developpement. Elles devront etre mises a jour periodiquement.
- Les montants des fonds sont exprimes en FCFA (XOF) comme devise principale, coherent avec la zone UEMOA ciblee.
- La fiche de preparation est un document simple telechargeable (pas necessairement un PDF complexe — un format imprimable suffit).
- Le matching initial est base sur des regles deterministes (ponderation fixe). L'enrichissement par IA (Claude) genere le parcours d'acces textuel mais ne modifie pas le score numerique.
- La recherche semantique (RAG) reutilise l'infrastructure pgvector deja en place pour les documents.
- Un seul utilisateur a la fois consulte ses recommandations (pas de contrainte de concurrence massive a ce stade).
- Les donnees des fonds sont relativement stables (mises a jour manuelles par un admin, pas de synchronisation automatique avec des sources externes).
