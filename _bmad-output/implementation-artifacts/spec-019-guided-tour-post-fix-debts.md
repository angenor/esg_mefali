---
title: 'Feature 019 — 3 dettes techniques post-fix guided_tour (2026-04-15)'
type: 'bugfix'
created: '2026-04-15'
status: 'in-review'
baseline_commit: '95871ea0cc50b389c0dd14bd55fa4ba88290e77d'
context:
  - '_bmad-output/implementation-artifacts/deferred-work.md'
  - 'frontend/app/lib/guided-tours/registry.ts'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Le fix SSE whitelist du 2026-04-15 a restaure le declenchement de driver.js, mais a revele 3 dettes residuelles : (1) placeholders `{{...}}` non interpoles (`context=None` passe par le LLM), (2) whitelist SSE incomplete pour `profile_update`/`profile_completion` (meme classe de bug), (3) bruit visuel dans le chat (1 message vide + N messages fallback duplicables) quand des etapes ciblent des elements absents du DOM (blocs `v-if` conditionnels).

**Approach:** 3 correctifs chirurgicaux commites separement. (1) Enrichir `GUIDED_TOUR_INSTRUCTION` avec la liste exhaustive des cles `context` attendues par tour + exemples. (2) Si live confirme la casse : etendre la whitelist `generate_sse` + le test statique. (3) Supprimer le message vide post guided_tour et consolider les fallbacks "element absent" en un seul message final.

## Boundaries & Constraints

**Always:**
- Un commit par BUG pour faciliter la revue (3 commits).
- Conserver la couverture existante (935+ tests backend, suites frontend).
- Validation live via `agent-browser --headed` sur compte `fatou1@gmail.com` page `/carbon/results` pour BUG-1 et BUG-3.
- BUG-2 : valider d'abord live si `profile_update` arrive au frontend. Ne forwarder dans la whitelist QUE si la voie SSE est effectivement la route utilisee (eviter d'ajouter du code mort).

**Ask First:**
- BUG-2 : si la validation live montre que les events `profile_update`/`profile_completion` ne sont pas attendus cote frontend (autre voie, e.g. rechargement REST), confirmer l'orientation (documenter la double-voie vs forwarder quand meme par defense en profondeur) avant d'editer la whitelist.
- BUG-3 action 2 : si le volume de fallbacks depasse l'attendu (>3 etapes sautees), confirmer le wording du message consolide.

**Never:**
- Ne pas refondre le messaging guided tour.
- Ne pas migrer le scope localStorage multi-user (cf. dette 6-4 distincte).
- Ne pas toucher a `useChat.ts` pour ajouter de la logique guided-tour (story 6.3 l'a explicitement interdit). Les modifs de consolidation vont dans `useGuidedTour.ts`.
- Ne pas creer un nouveau composable, nouveau module, ou helper partage pour ces 3 correctifs.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| BUG-1 happy | User : « Montre-moi mes resultats carbone » sur `/carbon/results` | LLM appelle `trigger_guided_tour("show_carbon_results", context={"total_tco2":X, "top_category":"…", "top_category_pct":Y, "sector":"…"})`, popover interpole les valeurs | Si LLM omet une cle : placeholder brut `{{...}}` visible (status quo, non regresse) |
| BUG-2 happy | User modifie profil via chat → tool `update_company_profile` emet marker SSE profile | Si voie SSE utilisee : event `profile_update`/`profile_completion` recu cote client | Si voie non utilisee : documenter dans deferred-work et ne pas toucher au code |
| BUG-3 msg vide | `full_response == ""` ET >=1 event `guided_tour` emis dans ce tour | Aucun `Message` assistant persiste ; le tour demarre sans bulle vide | Si erreur persistance : logger + continuer (le tour reste lance) |
| BUG-3 fallback unique | 1 seule etape sautee (element absent) | Message unique : « Je n'ai pas pu pointer cet element. Passons a la suite. » (comportement actuel) | — |
| BUG-3 fallback multi | N>=2 etapes sautees (elements absents) | 1 seul message final : « Certaines sections ne sont pas encore disponibles sur cette page — les autres ont ete montrees. » | Si l'integralite du tour est sautee : fallback individuel existant (« Je n'ai pas pu pointer… ») preserve pour compatibilite |
| BUG-3 timeout navigation | `waitForElementExtended` retourne null apres navigation | Message specifique `La page met trop de temps a charger` preserve (distinct du fallback "element absent") | interruptTour (comportement existant) |

</frozen-after-approval>

## Code Map

- `backend/app/prompts/guided_tour.py` -- `GUIDED_TOUR_INSTRUCTION` : enrichir avec la section « Cles `context` par tour_id » + exemples concrets (BUG-1).
- `backend/tests/test_prompts/test_guided_tour_instruction.py` -- ajouter un test verifiant la presence des 8 cles : `total_tco2`, `top_category`, `top_category_pct`, `sector`, `esg_score`, `credit_score`, `matched_count`, `active_actions` (BUG-1).
- `backend/app/api/chat.py:865-869` -- whitelist `generate_sse` (BUG-2, conditionnel sur validation live).
- `backend/app/api/chat.py:874-883` -- persistance `assistant_message` : gate sur `full_response` non vide OU pas d'event guided_tour (BUG-3 action 1).
- `backend/tests/test_api/test_sse_event_whitelist.py` -- etendre `_REQUIRED_EVENT_TYPES` avec `profile_update` et `profile_completion` (BUG-2, conditionnel).
- `frontend/app/composables/useGuidedTour.ts:528-533` -- remplacer `addSystemMessage` immediat par un compteur `skippedStepsCount` ; emettre le message consolide apres la boucle (BUG-3 action 2).
- `frontend/tests/e2e/8-1-parcours-fatou.spec.ts` -- ajouter un scenario « donnees partielles » (pas de reduction_plan, pas de benchmark) (BUG-3 action 3).
- `frontend/app/lib/guided-tours/registry.ts` -- reference (pas de modification) : source des cles context attendues.

## Tasks & Acceptance

**Execution:**

BUG-1 (commit 1 — prompt context keys) — commit 8c71101
- [x] `backend/app/prompts/guided_tour.py` -- section « Cles `context` par tour_id » ajoutee avec tableau 6 tours + exemple concret carbon.
- [x] `backend/tests/test_prompts/test_guided_tour_instruction.py` -- `test_instruction_documents_context_keys_per_tour` verrouille les 8 cles. Adaptation borne longueur prompt (3500-6000 -> 3500-7000).
- [x] Validation live (agent-browser --headed, `fatou1@gmail.com`, `/carbon/results`, nouvelle conversation, « Guide-moi visuellement sur ma page carbon results ») : `tool_call_logs` confirme que le LLM appelle desormais `trigger_guided_tour(context={sector, total_tco2, top_category, top_category_pct})` avec les 4 bonnes cles (au lieu de `context=None`). Les valeurs numeriques restent None car le chat_node n'a pas les stats carbon dans son contexte (dette secondaire consignee dans `deferred-work.md` sous « 019-guided-tour-post-fix-debts validation live »). Le contrat context est cependant respecte : le prompt a bien force l'ecriture des cles.

BUG-2 (commit 2 — whitelist SSE profile events) — commit d10edd2
- [x] Validation statique : `useChat.ts:407` et `:416` lisent `profile_update`/`profile_completion` pour mettre a jour companyStore. Confirmation : les events etaient drop silencieusement depuis feature 012.
- [x] `backend/app/api/chat.py` -- ajout de `"profile_update", "profile_completion"` dans la whitelist de `generate_sse`.
- [x] `backend/tests/test_api/test_sse_event_whitelist.py` -- `_REQUIRED_EVENT_TYPES` etendu, docstring mis a jour.

BUG-3 (commit 3 — message vide + consolidation fallbacks + E2E) — commit ee04069
- [x] `backend/app/api/chat.py` -- flag `guided_tour_emitted`, branche `if not full_response.strip() and guided_tour_emitted` emet `{type: 'done', message_id: None, skipped_empty: True}` sans persister `Message`. La liaison interactive_question est desormais dans la branche `else` (aucune question n'est pending quand guided_tour est emis).
- [x] `frontend/app/composables/useChat.ts` -- 2 branches `done && skipped_empty` (sendMessage + submitInteractiveAnswer), retire le placeholder vide. Types etendus avec `message_id?: string | null` et `skipped_empty?: boolean`.
- [x] `frontend/app/composables/useGuidedTour.ts` -- compteur `skippedSteps`, message consolide apres la boucle for : singulier conserve (1 etape sautee), pluriel consolide pour >=2 etapes.
- [x] `frontend/tests/e2e/8-1-parcours-fatou.spec.ts` -- scenario « page avec donnees partielles » : override `/api/carbon/assessments/.../summary` pour retourner `reduction_plan=null` et `sector_benchmark=null`, assert 0 bulle vide + 1 seul message consolide + 0 message fallback individuel.
- [x] Validation live (agent-browser --headed, meme session Fatou) : apres declenchement du tour, `emptyAsstMsgs === 0` confirme ; message final dans le chat = « Certaines sections ne sont pas encore disponibles sur cette page — les autres ont ete montrees. » (exactement le wording BUG-3) ; aucun « Je n'ai pas pu pointer cet element » observe.

**Acceptance Criteria:**
- Given un utilisateur sur `/carbon/results` avec un bilan carbone complet, when il envoie « Montre-moi mes resultats carbone », then le popover de l'etape 1 affiche les valeurs reelles (pas de `{{...}}` brut visible).
- Given la suite de tests statique `test_sse_event_whitelist.py`, when elle s'execute, then elle echoue si un type d'event yielded par `stream_graph_events` est absent de la whitelist `generate_sse` (verrou anti-regression pour la classe de bug).
- Given un utilisateur avec un bilan carbone partiel (sans plan de reduction ni benchmark), when il declenche `show_carbon_results`, then le chat n'affiche ni bulle vide, ni messages fallback dupliques ; au plus 1 message consolide est ajoute apres le parcours.
- Given les 3 commits, when on inspecte `git log`, then chaque commit a un scope clair (prompt / whitelist / consolidation) et une reference au bug fix.

## Spec Change Log

## Design Notes

Enrichissement du prompt BUG-1 — format propose (a adapter par l'agent d'implementation, boundaries fixes, wording libre) :

```
### Cles `context` par tour_id (OBLIGATOIRE — remplis toujours context)

| tour_id | Cles requises |
|---|---|
| show_carbon_results | total_tco2, top_category, top_category_pct, sector |
| show_esg_results | esg_score (+ pillar_top optionnel) |
| show_credit_score | credit_score |
| show_financing_catalog | matched_count |
| show_action_plan | active_actions |
| show_dashboard_overview | esg_score, total_tco2, credit_score, matched_count |

Exemple concret (user : « montre-moi mon bilan carbone ») :
trigger_guided_tour(
  tour_id="show_carbon_results",
  context={"total_tco2": 12.4, "top_category": "Transport",
           "top_category_pct": 38, "sector": "Agro-alimentaire"},
)
```

Consolidation BUG-3 action 2 — pseudo-code pour useGuidedTour.ts :

```ts
let skippedSteps = 0
for (let i = 0; i < interpolatedSteps.length; i++) {
  // ... existing logic ...
  if (!element) {
    skippedSteps += 1  // au lieu d'un addSystemMessage immediat
    continue
  }
  // ...
}
// Apres la boucle, avant la finalisation :
if (skippedSteps === 1) {
  addSystemMessage('Je n\'ai pas pu pointer cet element. Passons a la suite.')
} else if (skippedSteps >= 2) {
  addSystemMessage('Certaines sections ne sont pas encore disponibles sur cette page — les autres ont ete montrees.')
}
```

Notes de garde :
- BUG-3 action 1 : le frontend `useChat` doit tolerer `done` sans `message_id` ; si non, ajouter un guard cote client au lieu de casser l'invariant backend.
- BUG-3 action 2 : les timeouts navigation (lignes 425/516) ne sont PAS consolides — ils interrompent le tour, leur message specifique reste utile et n'est emis qu'une fois.

## Verification

**Commands:**
- `cd backend && source venv/bin/activate && pytest tests/test_prompts/test_guided_tour_instruction.py tests/test_api/test_sse_event_whitelist.py -v` -- expected: tous verts, nouveaux tests inclus.
- `cd backend && source venv/bin/activate && pytest -x` -- expected: 935+ tests backend verts, zero regression.
- `cd frontend && npm run test:e2e -- 8-1-parcours-fatou` -- expected: scenarios existants + nouveau "donnees partielles" verts.
- `cd frontend && npm run build` -- expected: build Nuxt OK.

**Manual checks (agent-browser --headed):**
- BUG-1 live : popover etape 1 affiche `Votre empreinte est de 12.4 tCO2e. Ce graphique montre la repartition par categorie — Transport represente 38% du total.` (valeurs reelles selon donnees Fatou).
- BUG-2 live : devtools Network → onglet EventStream pendant une mise a jour profil ; verifier presence de `data: {"type":"profile_update",...}`.
- BUG-3 live : apres reproduction Fatou, `document.querySelectorAll('[data-testid="chat-message"][data-role="assistant"]').length` ne contient aucun `textContent === ""`, et au plus 1 message systeme apres le parcours.
