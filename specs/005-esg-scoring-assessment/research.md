# Research: Evaluation et Scoring ESG Contextualise

**Feature**: 005-esg-scoring-assessment
**Date**: 2026-03-31

## R1 — Grille d'evaluation ESG contextualise Afrique

**Decision**: Grille de 30 criteres (10 par pilier) avec ponderation sectorielle configurable, definie comme donnees de reference dans le code (dict Python).

**Rationale**: Les frameworks ESG internationaux (GRI, SASB) sont trop complexes pour les PME africaines. La grille simplifiee a 30 criteres (0-10 chacun) offre un equilibre entre exhaustivite et accessibilite. La ponderation sectorielle permet d'adapter l'evaluation au contexte (ex: gestion de l'eau critique pour l'agriculture, moins pour les services numeriques).

**Alternatives considered**:
- GRI Standards complets (300+ indicateurs) : trop lourd pour les PME, non adapte au secteur informel
- Score binaire (oui/non) : trop simpliste, ne permet pas de mesurer la progression
- Questionnaire a choix multiples fixe : rigide, pas conversationnel

## R2 — Ponderation sectorielle

**Decision**: Dictionnaire Python de ponderations par secteur, avec des poids par defaut de 1.0 si le secteur n'est pas specifiquement configure. Score par pilier = somme ponderee des criteres normalises a 100. Score global = moyenne des 3 piliers (ponderation egale E/S/G par defaut).

**Rationale**: Les ponderations sont des donnees metier qui evoluent rarement. Les stocker comme configuration dans le code (fichier `weights.py`) simplifie le systeme sans perte de flexibilite. Les secteurs principaux de la zone UEMOA sont couverts : agriculture, energie, recyclage, transport, construction, textile, agroalimentaire, services, commerce, artisanat.

**Alternatives considered**:
- Ponderations en base de donnees : over-engineering pour un premier deploiement, les ponderations sont stables
- Ponderations via API externe : ajoute une dependance, pas justifie au stade actuel
- Ponderation IA dynamique : complexite excessive, manque de transparence pour l'utilisateur

## R3 — Integration dans le graph LangGraph

**Decision**: Ajouter `esg_scoring_node` dans `graph/nodes.py` existant. Le `router_node` detecte les intentions ESG (regex + mots-cles) et route vers ce noeud. Le ConversationState est enrichi avec un champ `esg_assessment` (dict) pour maintenir l'etat de l'evaluation en cours.

**Rationale**: Le pattern est identique au routage existant (profiling, documents). Garder les noeuds dans un seul fichier (`nodes.py`) est coherent avec l'architecture actuelle. Le state LangGraph gere naturellement la persistance entre les tours de conversation.

**Alternatives considered**:
- Fichier `nodes/esg_scoring.py` separe : diverge de l'architecture actuelle (tous les noeuds sont dans `graph/nodes.py`)
- Sous-graph LangGraph dedie : complexite prematuree, un noeud suffit pour gerer l'evaluation sequentielle
- Workflow separe (hors LangGraph) : perd les avantages du state management et du streaming

## R4 — Enrichissement RAG pour l'evaluation

**Decision**: Lors de l'evaluation de chaque critere, le `esg_scoring_node` effectue une recherche vectorielle dans les `DocumentChunk` pour trouver des informations pertinentes. Les resultats sont injectes dans le prompt comme contexte additionnel.

**Rationale**: L'infrastructure RAG (pgvector, DocumentChunk, embeddings) est deja en place via la feature 004. La recherche vectorielle par critere permet une granularite fine. Le prompt systeme du noeud ESG inclut des instructions pour citer les sources documentaires.

**Alternatives considered**:
- RAG global (un seul appel pour tous les criteres) : perd la granularite, resultats moins pertinents
- Pas de RAG (conversationnel pur) : fonctionnel mais sous-utilise les documents uploades
- Pre-processing complet des documents en scores : trop deterministe, ne permet pas le dialogue

## R5 — Benchmarks sectoriels

**Decision**: Donnees de reference predefinies dans un fichier `weights.py` (ou integrees dans `criteria.py`), contenant les moyennes E, S, G par secteur. Basees sur des estimations de contexte UEMOA.

**Rationale**: En l'absence de donnees reelles massives, des benchmarks de reference sont necessaires pour donner du contexte aux scores. Ils sont presentes comme "moyennes estimees" et seront affines au fil du temps avec les donnees reelles de la plateforme.

**Alternatives considered**:
- Calcul dynamique a partir des evaluations existantes : necesssite une masse critique de donnees (pas disponible au lancement)
- API externe de benchmarks ESG : n'existe pas pour le contexte PME Afrique
- Pas de benchmark : perd un element de valeur important pour l'utilisateur

## R6 — Instructions visuelles dans le prompt du noeud ESG

**Decision**: Le prompt systeme du `esg_scoring_node` inclut des instructions explicites pour generer des blocs visuels (```progress, ```chart, ```gauge, ```table, ```mermaid) a des moments precis de l'evaluation. Le format JSON des blocs est documente dans le prompt.

**Rationale**: Les blocs visuels du chat sont deja implementes et parses par le frontend (feature 002). Il suffit d'instruire Claude pour les generer dans ses reponses. Cela reutilise l'infrastructure existante sans modification du frontend.

**Alternatives considered**:
- Generation des visuels cote backend (pas par le LLM) : perd la flexibilite conversationnelle, plus complexe
- Composants frontend dedies hors chat : duplique la logique, les blocs visuels existent deja
- Pas de visuels dans le chat : sous-utilise le systeme de rendu riche, experience utilisateur degradee

## R7 — Page de resultats persistante vs chat

**Decision**: La page `/esg/results` charge les donnees depuis l'API REST (`GET /api/esg/assessments/{id}/score`), independamment du chat. Les visuels sont rendus par des composants Vue dedies (Chart.js pour radar/barres, composant cercle pour le score global).

**Rationale**: Le chat offre une experience temps reel mais ephemere. La page de resultats est la reference persistante, navigable, et partageable. Les deux sont complementaires.

**Alternatives considered**:
- Tout dans le chat : pas de vue persistante, difficulte a retrouver les resultats
- Tout sur la page (pas de visuels chat) : perd l'experience conversationnelle engageante
- Page generee depuis les messages du chat : fragile, dependant du format des messages
