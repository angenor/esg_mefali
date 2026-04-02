# Research: 015-fix-toolcall-esg-timeout

## R1: Cause reelle du tool calling absent (application + credit)

**Decision**: Le probleme n'est PAS des instructions "JSON only" bloquantes (elles n'existent pas dans le code). Le probleme est double :
1. Le prompt application a un ROLE passif ("Tu informes") au lieu d'actif ("Tu crees et geres")
2. Le tool `create_fund_application` est absent — le LLM ne peut pas creer de dossier

**Rationale**: Inspection directe des fichiers `application.py`, `credit.py`, `nodes.py` et `graph.py`. L'architecture ToolNode est correcte (boucle conditionnelle max 5 iterations). Les prompts manquent de directivite sur l'utilisation des tools.

**Alternatives considered**:
- Modifier les noeuds pour executer manuellement les tool_calls → Rejecte car `create_tool_loop` dans `graph.py` le fait deja
- Ajouter un middleware de tool calling → Rejecte car l'architecture existante est correcte

## R2: Tool create_fund_application manquant

**Decision**: Creer le tool `create_fund_application` dans `application_tools.py` qui cree un dossier en base avec un `fund_id` et retourne l'`application_id`.

**Rationale**: Les tools existants (`generate_application_section`, `update_application_section`, etc.) requierent tous un `application_id` existant. Sans tool de creation, le LLM ne peut pas initier un dossier.

**Alternatives considered**:
- Creer le dossier dans le noeud avant l'appel LLM → Rejecte car le LLM doit pouvoir decider quand creer un dossier en fonction de la conversation
- Creer automatiquement un dossier quand le module application est active → Rejecte car l'utilisateur peut juste demander des informations sans vouloir creer un dossier

## R3: Strategie batch pour ESG scoring

**Decision**: Ajouter un tool `batch_save_esg_criteria` qui sauvegarde N criteres en une seule transaction DB.

**Rationale**: Le tool `save_esg_criterion_score` fait 1 write par appel. Avec la boucle max 5 du graphe, le LLM ne peut sauvegarder que 5 criteres par tour avant de terminer. Pour un pilier de 10 criteres, il faudrait 2 tours au minimum. Le batch permet 10 ou 30 criteres en 1 seul tool call.

**Alternatives considered**:
- Augmenter `MAX_TOOL_CALLS_PER_TURN` a 30 → Rejecte car ca multiplierait la latence (30 * 1-2s = 30-60s)
- Sauvegarder tous les criteres dans `finalize_esg_assessment` → Rejecte car `finalize` lit deja les criteres en base et ne fait que les agreger, ce qui est correct

## R4: Configuration timeout LLM

**Decision**: Ajouter `request_timeout=60` dans `get_llm()` et documenter.

**Rationale**: `get_llm()` utilise `ChatOpenAI` sans timeout explicite, ce qui depend du defaut httpx (~30s). Pour les operations batch ESG, 60 secondes est necessaire.

**Alternatives considered**:
- Timeout par noeud (different pour ESG vs chat) → Rejecte car complexite inutile, 60s est raisonnable pour tous les noeuds
- Pas de timeout (defaut httpx) → Rejecte car non predictible et potentiellement trop court
