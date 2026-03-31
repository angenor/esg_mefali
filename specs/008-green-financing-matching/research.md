# Research: 008-green-financing-matching

**Date**: 2026-03-31
**Feature**: Financements Verts — BDD, Matching & Parcours d'Acces

## R1 — Modele de donnees statiques vs dynamiques pour les fonds

**Decision**: Modele hybride — tables SQL pour les entites (Fund, Intermediary, FundIntermediary) avec seed data via un script Python dedie (`seed_financing.py`), et non des constantes Python comme les modules ESG/carbone.

**Rationale**: Contrairement aux criteres ESG (fixes par nature) ou aux facteurs d'emission (standards scientifiques), les fonds et intermediaires changent dans le temps (statuts, deadlines, contacts). Une table SQL permet les mises a jour admin sans redeploiement. Le seed script initialise les 12 fonds et 14+ intermediaires au premier lancement.

**Alternatives considered**:
- Constantes Python (comme `emission_factors.py`) — rejete car les donnees evoluent et un admin doit pouvoir les modifier.
- Fichier JSON externe — rejete car ajoute un point de lecture supplementaire sans benefice par rapport a la BDD.

## R2 — Strategie d'embeddings pour le RAG financement

**Decision**: Reutiliser l'infrastructure `DocumentChunk` existante avec `Vector(1536)` et `text-embedding-3-small`. Creer des chunks dedies pour les fonds et intermediaires (description + eligibilite + services), stockes dans une nouvelle table `financing_chunk` avec le meme schema que `DocumentChunk` mais liee a `fund_id` ou `intermediary_id` au lieu de `document_id`.

**Rationale**: Le modele d'embedding est deja configure et fonctionne via OpenRouter. Une table separee evite de polluer les chunks documentaires utilisateur avec les donnees de reference, et permet une recherche ciblee (chercher uniquement dans les fonds ou uniquement dans les intermediaires).

**Alternatives considered**:
- Reutiliser `DocumentChunk` avec un champ `source_type` — rejete car le filtrage serait plus complexe et les chunks fonds ne sont pas lies a un utilisateur.
- Pas de RAG (recherche par mots-cles SQL) — rejete car la recherche semantique est requise (FR-013) et les questions en langage naturel beneficient d'embeddings.

## R3 — Generation du parcours d'acces par Claude

**Decision**: Utiliser une chaine LangChain simple (prompt template + LLM call) dans le `financing_node` pour generer le parcours d'acces textuel. Le prompt recoit le profil PME, le fonds match, les intermediaires disponibles, et produit un parcours en 5 etapes structure.

**Rationale**: Le parcours d'acces est contextuel (depend du profil PME + fonds + intermediaires locaux) et doit etre en francais naturel. Un template statique ne couvrirait pas tous les cas. L'appel LLM est deja le pattern standard du projet (tous les nodes font un appel LLM via `get_llm()`).

**Alternatives considered**:
- Template statique avec variables — rejete car trop rigide pour les 12 fonds tres differents (SUNREF vs Gold Standard vs GCF).
- Pre-generer les parcours au seed — rejete car le parcours depend du profil PME specifique.

## R4 — Fiche de preparation : format de sortie

**Decision**: Generer la fiche en HTML via un template Jinja2, convertie en PDF avec WeasyPrint (meme pattern que le module reports). La fiche est legere (1-2 pages) et stockee temporairement.

**Rationale**: WeasyPrint est deja installe et maitrise dans le module reports. Le pattern Jinja2 + WeasyPrint est eprouve. Un PDF est le format le plus pratique pour imprimer et apporter a un rendez-vous.

**Alternatives considered**:
- Document HTML imprimable (sans PDF) — acceptable comme fallback, mais le PDF est plus professionnel pour un rendez-vous bancaire.
- DOCX via python-docx — rejete car WeasyPrint est deja en place.

## R5 — Strategie de scoring/matching

**Decision**: Scoring deterministe avec ponderation fixe : secteur (30%), ESG (25%), taille (15%), localisation (10%), documents (20%). Chaque dimension produit un sous-score 0-100, le score final est la moyenne ponderee. Pas d'appel LLM pour le calcul du score.

**Rationale**: La ponderation est specifiee dans les requirements (FR-004). Un calcul deterministe est reproductible, testable et instantane. Le LLM est utilise ensuite pour generer le parcours d'acces, pas pour le score numerique.

**Alternatives considered**:
- Scoring par LLM (Claude evalue la compatibilite) — rejete car non reproductible, lent, couteux.
- ML/modele entraine — rejete car pas de donnees d'entrainement disponibles.

## R6 — Integration dans le graphe LangGraph

**Decision**: Ajouter `financing_node` comme nouveau noeud dans le graphe existant, avec une priorite entre carbon et document. Ajouter `_route_financing: bool` et `financing_data: dict | None` au `ConversationState`. Le routeur detecte les intentions financement via regex (mots-cles : financement, fonds, SUNREF, GCF, credit carbone, intermediaire, banque verte, etc.).

**Rationale**: Suit exactement le pattern des noeuds existants (esg_scoring_node, carbon_node). La priorite de routage devient : ESG > carbon > financing > document > chat.

**Alternatives considered**:
- Module separe sans integration LangGraph — rejete car le chat doit pouvoir repondre aux questions de financement (FR-012).
- Sous-graphe LangGraph — rejete car les noeuds existants sont simples (pas de sous-graphes) et un noeud unique suffit.
