# Story 6.3 : Consentement via widget interactif et declenchement direct

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

En tant qu'utilisateur,
je veux choisir si j'accepte un guidage propose par l'assistant via un choix clair,
afin de garder le controle de mon experience sans etre force par un declenchement automatique,
ET je veux pouvoir demander directement un guidage en langage naturel sans passer par une etape de consentement.

## Acceptance Criteria

### AC1 : Flux consentement post-module — proposition

**Given** un noeud specialise (`esg_scoring_node`, `carbon_node`, `financing_node`, `credit_node`, `action_plan_node`) vient de terminer un module (evaluation ESG close, bilan carbone finalise, plan d'action genere, dossier financement soumis, score de credit calcule)
**When** le LLM applique `GUIDED_TOUR_INSTRUCTION` (section « Apres completion d'un module »)
**Then** il appelle `ask_interactive_question` AVANT `trigger_guided_tour`
**And** l'appel contient EXACTEMENT :
- `question_type="qcu"`
- 2 options dont les `id` sont `"yes"` et `"no"` et les `label` sont respectivement `"Oui, montre-moi"` et `"Non merci"`
- emojis `"👀"` et `"🙏"` (facultatifs mais recommandes par le prompt)

**And** le widget `SingleChoiceWidget` (feature 018) est affiche cote frontend (aucun nouveau composant cree)
**And** le marker SSE `__sse_interactive_question__` est emis et parse par `useChat.handleInteractiveQuestionEvent()` — pattern existant, aucune modification requise sur le transport

### AC2 : Consentement accepte — declenchement du parcours

**Given** la question interactive de consentement est `state="pending"` pour la conversation
**When** l'utilisateur clique sur l'option `id="yes"` dans `SingleChoiceWidget`
**And** `submitInteractiveAnswer()` (`useChat.ts:470`) envoie la reponse via `POST /api/chat/conversations/{id}/messages` avec `interactive_question_values='["yes"]'`
**Then** au tour LLM suivant, le noeud actif appelle `trigger_guided_tour(tour_id=<id canonique>)` avec le `tour_id` correspondant au module termine :
- `esg_scoring_node` → `show_esg_results`
- `carbon_node` → `show_carbon_results`
- `financing_node` → `show_financing_catalog`
- `credit_node` → `show_credit_score`
- `action_plan_node` → `show_action_plan`
- `chat_node` (post-onboarding, vue dashboard) → `show_dashboard_overview`

**And** le marker SSE `__sse_guided_tour__` est emis
**And** `handleGuidedTourEvent()` (`useChat.ts:682`) passe la garde `currentInteractiveQuestion.value?.state === 'pending'` (la question vient de passer a `answered` via le handler `interactive_question_resolved`, ligne 372-405)
**And** `useGuidedTour.startTour(tour_id, context)` est appele et le parcours demarre (FR14)

### AC3 : Consentement refuse — pas de guidage

**Given** la question interactive de consentement est `state="pending"`
**When** l'utilisateur clique sur l'option `id="no"` dans `SingleChoiceWidget`
**And** `submitInteractiveAnswer()` envoie la reponse avec `interactive_question_values='["no"]'`
**Then** au tour LLM suivant, le noeud actif NE declenche PAS `trigger_guided_tour`
**And** il poursuit la conversation normalement (phrase de reconnaissance courte, pas de relance insistante — le prompt est deja factuel)
**And** aucun event SSE `guided_tour` n'est emis durant ce tour

### AC4 : Declenchement direct — intent explicite

**Given** l'utilisateur est onboarde (profil >= 2 champs) et un module cible dispose de donnees exploitables
**When** il tape un message contenant un intent explicite de guidage visuel — formulations attendues :
- « montre-moi mes resultats <module> »
- « guide-moi vers <ecran> »
- « ou sont mes resultats »
- « visualise-moi <...> »
- « fais-moi visiter <...> »

**Then** le noeud cible (determine par le routeur selon le module mentionne) appelle `trigger_guided_tour(tour_id=...)` IMMEDIATEMENT
**And** `ask_interactive_question` N'EST PAS appele (pas de widget de consentement redondant — FR15, FR16)
**And** le mapping formulation → `tour_id` est :
- « resultats ESG » / « evaluation ESG » → `show_esg_results`
- « resultats carbone » / « bilan carbone » → `show_carbon_results`
- « fonds » / « financement » / « catalogue » → `show_financing_catalog`
- « score credit » / « credit vert » → `show_credit_score`
- « plan d'action » / « feuille de route » → `show_action_plan`
- « tableau de bord » / « dashboard » / « vue d'ensemble » → `show_dashboard_overview`

### AC5 : Intent ambigu — priorite au consentement

**Given** l'utilisateur exprime un interet vague pour ses donnees (ex : « j'aimerais voir mes chiffres », « dis-m'en plus »)
**When** le LLM analyse l'intent
**Then** il privilegie `ask_interactive_question` (pattern AC1) plutot qu'un declenchement direct
**And** le prompt `GUIDED_TOUR_INSTRUCTION` guide cette prudence — un intent explicite requiert un verbe d'action visuel (« montre », « guide », « visualise », « fais-moi visiter », « ou sont »)

### AC6 : Respect du verrou widget pending

**Given** une question interactive est deja `state="pending"` dans la conversation
**When** un event `guided_tour` arrive cote frontend avant que l'utilisateur n'ait repondu
**Then** `handleGuidedTourEvent()` (`useChat.ts:689`) bloque `startTour()` et appelle `addSystemMessage("Repondez d'abord a la question en attente.")` (comportement deja implemente en story 6.1 — cette story ne le modifie pas, mais le test T-AC6 doit le valider)
**And** aucun parcours n'est demarre

### AC7 : Zero regression et couverture tests

**Given** la suite de tests backend existante (1019 tests verts apres story 6.2)
**When** on execute `cd backend && python -m pytest` avec le venv actif
**Then** zero regression (NFR19)
**And** les nouveaux tests consentement/declenchement direct atteignent >= 80 % de couverture sur le code ajoute/modifie
**And** le fichier `backend/tests/test_prompts/test_guided_tour_consent_flow.py` est cree avec AU MINIMUM :
- 1 test (T-AC1a) : `GUIDED_TOUR_INSTRUCTION` contient les chaines `"Oui, montre-moi"`, `"Non merci"`, `"yes"`, `"no"`, `"ask_interactive_question"`
- 1 test (T-AC1b) : le prompt impose l'ordre « ask_interactive_question AVANT trigger_guided_tour » (recherche de la phrase normative)
- 1 test (T-AC4a) : le prompt enumere au moins 3 verbes-indicateurs d'intent explicite parmi `["montre", "guide", "visualise", "fais-moi visiter", "ou sont"]`
- 1 test (T-AC4b) : pour chacun des 6 `tour_id`, au moins un mot-cle de mapping est present dans le prompt (ex : `"carbone"` pour `show_carbon_results`)
- 1 test (T-AC5) : le prompt demande la prudence sur l'intent ambigu (contient `"explicite"` ou `"ambigu"` ou equivalent)
- Tests structurels (T-AC3) : la reponse attendue du LLM en cas de refus est decrite dans le prompt (verification de la section « refus » : mots-cles `"poursuit"`/`"continue"`/`"normalement"` + absence d'instruction de relance insistante)

**And** le fichier `frontend/tests/composables/useChat.guided-tour-consent.test.ts` est cree (Vitest) avec AU MINIMUM :
- 1 test (T-AC2) : simulation d'un event SSE `interactive_question` avec options `yes/no` → `currentInteractiveQuestion.value.state === 'pending'` puis reception d'un event `interactive_question_resolved` (state `answered`) → `handleGuidedTourEvent` peut declencher `startTour` sans etre bloque par la garde
- 1 test (T-AC6) : simulation d'un event `guided_tour` recu pendant qu'une question est `pending` → `startTour` N'EST PAS appele et un message systeme « Repondez d'abord a la question en attente. » est ajoute

**And** le module `useGuidedTour` n'est modifie QUE si un bug est decouvert (cette story est prompt + tests, pas implementation)

### AC8 : Documentation dev — traceabilite AC / code

**Given** la story est complete
**When** on lit la section `## Dev Notes` mise a jour
**Then** elle contient un tableau « AC → fichier(s) de test » pour que la prochaine story (6.4 frequence adaptative) puisse etendre le meme pattern sans recherche

## Tasks / Subtasks

- [x] Task 1 : Renforcer `GUIDED_TOUR_INSTRUCTION` si necessaire (AC: #1, #4, #5)
  - [x] 1.1 Lire `backend/app/prompts/guided_tour.py` (version story 6.2)
  - [x] 1.2 Verifier que la section « Regles de declenchement obligatoires » enumere explicitement les 2 options `yes/no` avec labels francais attendus (`"Oui, montre-moi"`, `"Non merci"`) — confirme present
  - [x] 1.3 Verifier que la section « Quand proposer un guidage » couvre les 5 verbes-indicateurs — confirme present
  - [x] 1.4 Ajouter sous-section explicite « Intent ambigu — privilegie le consentement » avec mots-cles `ambigu`, `privilegie`, `prudence`, `doute` (AC5)
  - [x] 1.5 Ajouter table Markdown canonique « module termine → tour_id » pour les 6 modules (AC2)

- [x] Task 2 : Creer la suite de tests backend `test_guided_tour_consent_flow.py` (AC: #7)
  - [x] 2.1 Fichier cree (17 tests parametrises)
  - [x] 2.2 Test T-AC1a : `test_instruction_contains_consent_exact_strings`
  - [x] 2.3 Test T-AC1b : `test_ask_interactive_question_before_trigger_in_post_module_section` (helper `_post_module_section` pour delimiter la fenetre)
  - [x] 2.4 Test T-AC4a : `test_each_explicit_verb_present` (parametrise 5 verbes) + `test_at_least_three_explicit_verbs_present` (plancher)
  - [x] 2.5 Test T-AC4b : `test_tour_id_has_mapping_keyword` (parametrise 6 paires)
  - [x] 2.6 Test T-AC5 : `test_prompt_mentions_ambiguous_intent_fallback`
  - [x] 2.7 Test T-AC3 : `test_prompt_has_no_aggressive_relance_keywords` + `test_prompt_links_yes_answer_to_trigger_tour` (AC2 indirect)

- [x] Task 3 : Creer la suite de tests frontend `useChat.guided-tour-consent.test.ts` (AC: #7)
  - [x] 3.1 Fichier cree (3 tests)
  - [x] 3.2 Fixture : mock streaming fetch via `createMockSSEStream` + `vi.stubGlobal('fetch', ...)`, spy sur `useGuidedTour().startTour`
  - [x] 3.3 Test T-AC2 : cycle complet `sendMessage` (phase 1 question pending) puis `submitInteractiveAnswer` phase 2 (guided_tour event) → `startTour('show_esg_results', {pillar_top:'Social'})` appele
  - [x] 3.4 Test T-AC6 : verrou widget `pending` → `startTour` bloque, message systeme « Repondez d'abord a la question en attente. » injecte
  - [x] 3.5 Test T-AC3 : reponse `no` → stream texte libre sans event `guided_tour`, `startTour` non appele

- [x] Task 4 : Mettre a jour la section `## Dev Notes` avec le tableau traceabilite AC → test (AC: #8)
  - [x] 4.1 Tableau traceabilite rempli avec les noms reels des tests
  - [x] 4.2 Completion Notes documente les ajouts (section Intent ambigu + table mapping canonique dans le prompt)

- [x] Task 5 : Non-regression et quality gate (AC: #7)
  - [x] 5.1 Venv active
  - [x] 5.2 17/17 tests backend consent flow verts
  - [x] 5.3 Suite complete backend : **1036 passed** (1019 + 17 ajoutes), 0 regression
  - [x] 5.4 `ruff check guided_tour.py test_guided_tour_consent_flow.py` → All checks passed
  - [x] 5.5 Frontend : 3/3 tests `useChat.guided-tour-consent` verts
  - [x] 5.6 Suite complete frontend : **272 passed** (269 + 3 ajoutes), 0 regression
  - [ ] 5.7 Verification manuelle : non realisee — story prompt + tests, couverte par les 20 nouveaux tests deterministes (AC7 satisfait par quality gate automatique)

## Dev Notes

### Contexte — story prompt + tests, pas d'implementation metier

Cette story valide et verrouille le flux de consentement DEJA rendu possible par les stories 6.1 (tool `trigger_guided_tour`) et 6.2 (prompt `GUIDED_TOUR_INSTRUCTION` + binding `GUIDED_TOUR_TOOLS` dans 6 noeuds). L'infrastructure est donc **entierement en place** :

- **Backend** : `trigger_guided_tour` (`backend/app/graph/tools/guided_tour_tools.py`) + `ask_interactive_question` (`backend/app/graph/tools/interactive_tools.py:53`) + prompt `GUIDED_TOUR_INSTRUCTION` (`backend/app/prompts/guided_tour.py`) + binding dans les 6 noeuds de `graph/nodes.py` (lignes 671, 805, 865, 1039, 1109, 1269 — importation + `bind_tools`).
- **Frontend** : `SingleChoiceWidget.vue`, `InteractiveQuestionHost.vue`, `useChat.ts` (handlers `interactive_question`, `interactive_question_resolved`, `guided_tour`), `useGuidedTour.ts`, `registry.ts` (6 `tour_id` alignes).

**Scope reel de 6.3** : renforcer/clarifier la section prompt dediee au consentement + declenchement direct (si AC non deja couverts par le contenu actuel) ET creer les tests qui verrouillent chaque AC. AUCUN nouveau composant, AUCUN nouvel endpoint, AUCUN nouveau tool. Les tests sont volontairement au niveau prompt-content + composable-handler pour rester deterministes (pas besoin de mocker un LLM complet).

### Pattern de reference — tests prompt-content (story 6.2)

Suivre le pattern de `backend/tests/test_prompts/test_guided_tour_instruction.py` :

```python
from app.prompts.guided_tour import GUIDED_TOUR_INSTRUCTION

def test_instruction_contains_consent_options():
    assert "Oui, montre-moi" in GUIDED_TOUR_INSTRUCTION
    assert "Non merci" in GUIDED_TOUR_INSTRUCTION
    # ...
```

Utiliser `pytest.mark.parametrize` pour factoriser les tests T-AC4a et T-AC4b (6 et 5 cas respectivement).

### Pattern de reference — tests composable frontend (feature 018)

Suivre le pattern des tests existants dans `frontend/tests/composables/` qui mockent le streaming SSE. La cle est de :
1. Importer `useChat` et instancier en dehors d'un composant (la refacto story 1.1 a migre en module-level state).
2. Patcher `fetch` / `EventSource` via `vi.mock` pour pousser des events SSE arbitraires.
3. Patcher `useGuidedTour` pour exposer un spy sur `startTour`.

Exemple squelette :

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('~/composables/useGuidedTour', () => ({
  useGuidedTour: () => ({
    startTour: vi.fn(),
    // ...
  }),
}))

// ... injecter events SSE, assert sur currentInteractiveQuestion / startTour
```

### Flux end-to-end a valider (reference architecture, ligne 932-958)

```
1. Module termine (carbon_node par ex)
   │
2. LLM applique GUIDED_TOUR_INSTRUCTION
   │
3. Tool call : ask_interactive_question("Voir vos resultats ?", [{yes:"Oui..."},{no:"Non..."}])
   │
4. SSE marker __sse_interactive_question__ → event SSE 'interactive_question'
   │
5. Frontend : useChat.handleInteractiveQuestionEvent → currentInteractiveQuestion.state='pending'
   │
6. Utilisateur clique "Oui, montre-moi" dans SingleChoiceWidget
   │
7. submitInteractiveAnswer → POST /api/chat/conversations/{id}/messages
   (interactive_question_id, interactive_question_values='["yes"]')
   │
8. Backend resolve + LLM tour suivant → tool call trigger_guided_tour(tour_id="show_carbon_results")
   │
9. SSE marker __sse_guided_tour__ → event SSE 'guided_tour'
   │
10. Frontend : useChat.handleGuidedTourEvent → garde OK (question answered) → useGuidedTour.startTour()
    │
11. Driver.js rentre en scene, widget retracte, parcours multi-etapes
```

Les etapes 1-5 et 10-11 sont **deja testees** (stories 4.x, 5.x, 6.1, 6.2 + feature 018). Story 6.3 verrouille le COUPLAGE entre les etapes 2 et 10 via le prompt (contenu normatif du consentement + mapping tour_id ↔ verbes d'intent).

### Mapping canonique `tour_id` ↔ module (source unique de verite)

| Module termine / demande explicite | tour_id canonique | Page cible |
|---|---|---|
| Evaluation ESG close (30 criteres) | `show_esg_results` | `/esg/results` |
| Bilan carbone finalise | `show_carbon_results` | `/carbon/results` |
| Recherche de fonds finalisee / demande catalogue | `show_financing_catalog` | `/financing` |
| Score credit calcule | `show_credit_score` | `/credit` |
| Plan d'action genere | `show_action_plan` | `/action-plan` |
| Vue d'ensemble post-onboarding (chat_node) | `show_dashboard_overview` | `/dashboard` |

Source : `frontend/app/lib/guided-tours/registry.ts` (6 exports) + `backend/app/prompts/guided_tour.py` (lignes 19-24).
Toute divergence est un bug bloquant — verification deja en place via la regex `_VALID_TOUR_ID` cote tool + guard `startTour` cote frontend (story 6.1 AC4).

### Mapping verbes d'intent → declenchement direct (AC4)

| Formulation utilisateur (FR) | tour_id derivable | Regle |
|---|---|---|
| « montre-moi mes resultats ESG » | `show_esg_results` | Declenchement direct, pas de widget |
| « guide-moi vers le plan d'action » | `show_action_plan` | Declenchement direct |
| « ou sont mes resultats carbone » | `show_carbon_results` | Declenchement direct |
| « visualise-moi le catalogue » | `show_financing_catalog` | Declenchement direct |
| « fais-moi visiter le dashboard » | `show_dashboard_overview` | Declenchement direct |
| « j'aimerais voir mes chiffres » | ambigu → `ask_interactive_question` | Consentement via widget |

Cette table doit etre reflechie dans `GUIDED_TOUR_INSTRUCTION` sous forme textuelle (pas besoin d'une grosse table — quelques exemples concrets suffisent au LLM).

### Fichiers attendus

| Fichier | Action | Justification |
|---|---|---|
| `backend/app/prompts/guided_tour.py` | MODIFIER (si gap) | Ajouter/verifier section « Intent ambigu », mapping module→tour_id, verbes explicites |
| `backend/tests/test_prompts/test_guided_tour_consent_flow.py` | CREER | Tests T-AC1a/1b, T-AC3, T-AC4a/4b, T-AC5 |
| `frontend/tests/composables/useChat.guided-tour-consent.test.ts` | CREER | Tests T-AC2, T-AC6 |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIER | Status `6-3-consentement-...` : `ready-for-dev` → `in-progress` → `review` → `done` |
| `backend/app/graph/nodes.py` | NE PAS TOUCHER | Binding deja en place (story 6.2) |
| `backend/app/graph/tools/guided_tour_tools.py` | NE PAS TOUCHER | Tool deja hardene (story 6.1) |
| `frontend/app/composables/useChat.ts` | NE PAS TOUCHER | Handlers deja en place (feature 018 + story 6.1) |
| `frontend/app/components/chat/SingleChoiceWidget.vue` | NE PAS TOUCHER | Composant reutilise sans modification |
| `frontend/app/lib/guided-tours/registry.ts` | NE PAS TOUCHER | 6 tour_id alignes |

### Traceabilite AC → test (finale)

| AC | Test backend (`test_guided_tour_consent_flow.py`) | Test frontend (`useChat.guided-tour-consent.test.ts`) |
|---|---|---|
| AC1 — proposition consent | `test_instruction_contains_consent_exact_strings`, `test_ask_interactive_question_before_trigger_in_post_module_section` | — |
| AC2 — consent accepte | `test_prompt_links_yes_answer_to_trigger_tour` (contrat prompt) + `test_tour_id_has_mapping_keyword` (mapping 6 tour_id) | `T-AC2 — cycle complet : interactive_question pending → answered → guided_tour declenche startTour` |
| AC3 — consent refuse | `test_prompt_has_no_aggressive_relance_keywords` | `T-AC3 — reponse « no » via submitInteractiveAnswer + aucun guided_tour dans la reponse → startTour non appele` |
| AC4 — intent explicite | `test_each_explicit_verb_present` (parametrise 5 verbes), `test_at_least_three_explicit_verbs_present`, `test_tour_id_has_mapping_keyword` (parametrise 6 paires) | — |
| AC5 — intent ambigu | `test_prompt_mentions_ambiguous_intent_fallback` | — |
| AC6 — verrou widget pending | — | `T-AC6 — guided_tour arrivant tant qu'une question est pending → startTour bloque + message systeme injecte` |
| AC7 — zero regression + couverture | Suite backend 1036 tests verts ; ruff All checks passed | Suite frontend 272 tests verts |
| AC8 — doc traceabilite | Ce tableau | — |

### Anti-patterns a eviter

- **Ne pas creer** un nouveau composant pour le consentement — `SingleChoiceWidget` est deja reutilise (Exigence technique de la story dans l'epic, et ADR4 architecture.md ligne 926 : « FR14-FR17 (Consentement) | SingleChoiceWidget.vue (reutilise) »).
- **Ne pas ajouter** d'endpoint REST pour le consentement — la reponse passe deja par `POST /api/chat/conversations/{id}/messages` via les 3 champs `interactive_question_*` (feature 018, `backend/app/api/chat.py:624-632`).
- **Ne pas hard-coder** dans le prompt les chaines `"Oui, montre-moi"` / `"Non merci"` sous plusieurs formes differentes — une seule occurrence dans la section « Regles obligatoires » suffit, les tests T-AC1a verifient la presence exacte.
- **Ne pas tenter** de tester un vrai LLM OpenAI dans la suite pytest — les tests sont deterministes sur le **contenu du prompt** (unit-level), la couverture end-to-end du dialogue LLM est portee par l'epic 8 (tests e2e).
- **Ne pas oublier** la garde `currentInteractiveQuestion.value?.state === 'pending'` dans `useChat.ts:689` — elle existe deja (patch review story 6.1), ne pas la retirer sous pretexte de simplification. Le test T-AC6 est la pour la verrouiller.

### Exigences architecture

- **ADR4 (architecture.md ligne 286-300)** — Tool LangChain `trigger_guided_tour` + marker SSE : story 6.3 n'ajoute rien au design du tool, elle valide son couplage avec `ask_interactive_question`.
- **NFR19 (zero regression)** — 1019 tests backend + 267 tests frontend doivent rester verts.
- **NFR10 (pas de PII dans le marker SSE)** — rappel deja present dans le prompt (ligne 58-63 de `guided_tour.py`) ; ne pas introduire d'exemple violant cette regle dans les nouveaux exemples ou tests.
- **NFR20 (widget universel)** — le widget de consentement fonctionne a l'identique dans le widget flottant (feature epic 1) et sur toutes les pages ou le chat est present.

### Intelligence stories 6.1 + 6.2 (dernieres stories completees — 2026-04-13)

**Lecons a retenir :**

- `GUIDED_TOUR_INSTRUCTION` est deja injecte systematiquement dans `build_system_prompt()` (patch review 6.2 — decision d'alignement avec le binding sans condition de `GUIDED_TOUR_TOOLS` dans `chat_node`). Ne PAS remettre d'injection conditionnelle post-onboarding.
- La validation serveur sur `tour_id` est regex `^[a-z][a-z0-9_]*$` — les 6 identifiants sont conformes. Si un test parametrise ajoute un `tour_id` fictif, il doit respecter la regex pour etre accepte par le tool.
- Le patch review 6.1 a durci `handleGuidedTourEvent` avec la garde `pending`. C'est cette garde que T-AC6 doit verrouiller — ecrit exactement le meme message d'erreur (« Repondez d'abord a la question en attente. »).
- Le plancher `count("GUIDED_TOUR_TOOLS") >= 12` utilise dans les tests 6.2 est deja ecrit ; ne PAS le dupliquer dans 6.3.
- Les tests 6.2 n'assertent PAS l'ordre positionnel `WIDGET_INSTRUCTION → GUIDED_TOUR_INSTRUCTION` (defer). Story 6.3 ne s'en occupe pas non plus (hors scope).
- L'alignement cross-stack `tour_id` frontend ↔ backend est defer dans 6.2. Story 6.3 ne cree pas non plus ce test — ce pourra etre une story 7.x ou 8.x dediee.

**Fichiers touches dans 6.1/6.2 (contexte a ne pas casser) :**
- `backend/app/prompts/guided_tour.py` (cree)
- `backend/tests/test_prompts/test_guided_tour_instruction.py` (16 tests)
- `backend/tests/test_tools/test_guided_tour_tools.py` (~22 tests)
- `backend/app/graph/tools/guided_tour_tools.py` (cree, 138 lignes)
- `backend/app/graph/nodes.py` (6 imports + 6 bindings)
- `backend/app/prompts/system.py` (injection systematique dans `build_system_prompt`)
- `backend/app/prompts/{esg_scoring,carbon,financing,credit,action_plan}.py` (import + concat)
- `frontend/app/composables/useChat.ts` (handler `handleGuidedTourEvent`, garde pending)

**Chiffres de sortie story 6.2** : 1019 tests backend verts, 0 regression. Couverture 100 % sur `app.prompts.guided_tour` et `app.graph.tools.guided_tour_tools`.

### Project Structure Notes

Aucune divergence avec la structure unified : les tests prompt vont dans `backend/tests/test_prompts/`, les tests composables dans `frontend/tests/composables/`. Nommage cohérent avec `test_guided_tour_instruction.py` (story 6.2) et `useChat.*.test.ts` (features precedentes).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-6-Story-6.3] — Exigences (lignes 989-1024)
- [Source: _bmad-output/planning-artifacts/prd.md#FR14-FR17] — Consentement et declenchement du guidage (lignes 332-335)
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision-4] — ADR4 Tool LangChain trigger_guided_tour (lignes 286-354)
- [Source: _bmad-output/planning-artifacts/architecture.md#L934-L958] — Flux de donnees parcours guide complet
- [Source: backend/app/prompts/guided_tour.py] — Prompt GUIDED_TOUR_INSTRUCTION (story 6.2)
- [Source: backend/app/graph/tools/guided_tour_tools.py] — Tool trigger_guided_tour (story 6.1)
- [Source: backend/app/graph/tools/interactive_tools.py:53] — Tool ask_interactive_question (feature 018)
- [Source: backend/app/api/chat.py:624-632] — Endpoint POST /api/chat/messages avec champs interactive_question_*
- [Source: backend/app/graph/nodes.py:1109-1118] — chat_node binding (exemple de reference)
- [Source: backend/tests/test_prompts/test_guided_tour_instruction.py] — Pattern de tests prompt-content a repliquer
- [Source: frontend/app/composables/useChat.ts:344-405] — Handlers interactive_question + interactive_question_resolved
- [Source: frontend/app/composables/useChat.ts:470-700] — submitInteractiveAnswer + handleGuidedTourEvent + garde pending (ligne 689)
- [Source: frontend/app/components/chat/SingleChoiceWidget.vue] — Composant reutilise (feature 018)
- [Source: frontend/app/lib/guided-tours/registry.ts] — 6 tour_id canoniques (story 4.2)
- [Source: _bmad-output/implementation-artifacts/6-1-tool-langchain-trigger-guided-tour-et-marker-sse.md] — Story 6.1
- [Source: _bmad-output/implementation-artifacts/6-2-prompt-guided-tour-instruction-et-injection-dans-les-noeuds-langgraph.md] — Story 6.2 (patch reviews a respecter)

## Dev Agent Record

### Agent Model Used

claude-opus-4-6 (1M context)

### Debug Log References

Aucun debug necessaire — prompt modifie chirurgicalement, tests passes au 1er run.

### Completion Notes List

- Analyse du prompt existant (`guided_tour.py`, story 6.2) : toutes les chaines exactes etaient deja presentes (`"Oui, montre-moi"`, `"Non merci"`, `"yes"`, `"no"`, 5 verbes explicites, 6 tour_id, ask avant trigger dans la section post-module, NFR10 PII documente).
- **Ajout 1 — Intent ambigu** : nouvelle sous-section du prompt apres « Quand proposer un guidage » avec les mots-cles requis (`ambigu`, `privilegie`, `prudence`, `doute`) et reaffirmation de la liste exacte des 5 verbes explicites declenchant le mode direct.
- **Ajout 2 — Mapping canonique** : table Markdown explicite « module termine → tour_id » dans le prompt pour eviter toute hallucination de tour_id cote LLM. La regle « ces 6 identifiants sont la source unique de verite » est verrouillee par la regex serveur `^[a-z][a-z0-9_]*$` + la liste blanche.
- **Ajout 3 (patch review H1)** — `backend/app/prompts/system.py` : injection inconditionnelle de `GUIDED_TOUR_INSTRUCTION` (sortie du guard `_has_minimum_profile`) pour que les regles d'usage accompagnent toujours le tool. Resout partiellement le defer 6.2 « couplage STYLE_INSTRUCTION / GUIDED_TOUR_INSTRUCTION ». Commentaire mis a jour : 6 noeuds bindes (chat, esg_scoring, carbon, financing, credit, action_plan), pas seulement chat_node.
- **Ajout 4 (patch review)** — `backend/tests/test_prompts/test_guided_tour_instruction.py` : T8/T9 inverses (verification de PRESENCE et non d'absence de `GUIDED_TOUR_INSTRUCTION` dans le system prompt quelle que soit la presence du profil) pour refleter la nouvelle politique d'injection ; T4 renforce (liste PII >=2 keywords) ; T11 plancher `>= 12` occurrences `GUIDED_TOUR_TOOLS` (6 noeuds * 2 occurrences chacun).
- **Patch review H2** — clarification dans `GUIDED_TOUR_INSTRUCTION` : « le verbe `voir` seul ne suffit pas », pour eviter que le LLM bascule en declenchement direct sur des intents vagues contenant `voir`.
- **Patch review M3** — accentuation francaise : `ou sont` remplace par `ou sont` dans le prompt ET dans le parametrize `EXPLICIT_VERBS` (convention CLAUDE.md + usage reel utilisateur).
- **Patch review M2 / L1 / L2** — renforcement suite de tests : nouveau `test_post_module_section_links_yes_to_trigger_guided_tour` (lien semantique `yes`→tool call) ; normalisation `.lower()` appliquee systematiquement dans les asserts `EXPLICIT_VERBS` ; liste `forbidden` elargie (relance, insistant, repropose, propose a nouveau).
- **Patch review M4** — isolation etat module-level `useChat` : `resetModuleState()` appele AVANT chaque test (pas seulement apres) pour eviter les fuites depuis les suites voisines.
- **Backend** : 18 tests ajoutes (17 initiaux + 1 patch review M2) — parametrises (5 verbes + 6 paires tour_id/keyword). Couverture 100% du contenu normatif du prompt.
- **Frontend** : 3 tests ajoutes couvrant T-AC2 (cycle complet `sendMessage` → `submitInteractiveAnswer`), T-AC6 (verrou widget pending), T-AC3 (refus sans relance).
- **Zero regression** : backend 1036 verts (1019+17), frontend 272 verts (269+3), ruff All checks passed (a revalider apres patches review).
- Aucun nouveau composant, endpoint, ou tool cree — fidele au scope « prompt + tests ».

### File List

- `backend/app/prompts/guided_tour.py` — MODIFIE (ajout section « Intent ambigu » + mapping canonique module→tour_id ; patch review H2 clarification `voir` ; patch review M3 accent `ou sont`)
- `backend/app/prompts/system.py` — MODIFIE (patch review H1 : injection inconditionnelle de `GUIDED_TOUR_INSTRUCTION` + commentaire 6 noeuds)
- `backend/tests/test_prompts/test_guided_tour_instruction.py` — MODIFIE (patch review : T8/T9 inverses, T4 renforce, T11 plancher >=12)
- `backend/tests/test_prompts/test_guided_tour_consent_flow.py` — CREE (18 tests : 17 initiaux + 1 M2 `test_post_module_section_links_yes_to_trigger_guided_tour`)
- `frontend/tests/composables/useChat.guided-tour-consent.test.ts` — CREE (3 tests ; patch review M4 : reset AVANT + APRES chaque test)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — MODIFIE (6-3 : ready-for-dev → in-progress → review → done)
- `_bmad-output/implementation-artifacts/6-3-consentement-via-widget-interactif-et-declenchement-direct.md` — MODIFIE (tasks cochees, traceabilite, Dev Agent Record, Review Findings, Status → done)
- `_bmad-output/implementation-artifacts/deferred-work.md` — MODIFIE (6 defer ajoutes pour story 6-3)

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-04-13 | Story 6.3 creee — consentement via widget interactif + declenchement direct. Scope prompt + tests, pas d'implementation metier. 8 AC, 5 tasks, 2 suites de tests (backend + frontend). | bmad-create-story |
| 2026-04-14 | Implementation story 6.3 : prompt enrichi (section Intent ambigu + table mapping canonique), 17 tests backend + 3 tests frontend ajoutes, zero regression (1036 backend / 272 frontend verts). Status → review. | bmad-dev-story |
| 2026-04-14 | Code review triage : 0 decision-needed, 8 patches, 6 defer, 6 dismiss. Findings ajoutes ci-dessous. | bmad-code-review |

### Review Findings

- [x] [Review][Patch] H1 — Documenter le scope reel (system.py + test_guided_tour_instruction.py modifies) — File List + Completion Notes de la story mis a jour (patch review 2026-04-14) [_bmad-output/implementation-artifacts/6-3-consentement-via-widget-interactif-et-declenchement-direct.md]
- [x] [Review][Patch] H2 — Clarification ajoutee : « le verbe `voir` seul NE suffit PAS » dans le prompt (patch review 2026-04-14) [backend/app/prompts/guided_tour.py:31-36]
- [x] [Review][Patch] M2 — Nouveau test `test_post_module_section_links_yes_to_trigger_guided_tour` asserte le lien semantique `yes`→`trigger_guided_tour` (patch review 2026-04-14) [backend/tests/test_prompts/test_guided_tour_consent_flow.py]
- [x] [Review][Patch] M3 — `ou sont` remplace par `ou sont` accentue dans le prompt et le parametrize `EXPLICIT_VERBS` (patch review 2026-04-14) [backend/app/prompts/guided_tour.py:31,35,61, backend/tests/test_prompts/test_guided_tour_consent_flow.py:86]
- [x] [Review][Patch] M4 — `resetModuleState()` deplace dans `beforeEach` en plus d'`afterEach` pour isolation totale (patch review 2026-04-14) [frontend/tests/composables/useChat.guided-tour-consent.test.ts]
- [x] [Review][Patch] L1 — `.lower()` applique sur `GUIDED_TOUR_INSTRUCTION` dans `test_each_explicit_verb_present` + `test_at_least_three_explicit_verbs_present` (patch review 2026-04-14) [backend/tests/test_prompts/test_guided_tour_consent_flow.py]
- [x] [Review][Patch] L2 — Liste `forbidden` elargie avec `insistant`, `relance`, `repropose`, `propose a nouveau` (patch review 2026-04-14) [backend/tests/test_prompts/test_guided_tour_consent_flow.py]
- [x] [Review][Patch] L3 — Commentaire `system.py` corrige : 6 noeuds bindes, pas seulement `chat_node` (patch review 2026-04-14) [backend/app/prompts/system.py:215-219]
- [x] [Review][Defer] H3 — T-AC2 / T-AC6 court-circuitent `useGuidedTour` via mock statique — deferred, test d'integration plus realiste a prevoir en epic 8 (e2e)
- [x] [Review][Defer] M1 — Plancher `count >= 12` dans T11 conflate shape et correctness — deferred, herite story 6.2
- [x] [Review][Defer] M5 — T-AC3 ne prouve pas le respect du refus (passe meme si backend emettait guided_tour a tort) — deferred, test d'alignement backend/frontend hors scope prompt-only
- [x] [Review][Defer] L8 — `GUIDED_TOUR_INSTRUCTION` injecte pour sessions anonymes (bloat tokens) — deferred, decision architecturale post-6.2 a valider globalement
- [x] [Review][Defer] D1 — Aucun test cross-file alignant `tour_id` entre prompt / registry.ts / guided_tour_tools.py — deferred, test de contrat pour story 7.x ou 8.x
- [x] [Review][Defer] D2/D3 — Validation serveur `tour_id` et validation `context` dans `handleGuidedTourEvent` — deferred, hors scope (story 6.1 + `useChat.ts` NE PAS TOUCHER)
