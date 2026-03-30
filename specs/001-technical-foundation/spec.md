# Feature Specification: Foundation Technique ESG Mefali

**Feature Branch**: `001-technical-foundation`
**Created**: 2026-03-30
**Status**: Draft
**Input**: User description: "Foundation technique du projet ESG Mefali — socle infrastructure sur lequel tous les modules metier seront construits. Aucune logique metier ESG dans cette feature."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inscription et connexion (Priority: P1)

Un nouveau visiteur arrive sur la plateforme ESG Mefali. Il doit pouvoir creer un compte avec ses informations de base (email, mot de passe, nom complet, nom d'entreprise), puis se connecter pour acceder a un espace protege. Une fois connecte, il voit une page d'accueil vide qui servira de futur tableau de bord.

**Why this priority**: Sans authentification, aucun autre module ne peut fonctionner. C'est le point d'entree obligatoire de toute l'application.

**Independent Test**: Peut etre teste en creant un compte, se connectant, verifiant l'acces a la page d'accueil protegee, puis en se deconnectant.

**Acceptance Scenarios**:

1. **Given** un visiteur non inscrit, **When** il remplit le formulaire d'inscription avec email, mot de passe, nom complet et nom d'entreprise, **Then** son compte est cree et il est redirige vers la page de connexion avec un message de succes.
2. **Given** un utilisateur inscrit, **When** il saisit ses identifiants corrects sur la page de connexion, **Then** il est authentifie et redirige vers la page d'accueil protegee.
3. **Given** un utilisateur inscrit, **When** il saisit un mot de passe incorrect, **Then** il recoit un message d'erreur clair sans reveler si l'email existe.
4. **Given** un utilisateur non authentifie, **When** il tente d'acceder a la page d'accueil protegee, **Then** il est redirige vers la page de connexion.
5. **Given** un utilisateur connecte, **When** son jeton d'authentification expire, **Then** le systeme tente un rafraichissement automatique avant de le deconnecter.

---

### User Story 2 - Conversation IA de base (Priority: P1)

Un utilisateur connecte dispose d'un panneau de conversation IA persistant, accessible depuis n'importe quelle page de l'application. Il envoie un message en francais. Le systeme transmet ce message a un assistant IA qui repond en streaming (les mots apparaissent progressivement). L'historique de la conversation est conserve entre les sessions.

**Why this priority**: Le coeur de la plateforme est l'agent conversationnel IA. Sans cette brique, aucun module metier ne peut etre construit par-dessus.

**Independent Test**: Peut etre teste en envoyant un message et en verifiant qu'une reponse streamee arrive, puis en rechargeant la page pour verifier que l'historique est conserve.

**Acceptance Scenarios**:

1. **Given** un utilisateur connecte, **When** il envoie un message texte, **Then** il recoit une reponse de l'assistant IA affichee progressivement (streaming).
2. **Given** un utilisateur ayant deja eu une conversation, **When** il revient sur la plateforme, **Then** il voit la liste de ses conversations et peut reprendre n'importe laquelle.
3. **Given** un utilisateur connecte, **When** il clique sur "nouvelle conversation", **Then** un nouveau thread est cree et il peut commencer a echanger.
4. **Given** un utilisateur connecte, **When** le service IA est temporairement indisponible, **Then** il recoit un message d'erreur comprehensible l'invitant a reessayer.

---

### User Story 3 - Lancement de l'environnement de developpement (Priority: P1)

Un developpeur rejoint le projet et doit pouvoir lancer l'ensemble de l'environnement (frontend, backend, base de donnees) avec une seule commande. Il doit avoir acces a la documentation technique auto-generee du backend.

**Why this priority**: Sans un environnement de developpement fonctionnel, aucun travail ne peut commencer sur les modules metier.

**Independent Test**: Peut etre teste en clonant le depot, lancant la commande unique de demarrage, et verifiant que les 3 services sont accessibles.

**Acceptance Scenarios**:

1. **Given** un developpeur avec les prerequis installes, **When** il lance la commande de demarrage, **Then** les trois services (frontend, backend, base de donnees) demarrent et sont accessibles.
2. **Given** les services en cours d'execution, **When** le developpeur accede a la documentation du backend, **Then** il voit la documentation interactive auto-generee de tous les endpoints.
3. **Given** un projet fraichement clone, **When** le developpeur suit les instructions du README, **Then** il a un environnement fonctionnel sans configuration manuelle supplementaire au-dela des variables d'environnement.

---

### User Story 4 - Navigation et interface de base (Priority: P2)

Un utilisateur connecte navigue dans l'application via une sidebar retractable. Un panneau de chat IA est visible en permanence sur le cote droit (repliable sur mobile). Sur mobile, la sidebar de navigation est masquee par defaut et accessible via un bouton menu. L'interface utilise un design system coherent avec les couleurs de la marque. Les notifications (succes, erreur, info) s'affichent via des toasts.

**Why this priority**: L'interface de navigation est necessaire pour structurer les futurs modules, mais un prototype minimal peut fonctionner sans elle.

**Independent Test**: Peut etre teste en naviguant entre les pages, en retractant/deployant la sidebar, en verifiant le responsive mobile, et en declenchant des notifications toast.

**Acceptance Scenarios**:

1. **Given** un utilisateur connecte sur desktop, **When** il clique sur le bouton de retraction de la sidebar, **Then** la sidebar se replie et la zone de contenu s'elargit.
2. **Given** un utilisateur sur mobile, **When** il charge l'application, **Then** la sidebar est masquee et un bouton menu est visible.
3. **Given** une action reussie (ex: connexion), **When** le systeme affiche une notification, **Then** un toast de succes apparait et disparait automatiquement apres quelques secondes.
4. **Given** une erreur (ex: echec de connexion), **When** le systeme affiche une notification, **Then** un toast d'erreur apparait avec un message comprehensible.

---

### User Story 5 - Verification de sante du systeme (Priority: P3)

Un operateur ou un systeme de monitoring interroge le point de sante du backend pour verifier que le service est en fonctionnement normal.

**Why this priority**: Utile pour la production et le monitoring, mais pas bloquant pour le developpement des fonctionnalites.

**Independent Test**: Peut etre teste en envoyant une requete au point de sante et en verifiant la reponse positive.

**Acceptance Scenarios**:

1. **Given** le backend en fonctionnement, **When** une requete est envoyee au point de sante, **Then** une reponse positive est retournee avec le statut du service.
2. **Given** le backend en fonctionnement, **When** la base de donnees est inaccessible, **Then** le point de sante indique un etat degrade.

---

### Edge Cases

- Que se passe-t-il quand un utilisateur tente de s'inscrire avec un email deja utilise ? Le systeme doit refuser l'inscription avec un message d'erreur clair.
- Comment le systeme reagit-il si la connexion a la base de donnees est perdue en cours de session ? Les requetes en cours echouent gracieusement avec un message d'erreur.
- Que se passe-t-il si le service IA repond avec un delai superieur a 30 secondes ? Un timeout est declenche et l'utilisateur est informe.
- Comment le systeme gere-t-il les jetons d'authentification expires pendant une conversation IA en cours de streaming ? Le rafraichissement automatique est tente ; en cas d'echec, le streaming s'arrete et l'utilisateur est invite a se reconnecter.
- Que se passe-t-il si un utilisateur envoie un message vide ou excessivement long ? Le systeme valide la longueur (1 a 5000 caracteres) et rejette les messages hors limites.

## Requirements *(mandatory)*

### Functional Requirements

**Authentification**

- **FR-001**: Le systeme DOIT permettre l'inscription avec email, mot de passe, nom complet et nom d'entreprise.
- **FR-002**: Le systeme DOIT valider le format de l'email et exiger un mot de passe d'au moins 8 caracteres.
- **FR-003**: Le systeme DOIT hasher les mots de passe avant stockage (jamais en clair).
- **FR-004**: Le systeme DOIT authentifier les utilisateurs via email et mot de passe et retourner un jeton d'acces (duree de vie : 1 heure) et un jeton de rafraichissement (duree de vie : 30 jours).
- **FR-005**: Le systeme DOIT permettre le rafraichissement des jetons d'acces expires via le jeton de rafraichissement.
- **FR-006**: Le systeme DOIT fournir un endpoint pour recuperer le profil de l'utilisateur connecte.
- **FR-007**: Le systeme DOIT proteger les pages et endpoints non publics en exigeant un jeton d'acces valide.

**Conversation IA**

- **FR-008**: Le systeme DOIT transmettre les messages utilisateur a un assistant IA via un panneau lateral persistant (visible sur toutes les pages) et retourner les reponses en streaming (affichage progressif).
- **FR-009**: Le systeme DOIT persister l'etat des conversations entre les sessions pour chaque utilisateur. Un utilisateur peut creer plusieurs conversations et naviguer entre elles.
- **FR-010**: L'assistant IA DOIT repondre en francais avec un ton professionnel et bienveillant.
- **FR-011**: Le systeme DOIT limiter la taille des messages entrants a 5 000 caracteres maximum.

**Interface utilisateur**

- **FR-012**: L'application DOIT proposer un layout responsive mobile-first avec sidebar de navigation retractable, header, zone de contenu principale, et panneau de chat IA lateral persistant.
- **FR-013**: L'application DOIT afficher des notifications toast pour les evenements succes, erreur et info.
- **FR-014**: L'application DOIT utiliser un design system coherent avec les couleurs de la marque definies (vert principal, bleu secondaire, violet, orange, rouge, fond clair, texte sombre).
- **FR-015**: L'application DOIT rediriger les utilisateurs non authentifies vers la page de connexion.

**Infrastructure**

- **FR-016**: Le systeme DOIT pouvoir etre lance dans son integralite (frontend, backend, base de donnees) avec une seule commande.
- **FR-017**: Le backend DOIT exposer une documentation interactive auto-generee de tous les endpoints.
- **FR-018**: Le backend DOIT fournir un endpoint de verification de sante.
- **FR-019**: Le systeme DOIT fournir un fichier de configuration exemple listant toutes les variables d'environnement necessaires.
- **FR-020**: Les bibliotheques de graphiques et de diagrammes DOIVENT etre installees et pretes a l'emploi dans le frontend pour les futures features.

### Key Entities

- **Utilisateur (User)**: Represente une personne inscrite sur la plateforme. Attributs cles : identifiant unique, email (unique), mot de passe hashe, nom complet, nom d'entreprise, date de creation, date de derniere modification.
- **Conversation**: Represente un fil d'echange entre un utilisateur et l'assistant IA. Un utilisateur peut avoir plusieurs conversations. Attributs cles : identifiant unique, titre (auto-genere ou editable), identifiant de l'utilisateur, module courant (par defaut "chat"), date de creation, date de derniere activite.
- **Message**: Unite d'echange dans une conversation. Peut etre de l'utilisateur ou de l'assistant. Contient le contenu textuel et les metadonnees temporelles.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un nouvel utilisateur peut completer le parcours inscription, connexion et acces a la page d'accueil en moins de 2 minutes.
- **SC-002**: La reponse de l'assistant IA commence a s'afficher (premier token) en moins de 3 secondes apres l'envoi du message.
- **SC-003**: L'historique de conversation est restaure integralement lorsqu'un utilisateur revient sur la plateforme.
- **SC-004**: Les trois services demarrent et sont accessibles en moins de 2 minutes apres la commande de lancement.
- **SC-005**: L'interface s'adapte correctement aux ecrans de 320px a 1920px de large.
- **SC-006**: Les tests unitaires d'authentification couvrent au moins 80% du code concerne.
- **SC-007**: Un nouveau developpeur peut avoir un environnement fonctionnel en suivant le README en moins de 10 minutes (hors telechargement des dependances).

## Clarifications

### Session 2026-03-30

- Q: Un utilisateur a-t-il une seule conversation continue ou peut-il creer plusieurs conversations separees ? → A: Plusieurs conversations (threads multiples). L'utilisateur peut creer de nouveaux threads et lister les anciens.
- Q: Quelle duree de vie pour les jetons d'authentification ? → A: Jeton d'acces : 1 heure. Jeton de rafraichissement : 30 jours.
- Q: Comment l'utilisateur accede-t-il au chat ? → A: Le chat est un panneau lateral persistant visible sur toutes les pages (apres connexion). Le dashboard reste la page d'accueil.

## Assumptions

- Les utilisateurs disposent d'une connexion internet stable (cible : PME africaines en zone urbaine).
- Le projet demarre sans utilisateurs existants — pas de migration de donnees necessaire.
- L'assistant IA est accessible via un service tiers (OpenRouter) qui fournit l'acces au modele Claude.
- Le mot de passe est le seul mode d'authentification pour la v1 (pas de SSO, OAuth2, ou authentification biometrique).
- Les emails ne necessitent pas de verification (pas de lien de confirmation) pour la v1.
- La gestion des roles (admin, collaborateur, lecteur) sera implementee dans une feature ulterieure.
- Le stockage de fichiers n'est pas necessaire pour cette foundation technique.
- La plateforme est monolingue francais pour la v1.
- Les limites de taux (rate limiting) sur les endpoints seront implementees dans une feature ulterieure.
