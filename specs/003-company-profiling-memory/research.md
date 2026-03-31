# Research: 003-company-profiling-memory

**Date**: 2026-03-30
**Branch**: `003-company-profiling-memory`

## R1: Streaming SSE et integration LangGraph

### Probleme
Le streaming actuel (`api/chat.py`) contourne le graphe LangGraph : il appelle `llm.astream()` directement. Pour que le `profiling_node` s'execute dans le graphe et que le state partage (`user_profile`) soit accessible a tous les noeuds, le streaming doit passer par le graphe.

### Decision
Refactorer le streaming pour utiliser `graph.astream_events()` (LangGraph v2) qui permet de streamer les tokens du LLM tout en executant les noeuds du graphe. L'endpoint SSE ecoute les events `on_chat_model_stream` pour le texte et les events custom pour les mises a jour de profil.

### Rationale
- `astream_events()` est le mecanisme officiel LangGraph pour combiner streaming de tokens et execution de noeuds
- Permet d'emettre des events SSE custom (ex: `profile_update`) en plus des tokens de chat
- Le checkpointer (MemorySaver ou PostgresSaver) persiste l'etat entre les invocations

### Alternatives considerees
- **Appel parallele hors-graphe** : appeler le LLM en streaming + extraire le profil separement. Rejete car l'etat du profil serait deconnecte du graphe et difficile a maintenir.
- **Middleware FastAPI** : intercepter les reponses pour extraire le profil. Rejete car fragile et non integre a l'etat conversationnel.

## R2: Extraction structuree via LangChain

### Decision
Utiliser `ChatOpenAI.with_structured_output()` avec un modele Pydantic `ProfileExtraction` pour extraire les informations de profil depuis les messages utilisateur. La chaine prend en entree le message utilisateur + le profil actuel et retourne les champs a mettre a jour.

### Rationale
- `with_structured_output()` force le LLM a retourner un JSON valide conforme au schema Pydantic
- Le profil actuel en entree permet au LLM de ne retourner que les champs nouveaux/modifies
- Les champs optionnels (Optional) permettent de ne retourner que les champs detectes avec confiance

### Alternatives considerees
- **Output parser avec regex** : fragile, ne gere pas bien les cas limites francophones
- **NER/NLP classique** : necesiterait un modele entraine sur le vocabulaire metier africain, complexite excessive
- **Function calling** : equivalent a `with_structured_output()` mais plus verbeux

## R3: Graphe multi-noeuds avec routage conditionnel

### Decision
Transformer le graphe lineaire (chat seul) en graphe conditionnel :
1. `router_node` : analyse le message et decide du routage
2. Si extraction detectee : execution parallele `chat_node` + `profiling_node`
3. Si pas d'extraction : `chat_node` seul
4. Le `router_node` injecte aussi les instructions de profilage si le profil est < 70% complet

### Rationale
- LangGraph supporte nativement les branches conditionnelles et l'execution parallele via `Send()`
- Le routeur est un noeud leger (pas d'appel LLM, juste de la logique Python basee sur le completion_percentage et des heuristiques simples)
- L'execution parallele respecte la contrainte de latence < 1s (FR-009)

### Structure du graphe
```
START → router_node → [conditional]
  ├── chat_node (toujours)
  └── profiling_node (si extraction detectee)
       → update_profile → END
chat_node → END
```

### Alternatives considerees
- **Subgraph separe** : profiling dans un sous-graphe. Rejete car surconception pour 2-3 noeuds.
- **Tool calling** : le chat_node appelle une tool d'extraction. Rejete car lie l'extraction au chat et empeche l'execution parallele.

## R4: Calcul du pourcentage de completion

### Decision
Deux pourcentages calcules dynamiquement :
1. **Identite & Localisation** (pour le seuil 70%) : 8 champs (company_name, sector, sub_sector, employee_count, annual_revenue_xof, year_founded, city, country). Chaque champ rempli = 12.5%.
2. **ESG** (suivi separe) : 8 champs (5 booleens + 3 textuels). Chaque champ rempli = 12.5%.

Le `completion_percentage` global affiche dans la sidebar/page profil = moyenne ponderee ou les deux barres separees.

### Rationale
- Conforme a la clarification : le seuil de 70% ne porte que sur identite + localisation
- Les booleens ESG etant oui/non, ils sont consideres "remplis" des qu'ils ont une valeur (True ou False)
- Le champ `country` a un defaut ("Cote d'Ivoire") donc il est toujours rempli → 7 champs restants a remplir pour atteindre 100% identite

## R5: Memoire contextuelle et resumes de conversation

### Decision
Un resume est genere par le LLM quand l'utilisateur cree un nouveau thread/conversation. Le resume du thread precedent est genere a ce moment via une chaine LangChain dediee (prompt de summarization). Les 3 derniers resumes sont stockes dans le champ `context_memory` du ConversationState et injectes dans le prompt systeme.

### Rationale
- Conforme a la clarification : generation au moment de la creation d'un nouveau thread
- Stockage dans le state LangGraph = accessible a tous les noeuds automatiquement
- 3 resumes = compromis entre contexte suffisant et taille du prompt

### Implementation
- Un champ `summary` sur le modele `Conversation` en base stocke le resume
- A la creation d'un nouveau thread, on genere le resume du thread precedent (s'il n'en a pas)
- On charge les 3 derniers resumes des conversations de l'utilisateur dans le state

## R6: Detection d'informations extractibles dans le routeur

### Decision
Le `router_node` utilise des heuristiques simples (mots-cles, patterns regex) pour detecter si un message POURRAIT contenir des informations de profil, sans appel LLM. Si le doute existe, il route vers le `profiling_node` qui fait l'extraction fine via LLM.

### Heuristiques
- Mots-cles : "employes", "salaries", "effectifs", "chiffre d'affaires", "CA", noms de villes africaines, noms de secteurs
- Patterns : nombres suivis de "personnes/employes/FCFA/millions"
- Seuil : si au moins 1 match → route vers profiling_node

### Rationale
- Pas d'appel LLM dans le routeur = latence ~0ms pour le routage
- Faux positifs acceptables : le profiling_node retournera simplement aucune extraction
- Faux negatifs minimises par des heuristiques larges
