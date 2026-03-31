# Feature Specification: Génération de Rapports ESG en PDF

**Feature Branch**: `006-esg-pdf-reports`
**Created**: 2026-03-31
**Status**: Draft
**Input**: User description: "Module 2.4 — Rapport de Conformité Généré. Transforme le scoring ESG en un document professionnel téléchargeable (PDF)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Générer un rapport PDF après une évaluation ESG (Priority: P1)

En tant que dirigeant de PME ayant complété une évaluation ESG, je veux générer un rapport PDF professionnel de mes résultats afin de le présenter à des investisseurs, partenaires ou organismes de financement vert.

**Why this priority** : C'est la fonctionnalité coeur — sans génération de PDF, la feature n'a pas de raison d'être. Le rapport est l'artefact tangible que l'utilisateur emporte avec lui.

**Independent Test** : Peut être testé en complétant une évaluation ESG existante, puis en cliquant sur "Générer le rapport PDF" et en vérifiant que le fichier PDF est téléchargé avec toutes les sections attendues.

**Acceptance Scenarios** :

1. **Given** une évaluation ESG complétée (statut "completed"), **When** l'utilisateur clique sur "Générer le rapport PDF", **Then** le système lance la génération et affiche un indicateur de progression.
2. **Given** la génération est en cours, **When** le rapport est prêt, **Then** l'utilisateur peut le télécharger et le PDF contient toutes les 9 sections requises (couverture, résumé exécutif, scores détaillés, points forts, axes d'amélioration, benchmarking, conformité réglementaire, plan d'action, méthodologie).
3. **Given** une évaluation ESG non complétée (statut "draft" ou "in_progress"), **When** l'utilisateur tente de générer un rapport, **Then** le système affiche un message indiquant que l'évaluation doit être finalisée d'abord.
4. **Given** le rapport généré, **When** l'utilisateur l'ouvre dans un lecteur PDF, **Then** le document fait entre 5 et 10 pages, les graphiques sont lisibles et le texte est en français correct.

---

### User Story 2 - Télécharger et consulter un rapport généré (Priority: P1)

En tant qu'utilisateur ayant déjà généré un rapport, je veux pouvoir le retrouver et le télécharger à nouveau sans avoir à le régénérer.

**Why this priority** : L'accès aux rapports déjà générés est essentiel pour l'usage quotidien — un utilisateur peut avoir besoin de partager son rapport plusieurs fois.

**Independent Test** : Peut être testé en accédant à la liste des rapports, en sélectionnant un rapport existant et en vérifiant que le téléchargement fonctionne.

**Acceptance Scenarios** :

1. **Given** un ou plusieurs rapports déjà générés, **When** l'utilisateur accède à la page des rapports, **Then** il voit la liste de ses rapports avec la date de génération, le type et l'évaluation associée.
2. **Given** un rapport dans la liste, **When** l'utilisateur clique sur "Télécharger", **Then** le fichier PDF est téléchargé sur son appareil.
3. **Given** un rapport dans la liste, **When** l'utilisateur clique dessus, **Then** il peut prévisualiser le PDF directement dans le navigateur avant de décider de le télécharger.

---

### User Story 3 - Visualiser le contenu narratif et les graphiques du rapport (Priority: P2)

En tant que dirigeant de PME, je veux que le rapport contienne un résumé exécutif rédigé en français professionnel, des graphiques radar et barres lisibles, ainsi qu'un tableau de conformité réglementaire UEMOA/BCEAO, afin de présenter un document crédible à des partenaires financiers.

**Why this priority** : La qualité du contenu différencie un simple export de données d'un rapport professionnel utilisable dans un contexte institutionnel.

**Independent Test** : Peut être testé en ouvrant un rapport PDF généré et en vérifiant visuellement la présence et la lisibilité de chaque section : résumé narratif, graphique radar des 3 piliers, barres de progression par critère, tableau de conformité.

**Acceptance Scenarios** :

1. **Given** un rapport PDF généré, **When** l'utilisateur lit le résumé exécutif, **Then** le texte est pertinent par rapport aux scores de l'évaluation, rédigé en français professionnel et fait entre 150 et 300 mots.
2. **Given** un rapport PDF généré, **When** l'utilisateur consulte la section scores détaillés, **Then** un graphique radar affiche les scores des 3 piliers (E, S, G) et des barres de progression montrent chaque critère avec son score.
3. **Given** un rapport PDF généré, **When** l'utilisateur consulte la section conformité réglementaire, **Then** un tableau présente le positionnement vis-à-vis des taxonomies UEMOA et BCEAO.
4. **Given** un rapport PDF généré, **When** l'utilisateur consulte la section benchmarking, **Then** un graphique montre le positionnement de l'entreprise par rapport à la moyenne de son secteur.

---

### User Story 4 - Notification dans le chat après génération (Priority: P3)

En tant qu'utilisateur du chatbot ESG, je veux être informé dans le chat quand mon rapport est prêt, avec un aperçu de sa structure et un lien direct de téléchargement.

**Why this priority** : Améliore l'expérience utilisateur en intégrant le rapport dans le flux conversationnel, mais n'est pas bloquant pour la fonctionnalité de base.

**Independent Test** : Peut être testé en lançant une génération de rapport depuis le chat et en vérifiant qu'un message apparaît avec le lien de téléchargement.

**Acceptance Scenarios** :

1. **Given** une génération de rapport déclenchée, **When** le rapport est prêt, **Then** le chatbot affiche un message contenant un diagramme de la structure du rapport et un lien de téléchargement cliquable.

---

### Edge Cases

- Que se passe-t-il si l'évaluation ESG est incomplète (certains critères non évalués) ? Le système refuse la génération et indique les critères manquants.
- Que se passe-t-il si la génération échoue en cours de route (erreur serveur) ? L'utilisateur est informé avec un message d'erreur clair et peut réessayer.
- Que se passe-t-il si le secteur de l'entreprise n'a pas de données de benchmark ? Le rapport affiche les scores sans comparaison sectorielle, avec une mention explicite.
- Que se passe-t-il si l'utilisateur tente de télécharger un rapport dont le fichier a été supprimé du stockage ? Le système affiche une erreur et propose de régénérer le rapport.
- Que se passe-t-il si plusieurs générations sont lancées simultanément pour la même évaluation ? Le système empêche les doublons et renvoie le rapport en cours de génération.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** : Le système DOIT permettre de générer un rapport PDF à partir d'une évaluation ESG complétée.
- **FR-002** : Le rapport DOIT contenir 9 sections : page de couverture, résumé exécutif, scores détaillés, points forts, axes d'amélioration, benchmarking sectoriel, conformité réglementaire, plan d'action synthétique, méthodologie.
- **FR-003** : La page de couverture DOIT afficher le nom de l'entreprise, la date de génération, le logo ESG Mefali et le score global.
- **FR-004** : Le résumé exécutif DOIT être généré automatiquement par IA, en français professionnel, synthétisant les résultats clés de l'évaluation.
- **FR-005** : La section scores détaillés DOIT inclure un graphique radar des 3 piliers et des barres de progression pour chaque critère évalué.
- **FR-006** : La section axes d'amélioration DOIT présenter un tableau priorisé avec colonnes : urgence, actions recommandées, coût estimé, impact attendu.
- **FR-007** : La section benchmarking DOIT positionner l'entreprise par rapport aux moyennes de son secteur via un graphique.
- **FR-008** : La section conformité réglementaire DOIT référencer les taxonomies vertes UEMOA et la réglementation BCEAO.
- **FR-009** : La section plan d'action DOIT proposer 5 actions prioritaires sur un horizon de 6 mois.
- **FR-010** : La section méthodologie DOIT expliquer la grille de scoring (30 critères, pondération sectorielle, échelle 0-100).
- **FR-011** : Les graphiques (radar, barres, positionnement sectoriel) DOIVENT être générés côté serveur et intégrés dans le PDF de manière lisible.
- **FR-012** : Le rapport PDF DOIT faire entre 5 et 10 pages.
- **FR-013** : Le système DOIT permettre le téléchargement du PDF via un lien direct.
- **FR-014** : Le système DOIT conserver l'historique des rapports générés pour chaque utilisateur.
- **FR-015** : Le système DOIT fournir une liste consultable des rapports générés avec date, type et évaluation associée.
- **FR-016** : Le système DOIT permettre la prévisualisation inline du PDF dans le navigateur.
- **FR-017** : Le système DOIT afficher un indicateur de progression pendant la génération du rapport.
- **FR-018** : Le système DOIT refuser la génération si l'évaluation ESG n'est pas au statut "completed".
- **FR-019** : Le chatbot DOIT informer l'utilisateur quand le rapport est prêt, avec un aperçu structurel et un lien de téléchargement.
- **FR-020** : Le système DOIT empêcher les générations simultanées multiples pour la même évaluation.

### Key Entities

- **Report** : Représente un rapport généré. Attributs clés : identifiant unique, utilisateur propriétaire, évaluation ESG source, type de rapport (conformité ESG), chemin du fichier généré, date de génération.
- **ESGAssessment** (existant) : L'évaluation ESG complétée qui sert de source de données pour le rapport. Contient les scores, recommandations, forces, faiblesses et benchmark sectoriel.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** : 100% des rapports générés contiennent les 9 sections requises et font entre 5 et 10 pages.
- **SC-002** : Le temps de génération d'un rapport est inférieur à 30 secondes pour l'utilisateur.
- **SC-003** : Les graphiques (radar, barres) sont lisibles à l'impression sur papier A4.
- **SC-004** : Le résumé exécutif est jugé pertinent et en bon français (cohérent avec les scores affichés).
- **SC-005** : 100% des rapports générés sont téléchargeables et s'ouvrent correctement dans les lecteurs PDF courants (navigateur, Adobe Reader, Aperçu macOS).
- **SC-006** : La conformité UEMOA/BCEAO est mentionnée dans chaque rapport avec des références spécifiques aux taxonomies applicables.
- **SC-007** : Les utilisateurs peuvent retrouver et re-télécharger un rapport précédemment généré en moins de 3 clics.

## Assumptions

- L'évaluation ESG (feature 005) est entièrement fonctionnelle et produit des données complètes (scores, recommandations, forces, faiblesses, benchmark).
- Le système d'authentification utilisateur est en place (user_id disponible).
- Le stockage local des fichiers est suffisant pour les PDF générés (migration vers S3/MinIO prévue ultérieurement).
- Les données de benchmark sectoriel peuvent être absentes pour certains secteurs — le rapport s'adapte en conséquence.
- Le logo ESG Mefali est disponible en tant qu'asset statique dans le projet.
- La génération est synchrone (pas de queue de tâches asynchrone pour cette version).
- Le rapport est en français uniquement (pas de support multilingue pour v1).
