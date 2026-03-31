# Feature Specification: Profilage Intelligent et Memoire Contextuelle

**Feature Branch**: `003-company-profiling-memory`
**Created**: 2026-03-30
**Status**: Draft
**Input**: User description: "Profilage intelligent de l'entreprise par conversation et memoire contextuelle - Modules 1.2 et 1.3"

## Clarifications

### Session 2026-03-30

- Q: Comment sont ponderes les champs pour le calcul du pourcentage de completion et le seuil de 70% ? → A: Seuls les champs d'identite + localisation comptent pour le seuil de 70%. Les champs ESG sont suivis separement avec leur propre pourcentage.
- Q: Quand un resume de conversation est-il genere pour la memoire contextuelle ? → A: Un resume est genere par le LLM a chaque nouveau thread/conversation cree par l'utilisateur (le thread precedent est resume a ce moment).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extraction automatique du profil via conversation (Priority: P1)

Un dirigeant de PME africaine discute naturellement avec son conseiller ESG. Au fil de la conversation, il mentionne des informations sur son entreprise : "je fais du recyclage de plastique a Abidjan avec 15 employes". Le systeme extrait automatiquement ces informations (secteur, ville, effectifs) et met a jour le profil entreprise sans interrompre le flux conversationnel. Une notification discrete confirme la mise a jour.

**Why this priority**: C'est le coeur de la feature - sans extraction automatique, le profilage intelligent n'existe pas. C'est ce qui differencie l'experience d'un simple formulaire.

**Independent Test**: Peut etre teste en envoyant un message contenant des informations d'entreprise et en verifiant que le profil est mis a jour avec les bons champs extraits.

**Acceptance Scenarios**:

1. **Given** un utilisateur avec un profil vide, **When** il envoie "je fais du recyclage de plastique a Abidjan avec 15 employes", **Then** le systeme extrait sector=recyclage, city=Abidjan, employee_count=15 et met a jour le profil automatiquement.
2. **Given** un utilisateur avec un profil partiellement rempli (secteur deja connu), **When** il mentionne "on a un chiffre d'affaires de 50 millions de FCFA", **Then** seul le champ revenue est mis a jour, les champs existants sont preserves.
3. **Given** un utilisateur en conversation, **When** le systeme extrait une information, **Then** une notification discrete apparait dans le chat : "Profil mis a jour : secteur = Recyclage".
4. **Given** un message ambigu comme "on est dans le commerce, enfin plutot l'agroalimentaire", **When** le systeme analyse le message, **Then** seul le dernier choix explicite (agroalimentaire) est retenu avec haute confiance.

---

### User Story 2 - Personnalisation contextuelle des reponses (Priority: P1)

Quand le profil de l'entreprise est connu (meme partiellement), le conseiller ESG adapte ses reponses en fonction du secteur, de la localisation et de la taille de l'entreprise. Il ne repose pas de questions dont il a deja la reponse. Il utilise la memoire des conversations precedentes pour maintenir la continuite.

**Why this priority**: La valeur du profilage reside dans la personnalisation. Sans elle, l'extraction est inutile.

**Independent Test**: Peut etre teste en verifiant que le prompt systeme contient les informations du profil et que les reponses sont contextualisees.

**Acceptance Scenarios**:

1. **Given** un profil avec sector=agriculture et city=Bamako, **When** l'utilisateur demande des conseils ESG, **Then** les reponses sont adaptees au contexte agricole malien (referentiels locaux, fonds disponibles pour le Mali).
2. **Given** un utilisateur qui a deja dit son secteur dans une conversation precedente, **When** il demarre une nouvelle conversation, **Then** le conseiller ne repose pas la question du secteur.
3. **Given** un profil complet a 100%, **When** l'utilisateur interagit avec le chat, **Then** le conseiller celebre cette etape avec une jauge visuelle et propose de passer aux modules d'analyse ESG.

---

### User Story 3 - Profilage guide quand le profil est incomplet (Priority: P2)

Quand le profil de l'utilisateur est en dessous de 70% de completion et que l'utilisateur n'est pas en train d'utiliser un module specifique (scoring ESG, carbone), le conseiller integre naturellement des questions de profilage dans la conversation pour combler les lacunes.

**Why this priority**: Permet de remplir le profil progressivement sans forcer l'utilisateur a remplir un formulaire. Depend de P1 pour fonctionner.

**Independent Test**: Peut etre teste en verifiant que le routeur injecte des instructions de profilage quand le profil est incomplet et que l'utilisateur n'est pas dans un module specifique.

**Acceptance Scenarios**:

1. **Given** un profil a 40% de completion et une conversation generique, **When** le conseiller repond, **Then** il integre une question naturelle sur un champ manquant (ex: "Au fait, combien de personnes travaillent dans votre entreprise ?").
2. **Given** un profil a 40% mais l'utilisateur demande un scoring ESG, **When** le routeur analyse la requete, **Then** il ne force PAS le profilage et laisse le module ESG s'executer.
3. **Given** un profil a 80% de completion, **When** le conseiller interagit, **Then** il ne force pas le profilage car le seuil de 70% est depasse.

---

### User Story 4 - Page profil et edition manuelle (Priority: P2)

L'utilisateur peut consulter et editer son profil entreprise depuis une page dediee accessible dans la sidebar. La page affiche les informations remplies, celles manquantes, et le pourcentage de completion. Un message encourage l'approche conversationnelle.

**Why this priority**: Offre une alternative au profilage conversationnel et permet a l'utilisateur de verifier/corriger les informations extraites.

**Independent Test**: Peut etre teste en accedant a la page profil, en verifiant l'affichage des champs et en modifiant un champ manuellement.

**Acceptance Scenarios**:

1. **Given** un utilisateur connecte, **When** il clique sur "Profil" dans la sidebar, **Then** il voit la page profil avec tous les champs organises par categorie (Identite, Localisation, ESG).
2. **Given** un profil avec des champs vides, **When** l'utilisateur consulte la page, **Then** les champs manquants sont visuellement distincts des champs remplis.
3. **Given** un utilisateur sur la page profil, **When** il modifie un champ et sauvegarde, **Then** le profil est mis a jour et le pourcentage de completion recalcule.
4. **Given** la page profil, **When** elle est affichee, **Then** un message encourage l'approche conversationnelle : "Discutez avec votre conseiller ESG pour completer votre profil naturellement, ou remplissez les champs ci-dessous."

---

### User Story 5 - Indicateur de completion dans la sidebar et visualisations chat (Priority: P3)

La sidebar affiche un badge avec le pourcentage de completion du profil. Dans le chat, le conseiller peut afficher des blocs visuels (progress, gauge) montrant l'etat du profil pour motiver l'utilisateur.

**Why this priority**: Gamification et motivation - important mais pas bloquant pour le fonctionnement du profilage.

**Independent Test**: Peut etre teste en verifiant l'affichage du badge dans la sidebar et des blocs visuels dans le chat.

**Acceptance Scenarios**:

1. **Given** un profil a 65% de completion, **When** l'utilisateur consulte la sidebar, **Then** un badge affiche "65%" a cote du lien profil.
2. **Given** une conversation en cours, **When** le conseiller mentionne la progression du profil, **Then** il utilise un bloc progress montrant la completion par categorie (Identite, Localisation, ESG).
3. **Given** un profil qui vient d'atteindre 100%, **When** le conseiller repond, **Then** il affiche un bloc gauge celebrant la completion totale.

---

### Edge Cases

- Que se passe-t-il quand l'utilisateur fournit des informations contradictoires entre deux conversations ? (ex: "je suis a Abidjan" puis "je suis base a Dakar") - La derniere information prevaut, l'ancienne est ecrasee.
- Que se passe-t-il quand le message contient des informations ambigues ou a faible confiance ? (ex: "on est un peu dans l'agriculture") - Le systeme ne met a jour que les champs avec une confiance elevee.
- Que se passe-t-il quand l'utilisateur modifie manuellement le profil apres une extraction automatique ? - La modification manuelle prevaut toujours.
- Que se passe-t-il quand l'utilisateur n'a pas encore de profil ? - Un profil vide est cree automatiquement a la premiere interaction.
- Que se passe-t-il quand le message contient des informations de profil ET une question metier ? - Les deux sont traitees en parallele : extraction de profil + reponse a la question.
- Que se passe-t-il en mode sombre ? - Tous les composants (page profil, notifications, badges) doivent supporter le dark mode.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le systeme DOIT extraire automatiquement les informations d'entreprise mentionnees dans les messages de l'utilisateur (secteur, ville, effectifs, chiffre d'affaires, etc.) avec un niveau de confiance eleve.
- **FR-002**: Le systeme DOIT stocker le profil entreprise avec les champs : nom, secteur (parmi une liste predeterminee de 11 secteurs), sous-secteur libre, effectifs, chiffre d'affaires en FCFA, ville, pays (defaut Cote d'Ivoire), annee de creation.
- **FR-003**: Le systeme DOIT stocker les indicateurs ESG de base du profil : gestion des dechets, politique energetique, politique genre, programme de formation, transparence financiere, structure de gouvernance, pratiques environnementales, pratiques sociales.
- **FR-004**: Le systeme DOIT calculer deux pourcentages de completion : (1) un pourcentage "identite & localisation" base uniquement sur les champs d'identite (nom, secteur, sous-secteur, effectifs, CA, annee de creation) et de localisation (ville, pays) — c'est ce pourcentage qui determine le seuil de 70% pour le profilage guide (FR-008) ; (2) un pourcentage "ESG" base sur les 8 champs ESG, suivi separement.
- **FR-005**: Le systeme DOIT fournir un champ "notes" libre pour stocker les informations qualitatives detectees par le conseiller mais ne correspondant a aucun champ structure.
- **FR-006**: Le conseiller DOIT personnaliser ses reponses en fonction du profil connu de l'entreprise (secteur, localisation, taille).
- **FR-007**: Le conseiller NE DOIT PAS reposer des questions dont il a deja la reponse dans le profil.
- **FR-008**: Quand le profil est en dessous de 70% de completion ET que l'utilisateur n'est pas dans un module specifique (scoring ESG, carbone), le systeme DOIT integrer des questions de profilage dans le contexte conversationnel.
- **FR-009**: Quand le message contient des informations d'entreprise extractibles, le systeme DOIT traiter l'extraction en parallele de la reponse conversationnelle.
- **FR-010**: Le systeme DOIT conserver les 3 derniers resumes de conversation pour maintenir la continuite contextuelle entre les sessions. Un resume est genere automatiquement par le LLM lorsque l'utilisateur cree un nouveau thread/conversation (le thread precedent est resume a ce moment).
- **FR-011**: Le systeme DOIT fournir une page profil editable affichant les informations remplies, les champs manquants, et le pourcentage de completion.
- **FR-012**: Le systeme DOIT afficher un badge de completion du profil dans la sidebar.
- **FR-013**: Le systeme DOIT fournir des endpoints REST pour consulter, modifier et obtenir la completion du profil independamment du chat.
- **FR-014**: Quand une information de profil est extraite via le chat, le systeme DOIT afficher une notification discrete dans le chat confirmant la mise a jour.
- **FR-015**: Le conseiller DOIT pouvoir utiliser des blocs visuels (progress par categorie, gauge) pour afficher l'etat du profil dans le chat.
- **FR-016**: Quand le profil atteint 100% de completion, le conseiller DOIT celebrer l'etape avec un bloc visuel gauge.
- **FR-017**: Tous les composants (page profil, notifications, badges, blocs visuels) DOIVENT supporter le mode sombre.

### Key Entities

- **CompanyProfile**: Profil d'entreprise lie a un utilisateur (relation un-a-un). Contient les informations d'identite (nom, secteur, sous-secteur, effectifs, CA, annee de creation), de localisation (ville, pays), les indicateurs ESG de base (8 champs booleens et textuels), un champ notes libre, et deux pourcentages de completion calcules separement : identite/localisation et ESG. Horodate (creation, mise a jour).
- **SectorEnum**: Liste fermee de 11 secteurs d'activite adaptes au contexte africain : agriculture, energie, recyclage, transport, construction, textile, agroalimentaire, services, commerce, artisanat, autre.
- **ContextMemory**: Les 3 derniers resumes de conversation stockes dans l'etat conversationnel, incluant les points cles de chaque echange pour assurer la continuite entre sessions. Chaque resume est genere par le LLM au moment ou l'utilisateur cree un nouveau thread (le thread precedent est resume a ce moment-la).
- **ProfileExtraction**: Resultat de l'extraction structuree a partir d'un message utilisateur. Contient les champs identifies avec leur valeur et leur niveau de confiance. Seuls les champs a haute confiance sont appliques au profil.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Quand un utilisateur mentionne des informations d'entreprise dans un message, le systeme extrait correctement au moins 90% des champs identifiables en une seule passe.
- **SC-002**: Le profil entreprise peut etre rempli a 80% en moins de 5 echanges conversationnels naturels (sans formulaire).
- **SC-003**: Le pourcentage de completion du profil est calcule et affiche en temps reel, mis a jour en moins de 2 secondes apres chaque modification.
- **SC-004**: Les reponses du conseiller sont contextualisees au profil de l'entreprise dans 100% des cas ou le profil contient des informations pertinentes.
- **SC-005**: Le conseiller ne repose jamais une question dont la reponse est deja dans le profil (0% de questions redondantes).
- **SC-006**: L'extraction de profil n'ajoute pas plus de 1 seconde de latence au flux conversationnel (execution en parallele).
- **SC-007**: La page profil permet la consultation et l'edition manuelle de tous les champs en moins de 3 clics par champ.
- **SC-008**: Le systeme maintient la continuite contextuelle entre les sessions grace aux resumes de conversation stockes.

## Assumptions

- L'utilisateur est deja authentifie (systeme d'authentification existant ou en cours). Un utilisateur = un profil entreprise (relation un-a-un).
- Le chat avec streaming et le rendu de blocs visuels (progress, gauge) fonctionnent deja (features 001 et 002 implementees).
- Le graphe conversationnel LangGraph avec router_node et chat_node est deja en place.
- Le pays par defaut est "Cote d'Ivoire" car la majorite des utilisateurs cibles sont dans la zone UEMOA/CEDEAO.
- Les montants financiers sont en FCFA (franc CFA - devise commune de la zone UEMOA).
- L'extraction structuree utilise le LLM deja configure (Claude via OpenRouter) pour analyser les messages, pas un modele NER separe.
- Un seul profil entreprise par utilisateur (pas de multi-entreprises dans cette version).
- Les 11 secteurs d'activite couvrent les principaux domaines des PME africaines francophones.
- La memoire contextuelle se limite aux 3 derniers resumes de conversation (pas d'historique complet).
