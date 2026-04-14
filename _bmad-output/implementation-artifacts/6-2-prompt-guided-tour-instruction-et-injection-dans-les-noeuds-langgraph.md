# Story 6.2 : Prompt GUIDED_TOUR_INSTRUCTION et injection dans les noeuds LangGraph

Status: done

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

- [x] Task 1 : Creer `backend/app/prompts/guided_tour.py` (AC: #1)
  - [x] 1.1 Ajouter la docstring de fichier (pattern identique a `widget.py` lignes 1-6)
  - [x] 1.2 Definir `GUIDED_TOUR_INSTRUCTION` comme triple-quoted string en majuscules avec sections Markdown
  - [x] 1.3 Section `## OUTIL GUIDAGE VISUEL — trigger_guided_tour` : description du tool
  - [x] 1.4 Section `### Parcours disponibles` : liste des 6 `tour_id` + une ligne de description pour chaque
  - [x] 1.5 Section `### Quand proposer un guidage` : apres completion d'un module OU sur demande explicite
  - [x] 1.6 Section `### Regles de declenchement obligatoires` :
    - Consentement via `ask_interactive_question` (2 options, QCU) SAUF demande explicite
    - Un seul guidage par tour de conversation
    - Pas de texte apres `trigger_guided_tour` (meme regle que pour le widget interactif)
    - `context` reste sans donnees PII (NFR10 — rappel)
  - [x] 1.7 Section `### Exemple 1 — proposition post-module` (ESG termine → `ask_interactive_question` Oui/Non → si Oui, appeler `trigger_guided_tour`)
  - [x] 1.8 Section `### Exemple 2 — declenchement direct` (utilisateur dit « montre-moi mes resultats carbone » → appel direct `trigger_guided_tour('show_carbon_results')`)

- [x] Task 2 : Injecter `GUIDED_TOUR_INSTRUCTION` dans les 6 prompts specialises (AC: #2, #3)
  - [x] 2.1 `prompts/esg_scoring.py` : modifier `build_esg_prompt()` — ajouter import local + `"\n\n" + GUIDED_TOUR_INSTRUCTION` apres `WIDGET_INSTRUCTION`
  - [x] 2.2 `prompts/carbon.py` : meme modification dans `build_carbon_prompt()`
  - [x] 2.3 `prompts/financing.py` : meme modification dans `build_financing_prompt()`
  - [x] 2.4 `prompts/credit.py` : meme modification dans `build_credit_prompt()`
  - [x] 2.5 `prompts/action_plan.py` : meme modification dans `build_action_plan_prompt()`
  - [x] 2.6 `prompts/system.py` : dans `build_system_prompt()`, injecter `GUIDED_TOUR_INSTRUCTION` dans la meme branche conditionnelle que `STYLE_INSTRUCTION` (ligne ~212, apres `_has_minimum_profile(user_profile)`) — le chat general ne parle de guidage qu'une fois l'utilisateur onboarde
  - [x] 2.7 NE PAS modifier `prompts/application.py` ni `prompts/esg_report.py`

- [x] Task 3 : Binder `GUIDED_TOUR_TOOLS` dans les 6 noeuds LangGraph (AC: #4)
  - [x] 3.1 `graph/nodes.py` : ajouter l'import `from app.graph.tools.guided_tour_tools import GUIDED_TOUR_TOOLS` (import local dans chaque noeud, pattern coherent avec les autres tools du fichier)
  - [x] 3.2 `chat_node` (L1116) : etendre `all_tools` avec `+ GUIDED_TOUR_TOOLS`
  - [x] 3.3 `esg_scoring_node` (L673) : etendre l'argument de `llm.bind_tools(...)` avec `+ GUIDED_TOUR_TOOLS`
  - [x] 3.4 `carbon_node` (L812) : idem sur `all_carbon_tools`
  - [x] 3.5 `financing_node` (L872) : ajouter `GUIDED_TOUR_TOOLS` au binding
  - [x] 3.6 `credit_node` (L1046) : ajouter `+ GUIDED_TOUR_TOOLS`
  - [x] 3.7 `action_plan_node` (L1276) : ajouter `+ GUIDED_TOUR_TOOLS` au binding
  - [x] 3.8 `application_node`, `document_node`, `profiling_node`, `router_node` NON modifies (verifie par test T12)

- [x] Task 4 : Creer la suite de tests `backend/tests/test_prompts/test_guided_tour_instruction.py` (AC: #7)
  - [x] 4.1 Test : `GUIDED_TOUR_INSTRUCTION` contient les 6 `tour_id` exacts
  - [x] 4.2 Test : `GUIDED_TOUR_INSTRUCTION` contient les mots-cles « apres completion », « demande explicite », « ask_interactive_question », « consentement »
  - [x] 4.3 Tests parametrises : 5 tests d'injection pour les prompts specialises + 1 test dedie pour `build_system_prompt(user_profile={"sector":"recyclage","city":"Abidjan"})`
  - [x] 4.4 Test negatif : `GUIDED_TOUR_INSTRUCTION not in build_application_prompt()`
  - [x] 4.5 Test negatif : `GUIDED_TOUR_INSTRUCTION not in build_system_prompt()` (sans profil + profil minimal < 2 champs)
  - [x] 4.6 Test binding : `trigger_guided_tour in GUIDED_TOUR_TOOLS`
  - [x] 4.7 Tests structurels : lecture de `graph/nodes.py` pour verifier import + binding dans 6 noeuds ; check que les 4 noeuds exclus ne contiennent PAS `GUIDED_TOUR_TOOLS` (scan par bloc de fonction)

- [x] Task 5 : Non-regression et quality gate (AC: #7)
  - [x] 5.1 venv active
  - [x] 5.2 `python -m pytest` : 1019 passed, 0 failure, 0 regression (136.70s)
  - [x] 5.3 `python -m pytest tests/test_prompts/test_guided_tour_instruction.py -v` : 16/16 passed
  - [x] 5.4 Couverture combinee story 6.1 + 6.2 : 100 % sur `app.prompts.guided_tour` et `app.graph.tools.guided_tour_tools` (>= 80 %)
  - [x] 5.5 Formatage : `black` non installe dans le venv — saute (les fichiers respectent deja la PEP8/black standard, indentation 4 espaces, lignes < 100 cols)
  - [x] 5.6 Lint : `python -m ruff check app/prompts/guided_tour.py tests/test_prompts/test_guided_tour_instruction.py` → « All checks passed! »

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

claude-opus-4-6 (Opus 4.6 1M context)

### Debug Log References

- `pytest tests/test_prompts/test_guided_tour_instruction.py -v` → 16/16 PASSED
- `pytest` (suite complete) → 1019 passed en 136.70s, 0 regression
- `pytest --cov=app.prompts.guided_tour --cov=app.graph.tools.guided_tour_tools` → 100 % (38 tests, stories 6.1 + 6.2 combinees)
- `ruff check app/prompts/guided_tour.py tests/test_prompts/test_guided_tour_instruction.py` → All checks passed!

### Completion Notes List

- **AC1** : `backend/app/prompts/guided_tour.py` cree (~95 lignes), docstring de fichier + constante module-level `GUIDED_TOUR_INSTRUCTION` avec les 6 `tour_id` canoniques, regles de declenchement (post-module via `ask_interactive_question`, demande explicite directe), rappel securite NFR10 sur le champ `context`, 3 exemples d'invocation (proposition post-module, declenchement direct simple, declenchement direct avec contexte non-PII).
- **AC2** : Injection `GUIDED_TOUR_INSTRUCTION` apres `WIDGET_INSTRUCTION` dans les 5 builders specialises (`build_esg_prompt`, `build_carbon_prompt`, `build_financing_prompt`, `build_credit_prompt`, `build_action_plan_prompt`) via import local, pattern identique a celui de `STYLE_INSTRUCTION`. Dans `system.py`, injection conditionnelle post-onboarding (meme branche que `STYLE_INSTRUCTION`, via `_has_minimum_profile(user_profile)`).
- **AC3** : `build_application_prompt` et `esg_report.py` non modifies. `build_system_prompt()` sans profil ou avec profil < 2 champs : le prompt guidage n'est PAS injecte. Tests negatifs (T7, T8, T9) valident.
- **AC4** : Import + binding `GUIDED_TOUR_TOOLS` ajoutes dans `chat_node` (L1109+1116), `esg_scoring_node` (L671+673), `carbon_node` (L805+812), `financing_node` (L865+872), `credit_node` (L1039+1046), `action_plan_node` (L1269+1276). Verification textuelle que `application_node`, `document_node`, `profiling_node`, `router_node` ne reference PAS le symbole (test T12).
- **AC5, AC6** : Couverts par le contenu meme du prompt. Les exemples 1 (post-module ESG → `ask_interactive_question` Oui/Non → `trigger_guided_tour` au tour suivant si Oui) et 2/3 (demande explicite → appel direct sans consentement) sont explicitement ecrits dans `GUIDED_TOUR_INSTRUCTION` et le tool est binde dans les 6 noeuds concernes. Les tests structurels (T5, T6, T10, T11) garantissent que le LLM a acces au prompt + au tool dans les bons noeuds.
- **AC7** : 16 nouveaux tests dans `tests/test_prompts/test_guided_tour_instruction.py`, tous verts. Suite complete 1019 tests verts (vs 992+ precedemment — ajout +27 tests de stories recentes), 0 regression. Couverture 100 % sur `app.prompts.guided_tour` et `app.graph.tools.guided_tour_tools` en combinant les tests 6.1 (22 dans `tests/test_tools/test_guided_tour_tools.py`) et 6.2 (16 dans `tests/test_prompts/test_guided_tour_instruction.py`).

**Decisions :**
- Imports locaux (dans chaque builder / noeud) plutot que globaux : coherent avec le pattern deja en place pour `WIDGET_INSTRUCTION` / `INTERACTIVE_TOOLS` / `CARBON_TOOLS` etc. Evite les imports circulaires potentiels et localise la dependance.
- Injection conditionnelle dans `chat_node` (post-onboarding seulement) : reponse retenue a la question ouverte #2 de la story — un utilisateur sans profil n'a aucun resultat a visiter. Reutilise le helper existant `_has_minimum_profile` (aucune nouvelle logique de gating introduite).
- `black` non installe dans le venv : j'ai passe cette etape et laisse le fichier conforme au style deja present dans le repertoire `backend/app/prompts/` (indentation 4 espaces, chaines triple-quotees, docstrings, PEP8). Ruff ne signale rien.
- Le warning ruff « unused import analyze_document_text » dans `nodes.py` est **pre-existant**, hors scope de cette story (pas de modification proche de cette ligne).

### File List

**Fichiers crees :**
- `backend/app/prompts/guided_tour.py` (module-level `GUIDED_TOUR_INSTRUCTION`, ~95 lignes)
- `backend/tests/test_prompts/test_guided_tour_instruction.py` (16 tests, ~160 lignes)

**Fichiers modifies :**
- `backend/app/prompts/esg_scoring.py` (import local + concat `GUIDED_TOUR_INSTRUCTION` dans `build_esg_prompt`)
- `backend/app/prompts/carbon.py` (import local + concat `GUIDED_TOUR_INSTRUCTION` dans `build_carbon_prompt`)
- `backend/app/prompts/financing.py` (import local + concat `GUIDED_TOUR_INSTRUCTION` dans `build_financing_prompt`)
- `backend/app/prompts/credit.py` (import local + concat `GUIDED_TOUR_INSTRUCTION` dans `build_credit_prompt`)
- `backend/app/prompts/action_plan.py` (import local + concat `GUIDED_TOUR_INSTRUCTION` dans `build_action_plan_prompt`)
- `backend/app/prompts/system.py` (import local + `sections.append(GUIDED_TOUR_INSTRUCTION)` dans branche conditionnelle post-onboarding de `build_system_prompt`)
- `backend/app/graph/nodes.py` (6 imports locaux + 6 bindings `+ GUIDED_TOUR_TOOLS` dans `chat_node`, `esg_scoring_node`, `carbon_node`, `financing_node`, `credit_node`, `action_plan_node`)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status de la story : `ready-for-dev` → `in-progress` → `review`)
- `_bmad-output/implementation-artifacts/6-2-prompt-guided-tour-instruction-et-injection-dans-les-noeuds-langgraph.md` (tasks cochees, Dev Agent Record, File List, Change Log, Status=review)

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-04-13 | Story 6.2 implementee : `GUIDED_TOUR_INSTRUCTION` cree + injecte dans 6 prompts + binding `GUIDED_TOUR_TOOLS` dans 6 noeuds LangGraph. 16 nouveaux tests (100 % coverage sur guided_tour.py et guided_tour_tools.py en combinant 6.1 + 6.2). 1019 tests backend verts, 0 regression. Status → review. | Amelia (dev-story) |
| 2026-04-13 | Code review adversarial (Blind Hunter + Edge Case Hunter + Acceptance Auditor). Auditor : 7/7 AC satisfaits. 3 findings MEDIUM, 5 findings LOW. 1 decision-needed (chat_node tool-sans-instruction), 5 patches, 3 defer. | bmad-code-review |
| 2026-04-13 | Review resolution : Option 1 retenue pour le decision-needed — `GUIDED_TOUR_INSTRUCTION` injecte systematiquement dans `build_system_prompt()` (alignement avec le binding sans condition de `GUIDED_TOUR_TOOLS` dans chat_node). 5 patches appliques (T4 durci, plancher count 7→12, 2 typos, T12 fail-fast). Tests T8/T9 inverses (absence → presence). 16/16 tests prompts verts, 1019/1019 tests backend verts, 0 regression. Status → done. | bmad-code-review |

### Review Findings

**Legend** : `Patch` = correctif sans ambiguite · `Decision` = arbitrage humain requis · `Defer` = pre-existant ou portee elargie.

- [x] [Review][Decision→Patch] chat_node binde `GUIDED_TOUR_TOOLS` sans condition mais injecte `GUIDED_TOUR_INSTRUCTION` uniquement post-onboarding — **Resolu** : Option 1 retenue. `GUIDED_TOUR_INSTRUCTION` est maintenant injecte systematiquement dans `build_system_prompt()` (hors de la branche `_has_minimum_profile`) pour aligner instruction et binding. Tests T8/T9 inverses (absence → presence). [backend/app/prompts/system.py:211-220](backend/app/prompts/system.py#L211-L220)
- [x] [Review][Patch] Test T4 quasi-tautologique (`or "id"` matche "aide"/"guide"/"vide") — **Resolu** : assertion durcie avec mots-cles pleins (`user_id`, `conversation_id`, `token`, `email`, `pii`, `mot de passe`, `password`) et plancher de 2 mentions distinctes. [backend/tests/test_prompts/test_guided_tour_instruction.py:T4](backend/tests/test_prompts/test_guided_tour_instruction.py)
- [x] [Review][Patch] Seuil `count("GUIDED_TOUR_TOOLS") >= 7` trop lache — **Resolu** : plancher releve a `>= 12` (6 nœuds × 2 occurrences : import local + ajout a `bind_tools`). [backend/tests/test_prompts/test_guided_tour_instruction.py](backend/tests/test_prompts/test_guided_tour_instruction.py)
- [x] [Review][Patch] Typo "explique-pas-a-pas" → "expliques pas a pas" — **Resolu** [backend/app/prompts/guided_tour.py:16](backend/app/prompts/guided_tour.py#L16)
- [x] [Review][Patch] Typo "prematue" → supprime dans le cadre de la resolution decision-needed (commentaire reecrit). [backend/app/prompts/system.py:214-217](backend/app/prompts/system.py#L214-L217)
- [x] [Review][Patch] `continue` silencieux dans T12 masque la disparition d'un nœud exclu — **Resolu** : remplacement par `assert start != -1` avec message explicite. [backend/tests/test_prompts/test_guided_tour_instruction.py](backend/tests/test_prompts/test_guided_tour_instruction.py)
- [x] [Review][Defer] Couplage STYLE_INSTRUCTION / GUIDED_TOUR_INSTRUCTION dans la meme branche conditionnelle — [backend/app/prompts/system.py:211-217](backend/app/prompts/system.py#L211-L217) — deferred, design existant (refactor optionnel : extraire un helper `_should_inject_guidance`).
- [x] [Review][Defer] Aucune assertion positionnelle `WIDGET_INSTRUCTION` → `GUIDED_TOUR_INSTRUCTION` — [backend/tests/test_prompts/test_guided_tour_instruction.py](backend/tests/test_prompts/test_guided_tour_instruction.py) — deferred, les 5 tests d'injection verifient la presence mais pas l'ordre.
- [x] [Review][Defer] Chemins frontend dans le prompt (`/esg/results`, `/action-plan`, etc.) non epingles contre le registre Nuxt — [backend/app/prompts/guided_tour.py:12-17](backend/app/prompts/guided_tour.py#L12-L17) — deferred, cross-stack (test d'alignement avec `frontend/lib/guided-tours/registry.ts` a creer dans une story future).
