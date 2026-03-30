# Feature Specification: Interface de Chat Conversationnel avec Rendu Visuel Enrichi

**Feature Branch**: `002-chat-rich-visuals`
**Created**: 2026-03-30
**Status**: Draft
**Input**: User description: "Interface de chat conversationnel avec Claude AI et rendu visuel enrichi — Module 1.1 (Interface de Chat Multimodale)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conversation de base avec le conseiller ESG (Priority: P1)

Un utilisateur PME se connecte, cree une nouvelle conversation et pose une question sur ses pratiques ESG. Le conseiller repond en streaming (effet de frappe en temps reel). L'utilisateur peut enchainer les questions dans le meme fil de conversation. Il peut ensuite retrouver cette conversation dans son historique.

**Why this priority**: C'est le flux fondamental de l'application. Sans conversation fonctionnelle, aucune autre fonctionnalite n'a de valeur. C'est le MVP absolu.

**Independent Test**: Peut etre teste en creant une conversation, envoyant un message, verifiant la reponse en streaming, puis en retrouvant la conversation dans l'historique.

**Acceptance Scenarios**:

1. **Given** un utilisateur authentifie sur la page chat, **When** il clique sur "Nouvelle conversation" et envoie "Qu'est-ce que l'ESG ?", **Then** une reponse en francais s'affiche progressivement en streaming et la conversation est sauvegardee avec un titre auto-genere.
2. **Given** une conversation existante avec des messages, **When** l'utilisateur envoie un message supplementaire, **Then** la reponse tient compte du contexte des messages precedents.
3. **Given** l'utilisateur a plusieurs conversations, **When** il consulte le panneau lateral, **Then** il voit la liste de ses conversations ordonnees par activite recente et peut en selectionner une pour la revoir avec tous ses messages.

---

### User Story 2 - Visualisation de graphiques dans le chat (Priority: P1)

L'utilisateur pose une question qui appelle une analyse visuelle (ex: "Montre-moi un radar chart ESG pour mon entreprise"). Le conseiller genere un graphique directement dans sa reponse. Le graphique est interactif (tooltips au survol), peut etre agrandi en plein ecran et telecharge en PNG.

**Why this priority**: La capacite de rendu visuel enrichi est la differenciation cle de cette feature par rapport a un simple chatbot textuel. C'est le coeur de l'innovation.

**Independent Test**: Demander "Montre-moi un exemple de radar chart ESG" et verifier qu'un graphique radar interactif s'affiche dans le message avec les boutons Agrandir et Telecharger.

**Acceptance Scenarios**:

1. **Given** une conversation active, **When** le conseiller genere un bloc chart dans sa reponse, **Then** un graphique interactif s'affiche a la place du code brut, avec des tooltips au survol.
2. **Given** un graphique affiche dans le chat, **When** l'utilisateur clique sur "Agrandir", **Then** le graphique s'ouvre en plein ecran dans une modale.
3. **Given** un graphique affiche dans le chat, **When** l'utilisateur clique sur "Telecharger", **Then** une image PNG du graphique est telechargee.
4. **Given** un bloc chart avec un JSON invalide, **When** le message est rendu, **Then** le code brut est affiche avec le message "Impossible d'afficher la visualisation".

---

### User Story 3 - Visualisation de diagrammes dans le chat (Priority: P1)

L'utilisateur pose une question sur un processus ESG. Le conseiller genere un diagramme de flux ou un organigramme directement dans la reponse. Le diagramme est rendu en SVG avec les couleurs de la marque.

**Why this priority**: Les diagrammes de flux sont essentiels pour expliquer les processus ESG et les demarches a suivre. C'est un complement indispensable aux graphiques.

**Independent Test**: Demander "Explique-moi le processus de certification ESG" et verifier qu'un diagramme s'affiche correctement avec les couleurs de la marque.

**Acceptance Scenarios**:

1. **Given** une conversation active, **When** le conseiller genere un bloc mermaid, **Then** un diagramme SVG s'affiche avec les couleurs de la marque.
2. **Given** un diagramme complexe affiche, **When** l'utilisateur clique sur "Agrandir", **Then** le diagramme s'ouvre en plein ecran.
3. **Given** un bloc mermaid avec une syntaxe invalide, **When** le message est rendu, **Then** le code brut est affiche avec un message d'erreur discret.

---

### User Story 4 - Blocs visuels complementaires : tableau, jauge, progression, timeline (Priority: P2)

Le conseiller peut enrichir ses reponses avec des tableaux comparatifs, des jauges de score, des barres de progression et des frises chronologiques. Ces blocs s'integrent naturellement dans le fil de conversation.

**Why this priority**: Ces blocs visuels enrichissent significativement l'experience mais ne sont pas aussi critiques que les graphiques et diagrammes pour un premier MVP.

**Independent Test**: Peut etre teste en envoyant des prompts qui declenchent chaque type de bloc et en verifiant le rendu.

**Acceptance Scenarios**:

1. **Given** le conseiller genere un bloc table, **When** le message est rendu, **Then** un tableau style s'affiche avec scroll horizontal sur mobile si necessaire.
2. **Given** le conseiller genere un bloc gauge avec des seuils, **When** le message est rendu, **Then** une jauge circulaire animee s'affiche avec la couleur correspondant au seuil (rouge/orange/vert).
3. **Given** le conseiller genere un bloc progress, **When** le message est rendu, **Then** des barres de progression horizontales animees s'affichent.
4. **Given** le conseiller genere un bloc timeline, **When** le message est rendu, **Then** une frise chronologique verticale s'affiche avec des points colores par statut.
5. **Given** un tableau avec tri activable, **When** l'utilisateur clique sur un en-tete de colonne, **Then** le tableau se trie par cette colonne.

---

### User Story 5 - Gestion des conversations (Priority: P2)

L'utilisateur peut gerer ses conversations : les renommer, les supprimer, et rechercher parmi ses conversations passees.

**Why this priority**: La gestion des conversations est importante pour l'experience utilisateur a long terme mais n'est pas bloquante pour un premier usage.

**Independent Test**: Creer plusieurs conversations, en renommer une, en supprimer une, rechercher par titre.

**Acceptance Scenarios**:

1. **Given** une conversation existante, **When** l'utilisateur modifie son titre, **Then** le nouveau titre est sauvegarde et affiche dans la liste.
2. **Given** une conversation existante, **When** l'utilisateur la supprime, **Then** la conversation et ses messages sont supprimes et n'apparaissent plus dans la liste.
3. **Given** plusieurs conversations, **When** l'utilisateur tape dans le champ de recherche, **Then** la liste est filtree par titre.

---

### User Story 6 - Mode guide pour les nouveaux utilisateurs (Priority: P2)

Lorsqu'un utilisateur demarre une nouvelle conversation, le conseiller affiche un menu visuel proposant les principales actions possibles, accompagne d'un message d'accueil.

**Why this priority**: Le mode guide ameliore significativement l'experience du premier usage mais n'est pas indispensable au fonctionnement de base.

**Independent Test**: Creer une nouvelle conversation et verifier que le message d'accueil avec le diagramme de navigation s'affiche automatiquement.

**Acceptance Scenarios**:

1. **Given** un utilisateur qui cree une nouvelle conversation, **When** la conversation s'ouvre, **Then** un message d'accueil s'affiche avec un diagramme de navigation proposant les actions principales et le texte "Comment puis-je vous aider aujourd'hui ?".

---

### User Story 7 - Experience mobile responsive (Priority: P2)

Sur mobile, la liste des conversations est accessible via un drawer lateral, les graphiques s'adaptent a la largeur de l'ecran, et les tableaux offrent un scroll horizontal.

**Why this priority**: Une part significative des utilisateurs PME africaines accede a internet via mobile. La responsivite est essentielle pour le public cible.

**Independent Test**: Ouvrir le chat sur un ecran mobile (ou en simulation), naviguer entre les conversations et verifier le rendu des blocs visuels.

**Acceptance Scenarios**:

1. **Given** un ecran mobile (< 768px), **When** l'utilisateur accede au chat, **Then** la liste des conversations est cachee et accessible via un bouton hamburger ou un swipe.
2. **Given** un graphique dans un message sur mobile, **When** le message est rendu, **Then** le graphique s'adapte a la largeur de l'ecran (hauteur 250px).
3. **Given** un tableau large dans un message sur mobile, **When** le message est rendu, **Then** le tableau offre un scroll horizontal.

---

### User Story 8 - Copie de messages et streaming fluide (Priority: P3)

L'utilisateur peut copier le contenu textuel d'un message de Claude (sans les visuels rendus). Le streaming est fluide avec un indicateur de chargement, et les blocs visuels affichent un placeholder pendant leur generation.

**Why this priority**: Ce sont des ameliorations d'experience utilisateur qui polissent le produit mais ne sont pas critiques pour la fonctionnalite de base.

**Independent Test**: Envoyer un message, observer l'indicateur de chargement, puis copier la reponse et verifier que le texte brut est copie sans le HTML des visuels.

**Acceptance Scenarios**:

1. **Given** un message du conseiller contenant du texte et des visuels, **When** l'utilisateur clique sur "Copier", **Then** seul le texte brut (markdown) est copie dans le presse-papiers.
2. **Given** une requete envoyee, **When** le conseiller commence a generer sa reponse, **Then** un indicateur de chargement anime s'affiche.
3. **Given** un bloc visuel en cours de streaming, **When** le bloc n'est pas encore complet, **Then** un placeholder "Generation du graphique..." avec un spinner est affiche.
4. **Given** le streaming d'un nouveau message, **When** du texte arrive, **Then** la vue scrolle automatiquement vers le bas.

---

### Edge Cases

- Que se passe-t-il quand le reseau est interrompu pendant le streaming d'une reponse ? Le message partiel doit etre conserve et un message d'erreur affiche.
- Comment le systeme reagit-il si l'utilisateur envoie un message alors qu'une reponse est encore en cours de streaming ? L'envoi est bloque jusqu'a la fin du streaming en cours.
- Que se passe-t-il si le JSON d'un bloc chart contient du code malveillant (tentative XSS) ? Le JSON est parse avec JSON.parse() et les chaines sanitizees, empechant l'execution de code.
- Comment le systeme se comporte-t-il quand un utilisateur atteint la limite de 30 messages par minute ? Un message d'erreur clair indique d'attendre avant de renvoyer.
- Que se passe-t-il si un message contient plusieurs blocs visuels de types differents melanges avec du texte ? Chaque bloc est rendu independamment et le texte entre les blocs est rendu en markdown.
- Comment le systeme gere-t-il un diagramme extremement long qui depasse la zone de message ? Le bouton "Agrandir" permet de le voir en plein ecran ; dans le message, il est contenu avec un overflow masque.
- Que se passe-t-il quand l'utilisateur tente d'envoyer un message vide ? Le bouton d'envoi est desactive si le champ est vide.

## Requirements *(mandatory)*

### Functional Requirements

**Gestion des conversations**
- **FR-001**: Le systeme DOIT permettre a un utilisateur authentifie de creer une nouvelle conversation.
- **FR-002**: Le systeme DOIT lister les conversations de l'utilisateur avec leur titre et date, ordonnees par activite recente.
- **FR-003**: Le systeme DOIT permettre de consulter une conversation existante avec tout son historique de messages.
- **FR-004**: Le systeme DOIT permettre de renommer une conversation.
- **FR-005**: Le systeme DOIT permettre de supprimer une conversation et tout son contenu.
- **FR-006**: Le systeme DOIT generer automatiquement un titre pour la conversation apres le premier echange.
- **FR-007**: Le systeme DOIT permettre la recherche de conversations par titre.

**Messagerie et streaming**
- **FR-008**: Le systeme DOIT permettre a l'utilisateur d'envoyer un message texte dans une conversation.
- **FR-009**: Le systeme DOIT transmettre la reponse du conseiller en streaming (tokens en temps reel).
- **FR-010**: Le systeme DOIT rendre le markdown standard dans les reponses (listes, gras, italique, code, liens).
- **FR-011**: Le systeme DOIT afficher un indicateur de chargement quand le conseiller genere sa reponse.
- **FR-012**: Le systeme DOIT scroller automatiquement vers le bas lors de l'arrivee de nouveaux messages.
- **FR-013**: Le systeme DOIT limiter l'envoi a 30 messages par minute par utilisateur.
- **FR-014**: Le systeme DOIT bloquer l'envoi d'un nouveau message tant qu'une reponse est en cours de streaming.

**Rendu visuel enrichi (Rich Blocks)**
- **FR-015**: Le systeme DOIT detecter les blocs de code speciaux (chart, mermaid, table, gauge, progress, timeline) dans les reponses et les rendre en composants visuels.
- **FR-016**: Le systeme DOIT rendre les blocs chart en graphiques interactifs (bar, line, pie, doughnut, radar, polarArea) avec tooltips au survol.
- **FR-017**: Le systeme DOIT rendre les blocs mermaid en diagrammes SVG avec les couleurs de la marque.
- **FR-018**: Le systeme DOIT rendre les blocs table en tableaux styles, avec tri par colonne optionnel et scroll horizontal sur mobile.
- **FR-019**: Le systeme DOIT rendre les blocs gauge en jauges circulaires animees avec couleur dynamique basee sur les seuils.
- **FR-020**: Le systeme DOIT rendre les blocs progress en barres de progression horizontales animees.
- **FR-021**: Le systeme DOIT rendre les blocs timeline en frises chronologiques verticales avec points colores par statut.
- **FR-022**: Le systeme DOIT proposer un bouton "Agrandir" pour les graphiques et diagrammes, ouvrant une vue plein ecran (modale).
- **FR-023**: Le systeme DOIT proposer un bouton "Telecharger" pour les graphiques, generant un export PNG.
- **FR-024**: Le systeme DOIT rendre le texte normal entre les blocs visuels correctement en markdown.

**Gestion des erreurs visuelles**
- **FR-025**: Le systeme DOIT afficher le code brut avec le message "Impossible d'afficher la visualisation" si le JSON d'un bloc est invalide.
- **FR-026**: Le systeme DOIT afficher un fallback en code brut si une librairie de rendu echoue.
- **FR-027**: Le systeme DOIT parser le JSON avec des methodes securisees et sanitizer les chaines avant insertion dans le DOM (prevention XSS).

**Streaming des blocs visuels**
- **FR-028**: Le systeme DOIT attendre la fermeture d'un bloc de code avant de tenter le rendu visuel.
- **FR-029**: Le systeme DOIT afficher un placeholder "Generation du graphique..." avec un spinner pendant le streaming d'un bloc visuel incomplet.

**Mode guide**
- **FR-030**: Le systeme DOIT afficher un message d'accueil avec un diagramme de navigation lors de la creation d'une nouvelle conversation.

**Interface responsive**
- **FR-031**: Le systeme DOIT afficher la liste des conversations dans un drawer lateral sur mobile (< 768px), accessible par bouton hamburger ou swipe.
- **FR-032**: Les graphiques DOIVENT s'adapter a la largeur du conteneur (250px de hauteur sur mobile, 300px sur desktop).

**Copie de messages**
- **FR-033**: Le systeme DOIT permettre de copier le contenu textuel brut d'un message du conseiller (sans les visuels rendus).

### Key Entities

- **Conversation**: Represente un echange entre l'utilisateur et le conseiller. Attributs : identifiant, utilisateur proprietaire, titre (auto-genere), reference au fil de traitement associe, dates de creation et mise a jour.
- **Message**: Un element dans une conversation. Attributs : identifiant, conversation parente, role (utilisateur/assistant/systeme), contenu textuel (pouvant inclure des blocs visuels encodes), date de creation.
- **Bloc Visuel (Rich Block)**: Sous-partie d'un message contenant une visualisation. Types : chart, mermaid, table, gauge, progress, timeline. Parse a partir du contenu textuel du message, non stocke separement.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: L'utilisateur peut creer une conversation et recevoir une premiere reponse en streaming en moins de 5 secondes apres l'envoi du message.
- **SC-002**: 100% des types de blocs visuels (chart, mermaid, table, gauge, progress, timeline) sont rendus correctement quand les donnees sont valides.
- **SC-003**: Les blocs visuels avec donnees invalides degradent gracieusement dans 100% des cas (affichage code brut au lieu d'un crash).
- **SC-004**: Les graphiques et diagrammes s'affichent correctement sur des ecrans de 320px a 1920px de largeur.
- **SC-005**: L'utilisateur peut retrouver et consulter une conversation passee avec tous ses messages et visuels en moins de 3 secondes.
- **SC-006**: Le mode guide s'affiche dans 100% des nouvelles conversations.
- **SC-007**: Le test de reference — demander "Montre-moi un exemple de radar chart ESG" — produit un graphique radar fonctionnel et interactif dans le chat.
- **SC-008**: L'interface mobile est utilisable avec tous les gestes standards (scroll, swipe, tap) sans perte de fonctionnalite.

## Assumptions

- L'authentification utilisateur est deja implementee et fonctionnelle (feature 001).
- Le graphe LangGraph minimal et les noeuds chat/router sont deja en place.
- Chart.js et Mermaid.js sont deja installes comme dependances du projet.
- Le layout principal de l'application (header, navigation) est deja en place.
- Les utilisateurs disposent d'une connexion internet stable pour le streaming SSE.
- Le systeme prompt dans le backend inclut deja les instructions de visualisation pour Claude.
- Le profilage intelligent et la memoire contextuelle sont exclus de cette feature (prevus pour la feature suivante).
- La palette de couleurs de la marque (vert #10B981, bleu #3B82F6, violet #8B5CF6, orange #F59E0B, rouge #EF4444) est celle utilisee pour tous les visuels.
- Le rate limiting (30 messages/minute) est gere cote backend.
