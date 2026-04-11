# Feature Specification: Widgets interactifs pour les questions de l'assistant IA

**Feature Branch**: `018-interactive-chat-widgets`
**Created**: 2026-04-11
**Status**: Draft
**Input**: User description: "un peut comme le fait l'extension de claude code dans vs-code, je veux que les questions du LLM soit plus intéractifs lorsque possible. C'est à dire l'utilisation d'un widget pour les questions à choix multiple QCM/QCU et justification de façon amusante afin optimiser l'expérience utilisateur"

## Clarifications

### Session 2026-04-11

- Q : Qui décide qu'une question est « widgetisable » (LLM à la volée vs catalogue prédéfini vs hybride) ? → A : Le LLM décide et structure le widget à la volée via un tool dédié (`ask_interactive_question`) qui produit le type, l'énoncé, les options, et les contraintes ; aucun catalogue figé n'est maintenu côté backend.
- Q : Quelle est l'autorité des données d'une réponse widget dans le pipeline backend ? → A : La réponse est à la fois un message utilisateur texte (continuité conversationnelle) ET un payload structuré attaché au message, injecté dans l'état LangGraph (`active_module_data`) et consommé directement par les tools du module actif sans re-parsing LLM.
- Q : Que devient un widget affiché si l'utilisateur veut répondre librement ? → A : Choix explicite : un bouton « Répondre autrement » est affiché à côté/dans le widget. Tant que l'utilisateur ne clique pas sur ce bouton, la zone de saisie libre peut être indisponible ou visuellement signaler que le widget attend une réponse ; en cliquant, le widget se ferme/désactive et marque son état « abandonné », puis l'utilisateur saisit librement.
- Q : Comment gérer un widget non répondu lors de la reprise d'un parcours interrompu ? → A : Expiration + régénération. Le widget non répondu est marqué « expiré » dans l'historique (grisé, non cliquable). À la reprise du module (pattern `in_progress` de feature 013), le noeud spécialiste détecte qu'il n'y a pas de réponse structurée pour sa dernière question et génère un nouveau widget équivalent adapté au contexte actuel.
- Q : Limite de caractères pour la justification libre d'un widget ? → A : 400 caractères maximum (environ 2 à 3 phrases). Au-delà, l'utilisateur peut toujours développer via la saisie libre standard s'il en a besoin.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Répondre à une question à choix unique via un widget cliquable (Priority: P1)

Lorsque l'assistant ESG pose une question fermée à choix unique (exemple : « Votre entreprise exploite-t-elle un système de gestion des déchets ? »), la réponse ne s'affiche plus sous forme de simple texte à saisir. Un widget interactif s'affiche dans la bulle de l'assistant avec les options proposées (Oui, Non, Je ne sais pas, etc.). L'utilisateur clique sur l'option souhaitée et la conversation continue automatiquement avec cette réponse envoyée comme message utilisateur, sans que l'utilisateur ait à retaper le texte.

**Why this priority** : C'est le cas le plus fréquent dans les parcours actuels (onboarding profil entreprise, questionnaire ESG, questionnaire carbone, scoring crédit). Réduire la friction de saisie sur ces questions fermées améliore immédiatement le taux de complétion des questionnaires, qui est le KPI cœur de la plateforme. Cette story seule livre déjà un MVP utilisable.

**Independent Test** : L'utilisateur ouvre le chat, lance un module (ESG, carbone ou profiling), reçoit une question à choix unique affichée sous forme de boutons, clique sur une option et observe (1) la réponse apparaît dans l'historique comme un message utilisateur normal, (2) l'assistant poursuit le parcours avec cette réponse, (3) les boutons du widget se désactivent pour empêcher un double clic.

**Acceptance Scenarios** :

1. **Given** l'utilisateur discute avec l'assistant dans le parcours de profiling entreprise, **When** l'assistant pose une question de type QCU (« Quelle est la taille de votre entreprise ? » avec options Micro / TPE / PME / ETI), **Then** un widget boutons radio s'affiche sous le texte de la question, chaque option est cliquable, et aucune saisie libre n'est requise pour avancer.
2. **Given** le widget QCU est affiché, **When** l'utilisateur clique sur « PME », **Then** l'option cliquée est envoyée comme message utilisateur, elle apparaît dans l'historique avec le libellé choisi, tous les boutons du widget deviennent inactifs (désactivés visuellement), et l'assistant enchaîne sur la question suivante.
3. **Given** l'utilisateur a répondu à une question widgetisée et recharge la page, **When** l'historique de la conversation est rechargé, **Then** le message utilisateur contenant la réponse choisie est bien présent et le widget initial apparaît en état « déjà répondu ».

---

### User Story 2 — Répondre à une question à choix multiples (QCM) (Priority: P1)

Lorsque l'assistant pose une question où plusieurs réponses sont possibles (exemple : « Parmi ces sources d'énergie, lesquelles utilisez-vous ? » avec Électricité nationale, Groupe électrogène, Solaire, Biomasse), le widget permet à l'utilisateur de cocher plusieurs options puis de valider son choix via un bouton « Valider ». L'ensemble des options sélectionnées est envoyé comme une seule réponse utilisateur.

**Why this priority** : Les questionnaires carbone, ESG et financement vert comportent de nombreuses questions à choix multiples. Actuellement, l'utilisateur doit lister ses réponses au clavier, ce qui est lent, sujet à erreur, et oblige l'assistant à re-parser du texte libre. Cette story complète la story 1 pour couvrir tous les cas standards de saisie guidée.

**Independent Test** : L'utilisateur reçoit une question QCM, coche 2 ou 3 options, clique sur « Valider », et observe que (1) un message utilisateur unique listant les options choisies apparaît dans l'historique, (2) l'assistant continue avec ces réponses prises en compte, (3) la sélection partielle sans validation n'envoie rien.

**Acceptance Scenarios** :

1. **Given** l'assistant carbone pose « Parmi ces sources d'énergie, lesquelles utilisez-vous ? », **When** l'utilisateur coche « Électricité nationale » et « Solaire » puis clique « Valider », **Then** un message utilisateur « Électricité nationale, Solaire » est envoyé et l'assistant poursuit avec ces deux sources enregistrées.
2. **Given** un widget QCM est affiché, **When** l'utilisateur ne sélectionne aucune option et clique « Valider », **Then** le bouton « Valider » est désactivé ou la validation est bloquée avec un retour visuel « Sélectionnez au moins une option ».
3. **Given** un widget QCM est affiché avec une contrainte « minimum 1, maximum 3 », **When** l'utilisateur tente de cocher une 4ᵉ option, **Then** la sélection est bloquée ou un message avertit qu'il faut décocher d'abord.

---

### User Story 3 — Répondre avec justification libre amusante après un choix (Priority: P2)

Pour certaines questions, après avoir fait son choix parmi des options, l'utilisateur est invité à justifier brièvement sa réponse dans un champ texte intégré au même widget, avec un ton engageant (exemple d'invite : « En une phrase, racontez-nous pourquoi 🙂 »). La justification est optionnelle ou obligatoire selon la question. Le choix et la justification sont envoyés comme une seule réponse utilisateur structurée.

**Why this priority** : La justification libre enrichit le profil qualitatif de l'entreprise (notamment pour l'évaluation ESG et le scoring crédit alternatif) et rend l'expérience moins sèche que de simples clics. Elle est prioritaire P2 car elle apporte une valeur différenciante sans être bloquante pour le MVP de la story 1 et 2.

**Independent Test** : L'utilisateur reçoit une question combinant choix + justification, sélectionne une option, écrit une justification courte, valide, et observe que (1) le message utilisateur agrège proprement le choix et la justification, (2) l'assistant prend bien en compte les deux éléments dans sa réponse suivante.

**Acceptance Scenarios** :

1. **Given** l'assistant ESG pose « Avez-vous un processus de tri des déchets ? » avec options Oui / Non / En cours et un champ justification optionnel, **When** l'utilisateur choisit « En cours » et tape « On démarre avec le plastique et le papier », **Then** la réponse envoyée contient à la fois le choix et la justification et l'assistant les exploite dans sa réponse suivante.
2. **Given** une question exige une justification obligatoire, **When** l'utilisateur tente de valider sans rien écrire, **Then** la validation est bloquée avec un message invitant à remplir la justification.
3. **Given** l'utilisateur ouvre le widget et clique sur une option mais ne valide pas, **When** il ferme et rouvre la conversation, **Then** la sélection non validée n'est pas persistée (seul l'état « sans réponse » est conservé).

---

### User Story 4 — Saisie libre classique quand la question ne s'y prête pas (Priority: P1)

Lorsque la question posée par l'assistant ne peut pas raisonnablement être réduite à des choix (exemple : « Décrivez votre projet en quelques lignes », « Quel est le nom de votre entreprise ? »), aucun widget n'est affiché et l'expérience reste celle du chat classique à saisie libre. Le moteur doit savoir décider quand une question est « widgetisable » et quand elle ne l'est pas.

**Why this priority** : Sans cette story, le widget risque d'apparaître de manière forcée et maladroite sur des questions ouvertes, dégradant l'expérience. C'est donc un P1 fondamental même s'il n'apporte pas de nouveauté visuelle : il préserve la qualité existante.

**Independent Test** : L'utilisateur lance un parcours, constate que les questions factuelles ouvertes (nom, description, texte libre) ne déclenchent pas de widget, et que la zone de saisie standard reste disponible et fonctionnelle.

**Acceptance Scenarios** :

1. **Given** l'utilisateur est en phase de profiling, **When** l'assistant demande « Quel est le nom de votre entreprise ? », **Then** aucun widget n'apparaît et l'utilisateur répond via la zone de saisie standard.
2. **Given** l'assistant a hésité et a proposé à tort un widget sur une question ouverte, **When** l'utilisateur préfère répondre librement, **Then** il doit pouvoir malgré tout saisir une réponse libre dans la zone de saisie standard sans être forcé de cliquer dans le widget.

---

### Edge Cases

- **Double réponse** : l'utilisateur clique sur une option d'un widget déjà validé (via un second onglet ou une reconnexion). Le système doit ignorer la deuxième soumission et ne pas dupliquer la réponse dans l'historique.
- **Changement de module pendant l'affichage d'un widget** : l'utilisateur change de sujet (passe du questionnaire ESG au chat général) alors qu'un widget est affiché. Le widget devient caduc, ne bloque pas la nouvelle conversation, et son état est marqué « abandonné ».
- **Rechargement de page / reprise différée** : au rechargement, un widget déjà répondu s'affiche en état « réponse finale visible / boutons désactivés ». Un widget non répondu est toujours marqué « expiré » dans l'historique (grisé, non cliquable) : à la reprise d'un module encore `in_progress`, le noeud spécialiste détecte l'absence de réponse structurée et régénère une nouvelle question widgetisée adaptée au contexte courant. Si le module n'est plus actif, le widget reste simplement visible en lecture comme trace historique expirée.
- **Accessibilité clavier et lecteurs d'écran** : chaque widget doit être utilisable au clavier (Tab, Espace/Entrée, flèches) et annoncer correctement les options et les états aux lecteurs d'écran.
- **Options longues ou nombreuses** : une question avec 10+ options doit rester lisible (wrap, scroll, ou recherche intégrée) sans casser la mise en page de la bulle de chat.
- **Widget incompatible côté ancien client** : un ancien client frontend ne sachant pas interpréter le widget doit malgré tout afficher la question et les options sous forme de texte lisible, pour ne pas bloquer l'utilisateur.
- **Annulation de la sélection** : l'utilisateur change d'avis avant validation (QCM/QCU+justification) ; il doit pouvoir décocher/désélectionner tant que la validation n'a pas été envoyée.
- **Bouton « Répondre autrement » cliqué par erreur** : l'utilisateur a cliqué sur « Répondre autrement » mais préfère finalement utiliser le widget. Le widget étant marqué « abandonné », il n'est plus cliquable ; l'utilisateur doit saisir sa réponse librement ou attendre que l'assistant repose la question.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** : L'assistant IA DOIT produire les widgets à la volée via un tool structuré dédié (`ask_interactive_question`) qui renvoie : énoncé, type de widget (QCU, QCM, QCU+justification, QCM+justification), liste d'options avec libellé affiché et valeur canonique, contraintes de sélection (min/max pour QCM), obligation ou non de la justification, et texte d'invite pour la justification. Aucun catalogue de questions figé n'est maintenu côté backend — la décision de widgetiser et le contenu du widget sont entièrement déterminés par le LLM en fonction du contexte conversationnel.
- **FR-002** : L'interface de chat DOIT rendre le widget interactif correspondant lorsqu'une question « widgetisable » est reçue, dans la bulle de l'assistant, en conservant l'énoncé textuel lisible au-dessus des contrôles.
- **FR-003** : L'utilisateur DOIT pouvoir répondre à une question QCU par un clic unique sur une option, ce clic envoyant automatiquement la réponse sans action supplémentaire.
- **FR-004** : L'utilisateur DOIT pouvoir répondre à une question QCM en sélectionnant une ou plusieurs options puis en validant via un bouton explicite « Valider » (ou équivalent), l'envoi n'ayant lieu qu'à la validation.
- **FR-005** : Pour les widgets avec justification, l'utilisateur DOIT pouvoir saisir un texte libre d'au maximum 400 caractères associé à son choix. Un compteur visible (X / 400) DOIT indiquer la limite et empêcher tout dépassement côté interface. La réponse envoyée DOIT contenir à la fois les options sélectionnées (valeurs canoniques) et la justification tronquée à 400 caractères côté backend en cas de contournement client.
- **FR-006** : Le système DOIT enregistrer la réponse du widget sous deux formes indissociables : (1) un message utilisateur texte lisible (libellés humains des options choisies + justification éventuelle) pour la continuité conversationnelle et l'historique, et (2) un payload structuré (valeurs canoniques des options et justification) attaché au même message, injecté dans l'état LangGraph (`active_module_data`) et directement consommable par les tools du module actif sans re-parsing LLM.
- **FR-007** : Le système DOIT empêcher qu'un même widget soit répondu plusieurs fois : après validation, les contrôles sont désactivés et un nouvel envoi pour le même widget est ignoré côté serveur.
- **FR-008** : Le système DOIT détecter lorsqu'une question est ouverte (texte libre) et NE PAS afficher de widget dans ce cas, la zone de saisie standard restant le canal de réponse.
- **FR-009** : Le système DOIT afficher un état « déjà répondu » pour les widgets des messages précédents lors du rechargement de l'historique, avec la sélection finale visible et les contrôles désactivés.
- **FR-010** : Le système DOIT respecter les contraintes de sélection d'un widget QCM (par exemple « minimum 1, maximum 3 ») et empêcher côté interface toute sélection hors contrainte, avec retour visuel explicite.
- **FR-011** : Les widgets DOIVENT être compatibles dark mode, comme le reste de l'interface de chat.
- **FR-012** : Les widgets DOIVENT être accessibles au clavier (navigation Tab, activation Entrée/Espace, gestion du focus) et compatibles avec les lecteurs d'écran (libellés explicites, annonces des états sélectionné / désélectionné / désactivé).
- **FR-013** : Lorsqu'un client frontend ne sait pas rendre un widget reçu, l'énoncé et les options DOIVENT rester visibles sous une forme textuelle lisible afin que l'utilisateur puisse répondre malgré tout.
- **FR-014** : L'utilisateur DOIT garder la possibilité de répondre en texte libre via un bouton explicite « Répondre autrement » intégré au widget. Ce bouton ferme et désactive le widget (état « abandonné ») et rend la zone de saisie libre disponible pour une réponse personnalisée. Tant que le bouton n'est pas activé, le widget reste la source de réponse attendue.
- **FR-015** : Le ton des invites de justification DOIT être engageant et cohérent avec le style conversationnel de l'assistant (par exemple « En une phrase, racontez-nous pourquoi 🙂 »), sans toutefois devenir intrusif ou obligatoire quand ce n'est pas nécessaire.
- **FR-016** : Les widgets DOIVENT être disponibles dans les modules où des questions fermées existent déjà : profiling entreprise, évaluation ESG, calculateur carbone, scoring crédit, financement vert, plan d'action. Le chat général sans module actif DOIT continuer de fonctionner en texte libre.

### Key Entities *(include if feature involves data)*

- **Question interactive** : représente une question posée par l'assistant qui peut être répondue via widget. Attributs clés : identifiant unique de question, type (QCU, QCM, QCU+justification, QCM+justification), énoncé, liste d'options, contraintes de sélection (min/max), exigence de justification, invite de justification. Elle est attachée à un message assistant donné dans une conversation.
- **Option de question** : une valeur proposée à l'utilisateur. Attributs clés : libellé affiché, valeur canonique renvoyée à l'assistant, éventuelle description courte.
- **Réponse interactive** : représente la réponse donnée par l'utilisateur via un widget. Attributs clés : identifiant de la question interactive associée, liste des valeurs choisies, justification libre éventuelle, état (soumise / abandonnée), horodatage. Elle se matérialise dans l'historique comme un message utilisateur standard pour la continuité de la conversation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** : Dans les modules où les questions sont majoritairement fermées (profiling, ESG, carbone, crédit), au moins 70 % des questions posées par l'assistant s'affichent via un widget interactif au lieu d'un simple texte.
- **SC-002** : Le temps moyen de réponse à une question fermée diminue d'au moins 30 % par rapport au mode texte libre (mesuré sur la durée entre l'affichage de la question et l'envoi de la réponse).
- **SC-003** : Le taux de complétion des questionnaires ESG et carbone (utilisateurs qui terminent le questionnaire jusqu'au score final) augmente d'au moins 15 points de pourcentage après mise en production des widgets.
- **SC-004** : Moins de 2 % des réponses envoyées via widget génèrent une incompréhension de l'assistant (mesuré par le taux de re-demande de la même information par l'assistant).
- **SC-005** : 100 % des widgets sont utilisables uniquement au clavier (validation par audit d'accessibilité interne).
- **SC-006** : Aucun widget existant ne rend un questionnaire plus lent qu'avant : le temps médian de complétion d'un parcours (onboarding, ESG, carbone) reste inférieur ou égal au temps médian mesuré avant cette fonctionnalité.
- **SC-007** : Lors d'un rechargement de page en cours de parcours, 100 % des widgets déjà répondus affichent correctement leur état final. 100 % des widgets non répondus s'affichent en état « expiré » dans l'historique, et si le module correspondant est encore `in_progress`, une nouvelle question widgetisée équivalente est régénérée par le noeud spécialiste dès la reprise.

## Assumptions

- L'assistant IA est déjà capable, via son architecture de prompts et d'outils, de produire des réponses structurées ; cette fonctionnalité s'appuie sur ce socle existant et n'exige pas une refonte de l'architecture LLM.
- Les parcours concernés (profiling, ESG, carbone, crédit, financement, plan d'action) possèdent déjà un inventaire implicite des questions fermées récurrentes, qui pourront être converties en questions widgetisables.
- Le ton « amusant » pour les invites de justification reste cohérent avec la charte éditoriale existante du produit en français (accents, style concis défini par la feature 014). Les invites ne contiennent pas d'éléments culturellement inappropriés pour le public cible PME africaines francophones.
- Le chat général hors module conserve son fonctionnement texte libre et n'est pas impacté par cette fonctionnalité.
- Les contraintes d'affichage (nombre d'options, longueur des libellés) sont bornées : une question avec plus de 15 options sera considérée comme une question nécessitant une autre forme d'interaction (recherche, arbre, etc.) hors scope de cette v1.
- Les widgets sont rendus uniquement dans l'interface web du chat (desktop et mobile). Les éventuelles intégrations externes (extension Chrome de la feature 8, exports PDF) ne sont pas concernées par cette v1 : elles continuent à voir le message utilisateur rendu sous sa forme textuelle.
- L'expérience cible s'inspire de l'extension Claude Code dans VS Code pour la sensation d'interactivité, mais le design visuel respecte la charte Tailwind/dark mode déjà en place.
