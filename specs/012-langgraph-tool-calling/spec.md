# Feature Specification: Intégration Tool Calling LangGraph

**Feature Branch**: `012-langgraph-tool-calling`
**Created**: 2026-04-01
**Status**: Draft
**Input**: Intégration du tool calling LangChain dans tous les noeuds LangGraph pour que le LLM puisse agir sur la plateforme (sauvegarder, modifier, lire des données) et non plus seulement répondre en texte.

## Problème

Actuellement, lorsqu'un utilisateur demande au conseiller IA de générer un plan d'action, sauvegarder un score ESG, ou mettre à jour son profil, le LLM répond uniquement en texte. Il formule "voici votre plan d'action" mais ne sauvegarde rien en base de données. L'utilisateur ne retrouve aucune donnée sur les pages dédiées (/action-plan, /esg, /carbon, /financing, /credit-score, /profile). Le LLM se comporte comme un chatbot passif au lieu d'un agent capable d'agir.

**Cause racine** : Les noeuds LangGraph appellent le LLM sans lui déclarer de tools (function calling). Sans tools, Claude ne peut que générer du texte.

## Clarifications

### Session 2026-04-01

- Q: Le LLM doit-il demander confirmation avant les tools irréversibles (finalize, generate_credit_score, export) ? → A: Confirmation uniquement pour les finalisations (finalize_esg_assessment, finalize_carbon_assessment), pas pour les exports ni les autres tools.
- Q: Combien de tools le LLM peut-il chaîner par tour de conversation ? → A: Maximum 5 tools par tour — couvre les demandes multi-actions courantes sans risque d'emballement.
- Q: Quelle politique de retry quand un tool échoue (timeout DB, service indisponible) ? → A: 1 retry automatique silencieux, puis message d'erreur compréhensible à l'utilisateur si le retry échoue aussi.
- Q: Faut-il journaliser les tool calls et à quel niveau de détail ? → A: Logger tout (nom du tool, paramètres, résultat complet, durée, succès/échec) pour un debug maximal en production.

## User Scenarios & Testing

### User Story 1 - Profilage automatique via conversation (Priority: P1)

L'utilisateur mentionne des informations sur son entreprise dans le chat (secteur, ville, nombre d'employés, chiffre d'affaires, pratiques ESG, etc.). Le conseiller IA sauvegarde automatiquement ces informations dans le profil entreprise en base de données, puis confirme la mise à jour dans le chat.

**Why this priority**: Le profilage est la brique fondamentale — tous les autres modules (ESG, carbone, financement, crédit) dépendent du profil entreprise pour fonctionner correctement. Sans profil sauvegardé, aucun matching ni scoring n'est possible.

**Independent Test**: Peut être testé en envoyant "je suis dans l'agriculture à Bouaké avec 30 employés" dans le chat et en vérifiant que les données apparaissent sur la page /profile.

**Acceptance Scenarios**:

1. **Given** un utilisateur connecté sans profil, **When** il dit "je suis dans l'agriculture à Bouaké avec 30 employés", **Then** le profil est sauvegardé en base avec sector=agriculture, city=Bouaké, employee_count=30 et la page /profile affiche ces données.
2. **Given** un utilisateur avec un profil existant (sector=agriculture), **When** il dit "en fait j'ai 50 employés maintenant", **Then** seul employee_count est mis à jour à 50, les autres champs restent inchangés.
3. **Given** un utilisateur connecté, **When** il demande "quel est mon profil ?", **Then** le LLM consulte la base en temps réel et retourne le profil complet avec le pourcentage de complétion.

---

### User Story 2 - Évaluation ESG sauvegardée critère par critère (Priority: P1)

L'utilisateur demande une évaluation ESG. Le conseiller IA crée une évaluation en base, pose les questions critère par critère, sauvegarde chaque réponse au fur et à mesure, et finalise l'évaluation avec les scores calculés.

**Why this priority**: L'évaluation ESG est le coeur du produit et le score ESG alimente directement le scoring crédit et le matching financement.

**Independent Test**: Peut être testé en démarrant une évaluation ESG via le chat, en répondant à plusieurs critères, puis en vérifiant que les scores partiels et finaux apparaissent sur /esg.

**Acceptance Scenarios**:

1. **Given** un utilisateur connecté, **When** il dit "je veux faire une évaluation ESG", **Then** une évaluation est créée en base avec status=draft et le LLM commence à poser les questions.
2. **Given** une évaluation en cours, **When** l'utilisateur répond à un critère, **Then** le score de ce critère est immédiatement sauvegardé en base (pas à la fin de l'évaluation).
3. **Given** une évaluation avec suffisamment de critères évalués, **When** le LLM finalise l'évaluation, **Then** les scores E, S, G et global sont calculés, sauvegardés, et visibles sur /esg avec des visualisations.
4. **Given** une évaluation interrompue, **When** l'utilisateur revient et pose une question sur son évaluation, **Then** le LLM consulte la base et reprend là où il en était.

---

### User Story 3 - Bilan carbone conversationnel sauvegardé (Priority: P1)

L'utilisateur fournit ses données de consommation dans le chat (litres de gasoil, factures d'électricité, km parcourus). Le conseiller IA convertit si nécessaire, calcule les émissions en tCO2e, et sauvegarde chaque entrée en base immédiatement.

**Why this priority**: Le bilan carbone est un module autonome à forte valeur ajoutée et les données alimentent le scoring crédit vert.

**Independent Test**: Peut être testé en déclarant "je consomme 200L de gasoil par mois pour mon générateur" et en vérifiant que l'entrée apparaît sur /carbon avec le calcul d'émissions.

**Acceptance Scenarios**:

1. **Given** un utilisateur connecté, **When** il dit "je veux faire un bilan carbone pour 2025", **Then** un bilan est créé en base pour l'année 2025.
2. **Given** un bilan en cours, **When** l'utilisateur dit "je consomme 200L de gasoil par mois", **Then** l'entrée est sauvegardée avec la catégorie "generator", les émissions calculées en tCO2e, et le total cumulé est retourné.
3. **Given** un bilan en cours, **When** l'utilisateur dit "ma facture CIE est de 150 000 FCFA par mois", **Then** le LLM convertit en kWh puis sauvegarde l'entrée avec la catégorie "electricity".
4. **Given** un bilan avec plusieurs entrées, **When** l'utilisateur dit "finalise mon bilan", **Then** le total, les répartitions par catégorie, les équivalences et les recommandations sont calculés et sauvegardés.

---

### User Story 4 - Recherche et suivi de financements (Priority: P2)

L'utilisateur demande des recommandations de financement. Le conseiller IA recherche les fonds compatibles en base (pas de mémoire), affiche les résultats avec les scores de compatibilité, et sauvegarde les intérêts de l'utilisateur.

**Why this priority**: Le financement est la finalité business du produit, mais nécessite un profil et idéalement un score ESG pour le matching.

**Independent Test**: Peut être testé en demandant "quels fonds sont compatibles avec mon profil ?" et en vérifiant que les résultats apparaissent sur /financing avec les scores de compatibilité.

**Acceptance Scenarios**:

1. **Given** un utilisateur avec un profil complété, **When** il demande "quels financements pour moi ?", **Then** le LLM appelle le service de matching et retourne les fonds triés par compatibilité avec mode d'accès.
2. **Given** une liste de fonds affichée, **When** l'utilisateur dit "le fonds GCF m'intéresse", **Then** l'intérêt est sauvegardé en base avec status=interested et visible sur /financing.
3. **Given** un utilisateur intéressé par un fonds, **When** il dit "je veux préparer un dossier pour ce fonds", **Then** un dossier de candidature est créé en base avec les sections à remplir.

---

### User Story 5 - Génération et suivi de dossiers de candidature (Priority: P2)

L'utilisateur travaille sur un dossier de candidature via le chat. Chaque section générée ou modifiée est sauvegardée dans le dossier en base, pas uniquement affichée en texte dans le chat.

**Why this priority**: La génération de dossiers est la valeur ajoutée différenciante du produit pour les PME, mais dépend du module financement.

**Independent Test**: Peut être testé en demandant de générer la section "présentation de l'entreprise" d'un dossier et en vérifiant qu'elle est sauvegardée et visible sur /applications.

**Acceptance Scenarios**:

1. **Given** un dossier de candidature créé, **When** l'utilisateur dit "génère la section présentation de l'entreprise", **Then** le contenu est généré via RAG, sauvegardé dans le dossier, et le statut de complétion est mis à jour.
2. **Given** une section déjà générée, **When** l'utilisateur dit "modifie le paragraphe sur l'impact environnemental", **Then** la section est mise à jour en base.
3. **Given** un dossier en cours, **When** l'utilisateur demande "exporte en PDF", **Then** le fichier est généré et l'URL de téléchargement est retournée.

---

### User Story 6 - Scoring crédit vert calculé et sauvegardé (Priority: P2)

L'utilisateur demande son score de crédit vert. Le conseiller IA collecte toutes les données disponibles (profil, ESG, carbone, financements, documents), calcule le score hybride, et le sauvegarde en base.

**Why this priority**: Le score de crédit vert est un livrable clé mais nécessite des données des autres modules pour être pertinent.

**Independent Test**: Peut être testé en demandant "calcule mon score de crédit vert" et en vérifiant que le score apparaît sur /credit-score.

**Acceptance Scenarios**:

1. **Given** un utilisateur avec des données (profil, ESG, carbone), **When** il dit "quel est mon score de crédit vert ?", **Then** le score hybride est calculé, sauvegardé, et affiché avec le détail des facteurs.
2. **Given** un score existant, **When** l'utilisateur demande une attestation, **Then** un PDF est généré et l'URL de téléchargement est retournée.

---

### User Story 7 - Analyse de documents via tools (Priority: P2)

Quand un document est uploadé, le conseiller IA lance l'analyse via le tool dédié (extraction texte, analyse structurée, embeddings), au lieu de simuler une analyse basée sur le nom du fichier.

**Why this priority**: L'analyse documentaire enrichit le RAG et améliore la qualité des scores et dossiers, mais l'upload fonctionne déjà mécaniquement.

**Independent Test**: Peut être testé en uploadant un document et en vérifiant que l'analyse complète apparaît sur /documents.

**Acceptance Scenarios**:

1. **Given** un document uploadé, **When** le noeud document est déclenché, **Then** le tool analyze_uploaded_document est appelé et l'analyse (résumé, type, points clés) est sauvegardée en base.
2. **Given** un utilisateur avec des documents, **When** il demande "quels documents ai-je uploadé ?", **Then** le LLM appelle le tool de lecture et retourne la liste réelle depuis la base.

---

### User Story 8 - Plan d'action généré et sauvegardé (Priority: P1)

L'utilisateur demande un plan d'action. Le conseiller IA génère un plan personnalisé avec des actions concrètes, des échéances, des coûts estimés, et le sauvegarde intégralement en base. L'utilisateur retrouve son plan sur /action-plan.

**Why this priority**: Le plan d'action est le livrable tangible que l'utilisateur emporte — c'est la valeur perçue immédiate du produit.

**Independent Test**: Peut être testé en demandant "génère-moi un plan d'action sur 12 mois" et en vérifiant que le plan apparaît sur /action-plan avec toutes les actions.

**Acceptance Scenarios**:

1. **Given** un utilisateur avec un profil et des scores, **When** il dit "génère un plan d'action sur 12 mois", **Then** le plan est créé en base avec 10-15 actions catégorisées, des échéances et des coûts estimés, visible immédiatement sur /action-plan.
2. **Given** un plan d'action existant, **When** l'utilisateur dit "j'ai terminé l'action X", **Then** le statut de l'action est mis à jour en base à "completed".

---

### User Story 9 - Chat avec lecture temps réel des données (Priority: P1)

Quand l'utilisateur pose une question factuelle sur ses données dans le chat généraliste ("quel est mon score ESG ?", "combien de CO2 j'émets ?"), le LLM consulte la base de données en temps réel au lieu de répondre de mémoire avec des informations potentiellement obsolètes.

**Why this priority**: C'est la cohérence globale du produit — si le chat répond des informations incorrectes ou obsolètes, la confiance utilisateur est détruite.

**Independent Test**: Peut être testé en modifiant des données via l'interface web puis en posant une question dans le chat et en vérifiant que la réponse reflète les données actuelles.

**Acceptance Scenarios**:

1. **Given** un utilisateur avec un score ESG de 72/100, **When** il demande "quel est mon score ESG ?" dans le chat, **Then** le LLM appelle le tool de lecture et répond avec le score actuel (72/100), pas une approximation de mémoire.
2. **Given** un utilisateur avec des données, **When** il demande "fais-moi un résumé de ma situation", **Then** le LLM appelle le tool dashboard summary et retourne les données réelles.

---

### User Story 10 - Indicateurs visuels pendant l'exécution des tools (Priority: P3)

Quand le LLM exécute un tool (sauvegarde, calcul), le frontend affiche un indicateur d'activité ("Sauvegarde en cours...", "Calcul du score...") pendant l'exécution, puis reprend l'affichage de la réponse textuelle.

**Why this priority**: Amélioration UX importante mais pas bloquante fonctionnellement — le tool calling fonctionne même sans indicateur visuel.

**Independent Test**: Peut être testé en déclenchant un tool call et en vérifiant qu'un indicateur apparaît pendant l'exécution.

**Acceptance Scenarios**:

1. **Given** l'utilisateur envoie un message qui déclenche un tool call, **When** le tool s'exécute, **Then** le frontend affiche un indicateur contextuel (ex: "Sauvegarde du profil...") pendant l'exécution.
2. **Given** un tool a fini de s'exécuter, **When** le LLM formule sa réponse finale, **Then** le streaming reprend normalement avec le texte et les blocs visuels.

---

### Edge Cases

- Que se passe-t-il si un tool échoue (erreur base de données, timeout) pendant l'exécution ? Le LLM doit informer l'utilisateur de l'échec et proposer de réessayer, sans perdre le contexte de conversation.
- Que se passe-t-il si l'utilisateur fournit des données ambiguës ("je suis dans l'énergie" — énergie solaire ? fossile ?) ? Le LLM doit sauvegarder le secteur "energie" et demander une précision sur le sous-secteur.
- Que se passe-t-il si le LLM appelle un tool avec des paramètres invalides ? Le tool doit retourner une erreur claire et le LLM doit reformuler sans crash.
- Que se passe-t-il si deux messages arrivent simultanément et déclenchent des tool calls concurrents sur les mêmes données ? Les opérations de base de données doivent être idempotentes ou sérialisées.
- Que se passe-t-il si le user_id n'est pas trouvé dans le state ? Le tool doit retourner une erreur explicite et le LLM doit demander à l'utilisateur de se reconnecter.
- Que se passe-t-il si un bilan carbone est déjà finalisé et l'utilisateur veut ajouter une entrée ? Le tool doit refuser avec un message clair et proposer de créer un nouveau bilan.
- Que se passe-t-il si le LLM tente d'appeler plus de 5 tools dans un seul tour ? Le système doit plafonner à 5 et indiquer que les actions restantes seront traitées au tour suivant.
- Que se passe-t-il si l'utilisateur refuse la confirmation de finalisation ? Le LLM doit poursuivre la conversation normalement (par exemple, continuer l'évaluation ESG ou ajouter d'autres entrées au bilan carbone).

## Requirements

### Functional Requirements

- **FR-001**: Chaque noeud LangGraph DOIT déclarer des tools LangChain correspondant aux actions qu'il peut effectuer (lecture, création, mise à jour).
- **FR-002**: Le LLM DOIT utiliser les tools systématiquement quand une action de sauvegarde, modification ou lecture de données est demandée — il ne DOIT JAMAIS répondre uniquement en texte quand une action sur les données est attendue.
- **FR-003**: Les tools DOIVENT appeler les services métier existants (modules backend) pour effectuer les opérations en base de données.
- **FR-004**: Le user_id DOIT être fourni automatiquement aux tools via un mécanisme de contexte injecté, sans que le LLM ait besoin de le passer comme paramètre.
- **FR-005**: Après l'exécution d'un tool (sauvegarde en base), le LLM DOIT formuler une réponse conversationnelle incluant les blocs visuels appropriés. Les visuels accompagnent l'action, ils ne la remplacent pas.
- **FR-006**: Le profiling_node DOIT disposer de tools pour mettre à jour le profil (mise à jour partielle des champs fournis) et lire le profil actuel.
- **FR-007**: L'esg_scoring_node DOIT disposer de tools pour créer une évaluation, sauvegarder un critère individuel, finaliser l'évaluation, et lire l'état d'une évaluation.
- **FR-008**: Le carbon_node DOIT disposer de tools pour créer un bilan, sauvegarder une entrée d'émission (avec calcul automatique des tCO2e), finaliser le bilan, et lire le résumé.
- **FR-009**: Le financing_node DOIT disposer de tools pour rechercher les fonds compatibles, enregistrer un intérêt, récupérer les détails d'un fonds, et créer un dossier de candidature.
- **FR-010**: L'application_node DOIT disposer de tools pour générer une section, mettre à jour une section, récupérer la checklist documentaire, lancer une simulation financière, et exporter en PDF/Word.
- **FR-011**: Le credit_node DOIT disposer de tools pour calculer et sauvegarder le score de crédit vert, récupérer le score actuel, et générer l'attestation PDF.
- **FR-012**: Le document_node DOIT disposer de tools pour lancer l'analyse d'un document uploadé, récupérer l'analyse, et lister les documents.
- **FR-013**: L'action_plan_node DOIT disposer de tools pour générer et sauvegarder un plan d'action complet, mettre à jour le statut d'une action, et récupérer le plan actif.
- **FR-014**: Le chat_node DOIT disposer de tools de lecture (dashboard summary, profil, évaluation ESG, bilan carbone) pour répondre aux questions factuelles avec des données temps réel.
- **FR-015**: L'endpoint SSE DOIT envoyer des événements distincts pour : tokens texte, appels de tools (nom du tool et paramètres), résultats de tools, et reprise du texte.
- **FR-016**: Le frontend DOIT afficher un indicateur visuel contextuel pendant l'exécution d'un tool call ("Sauvegarde en cours...", "Calcul du score...").
- **FR-017**: Les tools DOIVENT retourner des erreurs explicites en cas d'échec, et le LLM DOIT communiquer ces erreurs à l'utilisateur de manière compréhensible.
- **FR-018**: AUCUN noeud ne DOIT pouvoir répondre "je ne peux pas sauvegarder" ou demander à l'utilisateur de copier-coller manuellement.
- **FR-019**: Le LLM DOIT demander confirmation à l'utilisateur avant d'exécuter les tools de finalisation (finalize_esg_assessment, finalize_carbon_assessment). Les autres tools (lecture, sauvegarde incrémentale, export) s'exécutent sans confirmation.
- **FR-020**: Le LLM peut chaîner un maximum de 5 tool calls par tour de conversation. Au-delà, il DOIT compléter les actions restantes au tour suivant.
- **FR-021**: En cas d'échec d'un tool, le système DOIT effectuer 1 retry automatique silencieux. Si le retry échoue, le LLM DOIT informer l'utilisateur de l'erreur et proposer de réessayer, sans perdre le contexte de conversation.
- **FR-022**: Chaque tool call DOIT être journalisé avec : nom du tool, paramètres d'entrée, résultat complet, durée d'exécution, et statut (succès/échec/retry).

### Key Entities

- **Tool** : Fonction décorée qui encapsule un appel au service métier. Possède un nom, une description, des paramètres typés, et retourne un résultat structuré.
- **ToolMessage** : Message contenant le résultat d'un tool call, renvoyé au LLM pour qu'il formule sa réponse finale.
- **ConversationState** : État partagé dans le graphe LangGraph, contient le user_id, l'historique, et les métadonnées de session.
- **Événement SSE tool_call** : Nouvel événement dans le flux SSE pour notifier le frontend qu'un tool est en cours d'exécution.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Quand l'utilisateur fournit des informations d'entreprise dans le chat, les données apparaissent sur la page /profile en moins de 5 secondes sans action manuelle supplémentaire.
- **SC-002**: Pendant une évaluation ESG conversationnelle, chaque critère est sauvegardé individuellement — un rechargement de la page /esg en milieu d'évaluation affiche les critères déjà évalués.
- **SC-003**: Quand l'utilisateur fournit des données de consommation, l'entrée d'émission apparaît sur /carbon avec le calcul en tCO2e en moins de 5 secondes.
- **SC-004**: 100% des demandes d'action (sauvegarder, calculer, générer, exporter) déclenchent un tool call — 0% de réponses purement textuelles quand une action est demandée.
- **SC-005**: Les réponses aux questions factuelles ("quel est mon score ?") reflètent les données actuelles en base, pas des données obsolètes de la conversation.
- **SC-006**: Quand un plan d'action est demandé, il est sauvegardé et visible sur /action-plan immédiatement après la réponse du LLM.
- **SC-007**: Le frontend affiche un indicateur visuel pendant l'exécution des tools, et le streaming reprend automatiquement après.
- **SC-008**: En cas d'erreur d'un tool, l'utilisateur reçoit un message d'erreur compréhensible et la conversation reste fonctionnelle.

## Assumptions

- Les modules métier existants (services, modèles, endpoints REST) fonctionnent correctement et ne nécessitent pas de modification structurelle — seule la couche d'intégration tool calling est à ajouter.
- Le LLM utilisé (Claude via OpenRouter) supporte nativement le function calling / tool use.
- LangChain et LangGraph sont dans des versions compatibles avec le tool calling (décorateur @tool, bind_tools, tool_calls sur les responses).
- Le user_id est toujours disponible dans le ConversationState au moment de l'exécution des noeuds.
- Les opérations de base de données via les services existants sont suffisamment rapides (< 2 secondes) pour ne pas créer de timeout perceptible par l'utilisateur.
- Le frontend gère déjà les blocs visuels (chart, mermaid, gauge) dans les réponses du chat — seul l'ajout des événements SSE pour les tool calls est nécessaire côté frontend.
- Les sessions de base de données async (SQLAlchemy) sont correctement gérées dans le contexte des tools LangChain.
