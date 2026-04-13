# Story 6.2 : Prompt GUIDED_TOUR_INSTRUCTION et injection dans les noeuds LangGraph

Status: in-progress

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

En tant qu'utilisateur,
je veux que l'assistant sache quels parcours guides sont disponibles et quand les proposer,
afin de recevoir des suggestions de guidage pertinentes au bon moment.

## Acceptance Criteria

### AC1 : Creation du prompt `GUIDED_TOUR_INSTRUCTION`

**Given** le prompt `GUIDED_TOUR_INSTRUCTION` n'existe pas encore
**When** un developpeur le cree dans `backend/app/prompts/guided_tour.py`
**Then** il contient la liste des 6 parcours disponibles avec leurs identifiants exacts :
- `show_esg_results`
- `show_carbon_results`
- `show_financing_catalog`
- `show_credit_score`
- `show_action_plan`
- `show_dashboard_overview`

**And** il definit les regles de declenchement : proposer UNIQUEMENT apres completion d'un module ou sur demande explicite
**And** il precise d'utiliser `ask_interactive_question` (SingleChoiceWidget, 2 options « Oui / Non merci ») pour le consentement, SAUF sur demande explicite ou le tool `trigger_guided_tour` est appele directement
**And** le pattern suit exactement celui de `WIDGET_INSTRUCTION` (module-level string, docstring de fichier, exemples inclus)

### AC2 : Injection dans les 6 noeuds LangGraph autorises

**Given** le prompt `GUIDED_TOUR_INSTRUCTION` est cree
**When** les fonctions `build_*_prompt()` des noeuds specialises sont modifiees
**Then** `GUIDED_TOUR_INSTRUCTION` est concatene apres `WIDGET_INSTRUCTION` dans les 6 prompts suivants :
- `build_system_prompt()` dans `prompts/system.py` (pour chat_node) — injection conditionnelle post-onboarding (meme regle que `STYLE_INSTRUCTION`, voir `system.py:212`)
- `build_esg_prompt()` dans `prompts/esg_scoring.py`
- `build_carbon_prompt()` dans `prompts/carbon.py`
- `build_financing_prompt()` dans `prompts/financing.py`
- `build_credit_prompt()` dans `prompts/credit.py`
- `build_action_plan_prompt()` dans `prompts/action_plan.py`

**And** l'import `from app.prompts.guided_tour import GUIDED_TOUR_INSTRUCTION` est local (dans chaque fonction builder, pattern identique a l'import de `WIDGET_INSTRUCTION`)

### AC3 : Non-injection dans les noeuds exclus

**Given** les noeuds non autorises ne recoivent pas le prompt
**When** on inspecte les builders de prompts des noeuds exclus
**Then** `GUIDED_TOUR_INSTRUCTION` N'EST PAS present dans :
- `build_application_prompt()` dans `prompts/application.py` (module de generation de dossier, hors parcours visuels)
- `prompts/esg_report.py` (generation de rapport PDF, pas de chat interactif)
- `document_node`, `profiling_node`, `router_node` (pas de prompt systeme LLM cote chat conversationnel)

### AC4 : Binding du tool `trigger_guided_tour` dans les 6 noeuds

**Given** les noeuds doivent pouvoir APPELER le tool `trigger_guided_tour`
**When** on inspecte les appels `llm.bind_tools(...)` dans `graph/nodes.py`
**Then** `GUIDED_TOUR_TOOLS` (importe depuis `app.graph.tools.guided_tour_tools`) est ajoute aux listes d'outils pour :
- `chat_node` (ligne ~1111 : `all_tools = PROFILING_TOOLS + CHAT_TOOLS + DOCUMENT_TOOLS + INTERACTIVE_TOOLS + GUIDED_TOUR_TOOLS`)
- `esg_scoring_node` (ligne ~672 : `llm.bind_tools(ESG_TOOLS + INTERACTIVE_TOOLS + GUIDED_TOUR_TOOLS)`)
- `carbon_node` (ligne ~811)
- `financing_node` (ligne ~855 zone)
- `credit_node` (ligne ~1042)
- `action_plan_node` (ligne ~1257 zone)

**And** le tool N'EST PAS binde dans `application_node`, `document_node`, `profiling_node`, `router_node`

### AC5 : Cas d'usage LLM — proposition apres completion de module

**Given** `esg_scoring_node` termine une evaluation ESG complete (30 criteres)
**When** le LLM genere sa reponse finale
**Then** le prompt `GUIDED_TOUR_INSTRUCTION` lui permet de proposer textuellement un guidage puis d'appeler `ask_interactive_question` (Oui/Non merci) — le tool `trigger_guided_tour('show_esg_results')` sera appele au tour suivant si l'utilisateur accepte (la logique complete consentement est implementee dans story 6.3)

### AC6 : Cas d'usage LLM — declenchement direct sur demande explicite

**Given** `chat_node` recoit un message utilisateur explicite (« montre-moi mes resultats carbone », « guide-moi vers le plan d'action »)
**When** le LLM analyse la demande
**Then** le prompt lui indique de detecter l'intent de guidage explicite
**And** il appelle `trigger_guided_tour('show_carbon_results')` ou `trigger_guided_tour('show_action_plan')` directement SANS passer par `ask_interactive_question`

### AC7 : Zero regression et couverture tests

**Given** les tests existants (992+ tests backend, 267+ tests frontend)
**When** on execute la suite complete `cd backend && python -m pytest`
**Then** zero regression sur les suites existantes (NFR19)
**And** les nouveaux tests du prompt/injection atteignent >= 80 % de couverture sur le code ajoute
**And** le fichier `backend/tests/test_prompts/test_guided_tour_instruction.py` est cree avec AU MINIMUM :
- 1 test verifiant que `GUIDED_TOUR_INSTRUCTION` contient les 6 `tour_id`
- 1 test verifiant que `GUIDED_TOUR_INSTRUCTION` contient les mots-cles de declenchement (« apres completion », « demande explicite », `ask_interactive_question`)
- 6 tests d'injection positifs (un par noeud autorise)
- 2 tests d'exclusion negatifs (`build_application_prompt`, et absence dans le prompt chat minimal sans profil)
- 1 test parametrise verifiant le binding `GUIDED_TOUR_TOOLS` dans les 6 noeuds (peut etre un smoke test sur l'import et la signature de `bind_tools`)

## Tasks / Subtasks

- [ ] Task 1 : Creer `backend/app/prompts/guided_tour.py` (AC: #1)
  - [ ] 1.1 Ajouter la docstring de fichier (pattern identique a `widget.py` lignes 1-6)
  - [ ] 1.2 Definir `GUIDED_TOUR_INSTRUCTION` comme triple-quoted string en majuscules avec sections Markdown
  - [ ] 1.3 Section `## OUTIL GUIDAGE VISUEL — trigger_guided_tour` : description du tool
  - [ ] 1.4 Section `### Parcours disponibles` : liste des 6 `tour_id` + une ligne de description pour chaque
  - [ ] 1.5 Section `### Quand proposer un guidage` : apres completion d'un module OU sur demande explicite
  - [ ] 1.6 Section `### Regles de declenchement obligatoires` :
    - Consentement via `ask_interactive_question` (2 options, QCU) SAUF demande explicite
    - Un seul guidage par tour de conversation
    - Pas de texte apres `trigger_guided_tour` (meme regle que pour le widget interactif)
    - `context` reste sans donnees PII (NFR10 — rappel)
  - [ ] 1.7 Section `### Exemple 1 — proposition post-module` (ESG termine → `ask_interactive_question` Oui/Non → si Oui, appeler `trigger_guided_tour`)
  - [ ] 1.8 Section `### Exemple 2 — declenchement direct` (utilisateur dit « montre-moi mes resultats carbone » → appel direct `trigger_guided_tour('show_carbon_results')`)

- [ ] Task 2 : Injecter `GUIDED_TOUR_INSTRUCTION` dans les 6 prompts specialises (AC: #2, #3)
  - [ ] 2.1 `prompts/esg_scoring.py` : modifier `build_esg_prompt()` — ajouter import local + `"\n\n" + GUIDED_TOUR_INSTRUCTION` apres `WIDGET_INSTRUCTION`
  - [ ] 2.2 `prompts/carbon.py` : meme modification dans `build_carbon_prompt()`
  - [ ] 2.3 `prompts/financing.py` : meme modification dans `build_financing_prompt()`
  - [ ] 2.4 `prompts/credit.py` : meme modification dans `build_credit_prompt()`
  - [ ] 2.5 `prompts/action_plan.py` : meme modification dans `build_action_plan_prompt()`
  - [ ] 2.6 `prompts/system.py` : dans `build_system_prompt()`, injecter `GUIDED_TOUR_INSTRUCTION` dans la meme branche conditionnelle que `STYLE_INSTRUCTION` (ligne ~212, apres `_has_minimum_profile(user_profile)`) — le chat general ne parle de guidage qu'une fois l'utilisateur onboarde
  - [ ] 2.7 NE PAS modifier `prompts/application.py` ni `prompts/esg_report.py`

- [ ] Task 3 : Binder `GUIDED_TOUR_TOOLS` dans les 6 noeuds LangGraph (AC: #4)
  - [ ] 3.1 `graph/nodes.py` : ajouter l'import `from app.graph.tools.guided_tour_tools import GUIDED_TOUR_TOOLS` en tete de fichier (a cote des autres imports de tools)
  - [ ] 3.2 `chat_node` (~L1111) : etendre `all_tools` avec `+ GUIDED_TOUR_TOOLS`
  - [ ] 3.3 `esg_scoring_node` (~L672) : etendre l'argument de `llm.bind_tools(...)` avec `+ GUIDED_TOUR_TOOLS`
  - [ ] 3.4 `carbon_node` (~L811) : idem sur `all_carbon_tools`
  - [ ] 3.5 `financing_node` : ajouter `GUIDED_TOUR_TOOLS` au binding (verifier le nom exact de la variable `FINANCING_TOOLS`)
  - [ ] 3.6 `credit_node` (~L1042) : ajouter `+ GUIDED_TOUR_TOOLS`
  - [ ] 3.7 `action_plan_node` : ajouter `+ GUIDED_TOUR_TOOLS` au binding
  - [ ] 3.8 Verifier que `application_node`, `document_node`, `profiling_node`, `router_node` NE sont PAS modifies

- [ ] Task 4 : Creer la suite de tests `backend/tests/test_prompts/test_guided_tour_instruction.py` (AC: #7)
  - [ ] 4.1 Test : `GUIDED_TOUR_INSTRUCTION` contient les 6 `tour_id` exacts
  - [ ] 4.2 Test : `GUIDED_TOUR_INSTRUCTION` contient les mots-cles « apres completion », « demande explicite », « ask_interactive_question », « consentement »
  - [ ] 4.3 Tests (parametrises ou separes) : 6 tests d'injection positifs — `GUIDED_TOUR_INSTRUCTION in build_esg_prompt()` / `build_carbon_prompt()` / `build_financing_prompt()` / `build_credit_prompt()` / `build_action_plan_prompt()` / `build_system_prompt(user_profile={"sector":"...","city":"..."})` (profil minimal atteint pour la branche conditionnelle)
  - [ ] 4.4 Test negatif : `GUIDED_TOUR_INSTRUCTION not in build_application_prompt()`
  - [ ] 4.5 Test negatif : `GUIDED_TOUR_INSTRUCTION not in build_system_prompt()` (sans profil — meme logique que le test existant `test_style_instruction_absent_without_profile`)
  - [ ] 4.6 Test binding : importer `from app.graph.tools.guided_tour_tools import trigger_guided_tour, GUIDED_TOUR_TOOLS` + verifier que `trigger_guided_tour in GUIDED_TOUR_TOOLS`
  - [ ] 4.7 (Optionnel, defensif) Test d'import : verifier que les modules noeuds importent bien `GUIDED_TOUR_TOOLS` via inspection de `graph.nodes` avec `inspect.getsource(...)` ou `assert "GUIDED_TOUR_TOOLS" in open("backend/app/graph/nodes.py").read()`

- [ ] Task 5 : Non-regression et quality gate (AC: #7)
  - [ ] 5.1 Activer le venv : `source backend/venv/bin/activate`
  - [ ] 5.2 Executer `cd backend && python -m pytest` — viser 0 failure sur les 992+ tests existants
  - [ ] 5.3 Executer `cd backend && python -m pytest tests/test_prompts/test_guided_tour_instruction.py -v` — tous les nouveaux tests passent
  - [ ] 5.4 Verifier couverture via `python -m pytest --cov=app.prompts.guided_tour --cov=app.graph.tools.guided_tour_tools --cov-report=term-missing` — >= 80 %
  - [ ] 5.5 Formater : `black backend/app/prompts/guided_tour.py backend/tests/test_prompts/test_guided_tour_instruction.py`
  - [ ] 5.6 Lint : `ruff check backend/app/prompts/guided_tour.py` — 0 warning

## Dev Notes

### Pattern de reference : `WIDGET_INSTRUCTION` (feature 018)

Le fichier `backend/app/prompts/widget.py` (51 lignes) est la reference de design a reproduire :

```python
"""Helper partage : instructions communes pour le tool ask_interactive_question.

Injecte dans les 7 prompts des modules metier [...].
"""

WIDGET_INSTRUCTION = """## OUTIL INTERACTIF — ask_interactive_question

Tu disposes d'un outil [...].

### Quand l'utiliser
- [...]

### Regles d'emploi obligatoires
1. **Un seul appel par tour** : [...]

### Exemple d'invocation
```
ask_interactive_question(
  question_type="qcu",
  [...]
)
```
"""
```

Le fichier `guided_tour.py` doit suivre cette meme structure : docstring explicative, une seule constante module-level `GUIDED_TOUR_INSTRUCTION`, sections Markdown, un ou deux exemples concrets d'invocation du tool.

### Pattern d'injection dans les prompts (esg_scoring.py:83-107)

```python
def build_esg_prompt(
    company_context: str = "Aucun profil disponible.",
    document_context: str = "Aucun document analyse.",
    current_page: str | None = None,
) -> str:
    from app.prompts.system import STYLE_INSTRUCTION, build_page_context_instruction
    from app.prompts.widget import WIDGET_INSTRUCTION
    from app.prompts.guided_tour import GUIDED_TOUR_INSTRUCTION  # AJOUT story 6.2

    prompt = (
        ESG_SCORING_PROMPT.format(
            company_context=company_context,
            document_context=document_context,
        )
        + "\n\n"
        + STYLE_INSTRUCTION
        + "\n\n"
        + WIDGET_INSTRUCTION
        + "\n\n"
        + GUIDED_TOUR_INSTRUCTION  # AJOUT story 6.2
    )

    page_context = build_page_context_instruction(current_page)
    if page_context:
        prompt += "\n\n" + page_context

    return prompt
```

**A repliquer a l'identique** pour `carbon.py`, `financing.py`, `credit.py`, `action_plan.py`.

### Pattern d'injection conditionnel dans `system.py` (chat_node)

Reproduire la branche conditionnelle existante pour `STYLE_INSTRUCTION` (voir `system.py:211-213`) :

```python
# Injecter le style concis uniquement post-onboarding
if user_profile and _has_minimum_profile(user_profile):
    sections.append(STYLE_INSTRUCTION)
    # AJOUT story 6.2 : le guidage ne concerne que les utilisateurs onboardes
    from app.prompts.guided_tour import GUIDED_TOUR_INSTRUCTION
    sections.append(GUIDED_TOUR_INSTRUCTION)
```

Le helper `_has_minimum_profile` (system.py) exige au moins 2 champs non-vides dans le profil — pertinent car un utilisateur qui n'a pas encore rempli son profil n'a aucun resultat a visiter (rien a guider).

### Binding de `GUIDED_TOUR_TOOLS` dans les noeuds (graph/nodes.py)

Le tool `trigger_guided_tour` (story 6.1) existe deja dans `backend/app/graph/tools/guided_tour_tools.py` avec l'export `GUIDED_TOUR_TOOLS = [trigger_guided_tour]` (ligne 104 du fichier). Il N'EST binde dans AUCUN noeud aujourd'hui — c'est cette story qui active la capacite d'appel cote LLM.

Reference exacte des lignes de binding actuelles (a etendre) :

- `chat_node` (`nodes.py:~1111`) :
  ```python
  all_tools = PROFILING_TOOLS + CHAT_TOOLS + DOCUMENT_TOOLS + INTERACTIVE_TOOLS
  llm = llm.bind_tools(all_tools)
  ```
  → AJOUTER `+ GUIDED_TOUR_TOOLS`

- `esg_scoring_node` (`nodes.py:~672`) :
  ```python
  llm_with_tools = llm.bind_tools(ESG_TOOLS + INTERACTIVE_TOOLS)
  ```
  → AJOUTER `+ GUIDED_TOUR_TOOLS`

- `carbon_node` (`nodes.py:~811`) :
  ```python
  all_carbon_tools = (CARBON_TOOLS or []) + INTERACTIVE_TOOLS
  llm_with_tools = llm.bind_tools(all_carbon_tools)
  ```
  → AJOUTER `all_carbon_tools = (CARBON_TOOLS or []) + INTERACTIVE_TOOLS + GUIDED_TOUR_TOOLS`

- `credit_node` (`nodes.py:~1042`) :
  ```python
  llm = llm.bind_tools((CREDIT_TOOLS or []) + INTERACTIVE_TOOLS)
  ```
  → AJOUTER `+ GUIDED_TOUR_TOOLS`

- `financing_node` et `action_plan_node` : suivre la meme logique (verifier les variables de binding reelles dans `nodes.py`).

### Liste canonique des tour_ids (source unique de verite)

La verite cote frontend (registre `lib/guided-tours/registry.ts` — fichier story 4.2) doit correspondre EXACTEMENT a la liste declaree dans `GUIDED_TOUR_INSTRUCTION`. En cas de divergence, la guard cote `useGuidedTour.startTour()` ignore silencieusement l'appel + affiche `addSystemMessage()` (comportement story 6.1 AC4). Les 6 `tour_id` valides sont :

| tour_id | Description (pour le prompt) |
|---------|------------------------------|
| `show_esg_results` | Visiter les resultats de l'evaluation ESG (page /esg/results) |
| `show_carbon_results` | Decouvrir le bilan carbone et le plan de reduction (page /carbon/results) |
| `show_financing_catalog` | Parcourir le catalogue de fonds verts et les matchs (page /financing) |
| `show_credit_score` | Comprendre le score credit alternatif (page /credit) |
| `show_action_plan` | Suivre la feuille de route 6-12-24 mois (page /action-plan) |
| `show_dashboard_overview` | Vue d'ensemble du tableau de bord (page /dashboard) |

Le dev DOIT aligner la liste du prompt sur cette table ET sur le registre frontend. Si un tour_id du registre frontend n'est pas dans cette liste, l'ajouter des deux cotes ou retirer des deux — la cohesion est critique pour AC5/AC6.

### Securite (NFR10 — rappel)

Le prompt doit explicitement rappeler au LLM que le champ `context` passe a `trigger_guided_tour` NE DOIT JAMAIS contenir d'IDs utilisateur, de tokens, d'emails ou de donnees PII. Le context est destine uniquement a personnaliser l'affichage du parcours (ex : `{"user_first_name": "Fatou"}` est acceptable, `{"user_id": "uuid..."}` ne l'est pas). Ce rappel est deja partiellement applique cote backend par la story 6.1 (validation regex `tour_id` + echappement `-->`), mais le rappel cote prompt LLM reste la premiere ligne de defense.

### Structure de fichier recommandee pour `prompts/guided_tour.py`

Gabarit suggere (~60-100 lignes, pattern identique a `widget.py`) :

```python
"""Helper partage : instructions pour le tool trigger_guided_tour.

Injecte dans les 6 prompts systeme des modules eligibles au guidage visuel
(chat post-onboarding, esg_scoring, carbon, financing, credit, action_plan).
Les modules application, document, profiling et router ne recoivent PAS
ce prompt — le guidage ne concerne pas les phases de saisie ou d'extraction.
"""

GUIDED_TOUR_INSTRUCTION = """## OUTIL GUIDAGE VISUEL — trigger_guided_tour

Tu disposes d'un outil `trigger_guided_tour` qui lance un parcours
interactif sur l'interface (flechage, popovers, navigation inter-pages).

### Parcours disponibles
- `show_esg_results` — Resultats de l'evaluation ESG (/esg/results)
- `show_carbon_results` — Bilan carbone et plan de reduction (/carbon/results)
- `show_financing_catalog` — Catalogue de fonds verts (/financing)
- `show_credit_score` — Score credit alternatif (/credit)
- `show_action_plan` — Feuille de route 6-12-24 mois (/action-plan)
- `show_dashboard_overview` — Vue d'ensemble (/dashboard)

### Quand proposer un guidage
- APRES completion d'un module (evaluation ESG terminee, bilan carbone
  finalise, plan d'action genere, dossier financement envoye).
- SUR DEMANDE EXPLICITE de l'utilisateur (« montre-moi », « guide-moi
  vers », « ou sont mes resultats », « visualise-moi »).

### Regles obligatoires
1. **Apres un module** : appelle d'abord `ask_interactive_question`
   (question_type="qcu", 2 options : {"id":"yes","label":"Oui, montre-moi","emoji":"👀"},
   {"id":"no","label":"Non merci","emoji":"🙏"}). Si l'utilisateur accepte,
   appelle `trigger_guided_tour(tour_id)` au tour suivant.
2. **Sur demande explicite** : appelle `trigger_guided_tour(tour_id)`
   IMMEDIATEMENT, SANS widget de consentement.
3. **Un seul guidage par tour** : ne declenche jamais plusieurs tours.
4. **Pas de texte apres l'appel** : le frontend prend la main, le widget
   du chat se retracte automatiquement.
5. **Securite `context`** : `context` peut porter du prenom ou des chiffres
   non sensibles pour personnaliser le texte du popover. JAMAIS d'IDs
   techniques, de tokens, d'emails ou de montants personnels.

### Exemple 1 — Proposition post-module
Apres avoir clos une evaluation ESG :
```
ask_interactive_question(
  question_type="qcu",
  prompt="Evaluation terminee ! Veux-tu que je te montre tes resultats visuellement ?",
  options=[
    {"id":"yes","label":"Oui, montre-moi","emoji":"👀"},
    {"id":"no","label":"Non merci","emoji":"🙏"},
  ],
)
```
Si la reponse est "yes" au tour suivant :
```
trigger_guided_tour(
  tour_id="show_esg_results",
  context={"pillar_top":"Social"},
)
```

### Exemple 2 — Declenchement direct
Utilisateur : « Montre-moi mes resultats carbone »
```
trigger_guided_tour(
  tour_id="show_carbon_results",
)
```
(Pas de `ask_interactive_question` : l'intent est explicite.)
"""
```

### Structure de fichier recommandee pour `test_guided_tour_instruction.py`

Suivre le pattern de `test_style_instruction.py` (~110 lignes actuellement). Utiliser `pytest.mark.parametrize` pour les 6 tests d'injection afin de rester concis. Les tests doivent etre synchrones (les builders sont synchrones), aucun `pytest.mark.asyncio` necessaire.

### Project Structure Notes

| Fichier | Action | Localisation |
|---------|--------|--------------|
| `backend/app/prompts/guided_tour.py` | CREER | Nouveau, meme dossier que `widget.py` |
| `backend/app/prompts/esg_scoring.py` | MODIFIER | `build_esg_prompt()` — import + concat |
| `backend/app/prompts/carbon.py` | MODIFIER | `build_carbon_prompt()` — import + concat |
| `backend/app/prompts/financing.py` | MODIFIER | `build_financing_prompt()` — import + concat |
| `backend/app/prompts/credit.py` | MODIFIER | `build_credit_prompt()` — import + concat |
| `backend/app/prompts/action_plan.py` | MODIFIER | `build_action_plan_prompt()` — import + concat |
| `backend/app/prompts/system.py` | MODIFIER | `build_system_prompt()` — injection conditionnelle (branche `_has_minimum_profile`) |
| `backend/app/prompts/application.py` | NE PAS TOUCHER | Exclu explicitement |
| `backend/app/prompts/esg_report.py` | NE PAS TOUCHER | Generation PDF, hors scope |
| `backend/app/graph/nodes.py` | MODIFIER | Import `GUIDED_TOUR_TOOLS` + binding dans 6 noeuds |
| `backend/tests/test_prompts/test_guided_tour_instruction.py` | CREER | Nouveaux tests unitaires |

### Alignement architecture

- **ADR4** (`architecture.md`) : Tool LangChain `trigger_guided_tour` + marker SSE — cette story branche le tool cote LLM via le prompt + le binding
- **Pattern WIDGET_INSTRUCTION / STYLE_INSTRUCTION** : module-level constant, injection via concatenation `\n\n`, import local dans les builders
- **Convention tests prompts** : `backend/tests/test_prompts/test_[feature]_instruction.py` ou `test_[module]_prompt.py`
- **Convention injection conditionnelle chat_node** : reutiliser le helper `_has_minimum_profile` — pas de nouvelle logique de gating
- **Zero nouvelle migration BDD** : cette story est 100 % prompt + binding, aucun changement Alembic

### Intelligence story 6.1 (derniere story completee — 2026-04-13)

**Lecons a retenir :**
- Le tool `trigger_guided_tour` est deja implemente, hardene (regex `tour_id`, echappement `-->`, journalisation) et teste (25 tests backend + 6 tests frontend). Cette story 6.2 active sa capacite d'appel via le prompt + le binding.
- Le handler frontend `handleGuidedTourEvent` (`useChat.ts`) bloque deja les tours lancer si `currentInteractiveQuestion.value?.state === 'pending'` (patch review 6.1). Cela confirme que l'enchainement `ask_interactive_question` → reponse utilisateur → `trigger_guided_tour` est bien supporte bout-en-bout.
- La validation serveur sur `tour_id` est en regex `^[a-z][a-z0-9_]*$` — les 6 identifiants de `GUIDED_TOUR_INSTRUCTION` doivent respecter cette contrainte (deja le cas).

**Fichiers touches dans 6.1 (contexte a ne pas casser) :**
- `backend/app/graph/tools/guided_tour_tools.py` (cree, 138 lignes)
- `backend/app/api/chat.py` (modif detection marker SSE)
- `frontend/app/composables/useChat.ts` (modif, helper `handleGuidedTourEvent`)
- 992 tests backend, 267 tests frontend, 0 regression

### Questions ouvertes pour l'utilisateur

1. **Divergence dans l'epic** — Le texte de l'epic dit « injecte dans les prompts systeme de **7 noeuds** » mais la liste enumere 6 noeuds (`chat_node, esg_scoring_node, carbon_node, financing_node, credit_node, action_plan_node`). Ma lecture : il s'agit d'un typo dans l'epic, la liste explicite fait foi → **6 noeuds**. Confirmer avant implementation ?
2. **Chat_node et injection conditionnelle** — J'ai propose d'injecter `GUIDED_TOUR_INSTRUCTION` uniquement post-onboarding (meme branche que `STYLE_INSTRUCTION`, via `_has_minimum_profile`). Rationale : un utilisateur sans profil n'a aucun resultat a visiter. Accepter cette decision, ou injecter le prompt systematiquement dans chat_node ?
3. **Tour id `show_dashboard_overview`** — Confirmer que le tour correspondant est bien implemente dans le registre frontend (`lib/guided-tours/registry.ts`, story 4.2) avec la cible `/dashboard`. Si absent, la story 6.2 peut tout de meme declarer le `tour_id` dans le prompt — la guard `startTour` gere le cas d'id inconnu (story 6.1 AC4) — mais le LLM pourrait le proposer avant qu'il ne fonctionne.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-6-Story-6.2] — Exigences de la story (lignes 950-986)
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision-4] — ADR4 Tool LangChain trigger_guided_tour
- [Source: _bmad-output/planning-artifacts/prd.md#FR14-FR17] — Consentement et declenchement du guidage
- [Source: backend/app/prompts/widget.py] — Pattern de reference `WIDGET_INSTRUCTION`
- [Source: backend/app/prompts/system.py#L80-L106] — Pattern `STYLE_INSTRUCTION`
- [Source: backend/app/prompts/system.py#L211-L213] — Pattern d'injection conditionnelle post-onboarding
- [Source: backend/app/prompts/esg_scoring.py#L83-L107] — Pattern builder avec concatenation
- [Source: backend/app/graph/tools/guided_tour_tools.py] — Tool `trigger_guided_tour` (story 6.1)
- [Source: backend/app/graph/nodes.py] — Noeuds LangGraph a modifier pour binding
- [Source: backend/tests/test_prompts/test_style_instruction.py] — Pattern de test a repliquer
- [Source: _bmad-output/implementation-artifacts/6-1-tool-langchain-trigger-guided-tour-et-marker-sse.md] — Story precedente

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
