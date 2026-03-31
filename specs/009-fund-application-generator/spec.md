# Feature Specification: Generateur de Dossiers de Candidature aux Fonds Verts

**Feature Branch**: `009-fund-application-generator`
**Created**: 2026-03-31
**Status**: Draft
**Input**: Modules 3.3 & 3.4 — Generation automatique de dossiers de candidature adaptes au destinataire (fonds direct ou intermediaire)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Creer un dossier pour un fonds a acces direct (Priority: P1)

Un dirigeant de PME a identifie le FNDE (Fonds National pour le Developpement de l'Environnement) via le module de matching (feature 008). Il souhaite constituer un dossier de candidature directement aupres du fonds. Le systeme genere automatiquement un dossier au ton institutionnel, avec des sections axees sur l'impact environnemental et la conformite reglementaire.

**Why this priority**: C'est le parcours fondamental — sans generation de dossier, la plateforme ne depasse pas le stade du conseil. La creation de dossier est le coeur de valeur du module.

**Independent Test**: Creer un dossier pour le FNDE, verifier que le template contient les sections Presentation entreprise / Description projet / Impact environnemental / Plan financier / Annexes, et que le ton est formel et institutionnel.

**Acceptance Scenarios**:

1. **Given** un utilisateur avec un profil entreprise et un match vers le FNDE, **When** il cree un dossier pour ce fonds (acces direct), **Then** le systeme cree un dossier avec target_type=fund_direct, genere les sections du template "fonds direct" et affiche le statut "Brouillon".
2. **Given** un dossier en brouillon avec des sections generees, **When** l'utilisateur consulte le dossier, **Then** chaque section affiche un code couleur (vert=validee, orange=generee, gris=non generee) et est modifiable via un editeur rich text.
3. **Given** un dossier avec toutes les sections validees, **When** l'utilisateur exporte le dossier, **Then** le systeme produit un PDF ou Word professionnel au format adapte au fonds.

---

### User Story 2 - Creer un dossier via une banque partenaire (Priority: P1)

Un dirigeant souhaite acceder au programme SUNREF via la SIB (banque partenaire). Le systeme genere un dossier au ton bancaire, oriente business case et capacite de remboursement, avec des sections specifiques (historique bancaire, garanties, bilans financiers). Le contenu est fondamentalement different d'un dossier pour un fonds direct.

**Why this priority**: La majorite des fonds verts en Afrique de l'Ouest necessitent un intermediaire bancaire. Ce parcours represente le cas d'usage dominant.

**Independent Test**: Creer un dossier SUNREF via la SIB et verifier que le contenu est oriente "business case bancaire" (economies FCFA, retour sur investissement) et non "rapport d'impact ODD".

**Acceptance Scenarios**:

1. **Given** un utilisateur avec un match SUNREF et l'intermediaire SIB selectionne, **When** il cree un dossier, **Then** le systeme cree un dossier avec target_type=intermediary_bank, intermediary_id pointe vers la SIB, et le template bancaire est utilise (6 sections : presentation + historique bancaire, projet investissement vert, plan financier detaille, impact environnemental, documents financiers, annexes).
2. **Given** un dossier de type bancaire, **When** Claude genere la section "Impact environnemental", **Then** les formulations utilisent des termes bancaires ("economies annuelles estimees a X FCFA", "reduction de la facture energetique de Y%") au lieu de termes institutionnels ("impact sur les ODD").
3. **Given** un dossier de type bancaire, **When** l'utilisateur consulte la checklist, **Then** elle inclut des documents financiers (3 derniers bilans, releves bancaires, situation fiscale) et non des documents d'impact environnemental detailles.

---

### User Story 3 - Generer une fiche de preparation intermediaire (Priority: P2)

Quand le fonds necessite un intermediaire, l'utilisateur peut generer une "fiche de preparation" a emmener au rendez-vous. Cette fiche de 2-3 pages resume l'entreprise, le score ESG, le bilan carbone, l'eligibilite au fonds, les documents disponibles et propose 5 questions a poser.

**Why this priority**: Cette fiche est un outil d'accompagnement unique qui differencie la plateforme. Elle prepare concretement l'utilisateur a son rendez-vous chez l'intermediaire.

**Independent Test**: Generer une fiche de preparation pour un dossier SUNREF/SIB, telecharger le PDF et verifier qu'il contient les coordonnees de la SIB, le resume entreprise, le score ESG et les 5 questions.

**Acceptance Scenarios**:

1. **Given** un dossier avec un intermediaire (ex: SIB), **When** l'utilisateur demande la fiche de preparation, **Then** le systeme genere un PDF compact (2-3 pages) contenant : resume entreprise, score ESG avec points forts, bilan carbone synthetique, eligibilite au fonds, documents disponibles, 5 questions a poser.
2. **Given** la fiche de preparation generee, **When** l'utilisateur la visualise dans l'interface, **Then** les coordonnees de l'intermediaire (nom, adresse, telephone, email) sont affichees en evidence avec des boutons "Appeler" (tel:) et "Envoyer un email" (mailto:).
3. **Given** un dossier a acces direct (sans intermediaire), **When** l'utilisateur consulte le dossier, **Then** l'onglet "Fiche de preparation" n'est pas affiche.

---

### User Story 4 - Adapter le dossier pour une agence d'implementation (Priority: P2)

Un porteur de projet souhaite s'integrer a un programme du FEM via le PNUD. Le systeme genere un dossier au ton "developpement", axe sur l'alignement avec les priorites nationales, les indicateurs d'impact mesurables et le co-financement.

**Why this priority**: Les agences d'implementation (PNUD, FAO, BOAD) representent un canal d'acces majeur pour les grands fonds multilateraux. Le template doit etre specifique.

**Independent Test**: Creer un dossier FEM via PNUD et verifier que les sections sont : fiche d'identification, alignement programme-pays, description technique, budget/co-financement, indicateurs d'impact.

**Acceptance Scenarios**:

1. **Given** un match FEM avec intermediaire PNUD, **When** l'utilisateur cree un dossier, **Then** le systeme utilise le template agence (5 sections : identification porteur, alignement priorites nationales, description technique, budget/co-financement, indicateurs impact mesurables) avec target_type=intermediary_agency.
2. **Given** un dossier de type agence, **When** Claude genere le contenu, **Then** le ton est oriente developpement et alignement strategique, pas bancaire.

---

### User Story 5 - Adapter le dossier pour un developpeur de projets carbone (Priority: P3)

Un porteur de projet souhaite obtenir une certification Gold Standard ou Verra. Le systeme genere un dossier technique oriente methodologie carbone, avec des sections sur les reductions d'emissions, le monitoring et l'additionnalite.

**Why this priority**: C'est un parcours specialise pour la certification carbone volontaire. Moins frequent mais a forte valeur ajoutee pour les entreprises engagees dans la compensation carbone.

**Independent Test**: Creer un dossier Gold Standard et verifier les sections : methodologie, estimation emissions baseline vs projet, plan monitoring, additionnalite, co-benefices ODD.

**Acceptance Scenarios**:

1. **Given** un match vers un programme Gold Standard avec un developpeur de projets carbone, **When** l'utilisateur cree un dossier, **Then** le systeme utilise le template carbone (5 sections techniques) avec target_type=intermediary_developer.
2. **Given** un dossier de type developpeur carbone, **When** Claude genere la section "Estimation des reductions d'emissions", **Then** le contenu inclut une comparaison baseline vs projet en tCO2e.

---

### User Story 6 - Simuler le financement avec etape intermediaire (Priority: P2)

L'utilisateur lance une simulation financiere pour son dossier. Le simulateur estime le montant eligible, le ROI vert, la timeline et l'impact carbone. Si le parcours passe par un intermediaire, la timeline inclut l'etape intermediaire et les frais associes sont estimes.

**Why this priority**: La simulation aide l'utilisateur a evaluer la faisabilite avant d'investir du temps dans le montage du dossier. L'ajout de l'etape intermediaire rend la simulation realiste.

**Independent Test**: Lancer une simulation pour un dossier SUNREF/SIB et verifier que la timeline inclut "Traitement par la banque : 2-4 semaines" et que les frais intermediaire sont estimes.

**Acceptance Scenarios**:

1. **Given** un dossier avec intermediaire bancaire, **When** l'utilisateur lance la simulation, **Then** la timeline affiche l'etape intermediaire ("Traitement par la banque : 2-4 semaines") avant "Soumission au fonds" et les frais intermediaire sont estimes.
2. **Given** un dossier a acces direct, **When** l'utilisateur lance la simulation, **Then** la timeline n'inclut pas d'etape intermediaire et aucun frais intermediaire n'est affiche.

---

### User Story 7 - Generer/regenerer des sections individuelles (Priority: P2)

L'utilisateur peut generer ou regenerer une section specifique du dossier. Le contenu genere tient compte du type de destinataire (target_type) et utilise le RAG pour exploiter les documents deja uploades et les donnees de l'entreprise.

**Why this priority**: La generation section par section permet un controle fin et une iteration rapide sur le contenu du dossier.

**Independent Test**: Regenerer la section "Plan financier" d'un dossier bancaire et verifier que le nouveau contenu reste au ton bancaire.

**Acceptance Scenarios**:

1. **Given** un dossier de type bancaire avec une section "Plan financier" generee, **When** l'utilisateur clique "Regenerer" sur cette section, **Then** une nouvelle version est generee au ton bancaire, exploitant les documents financiers deja uploades via le RAG.
2. **Given** un dossier avec des sections, **When** l'utilisateur modifie manuellement une section puis la valide, **Then** le statut de la section passe a "validee" (vert) et le contenu manuel est preserve.

---

### User Story 8 - Suivre le statut enrichi du parcours (Priority: P3)

Le statut du dossier reflete le parcours complet, y compris les etapes via l'intermediaire. L'utilisateur voit des statuts comme "Pret pour l'intermediaire", "Soumis a l'intermediaire", "Transmis au fonds", "Accepte/Rejete".

**Why this priority**: Le suivi de statut detaille rassure l'utilisateur et l'accompagne a chaque etape du processus souvent long et complexe.

**Independent Test**: Faire progresser un dossier via les differents statuts et verifier que la liste des dossiers affiche des libelles comprehensibles en francais.

**Acceptance Scenarios**:

1. **Given** un dossier pret avec intermediaire, **When** l'utilisateur met a jour le statut, **Then** le statut progresse selon le parcours : draft → preparing_documents → in_progress → review → ready_for_intermediary → submitted_to_intermediary → submitted_to_fund → under_review → accepted/rejected.
2. **Given** la liste des dossiers, **When** l'utilisateur la consulte, **Then** chaque dossier affiche un statut en francais contextualise (ex: "En attente du rendez-vous SIB", "Soumis via PNUD").

---

### User Story 9 - Visualiser le parcours dans le chat (Priority: P3)

Quand l'utilisateur interagit via le chat conversationnel, le noeud application_node affiche des visualisations adaptees : diagramme mermaid du parcours, blocs progress pour la checklist, graphiques pour la simulation, timeline avec etapes intermediaire.

**Why this priority**: L'integration au chat maintient la coherence de l'experience conversationnelle. Les visualisations enrichies facilitent la comprehension du parcours complexe.

**Independent Test**: Demander au chatbot de montrer le parcours d'un dossier SUNREF/SIB et verifier qu'un diagramme mermaid s'affiche avec les etapes intermediaire.

**Acceptance Scenarios**:

1. **Given** un utilisateur dans le chat avec un dossier en cours, **When** il demande l'etat du dossier, **Then** le systeme affiche un bloc mermaid montrant la structure des sections adaptee au destinataire et un bloc progress montrant les documents fournis/manquants.
2. **Given** un fonds avec acces mixed (direct et intermediaire), **When** l'utilisateur demande une comparaison, **Then** le systeme affiche un bloc table comparant les deux parcours.

---

### Edge Cases

- Que se passe-t-il si l'utilisateur cree un dossier pour un fonds sans template specifique configure ? → Le systeme utilise le template generique adapte selon l'access_type.
- Que se passe-t-il si le profil entreprise est incomplet ? → Les sections generees signalent les informations manquantes et invitent l'utilisateur a completer son profil.
- Que se passe-t-il si l'intermediaire n'a pas de coordonnees renseignees ? → La fiche de preparation affiche un avertissement et omet la section contact.
- Que se passe-t-il si l'utilisateur change d'intermediaire apres avoir genere des sections ? → Le systeme propose de regenerer les sections pour adapter le ton et le contenu au nouveau destinataire.
- Que se passe-t-il si deux dossiers sont crees simultanement pour le meme fonds ? → Le systeme autorise plusieurs dossiers (brouillons) pour le meme fonds, avec un avertissement.
- Que se passe-t-il si l'export PDF echoue (document trop volumineux ou erreur de generation) ? → Le systeme affiche un message d'erreur clair et propose de reessayer.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le systeme DOIT permettre de creer un dossier de candidature en associant un fonds (fund_id) et optionnellement un intermediaire (intermediary_id).
- **FR-002**: Le systeme DOIT determiner automatiquement le target_type (fund_direct, intermediary_bank, intermediary_agency, intermediary_developer) en fonction du fonds et de l'intermediaire selectionne.
- **FR-003**: Le systeme DOIT utiliser un template de sections different selon le target_type : template fonds direct (5 sections institutionnelles), template bancaire (6 sections orientees solvabilite), template agence (5 sections orientees developpement), template carbone (5 sections techniques), template generique.
- **FR-004**: Le systeme DOIT adapter le ton et les formulations du contenu genere selon le target_type (institutionnel, bancaire, developpement, technique/methodologique).
- **FR-005**: Le systeme DOIT permettre de generer ou regenerer individuellement chaque section d'un dossier, en exploitant les documents uploades et le profil entreprise via RAG (pgvector).
- **FR-006**: Le systeme DOIT permettre la modification manuelle de chaque section via un editeur rich text.
- **FR-007**: Le systeme DOIT fournir une checklist de documents requis adaptee au destinataire (documents financiers pour une banque, documents d'impact pour un fonds, etc.).
- **FR-008**: Le systeme DOIT generer une fiche de preparation intermediaire (PDF 2-3 pages) contenant : resume entreprise, score ESG, bilan carbone, eligibilite, documents disponibles, 5 questions a poser, coordonnees de l'intermediaire.
- **FR-009**: Le systeme DOIT fournir un simulateur de financement estimant : montant eligible, ROI vert, timeline (incluant etape intermediaire si applicable), impact carbone, et frais intermediaire si applicable.
- **FR-010**: Le systeme DOIT gerer un cycle de vie de statuts enrichi refletant le parcours via intermediaire : draft → preparing_documents → in_progress → review → ready_for_intermediary → ready_for_fund → submitted_to_intermediary → submitted_to_fund → under_review → accepted → rejected.
- **FR-011**: Le systeme DOIT exporter le dossier complet en PDF et Word, avec un format professionnel adapte au destinataire.
- **FR-012**: Le systeme DOIT afficher un bandeau indiquant clairement le destinataire du dossier ("Prepare pour : SIB (partenaire SUNREF)" ou "Prepare pour : FNDE (candidature directe)").
- **FR-013**: Le systeme DOIT afficher les sections avec un code couleur indiquant leur statut : vert (validee), orange (generee), gris (non generee).
- **FR-014**: Le noeud conversationnel (application_node) DOIT afficher des visualisations adaptees : mermaid (structure dossier, parcours), progress (checklist), chart/gauge (simulation), timeline (etapes), table (comparaison direct/intermediaire).
- **FR-015**: La fiche de preparation DOIT afficher les coordonnees de l'intermediaire en evidence avec des liens cliquables (tel: pour appeler, mailto: pour email).

### Key Entities

- **FundApplication** : Represente un dossier de candidature. Lie a un utilisateur, un fonds, optionnellement un match et un intermediaire. Contient les sections generees (JSONB), la checklist documentaire (JSONB), la fiche de preparation intermediaire (JSONB), la simulation (JSONB). Possede un target_type et un statut enrichi.
- **ApplicationSection** : Section individuelle d'un dossier (stockee dans le JSONB sections). Possede une cle, un titre, un contenu genere, un statut (non_generee, generee, validee), et un historique de versions.
- **ApplicationChecklist** : Liste de documents requis (stockee dans le JSONB checklist). Chaque item a un nom, un statut (manquant, fourni), et une reference optionnelle vers un document uploade.
- **IntermediaryPrepSheet** : Fiche de preparation pour le rendez-vous chez l'intermediaire (stockee dans le JSONB intermediary_prep). Contient resume, score ESG, bilan carbone, eligibilite, documents, questions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un utilisateur peut creer un dossier de candidature complet (toutes sections generees et validees) en moins de 30 minutes, contre plusieurs jours manuellement.
- **SC-002**: Le contenu genere pour un dossier bancaire (SUNREF/SIB) differe de maniere verifiable d'un dossier fonds direct (FNDE) : vocabulaire, sections, et structure sont adaptes au destinataire.
- **SC-003**: La checklist documentaire generee pour un intermediaire bancaire inclut au minimum les documents financiers specifiques (bilans, releves, situation fiscale), tandis que celle d'un fonds direct inclut les documents d'impact environnemental.
- **SC-004**: La fiche de preparation intermediaire est generee en PDF compact (2-3 pages max) et contient les 6 elements requis (resume, score ESG, bilan carbone, eligibilite, documents, questions).
- **SC-005**: La simulation financiere avec intermediaire inclut visiblement l'etape intermediaire dans la timeline et les frais associes.
- **SC-006**: L'export PDF/Word produit un document professionnel lisible et correctement formate pour chaque type de destinataire.
- **SC-007**: Le parcours de statuts enrichi permet de suivre un dossier depuis le brouillon jusqu'a l'acceptation/rejet, en passant par les etapes intermediaire si applicable.
- **SC-008**: Les visualisations du chat (mermaid, progress, timeline) s'affichent correctement et sont adaptees au type de parcours (direct vs intermediaire).

## Assumptions

- Les features 001-008 sont implementees et fonctionnelles (profil entreprise, documents, scoring ESG, bilan carbone, matching financement avec intermediaires).
- La base de donnees contient deja les fonds verts (12 fonds), les intermediaires (14 avec coordonnees) et les liaisons fund-intermediary (~50) issus de la feature 008.
- L'utilisateur a deja un profil entreprise avec au minimum un scoring ESG et/ou un bilan carbone pour alimenter la generation de contenu.
- Le RAG via pgvector est operationnel pour exploiter les documents uploades lors de la generation de sections.
- WeasyPrint est deja installe et operationnel (utilise par la feature 006 pour les rapports PDF).
- Les templates de dossier sont definis dans le code (pas dans la base de donnees) ; un template generique est utilise pour les fonds sans configuration specifique.
- Le simulateur de financement utilise des estimations basees sur les parametres du fonds (montant min/max, duree) et des hypotheses standard (taux, frais) ; ce ne sont pas des offres engageantes.
- L'export Word utilise la librairie python-docx (a ajouter aux dependances).
