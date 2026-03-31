# Feature Specification: Calculateur d'Empreinte Carbone Conversationnel

**Feature Branch**: `007-carbon-footprint-calculator`
**Created**: 2026-03-31
**Status**: Draft
**Input**: Module 4 complet - Calculateur d'empreinte carbone conversationnel avec visualisations inline pour PME africaines francophones

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bilan carbone guide par conversation (Priority: P1)

En tant que dirigeant de PME africaine, je souhaite repondre a un questionnaire conversationnel guide par l'IA pour obtenir mon bilan carbone annuel, sans avoir besoin de connaissances techniques en comptabilite carbone.

L'IA me pose des questions categorie par categorie (energie, transport, dechets, etc.) en utilisant des unites que je comprends (FCFA, litres, km) et me montre un graphique a barres qui se remplit progressivement a chaque categorie completee.

**Why this priority**: C'est la fonctionnalite coeur du module. Sans la collecte conversationnelle, aucune autre fonctionnalite n'a de sens.

**Independent Test**: Peut etre teste en demarrant un bilan carbone dans le chat, en repondant aux questions categorie par categorie, et en verifiant que les graphiques progressifs s'affichent et que le total est calcule correctement.

**Acceptance Scenarios**:

1. **Given** un utilisateur connecte avec un profil entreprise, **When** il demande un bilan carbone dans le chat, **Then** l'IA demarre un questionnaire structure par categories (energie, transport, dechets, etc.) avec des questions en francais et des unites locales (FCFA, litres, kWh, km).
2. **Given** l'utilisateur repond a une categorie (ex: consommation electrique mensuelle), **When** la reponse est validee, **Then** l'IA affiche un graphique a barres horizontal dans le chat montrant les emissions par categorie deja collectees, et passe a la categorie suivante.
3. **Given** l'utilisateur a complete toutes les categories, **When** le bilan est finalise, **Then** l'IA affiche dans le chat : un diagramme en donut avec la repartition par source, une jauge avec le total en tCO2e et une equivalence parlante (ex: "equivalent a X vols Paris-Dakar"), et un tableau du plan de reduction avec actions, economies FCFA et reduction CO2.
4. **Given** l'utilisateur fournit une valeur incoherente (ex: consommation negative ou extremement elevee), **When** la valeur est soumise, **Then** l'IA signale l'anomalie et demande confirmation ou correction.

---

### User Story 2 - Dashboard de resultats carbone (Priority: P2)

En tant qu'utilisateur ayant complete un bilan carbone, je souhaite consulter mes resultats de maniere persistante sur une page dediee avec des visualisations interactives, afin de pouvoir y revenir a tout moment.

**Why this priority**: Apres la collecte conversationnelle, l'utilisateur a besoin d'un endroit permanent pour consulter et partager ses resultats.

**Independent Test**: Peut etre teste en accedant a la page /carbon/results apres avoir complete au moins un bilan, et en verifiant que toutes les visualisations s'affichent correctement.

**Acceptance Scenarios**:

1. **Given** un utilisateur ayant complete au moins un bilan, **When** il accede a la page des resultats carbone, **Then** il voit son empreinte totale annuelle en tCO2e, un diagramme en donut de repartition par source, des equivalences parlantes, et une comparaison avec la moyenne de son secteur.
2. **Given** un utilisateur ayant complete plusieurs bilans (annees differentes), **When** il consulte la page resultats, **Then** un graphique d'evolution temporelle montre la tendance de ses emissions.
3. **Given** un utilisateur sans aucun bilan, **When** il accede a la page resultats, **Then** un message l'invite a demarrer son premier bilan via le chat.

---

### User Story 3 - Plan de reduction personnalise (Priority: P2)

En tant que dirigeant de PME, je souhaite recevoir un plan de reduction carbone personnalise avec des actions concretes, des economies estimees en FCFA et des echeances, pour savoir par ou commencer.

**Why this priority**: Le plan de reduction transforme le diagnostic en actions concretes, ce qui est la valeur ajoutee principale pour l'utilisateur.

**Independent Test**: Peut etre teste en completant un bilan et en verifiant que le plan de reduction contient des quick wins et actions long terme avec chiffrage FCFA.

**Acceptance Scenarios**:

1. **Given** un bilan carbone complete, **When** le plan de reduction est genere, **Then** il contient au minimum 3 quick wins (actions a court terme) et 3 actions long terme, chacune avec une estimation de reduction en tCO2e et d'economies en FCFA.
2. **Given** un plan de reduction affiche, **When** l'utilisateur consulte la timeline, **Then** les actions sont reparties sur un horizon 6-12-24 mois avec des jalons clairs.

---

### User Story 4 - Comparaison sectorielle (Priority: P3)

En tant qu'utilisateur, je souhaite comparer mon empreinte carbone avec la moyenne de mon secteur d'activite en Afrique de l'Ouest, pour situer ma performance relative.

**Why this priority**: La comparaison sectorielle donne du contexte aux chiffres bruts et motive l'action.

**Independent Test**: Peut etre teste en completant un bilan pour un secteur donne et en verifiant que le benchmark sectoriel s'affiche avec les donnees comparatives.

**Acceptance Scenarios**:

1. **Given** un bilan complete et un secteur d'activite identifie, **When** la comparaison s'affiche, **Then** un graphique a barres montre l'empreinte de l'utilisateur vs la moyenne du secteur.
2. **Given** un secteur sans donnees de benchmark disponibles, **When** la comparaison est demandee, **Then** un message indique que les donnees sectorielles ne sont pas encore disponibles et propose une estimation basee sur les secteurs similaires.

---

### User Story 5 - Gestion des bilans (Priority: P3)

En tant qu'utilisateur, je souhaite pouvoir creer, consulter et gerer mes bilans carbone annuels depuis une page de liste, pour suivre mon historique.

**Why this priority**: Fonctionnalite de gestion necessaire mais secondaire par rapport au bilan et aux resultats.

**Independent Test**: Peut etre teste en creant plusieurs bilans et en verifiant la liste, l'acces aux details, et la navigation.

**Acceptance Scenarios**:

1. **Given** un utilisateur avec plusieurs bilans, **When** il accede a la page /carbon, **Then** il voit la liste de ses bilans avec annee, total tCO2e et statut.
2. **Given** un utilisateur sur la liste des bilans, **When** il clique sur un bilan, **Then** il accede aux resultats detailles de ce bilan.

---

### Edge Cases

- Que se passe-t-il si l'utilisateur interrompt le questionnaire en cours de route ? Le bilan partiel doit etre sauvegarde avec statut "en cours" et pouvoir etre repris.
- Comment le systeme gere-t-il les conversions d'unites ? L'utilisateur peut exprimer sa consommation en differentes unites (kWh, FCFA de facture, litres) et le systeme doit convertir correctement.
- Que se passe-t-il si les facteurs d'emission ne couvrent pas une source specifique ? Le systeme utilise un facteur par defaut avec un avertissement.
- Comment gerer les entreprises multi-sites ? Le bilan couvre l'ensemble de l'entreprise ; la ventilation par site est hors scope pour cette version.
- Que se passe-t-il lors d'une tentative de creation d'un deuxieme bilan pour la meme annee ? Le systeme empeche la creation et propose de reprendre ou consulter le bilan existant.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le systeme DOIT guider l'utilisateur a travers un questionnaire conversationnel structure par categories d'emissions (energie, transport, dechets, processus industriels, agriculture).
- **FR-002**: Le systeme DOIT poser des questions contextualisees en francais avec des unites locales (FCFA, litres, kWh, km, kg).
- **FR-003**: Le systeme DOIT calculer les emissions en tCO2e en utilisant les facteurs d'emission d'Afrique de l'Ouest (Electricite CI: 0.41 kgCO2e/kWh, Generateur diesel: 2.68 kgCO2e/L, Essence: 2.31 kgCO2e/L, Gasoil: 2.68 kgCO2e/L, Gaz butane: 2.98 kgCO2e/kg).
- **FR-004**: Le systeme DOIT afficher un graphique a barres horizontal progressif dans le chat apres chaque categorie collectee.
- **FR-005**: Le systeme DOIT afficher a la fin du bilan : un diagramme en donut (repartition par source), une jauge (total tCO2e + equivalence parlante), et un tableau (plan de reduction avec actions, economies FCFA, reduction CO2).
- **FR-006**: Le systeme DOIT afficher une comparaison sectorielle sous forme de graphique a barres et une timeline du plan d'action temporel.
- **FR-007**: Le systeme DOIT persister les bilans et leurs entrees d'emissions dans la base de donnees.
- **FR-008**: Le systeme DOIT permettre de creer, lister et consulter les bilans carbone via des endpoints dedies.
- **FR-009**: Le systeme DOIT fournir un resume/synthese pour chaque bilan complete.
- **FR-010**: Le systeme DOIT fournir des benchmarks sectoriels pour comparaison.
- **FR-011**: Le systeme DOIT permettre la reprise d'un bilan interrompu (statut "en cours").
- **FR-012**: Le systeme DOIT empecher la creation de deux bilans pour la meme annee et le meme utilisateur.
- **FR-013**: Le systeme DOIT proposer une page dediee (/carbon) listant les bilans avec acces a la page resultats.
- **FR-014**: Le systeme DOIT afficher un graphique d'evolution temporelle si l'utilisateur a plusieurs bilans.
- **FR-015**: Le systeme DOIT valider les donnees saisies et signaler les valeurs incoherentes (negatives, anormalement elevees).
- **FR-016**: La page /carbon DOIT etre accessible depuis la barre laterale de navigation.

### Key Entities

- **CarbonAssessment**: Represente un bilan carbone annuel d'une entreprise. Attributs cles : utilisateur associe, annee du bilan, total des emissions en tCO2e, statut (en cours / complete). Un seul bilan par annee et par utilisateur.
- **CarbonEmissionEntry**: Represente une ligne d'emission dans un bilan. Attributs cles : categorie (energie, transport, dechets...), sous-categorie, quantite, unite, facteur d'emission applique, emissions calculees en tCO2e, description de la source. Plusieurs entrees par bilan.
- **Relation**: Un CarbonAssessment contient plusieurs CarbonEmissionEntry. Un utilisateur possede plusieurs CarbonAssessment.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un utilisateur peut completer un bilan carbone complet en moins de 15 minutes via le questionnaire conversationnel.
- **SC-002**: Les graphiques progressifs s'affichent dans le chat en moins de 2 secondes apres chaque reponse de l'utilisateur.
- **SC-003**: Les calculs d'emissions sont corrects a 1% pres par rapport aux facteurs d'emission de reference d'Afrique de l'Ouest.
- **SC-004**: 100% des visualisations de fin de bilan (donut, jauge, tableau, comparaison) s'affichent correctement dans le chat et sur la page resultats.
- **SC-005**: Un bilan interrompu peut etre repris sans perte de donnees des categories deja completees.
- **SC-006**: La page resultats affiche les donnees de maniere coherente avec ce qui a ete presente dans le chat.
- **SC-007**: Les equivalences parlantes sont pertinentes pour le contexte africain (ex: vols regionaux, trajets en voiture Abidjan-Ouagadougou, etc.).

## Assumptions

- Les utilisateurs ont deja un profil entreprise avec un secteur d'activite renseigne (Feature 003 - Company Profiling).
- Le systeme de chat visuel avec rendu de blocs chart/gauge/table/timeline est deja fonctionnel (Features 001-002).
- Les facteurs d'emission fournis sont valides pour l'ensemble de la zone Afrique de l'Ouest (UEMOA/CEDEAO).
- La ventilation par site n'est pas requise pour cette version (bilan global entreprise).
- Les benchmarks sectoriels sont bases sur des donnees estimees/moyennes et non sur des donnees officielles certifiees.
- Un seul bilan par annee et par utilisateur est autorise.
- L'authentification et la gestion des sessions utilisateur sont deja en place.
- Les categories d'emissions couvrent : energie (electricite, generateurs), transport (vehicules, deplacement), dechets, et optionnellement processus industriels et agriculture selon le secteur.
