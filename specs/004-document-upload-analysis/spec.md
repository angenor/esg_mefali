# Feature Specification: Upload et Analyse Intelligente de Documents

**Feature Branch**: `004-document-upload-analysis`
**Created**: 2026-03-30
**Status**: Draft
**Input**: User description: "Module 2.1 - Upload et Analyse de Documents. Brique technique transversale pour le scoring ESG, la generation de dossiers, et le scoring de credit."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload et analyse d'un document depuis la page Documents (Priority: P1)

Un utilisateur PME uploade un document (PDF, image, Word ou Excel) depuis la page dediee "Documents". Le systeme valide le fichier, extrait le texte (y compris via OCR pour les documents scannes), puis analyse le contenu avec l'IA pour produire un resume en francais, des informations structurees, des points cles et des elements pertinents pour l'ESG. L'utilisateur voit la progression en temps reel et consulte ensuite le resultat complet de l'analyse.

**Why this priority**: C'est la fonctionnalite de base du module. Sans upload et analyse fonctionnels, aucune autre story n'a de valeur. Cette brique est aussi prerequise pour les modules scoring ESG et financement vert.

**Independent Test**: Peut etre teste en uploadant un PDF textuel, un PDF scanne, une image, un Word et un Excel, puis en verifiant que chaque type produit un resume et des donnees structurees.

**Acceptance Scenarios**:

1. **Given** un utilisateur sur la page Documents, **When** il uploade un fichier PDF textuel de 2MB, **Then** le systeme affiche la progression (upload, extraction, analyse, termine) et produit un resume, des points cles et des informations ESG.
2. **Given** un utilisateur sur la page Documents, **When** il uploade un PDF scanne (image), **Then** l'OCR extrait le texte et l'analyse produit les memes resultats qu'un PDF textuel.
3. **Given** un utilisateur qui tente d'uploader un fichier .exe de 5MB, **Then** le systeme refuse le fichier avec un message d'erreur clair indiquant les types acceptes.
4. **Given** un utilisateur qui tente d'uploader un fichier de 15MB, **Then** le systeme refuse le fichier avec un message indiquant la taille maximale autorisee (10MB).
5. **Given** un utilisateur sur la page Documents, **When** il uploade un fichier Excel, **Then** les donnees tabulaires sont extraites et structurees dans l'analyse.

---

### User Story 2 - Upload d'un document dans le chat et discussion contextuelle (Priority: P1)

Un utilisateur envoie un document directement dans le chat (via un bouton trombone). Le systeme analyse le document et Claude repond avec un resume utilisant des blocs visuels adaptes au type de document (tableaux pour les bilans financiers, diagrammes pour les rapports d'activite). L'utilisateur peut ensuite poser des questions sur le document dans le fil de conversation.

**Why this priority**: L'integration chat est le differentiant principal de la plateforme. Les utilisateurs PME s'attendent a pouvoir discuter naturellement de leurs documents avec l'IA plutot que de naviguer dans une interface separee.

**Independent Test**: Peut etre teste en uploadant un bilan financier dans le chat et en verifiant que Claude repond avec un tableau des chiffres cles, puis en posant une question de suivi.

**Acceptance Scenarios**:

1. **Given** un utilisateur dans le chat, **When** il uploade un bilan financier via le bouton trombone, **Then** Claude repond avec un resume et un tableau des chiffres cles extraits.
2. **Given** un document deja analyse dans le chat, **When** l'utilisateur demande "Quels sont les risques ESG identifies ?", **Then** Claude repond en se basant sur l'analyse du document.
3. **Given** un utilisateur dans le chat, **When** il uploade un rapport d'activite, **Then** Claude repond avec un resume et un diagramme des processus ou de l'organigramme detectes.
4. **Given** un utilisateur dans le chat, **When** il uploade une facture, **Then** Claude repond avec un tableau des lignes de facture extraites.

---

### User Story 3 - Gestion et consultation des documents (Priority: P2)

Un utilisateur consulte la liste de ses documents uploades, filtree par type. Il peut voir le detail d'un document (resume, points cles, informations ESG, texte brut). Il peut supprimer un document ou relancer l'analyse si necessaire.

**Why this priority**: La gestion des documents est necessaire pour une utilisation continue de la plateforme, mais n'est pas bloquante pour demontrer la valeur de l'analyse IA.

**Independent Test**: Peut etre teste en verifiant que la liste affiche les documents avec les bons filtres, que le detail montre toutes les sections, et que la suppression fonctionne.

**Acceptance Scenarios**:

1. **Given** un utilisateur avec 5 documents uploades de types differents, **When** il filtre par "bilan_financier", **Then** seuls les bilans financiers apparaissent dans la liste.
2. **Given** un document analyse, **When** l'utilisateur clique pour voir le detail, **Then** il voit le resume, les points cles, les informations ESG et le texte brut (dans un accordeon).
3. **Given** un document avec une analyse en erreur, **When** l'utilisateur clique "Relancer l'analyse", **Then** l'analyse est relancee et le statut se met a jour.
4. **Given** un utilisateur, **When** il supprime un document, **Then** le document et son fichier physique sont supprimes, et il disparait de la liste.

---

### User Story 4 - Stockage des embeddings pour le RAG futur (Priority: P2)

Apres l'analyse, le texte extrait des documents est decoupe en segments et leurs embeddings sont stockes pour permettre la recherche semantique future (RAG). Cela permettra aux modules scoring ESG et financement vert d'interroger les documents pertinents automatiquement.

**Why this priority**: Les embeddings sont une brique technique invisible pour l'utilisateur mais essentielle pour les modules en aval. Ils ne delivrent pas de valeur directe a ce stade mais conditionnent la qualite des fonctionnalites futures.

**Independent Test**: Peut etre teste en verifiant qu'apres l'analyse d'un document, des embeddings sont stockes et qu'une recherche semantique retourne des segments pertinents.

**Acceptance Scenarios**:

1. **Given** un document analyse, **When** le processus d'embedding est termine, **Then** les segments de texte et leurs vecteurs sont stockes dans la base de donnees vectorielle.
2. **Given** des documents analyses avec embeddings, **When** une requete semantique est effectuee, **Then** les segments les plus pertinents sont retournes.

---

### User Story 5 - Previsualisation des documents (Priority: P3)

Un utilisateur peut previsualiser les images et les PDFs directement dans l'interface sans avoir a telecharger le fichier.

**Why this priority**: Fonctionnalite de confort qui ameliore l'experience utilisateur mais n'est pas essentielle pour l'analyse documentaire.

**Independent Test**: Peut etre teste en verifiant qu'un PDF et une image s'affichent dans un visualiseur integre.

**Acceptance Scenarios**:

1. **Given** un document PDF uploade, **When** l'utilisateur demande la previsualisation, **Then** le PDF s'affiche dans un visualiseur integre a l'interface.
2. **Given** une image uploadee, **When** l'utilisateur demande la previsualisation, **Then** l'image s'affiche directement dans l'interface.

---

### Edge Cases

- Que se passe-t-il quand un PDF est protege par mot de passe ? Le systeme doit signaler l'erreur clairement et suggerer de fournir une version non protegee.
- Que se passe-t-il quand l'OCR ne detecte aucun texte exploitable (image floue, document vide) ? Le systeme doit indiquer que le texte n'a pas pu etre extrait et suggerer de reuploader un fichier de meilleure qualite.
- Que se passe-t-il quand l'analyse IA echoue (timeout, erreur API) ? Le document passe en statut "erreur" avec un message explicatif et l'option de relancer l'analyse.
- Que se passe-t-il quand un utilisateur uploade plusieurs fichiers simultanement ? Le systeme traite chaque fichier independamment avec des indicateurs de progression individuels.
- Que se passe-t-il quand un utilisateur tente d'acceder au document d'un autre utilisateur ? Le systeme retourne une erreur d'autorisation sans reveler l'existence du document.
- Que se passe-t-il quand l'espace disque est insuffisant ? Le systeme refuse l'upload avec un message d'erreur appropriate.
- Que se passe-t-il quand un document est uploade dans le chat sans conversation active ? Une nouvelle conversation est creee automatiquement.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le systeme DOIT accepter les fichiers de types PDF, PNG, JPG, JPEG, DOCX et XLSX uniquement.
- **FR-002**: Le systeme DOIT refuser tout fichier depassant 10MB avec un message d'erreur clair.
- **FR-003**: Le systeme DOIT extraire le texte des PDF textuels, des PDF scannes (via OCR), des images (via OCR), des documents Word et des fichiers Excel.
- **FR-004**: Le systeme DOIT analyser le texte extrait avec l'IA pour produire : un resume en francais, des informations structurees, une liste de points cles, et des elements pertinents pour l'ESG.
- **FR-005**: Le systeme DOIT identifier automatiquement le type de document parmi : statuts juridiques, rapport d'activite, facture, contrat, politique interne, bilan financier, autre.
- **FR-006**: Le systeme DOIT stocker les fichiers uploades de maniere organisee par utilisateur et document.
- **FR-007**: Le systeme DOIT afficher la progression de l'analyse en temps reel (upload, extraction texte, analyse IA, termine).
- **FR-008**: Le systeme DOIT permettre l'upload de documents depuis une page dediee et depuis le chat.
- **FR-009**: Le systeme DOIT permettre l'upload de plusieurs fichiers simultanement.
- **FR-010**: Le systeme DOIT permettre de lister les documents avec filtrage par type de document.
- **FR-011**: Le systeme DOIT permettre de consulter le detail d'un document analyse (resume, points cles, informations ESG, texte brut).
- **FR-012**: Le systeme DOIT permettre de supprimer un document et son fichier physique associe.
- **FR-013**: Le systeme DOIT permettre de relancer l'analyse d'un document en erreur.
- **FR-014**: Quand un document est uploade dans le chat, l'IA DOIT repondre avec un resume et des blocs visuels adaptes au type de document (tableaux pour les donnees financieres, diagrammes pour les processus).
- **FR-015**: Apres l'upload dans le chat, l'utilisateur DOIT pouvoir poser des questions de suivi sur le document dans la meme conversation.
- **FR-016**: Le systeme DOIT decouper le texte extrait en segments et stocker leurs embeddings vectoriels pour la recherche semantique future.
- **FR-017**: Les fichiers DOIVENT etre accessibles uniquement par leur proprietaire. Toute tentative d'acces non autorise DOIT etre rejetee.
- **FR-018**: Le systeme DOIT adapter le prompt d'analyse au type de document detecte pour une extraction plus pertinente.
- **FR-019**: Le systeme DOIT permettre la previsualisation basique des images et PDFs directement dans l'interface.
- **FR-020**: Un document PEUT etre associe a une conversation (upload chat) ou non (upload depuis la page documents).

### Key Entities

- **Document**: Represente un fichier uploade par un utilisateur. Attributs cles : nom original, type MIME, taille, chemin de stockage, statut de traitement (uploade, en cours, analyse, erreur), type de document (statuts juridiques, rapport d'activite, facture, contrat, politique interne, bilan financier, autre). Peut etre lie a une conversation ou non.
- **Analyse de Document**: Resultat de l'analyse IA d'un document. Contient le texte brut extrait, les donnees structurees, le resume en francais, les points cles et les informations pertinentes pour l'ESG. Lie a exactement un document.
- **Segment de Texte (Embedding)**: Fragment de texte extrait d'un document, accompagne de son vecteur d'embedding pour la recherche semantique. Lie a un document. Permet le RAG futur.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Les utilisateurs peuvent uploader et obtenir une analyse complete d'un document en moins de 2 minutes pour un fichier de 5 pages.
- **SC-002**: L'OCR extrait au moins 90% du texte lisible d'un document scanne de qualite standard.
- **SC-003**: L'analyse IA identifie correctement le type de document dans au moins 85% des cas.
- **SC-004**: Les informations structurees extraites d'un bilan financier contiennent au minimum les chiffres cles (chiffre d'affaires, resultat net, total actif) quand ils sont presents dans le document.
- **SC-005**: 100% des tentatives d'acces non autorise a un document sont bloquees.
- **SC-006**: L'upload et la discussion sur un document dans le chat fonctionnent sans quitter la conversation.
- **SC-007**: Les 6 types de fichiers acceptes (PDF, PNG, JPG, JPEG, DOCX, XLSX) sont uploades et analyses avec succes.
- **SC-008**: Apres analyse, les embeddings sont stockes et une recherche semantique retourne des resultats pertinents pour au moins 80% des requetes testees.

## Assumptions

- Les features 001 (fondation technique), 002 (chat visuel) et 003 (profil entreprise) sont implementees et fonctionnelles.
- Le chat fonctionne via LangGraph avec rendu de blocs visuels (tableaux, diagrammes mermaid).
- L'utilisateur a une connexion internet stable permettant l'upload de fichiers jusqu'a 10MB.
- Les documents uploades sont en francais ou en anglais (les deux langues les plus courantes pour les PME africaines francophones). L'analyse et le resume sont toujours produits en francais.
- Le stockage est local dans un premier temps. La migration vers un stockage distant (S3/MinIO) est hors perimetre de cette feature.
- Le systeme d'authentification utilisateur existe et fournit un identifiant utilisateur pour l'isolation des documents.
- Les outils OCR (Tesseract) sont disponibles sur le serveur de deploiement.
- Les documents uploades ne contiennent pas de malware ; la detection de malware est hors perimetre mais pourra etre ajoutee ulterieurement.
- Le RAG (Retrieval-Augmented Generation) complet est hors perimetre de cette feature ; seul le stockage des embeddings est inclus. L'exploitation des embeddings pour enrichir les reponses sera implementee dans un module ulterieur.
