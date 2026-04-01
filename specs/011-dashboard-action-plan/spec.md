# Feature Specification: Tableau de bord principal et plan d'action

**Feature Branch**: `011-dashboard-action-plan`
**Created**: 2026-03-31
**Status**: Draft
**Input**: User description: "Modules 6 et 7 — Dashboard principal et plan d'action intégrant le parcours intermédiaires financiers"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultation du tableau de bord synthétique (Priority: P1)

En tant que dirigeant de PME, je veux voir un tableau de bord agrégé de ma situation ESG, carbone, crédit vert et financements dès ma connexion, afin d'avoir une vue d'ensemble instantanée de ma progression et des prochaines actions à mener.

**Why this priority**: C'est le point d'entrée principal de l'application. Sans dashboard, l'utilisateur ne peut pas visualiser l'ensemble de ses données ni prioriser ses actions.

**Independent Test**: Peut être testé en accédant à /dashboard avec un compte ayant des données ESG, carbone et financements existantes. Le dashboard affiche les 4 cartes de synthèse et les prochaines actions.

**Acceptance Scenarios**:

1. **Given** un utilisateur connecté avec un score ESG calculé, un bilan carbone et des fonds recommandés, **When** il accède à /dashboard, **Then** il voit 4 cartes de synthèse (ESG, Carbone, Crédit Vert, Financements) avec les données à jour.
2. **Given** un utilisateur avec des parcours intermédiaires en cours, **When** il consulte la carte "Financements", **Then** il voit le nombre de fonds compatibles, le nombre de dossiers en cours avec leur statut, et la prochaine action intermédiaire planifiée.
3. **Given** un utilisateur avec des actions planifiées, **When** il consulte la section "Prochaines Actions", **Then** il voit les 5 prochaines actions triées par échéance, les actions de type "contact intermédiaire" étant visuellement distinguées avec les coordonnées de l'intermédiaire.
4. **Given** un utilisateur sans aucune donnée (nouveau compte), **When** il accède au dashboard, **Then** il voit des cartes vides avec des messages d'invitation à démarrer chaque module.

---

### User Story 2 - Génération et gestion du plan d'action (Priority: P1)

En tant que dirigeant de PME, je veux que le système me génère un plan d'action personnalisé sur 6, 12 ou 24 mois, incluant des actions concrètes liées aux intermédiaires financiers (rendez-vous, préparation de dossiers, relances), afin de savoir exactement quoi faire et quand pour obtenir mes financements verts.

**Why this priority**: Le plan d'action est le livrable principal qui transforme les analyses en actions concrètes. C'est la proposition de valeur différenciante de la plateforme.

**Independent Test**: Peut être testé en déclenchant la génération d'un plan pour un utilisateur ayant un profil complet. Le plan contient des actions ESG, carbone, financement et contacts intermédiaires avec coordonnées.

**Acceptance Scenarios**:

1. **Given** un utilisateur avec un profil entreprise, un score ESG et des fonds recommandés, **When** il demande la génération d'un plan d'action à 12 mois, **Then** le système génère un plan avec des actions catégorisées (environnement, social, gouvernance, financement, carbone, contact intermédiaire).
2. **Given** un plan généré contenant des actions intermédiaires, **When** l'utilisateur consulte une action de type "contact intermédiaire", **Then** il voit le nom de l'intermédiaire, son adresse, téléphone, email, et un lien vers la fiche de préparation du dossier correspondant.
3. **Given** un plan d'action existant, **When** l'utilisateur met à jour le statut d'une action (en cours, terminée), **Then** la barre de progression globale et les statistiques par catégorie se mettent à jour.
4. **Given** un utilisateur dans le chat, **When** le plan est généré, **Then** le système affiche des blocs visuels (timeline, table par catégorie, diagramme mermaid du parcours financement, jauge de complétion, graphique d'avancement par catégorie).

---

### User Story 3 - Consultation et filtrage du plan d'action (Priority: P2)

En tant que dirigeant de PME, je veux consulter mon plan d'action avec une timeline visuelle et pouvoir filtrer les actions par catégorie (dont "Contacts intermédiaires"), afin de me concentrer sur les actions les plus urgentes ou sur un domaine spécifique.

**Why this priority**: L'affichage et le filtrage enrichissent l'expérience mais dépendent de la génération du plan (P1).

**Independent Test**: Peut être testé avec un plan existant contenant des actions de différentes catégories. L'utilisateur filtre par "Contacts intermédiaires" et ne voit que les actions de ce type.

**Acceptance Scenarios**:

1. **Given** un plan d'action avec des actions de 6 catégories, **When** l'utilisateur sélectionne le filtre "Contacts intermédiaires", **Then** seules les actions de type contact intermédiaire sont affichées.
2. **Given** un plan d'action affiché en mode timeline, **When** l'utilisateur consulte la page /action-plan, **Then** les actions sont positionnées chronologiquement avec des indicateurs visuels par catégorie.
3. **Given** une action intermédiaire affichée en détail, **When** l'utilisateur clique dessus, **Then** il voit les coordonnées complètes de l'intermédiaire et un bouton vers la fiche de préparation dans /applications.

---

### User Story 4 - Rappels et notifications (Priority: P2)

En tant que dirigeant de PME, je veux recevoir des rappels in-app pour mes échéances d'actions et mes suivis avec les intermédiaires financiers, afin de ne manquer aucune étape critique de mon parcours de financement.

**Why this priority**: Les rappels complètent le plan d'action en assurant le suivi actif. Ils dépendent de l'existence des actions.

**Independent Test**: Peut être testé en créant un rappel avec une date proche. Le toast de rappel apparaît avec le bon style visuel (bleu pour les intermédiaires).

**Acceptance Scenarios**:

1. **Given** un rappel de suivi intermédiaire planifié pour aujourd'hui, **When** l'utilisateur est connecté, **Then** un toast de notification apparaît avec une icône banque et un style visuel bleu distinct.
2. **Given** un utilisateur sur le dashboard, **When** il consulte les prochains rappels, **Then** il voit la liste des rappels à venir triés par date, avec distinction visuelle par type.
3. **Given** un utilisateur, **When** il crée un rappel personnalisé lié à une action, **Then** le rappel est enregistré et apparaît dans la liste des rappels à venir.

---

### User Story 5 - Gamification et badges (Priority: P3)

En tant que dirigeant de PME, je veux obtenir des badges de progression quand j'atteins des jalons (premier bilan carbone, score ESG > 50, premier contact intermédiaire, dossier soumis, parcours complet), afin d'être motivé à poursuivre mes démarches ESG et de financement.

**Why this priority**: La gamification est un élément motivationnel qui complète l'expérience mais n'est pas bloquant pour la fonctionnalité principale.

**Independent Test**: Peut être testé en simulant les conditions de déclenchement de chaque badge et en vérifiant leur apparition dans le profil utilisateur.

**Acceptance Scenarios**:

1. **Given** un utilisateur qui complète son premier bilan carbone, **When** le bilan est enregistré, **Then** le badge "Premier bilan carbone" est débloqué et affiché.
2. **Given** un utilisateur qui marque une action de type "contact intermédiaire" comme terminée, **When** c'est son premier contact intermédiaire, **Then** le badge "Premier contact intermédiaire pris" est débloqué.
3. **Given** un utilisateur qui a un score ESG, un bilan carbone, une candidature soumise et un contact intermédiaire, **When** toutes les conditions du parcours complet sont remplies, **Then** le badge "Parcours complet : du diagnostic au financement" est débloqué.

---

### Edge Cases

- Que se passe-t-il si l'utilisateur n'a pas encore de données dans un module (ESG, carbone, crédit vert) ? Le dashboard affiche un état vide invitant à démarrer le module.
- Que se passe-t-il si un intermédiaire référencé dans une action a été supprimé ou mis à jour dans la base ? L'action conserve les informations au moment de la création et affiche un indicateur si les données sont potentiellement obsolètes.
- Que se passe-t-il si l'utilisateur tente de générer un plan d'action sans profil entreprise ? Le système affiche un message demandant de compléter le profil d'abord.
- Que se passe-t-il si un plan d'action existe déjà ? L'utilisateur peut regénérer un nouveau plan (l'ancien est archivé) ou mettre à jour l'existant.
- Que se passe-t-il si aucun fonds ni intermédiaire n'a été recommandé ? Le plan d'action est généré sans actions de type "contact intermédiaire" et suggère de lancer le module de matching financement.

## Clarifications

### Session 2026-03-31

- Q: Quels sont les statuts possibles d'une ActionItem ? → A: 5 statuts : à faire, en cours, en attente, terminée, annulée.
- Q: Que contient la section "Activité Récente" du dashboard ? → A: Actions (changements de statut) + événements système (badges débloqués, plan généré, rappels envoyés) + activité modules (nouveau score ESG, bilan carbone, candidature), 10 derniers éléments.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le système DOIT afficher un tableau de bord synthétique avec 4 cartes : Score ESG (score, radar miniature, tendance), Empreinte Carbone (total annuel, donut miniature, variation), Score de Crédit Vert (score combiné, jauge), Financements (fonds compatibles, dossiers en cours, prochaine action intermédiaire).
- **FR-002**: La carte "Financements" du dashboard DOIT afficher le nombre de fonds compatibles identifiés, le nombre de dossiers en cours avec mini badges de statut (préparation / soumis / en attente), et la prochaine action intermédiaire planifiée si elle existe.
- **FR-003**: Le dashboard DOIT afficher une section "Prochaines Actions" listant les 5 prochaines actions triées par échéance, les actions de type "contact intermédiaire" étant visuellement distinguées avec l'adresse de l'intermédiaire.
- **FR-004**: Le dashboard DOIT afficher une section "Activité Récente" montrant les 10 derniers événements : mises à jour d'actions (changements de statut), événements système (badges débloqués, plan généré, rappels envoyés) et activité modules (nouveau score ESG, bilan carbone, candidature soumise).
- **FR-005**: Le système DOIT permettre de générer un plan d'action personnalisé sur 3 horizons temporels (6, 12 ou 24 mois).
- **FR-006**: Le plan d'action généré DOIT contenir des actions catégorisées en 6 types : environnement, social, gouvernance, financement, carbone, contact intermédiaire.
- **FR-007**: Les actions de type "contact intermédiaire" DOIVENT être liées à un fonds et un intermédiaire spécifiques, et inclure les coordonnées complètes de l'intermédiaire (nom, adresse, téléphone, email).
- **FR-008**: Le système DOIT permettre de mettre à jour le statut (à faire, en cours, en attente, terminée, annulée) et le pourcentage de complétion de chaque action individuellement.
- **FR-009**: La page plan d'action DOIT afficher une timeline chronologique des actions avec filtrage par catégorie (incluant "Contacts intermédiaires").
- **FR-010**: Le système DOIT afficher une barre de progression globale et un graphique d'avancement par catégorie.
- **FR-011**: Le système DOIT permettre de créer des rappels liés aux actions, avec un type spécifique "suivi intermédiaire" pour les relances.
- **FR-012**: Les rappels de type "suivi intermédiaire" DOIVENT être visuellement distincts dans les notifications in-app (style et icône différenciés).
- **FR-013**: Le système DOIT gérer au minimum 5 badges de gamification : "Premier bilan carbone", "Score ESG > 50", "Première candidature", "Premier contact intermédiaire pris", "Parcours complet : du diagnostic au financement".
- **FR-014**: Lors de la génération du plan dans le chat, le système DOIT afficher des blocs visuels structurés : timeline, table par catégorie, diagramme mermaid du parcours financement, jauge de complétion, graphique d'avancement par catégorie.
- **FR-015**: Le détail d'une action intermédiaire DOIT proposer un lien vers la fiche de préparation du dossier correspondant dans le module candidatures (/applications).
- **FR-016**: Le dashboard DOIT gérer les états vides pour chaque module non encore utilisé, avec un message invitant à démarrer.

### Key Entities

- **Plan d'action (ActionPlan)** : Représente un plan personnalisé pour un utilisateur, avec un titre, un horizon temporel (6/12/24 mois), un statut (actif/archivé) et des horodatages. Un utilisateur a au plus un plan actif à la fois.
- **Action (ActionItem)** : Représente une tâche concrète du plan. Catégorisée en 6 types (environnement, social, gouvernance, financement, carbone, contact intermédiaire). Possède une priorité, un statut (à faire → en cours → en attente / terminée / annulée), une échéance, un coût estimé en XOF, un bénéfice attendu et un pourcentage de complétion. Peut être liée à un fonds et/ou un intermédiaire spécifique.
- **Rappel (Reminder)** : Notification programmée liée à une action. Typée (échéance action, renouvellement évaluation, deadline fonds, suivi intermédiaire, personnalisé). Possède un message, une date programmée et un indicateur d'envoi.
- **Badge** : Récompense de gamification attribuée quand des conditions métier sont remplies. Associé à un utilisateur avec une date de déclenchement.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: L'utilisateur peut visualiser l'ensemble de sa situation (ESG, carbone, crédit vert, financements) en moins de 3 secondes après connexion.
- **SC-002**: Un plan d'action complet est généré en moins de 30 secondes, contenant au minimum 10 actions couvrant au moins 4 catégories différentes.
- **SC-003**: 100% des actions de type "contact intermédiaire" générées contiennent les coordonnées complètes de l'intermédiaire (nom, adresse, téléphone).
- **SC-004**: L'utilisateur peut filtrer, mettre à jour le statut et suivre la progression de ses actions sans quitter la page plan d'action.
- **SC-005**: Les rappels de suivi intermédiaire sont visuellement identifiables en moins d'une seconde grâce à leur style distinct.
- **SC-006**: Au moins 5 badges de gamification sont disponibles et se déclenchent automatiquement quand les conditions sont remplies.
- **SC-007**: Les blocs visuels (timeline, table, mermaid, jauge, graphique) s'affichent correctement dans le chat lors de la génération du plan.

## Assumptions

- Les modules précédents (001 à 010) sont implémentés et fonctionnels, fournissant les données nécessaires au dashboard (scores ESG, bilans carbone, scores de crédit vert, fonds recommandés, intermédiaires, candidatures).
- Un utilisateur n'a qu'un seul plan d'action actif à la fois. La génération d'un nouveau plan archive l'ancien.
- Les coordonnées des intermédiaires proviennent de la base existante du module 008 (financement vert) et sont copiées dans l'action au moment de la génération pour éviter les incohérences si les données source changent.
- Les rappels sont des notifications in-app (toasts). Les notifications par email ou SMS sont hors périmètre pour cette version.
- La gamification est basée sur des conditions simples vérifiées à la volée. Il n'y a pas de système de points ou de niveaux complexe.
- Le dashboard est la page d'accueil après connexion (route /dashboard).
- Les graphiques du dashboard (radar, donut, jauge) utilisent des versions miniatures adaptées aux cartes de synthèse.
- Le badge "Parcours complet" nécessite : au moins un score ESG calculé, un bilan carbone, une candidature soumise, et un contact intermédiaire marqué comme terminé.
