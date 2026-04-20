# Story 3.2 : Injection de la page courante dans les prompts et adaptation des reponses

Status: done

## Story

En tant qu'utilisateur,
je veux que l'assistant adapte ses reponses en fonction de la page que je consulte,
afin de recevoir des conseils pertinents et contextuels.

## Acceptance Criteria

1. **AC1 — Injection dans le prompt du chat_node**
   - **Given** `current_page` est `'/carbon/results'` dans `ConversationState`
   - **When** le LLM genere une reponse via `chat_node`
   - **Then** le prompt systeme contient l'information de la page courante
   - **And** le LLM peut adapter son discours (ex: "Je vois que vous consultez vos resultats carbone...")

2. **AC2 — Proposition de guidage contextuel (FR13)**
   - **Given** `current_page` est `'/dashboard'` et l'utilisateur vient de completer un module ESG
   - **When** le LLM genere une reponse
   - **Then** il peut proposer un guidage vers les resultats ESG (proposition textuelle uniquement — le declenchement technique est dans l'Epic 6)

3. **AC3 — Degradation gracieuse**
   - **Given** `current_page` est `None` ou vide (premier message, erreur, endpoint JSON)
   - **When** le LLM genere une reponse
   - **Then** il repond normalement sans contexte de page — aucune erreur, aucune mention de page

4. **AC4 — Coexistence avec active_module (NFR22)**
   - **Given** le mecanisme `active_module` est actif (ex: `esg_scoring` en cours)
   - **When** `current_page` change parce que l'utilisateur navigue
   - **Then** `active_module` n'est pas affecte — le routage LangGraph continue de suivre `active_module`

5. **AC5 — Injection dans les noeuds specialistes**
   - **Given** `current_page` est disponible dans `ConversationState`
   - **When** un noeud specialiste (esg_scoring, carbon, financing, application, credit, action_plan) genere une reponse
   - **Then** le prompt systeme du noeud contient l'information de la page courante
   - **And** le noeud peut adapter ses reponses en consequence

6. **AC6 — Zero regression (NFR19)**
   - **Given** les modifications des prompts sont terminees
   - **When** on execute les tests backend + frontend
   - **Then** zero regression sur les tests existants (950+ backend, 176+ frontend)
   - **And** couverture >= 80% sur les fichiers modifies

## Tasks / Subtasks

- [x] **Task 1 : Creer PAGE_CONTEXT_INSTRUCTION dans les prompts** (AC: 1, 3, 5)
  - [x] 1.1 Creer une fonction `build_page_context_instruction(current_page: str | None) -> str` dans `backend/app/prompts/system.py`
  - [x] 1.2 Si `current_page` est `None` ou vide → retourner une chaine vide (degradation gracieuse AC3)
  - [x] 1.3 Si `current_page` est renseignee → retourner un bloc d'instruction PAGE_CONTEXT_INSTRUCTION contenant :
    - La page courante de l'utilisateur
    - Un mapping lisible page → description contextuelle (voir Dev Notes)
    - Des consignes pour le LLM : adapter le discours, eviter de repeter la page, etre naturel
  - [x] 1.4 Inclure la directive FR13 : quand l'utilisateur est sur `/dashboard` ou une page de resultats et qu'un module est termine, proposer textuellement de montrer les resultats (pas de declenchement technique — Epic 6)

- [x] **Task 2 : Injecter dans build_system_prompt (chat_node)** (AC: 1, 3)
  - [x] 2.1 Ajouter le parametre `current_page: str | None = None` a la signature de `build_system_prompt()` dans `backend/app/prompts/system.py`
  - [x] 2.2 Appeler `build_page_context_instruction(current_page)` et l'ajouter a `sections[]` (apres STYLE_INSTRUCTION, avant le return)
  - [x] 2.3 Dans `nodes.py` (`chat_node`, ~ligne 1117), passer `current_page=state.get("current_page")` a `build_system_prompt()`

- [x] **Task 3 : Injecter dans les 6 fonctions build_*_prompt des modules specialistes** (AC: 5, 3)
  - [x] 3.1 Ajouter le parametre `current_page: str | None = None` aux 6 fonctions :
    - `build_esg_prompt()` dans `backend/app/prompts/esg_scoring.py`
    - `build_carbon_prompt()` dans `backend/app/prompts/carbon.py`
    - `build_financing_prompt()` dans `backend/app/prompts/financing.py`
    - `build_application_prompt()` dans `backend/app/prompts/application.py`
    - `build_credit_prompt()` dans `backend/app/prompts/credit.py`
    - `build_action_plan_prompt()` dans `backend/app/prompts/action_plan.py`
  - [x] 3.2 Dans chaque fonction `build_*_prompt`, appeler `build_page_context_instruction(current_page)` et concatener au prompt retourne (apres WIDGET_INSTRUCTION)
  - [x] 3.3 Dans `nodes.py`, pour chaque noeud specialiste, passer `current_page=state.get("current_page")` a l'appel `build_*_prompt()` correspondant :
    - `esg_scoring_node` (~ligne 630)
    - `carbon_node` (~ligne 781)
    - `financing_node` (~ligne 894)
    - `application_node` (~ligne 1224)
    - `credit_node` (~ligne 1058)
    - `action_plan_node` (~ligne 1346)

- [x] **Task 4 : Tests unitaires — fonction PAGE_CONTEXT_INSTRUCTION** (AC: 1, 3, 6)
  - [x] 4.1 Creer `backend/tests/test_prompts/test_page_context.py`
  - [x] 4.2 Test : `build_page_context_instruction(None)` retourne `""`
  - [x] 4.3 Test : `build_page_context_instruction("")` retourne `""`
  - [x] 4.4 Test : `build_page_context_instruction("/carbon/results")` retourne un string non-vide contenant `/carbon/results`
  - [x] 4.5 Test : `build_page_context_instruction("/dashboard")` contient la mention de proposition de guidage (FR13)
  - [x] 4.6 Test : `build_page_context_instruction("/unknown-page")` retourne un string non-vide avec un contexte generique

- [x] **Task 5 : Tests unitaires — integration dans les prompts** (AC: 1, 5, 6)
  - [x] 5.1 Test : `build_system_prompt(current_page="/esg")` contient le contexte de page dans le prompt retourne
  - [x] 5.2 Test : `build_system_prompt(current_page=None)` ne contient PAS de bloc PAGE_CONTEXT
  - [x] 5.3 Test pour chaque `build_*_prompt(current_page="/dashboard")` : le prompt retourne contient le contexte de page
  - [x] 5.4 Test pour chaque `build_*_prompt(current_page=None)` : le prompt retourne ne contient pas de bloc PAGE_CONTEXT
  - [x] 5.5 Tests crees dans `backend/tests/test_prompts/test_page_context.py`

- [x] **Task 6 : Tests unitaires — noeuds LangGraph** (AC: 1, 5, 6)
  - [x] 6.1 Tests dans `backend/tests/test_graph/test_current_page.py` verifiant que `chat_node` passe `current_page` a `build_system_prompt`
  - [x] 6.2 Test verifiant que `esg_scoring_node` passe `current_page` a `build_esg_prompt`
  - [x] 6.3 Pattern de test direct (appel des fonctions build_*_prompt avec current_page)

- [x] **Task 7 : Verification finale**
  - [x] 7.1 `python -m pytest` — 979 tests passes, zero echec
  - [x] 7.2 `npx vitest run` — 176 tests passes, zero echec
  - [x] 7.3 Grep : `build_page_context_instruction` present dans system.py + 6 fichiers prompts modules (7 fichiers)
  - [x] 7.4 Grep : `current_page=state.get("current_page")` dans les 7 appels build_*_prompt dans nodes.py

## Dev Notes

### Portee de cette story

Cette story couvre FR12 et FR13 (adaptation des reponses et proposition textuelle de guidage). Elle est STRICTEMENT backend — aucune modification frontend. Le declenchement technique du guidage (tool `trigger_guided_tour`, marker SSE) est dans l'Epic 6.

### Pattern d'injection existant a suivre

Les prompts utilisent un pattern de couches concatenees. Voici l'ordre actuel pour `chat_node` :

```
BASE_PROMPT → Profile → Memory → Document → Profiling → Profile Visual → STYLE_INSTRUCTION → Tool Instructions → WIDGET_INSTRUCTION
```

PAGE_CONTEXT_INSTRUCTION doit s'inserer **apres STYLE_INSTRUCTION** dans `build_system_prompt()` et **apres WIDGET_INSTRUCTION** dans les `build_*_prompt()` des modules specialistes.

### Pattern de la fonction build_page_context_instruction

Suivre le meme pattern que `STYLE_INSTRUCTION` (constante conditionnelle) :

```python
# backend/app/prompts/system.py

# Mapping page → description contextuelle lisible par le LLM
PAGE_DESCRIPTIONS: dict[str, str] = {
    "/dashboard": "le tableau de bord principal avec les cartes de synthese ESG, carbone, credit et financement",
    "/esg": "la page d'evaluation ESG",
    "/esg/results": "la page des resultats detailles de l'evaluation ESG (score, piliers, recommandations)",
    "/carbon": "la page du calculateur d'empreinte carbone",
    "/carbon/results": "la page des resultats du bilan carbone (repartition, benchmark, plan de reduction)",
    "/financing": "le catalogue des fonds de financement vert",
    "/credit-score": "la page du score de credit vert alternatif",
    "/action-plan": "la page du plan d'action avec la timeline des actions recommandees",
    "/reports": "la page de generation des rapports PDF",
}

def build_page_context_instruction(current_page: str | None) -> str:
    """Generer l'instruction de contexte de page pour le LLM."""
    if not current_page:
        return ""
    
    page_desc = PAGE_DESCRIPTIONS.get(current_page)
    if page_desc:
        context_line = f"L'utilisateur consulte actuellement {page_desc} ({current_page})."
    else:
        context_line = f"L'utilisateur est actuellement sur la page {current_page}."
    
    instruction = (
        f"CONTEXTE DE NAVIGATION :\n"
        f"{context_line}\n"
        f"Adapte tes reponses a ce contexte : si l'utilisateur pose une question en lien avec cette page, "
        f"reponds en tenant compte de ce qu'il voit. Ne repete pas systematiquement le nom de la page.\n"
    )
    
    # FR13 : proposition de guidage sur les pages de resultats et le dashboard
    if current_page in ("/dashboard", "/esg/results", "/carbon/results", "/action-plan"):
        instruction += (
            "Si l'utilisateur vient de terminer un module ou si des resultats sont disponibles, "
            "tu peux lui proposer de l'accompagner vers les resultats ou les prochaines etapes "
            "(proposition textuelle uniquement).\n"
        )
    
    return instruction
```

### Modification de build_system_prompt

```python
def build_system_prompt(
    user_profile: dict | None = None,
    context_memory: list[str] | None = None,
    profiling_instructions: str | None = None,
    document_analysis_summary: str | None = None,
    current_page: str | None = None,  # NOUVEAU
) -> str:
    sections: list[str] = [BASE_PROMPT]
    # ... sections existantes inchangees ...
    
    if user_profile and _has_minimum_profile(user_profile):
        sections.append(STYLE_INSTRUCTION)
    
    # NOUVEAU — apres STYLE_INSTRUCTION
    page_context = build_page_context_instruction(current_page)
    if page_context:
        sections.append(page_context)
    
    return "\n\n".join(sections)
```

### Modification des build_*_prompt des modules

Chaque fonction `build_*_prompt` dans les fichiers prompts retourne une concatenation. Ajouter le parametre `current_page` et concatener le resultat de `build_page_context_instruction()` a la fin :

```python
# Exemple pour build_esg_prompt dans esg_scoring.py
def build_esg_prompt(
    company_context: str = "Aucun profil disponible.",
    document_context: str = "Aucun document disponible.",
    current_page: str | None = None,  # NOUVEAU
) -> str:
    from app.prompts.system import STYLE_INSTRUCTION, build_page_context_instruction
    from app.prompts.widget import WIDGET_INSTRUCTION
    
    prompt = (
        ESG_SCORING_PROMPT.format(
            company_context=company_context,
            document_context=document_context,
        )
        + "\n\n" + STYLE_INSTRUCTION
        + "\n\n" + WIDGET_INSTRUCTION
    )
    
    # NOUVEAU
    page_context = build_page_context_instruction(current_page)
    if page_context:
        prompt += "\n\n" + page_context
    
    return prompt
```

### Passage dans nodes.py

Pour chaque noeud, ajouter `current_page=state.get("current_page")` a l'appel de la fonction build correspondante. Exemple :

```python
# chat_node (~ligne 1095)
system_prompt = build_system_prompt(
    user_profile,
    context_memory,
    profiling_instructions,
    document_analysis_summary=document_summary,
    current_page=state.get("current_page"),  # NOUVEAU
)

# esg_scoring_node (~ligne 595)
system_prompt = build_esg_prompt(
    company_context=company_context,
    document_context=doc_context,
    current_page=state.get("current_page"),  # NOUVEAU
)
```

### Fichiers a modifier

| Fichier | Action | Detail |
|---------|--------|--------|
| `backend/app/prompts/system.py` | Modifier | Ajouter `PAGE_DESCRIPTIONS`, `build_page_context_instruction()`, parametre `current_page` a `build_system_prompt()` |
| `backend/app/prompts/esg_scoring.py` | Modifier | Parametre `current_page` a `build_esg_prompt()`, appel `build_page_context_instruction()` |
| `backend/app/prompts/carbon.py` | Modifier | Idem pour `build_carbon_prompt()` |
| `backend/app/prompts/financing.py` | Modifier | Idem pour `build_financing_prompt()` |
| `backend/app/prompts/application.py` | Modifier | Idem pour `build_application_prompt()` |
| `backend/app/prompts/credit.py` | Modifier | Idem pour `build_credit_prompt()` |
| `backend/app/prompts/action_plan.py` | Modifier | Idem pour `build_action_plan_prompt()` |
| `backend/app/graph/nodes.py` | Modifier | Passer `current_page=state.get("current_page")` dans 7 appels build_*_prompt |
| `backend/tests/test_prompts/test_page_context.py` | Nouveau | Tests pour `build_page_context_instruction()` |

### Fichiers a NE PAS modifier

- `backend/app/graph/state.py` — `current_page` est deja dans `ConversationState` (Story 3.1)
- `backend/app/api/chat.py` — La transmission est deja en place (Story 3.1)
- `frontend/**` — Aucune modification frontend dans cette story
- `backend/app/graph/prompts/widget.py` — Le WIDGET_INSTRUCTION reste inchange
- `backend/app/graph/tools/` — Pas de nouveau tool (le tool `trigger_guided_tour` est Epic 6)

### Coexistence current_page / active_module (AC4, NFR22)

- `active_module` : controle le routage LangGraph (quel noeud traite le message). DECISIF.
- `current_page` : information contextuelle injectee dans les prompts. INFORMATIF.
- `build_page_context_instruction()` ne modifie AUCUN comportement de routage — elle genere uniquement du texte pour le prompt systeme.
- Le `router_node` ne lit pas `current_page` et ne doit pas etre modifie.

### Intelligence de la story precedente (3.1)

**Learnings cles :**
- `current_page` est de type `str | None` dans `ConversationState` (ligne 36 de state.py)
- La sanitisation (strip + truncate 200 chars) est deja dans `send_message` (lignes 635-638 de chat.py)
- `state.get("current_page")` retourne `None` si non fourni — la degradation gracieuse (AC3) est naturelle
- Les auto-imports Python fonctionnent normalement — `from app.prompts.system import build_page_context_instruction` dans les fichiers prompts modules
- Review finding differe : pas d'annotation reducer pour `current_page` — le champ n'est pas modifie par les noeuds, uniquement lu, donc pas de probleme
- 950 tests backend verts, 176 tests frontend verts au moment du commit 3.1

### Pattern de test existant pour les prompts

Verifier dans `backend/tests/test_prompts/` si des fichiers de test existent deja. Sinon, creer `test_page_context.py` avec le pattern pytest standard :

```python
import pytest
from app.prompts.system import build_page_context_instruction, build_system_prompt

class TestBuildPageContextInstruction:
    def test_none_returns_empty(self):
        assert build_page_context_instruction(None) == ""
    
    def test_empty_string_returns_empty(self):
        assert build_page_context_instruction("") == ""
    
    def test_known_page_includes_description(self):
        result = build_page_context_instruction("/carbon/results")
        assert "/carbon/results" in result
        assert "CONTEXTE DE NAVIGATION" in result
    
    def test_dashboard_includes_guidance_suggestion(self):
        result = build_page_context_instruction("/dashboard")
        assert "proposer" in result.lower() or "accompagner" in result.lower()
    
    def test_unknown_page_returns_generic_context(self):
        result = build_page_context_instruction("/unknown-page")
        assert "/unknown-page" in result
        assert "CONTEXTE DE NAVIGATION" in result
```

### Commits recents

```
c489a6c 2-2-mise-a-jour-de-la-navigation-et-des-liens-internes: done
b7314e2 2-1-suppression-de-la-page-chat-et-de-chatpanel: done
39bbb14 1-6 + 1-7: done
e27120c 1-3 + 1-4 + 1-5: done
2785a59 1-1 + 1-2: done
```

### Project Structure Notes

- Backend prompts : `backend/app/prompts/` (system.py, esg_scoring.py, carbon.py, financing.py, application.py, credit.py, action_plan.py, widget.py)
- Noeuds LangGraph : `backend/app/graph/nodes.py` (fichier unique, ~1400 lignes)
- Tests backend : `backend/tests/` (pytest + pytest-asyncio)
- `ConversationState` est un `TypedDict` dans `backend/app/graph/state.py`
- Convention : textes en francais avec accents dans les prompts et messages utilisateur

### References

- [Source: _bmad-output/planning-artifacts/epics-019-floating-copilot.md — Epic 3, Story 3.2, lignes 552-582]
- [Source: _bmad-output/planning-artifacts/prd.md — FR11, FR12, FR13, NFR19, NFR22]
- [Source: _bmad-output/planning-artifacts/architecture-019-floating-copilot.md — Conscience contextuelle lignes 719-732, regles enforcement lignes 759-768]
- [Source: _bmad-output/implementation-artifacts/3-1-transmission-de-la-page-courante-au-backend.md — Dev Notes, Review Findings, Completion Notes]
- [Source: backend/app/prompts/system.py — build_system_prompt(), STYLE_INSTRUCTION, BASE_PROMPT]
- [Source: backend/app/graph/nodes.py — chat_node (~1092), esg_scoring_node (~554), carbon_node (~706), financing_node (~853), application_node (~1187), credit_node (~1026), action_plan_node (~1247)]
- [Source: backend/app/graph/state.py — ConversationState, current_page ligne 36]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

Aucun debug necessaire — implementation directe sans erreur.

### Completion Notes List

- PAGE_DESCRIPTIONS : mapping de 9 pages connues avec descriptions contextuelles en francais
- build_page_context_instruction() : fonction pure retournant "" si current_page est None/vide, sinon un bloc CONTEXTE DE NAVIGATION avec description contextuelle et consignes LLM
- FR13 : proposition textuelle de guidage sur /dashboard, /esg/results, /carbon/results, /action-plan
- Parametre current_page ajoute a build_system_prompt + 6 build_*_prompt (esg, carbon, financing, application, credit, action_plan)
- 7 appels dans nodes.py modifies pour passer state.get("current_page")
- 29 nouveaux tests (26 dans test_page_context.py + 3 dans test_current_page.py)
- 979 tests backend passes, 176 tests frontend passes, zero regression

### Review Findings

- [x] [Review][Defer] Vérifier le comportement du checkpointer LangGraph pour `current_page` — risque d'écrasement entre tours si `MemorySaver` fusionne l'état checkpointé avec le nouvel `initial_state`. Aucun nœud ne retourne `current_page` dans son `return {}`. Risque quasi nul car `current_page` est toujours re-injecté dans `initial_state` et est read-only. [backend/app/graph/nodes.py] — deferred, risque faible
- [x] [Review][Patch] Prompt injection via `current_page` inconnu — whitelist stricte appliquée : `build_page_context_instruction()` retourne `""` si page absente de `PAGE_DESCRIPTIONS`. [backend/app/prompts/system.py:139-140]
- [x] [Review][Patch] Ordre `PAGE_CONTEXT`/`WIDGET_INSTRUCTION` corrigé dans `chat_node` — `PAGE_CONTEXT` déplacé de `build_system_prompt()` vers `chat_node` après `WIDGET_INSTRUCTION`. [backend/app/graph/nodes.py:1140-1145]
- [x] [Review][Defer] `send_message_json` passe toujours `current_page=None` — endpoint de compatibilité, pas utilisé par le frontend actuel. [backend/app/api/chat.py:938] — deferred, pré-existant
- [x] [Review][Defer] Routes dynamiques (`/financing/123`) tombent sur la branche générique du prompt — nécessite un design de prefix matching. [backend/app/prompts/system.py:138] — deferred, hors scope story 3.2
- [x] [Review][Defer] Valeur initiale `"/"` envoyée au backend comme page inconnue — scope story 3.1 (frontend). [frontend/app/stores/ui.ts:17] — deferred, scope story 3.1
- [x] [Review][Defer] Tests ne couvrent pas le chemin complet nœud → prompt pour 5 des 6 spécialistes — couverture via tests prompts directs. [backend/tests/test_graph/test_current_page.py] — deferred, couverture indirecte suffisante

### Change Log

- 2026-04-13 : Implementation complete Story 3.2 — injection page courante dans prompts (FR12, FR13)

### File List

- backend/app/prompts/system.py (modifie — PAGE_DESCRIPTIONS, build_page_context_instruction, parametre current_page dans build_system_prompt)
- backend/app/prompts/esg_scoring.py (modifie — parametre current_page dans build_esg_prompt)
- backend/app/prompts/carbon.py (modifie — parametre current_page dans build_carbon_prompt)
- backend/app/prompts/financing.py (modifie — parametre current_page dans build_financing_prompt)
- backend/app/prompts/application.py (modifie — parametre current_page dans build_application_prompt)
- backend/app/prompts/credit.py (modifie — parametre current_page dans build_credit_prompt)
- backend/app/prompts/action_plan.py (modifie — parametre current_page dans build_action_plan_prompt)
- backend/app/graph/nodes.py (modifie — current_page=state.get("current_page") dans 7 appels build_*_prompt)
- backend/tests/test_prompts/test_page_context.py (nouveau — 26 tests)
- backend/tests/test_graph/test_current_page.py (modifie — 3 nouveaux tests classe TestNodesPassCurrentPageToPrompts)
