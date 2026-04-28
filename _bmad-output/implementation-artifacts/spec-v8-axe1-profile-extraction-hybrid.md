---
title: 'V8-AXE1 — Extraction profil hybride LLM + regex déterministe + few-shot'
type: 'bugfix'
created: '2026-04-28'
status: 'done'
baseline_commit: '4d62369'
context:
  - '{project-root}/docs/CODEMAPS/methodology.md'
  - '{project-root}/_bmad-output/implementation-artifacts/tests-manuels-vague-7-2026-04-28.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-v8-axe2-action-plan-fallback.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-v8-axe3-routing-credit-carbon-finalize.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem :** Lors du profilage onboarding chat, le tool `update_company_profile` est appelé avec des arguments majoritairement `null` malgré une phrase utilisateur structurée (« AgriVert Sarl, Agriculture, 15 employés, Sénégal »). Sous **MiniMax** (BUG-V7-001) : 4 appels avec tous les args = `null`. Sous **Claude Sonnet 4.6** (BUG-V7.1-001) : seul `employee_count` extrait, `sector` et `city` ratés alors qu'ils sont explicitement mentionnés. Le profil reste incomplet (19 % global) et bloque la cascade ESG / Carbone / Financement / Plan.

**Approach :** Mettre en place une **extraction hybride** : (1) renforcer le docstring du tool + injecter 3 exemples few-shot dans `_build_profiling_instructions` pour que le LLM extraie tous les champs en un seul appel ; (2) ajouter un **fallback déterministe regex** (`profile_extraction.py`) qui couvre les patterns évidents (forme juridique, secteurs FR, pays UEMOA, effectif) ; (3) merger les deux côté tool (les valeurs LLM gagnent toujours quand non-null, le regex ne comble que les trous). Aucun changement de graph LangGraph ni de schéma SQLAlchemy.

## Boundaries & Constraints

**Always :**
- Le LLM reste prioritaire : si une valeur LLM est non-null pour un champ, elle gagne sur la valeur regex (le LLM peut désambiguïser, le regex non).
- Le fallback regex ne s'active que si **≥2 champs LLM sont null** ET un texte utilisateur exploitable est disponible dans `configurable["last_user_message"]`.
- Conserver tous les contrôles existants : rejet whitespace-only (BUG-V6-011), validation Pydantic `CompanyProfileUpdate`, retours `str` exploitables par le LLM (§4nonies).
- Logger `regex_fallback_triggered` avec `user_id`, `null_field_count`, `regex_filled_fields`.
- Few-shot dans le prompt utilise les noms de champs **réels du schéma** (`company_name`, pas `name`).
- Regex sectors / countries en minuscules avec accents tolérés (`accents-insensitive` côté detection, valeur retournée canonique avec accents).

**Ask First :**
- Si le user a édité manuellement un champ (flag `manually_edited`), le service `update_profile` saute déjà ce champ → **ne pas** essayer de re-merger via regex (déjà géré côté service company).
- Si le texte source contient plusieurs entreprises mentionnées (cas exotique « j'ai vu EcoSolaire mais je travaille chez AgriVert »), retourner le 1er match canonique du regex et logger un avertissement — pas de heuristique de désambiguïsation côté V8.

**Never :**
- Ne jamais modifier le modèle SQLAlchemy `CompanyProfile` ni la migration.
- Ne jamais modifier le schéma Pydantic `CompanyProfileUpdate`.
- Ne jamais retirer le contrôle whitespace-only en place (BUG-V6-011).
- Ne jamais retourner directement les valeurs regex sans passage par `CompanyProfileUpdate` (validation Pydantic obligatoire).
- Ne jamais étendre le scope au-delà des **5 champs** ciblés (`company_name`, `sector`, `employee_count`, `country`, `city`). Les autres restent du domaine LLM exclusif.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| LLM-OK-COMPLET | LLM extrait 4-5/5 champs depuis « AgriVert Sarl, Agriculture, 15 employés, Sénégal » | Tool merge sans déclencher regex (≤1 null), persiste tel quel | N/A |
| LLM-PARTIEL | LLM extrait `employee_count=15` uniquement, 4 nulls | Regex complète `company_name=AgriVert Sarl`, `sector=agriculture`, `country=Sénégal` ; LLM employee_count=15 conservé | log `regex_fallback_triggered` |
| LLM-TOUS-NULL | LLM appelle avec tous args=null + texte exploitable | Regex remplit 4/5 champs, tool persiste | log `regex_fallback_triggered` |
| LLM-NULL-TEXTE-VIDE | LLM tous null + `last_user_message` absent ou non exploitable | Tool retourne « Aucun champ utile fourni… » (existant) | pas de regex |
| TEXT-AMBIGUOUS | « Je suis dans le sustainable business » | Aucun pattern matche → regex retourne `{}`, comportement nominal LLM seul | N/A |
| MANUAL-EDITED | LLM passe `sector=agriculture` mais user a déjà édité ce champ manuellement | Service company skippe `sector` → message « champs protégés » (existant) | N/A |
| WHITESPACE-LLM | LLM passe `company_name="   "` | Contrôle existant rejette → puis regex tente de combler depuis le texte | N/A |
| MULTI-SECTOR | « solaire et agriculture » dans le texte | Premier match canonique (`energie`), warning loggé | N/A |

</frozen-after-approval>

## Code Map

- `backend/app/graph/tools/profiling_tools.py` -- patcher `update_company_profile` : enrichir docstring avec 3 exemples few-shot ; après extraction LLM, si ≥2 args null et `configurable["last_user_message"]` non vide, appeler `extract_profile_from_text` et merger (LLM > regex).
- `backend/app/services/profile_extraction.py` -- **nouveau** : `extract_profile_from_text(text: str) -> ExtractedProfile` ; constantes `SECTORS_FR` (9 secteurs canoniques), `COUNTRIES_UEMOA` (8 pays), regex pour `company_name` (forme juridique Sarl/SA/SAS/S.A.) et `employee_count`. Tolérance accents.
- `backend/app/graph/nodes.py` -- enrichir `_build_profiling_instructions` (ligne ~429) : ajouter une section « EXTRACTION OBLIGATOIRE » + 3 exemples few-shot quand le profil est incomplet.
- `backend/app/api/chat.py` -- ajouter `last_user_message` dans `configurable` (extrait du dernier `HumanMessage` ajouté à `initial_state["messages"]`).
- `backend/app/services/__init__.py` -- (existant) noop.
- `backend/tests/test_services/test_profile_extraction.py` -- **nouveau** : tests unitaires regex couvrant les 8 scénarios de la matrice + cas accents/casse/multi-sector.
- `backend/tests/test_tools/test_profiling_tools_extraction_fallback.py` -- **nouveau** : tests intégration tool qui prouvent le merge LLM>regex et l'inactivation du fallback quand `last_user_message` absent.

## Tasks & Acceptance

**Execution :**
- [x] `backend/app/services/profile_extraction.py` -- créer le module avec `SECTORS_FR`, `COUNTRIES_UEMOA`, `ExtractedProfile` (TypedDict), `extract_profile_from_text(text)`. Tolérance accents (normalisation NFD lower) ; regex `company_name` capture nom + forme juridique ; regex `employee_count` numérique + mots-clés FR.
- [x] `backend/app/graph/tools/profiling_tools.py` -- enrichir docstring `update_company_profile` avec section « EXEMPLES OBLIGATOIRES » (3 cases), puis après le bloc whitespace-cleaning : si `len([v for v in raw_updates LLM-original if None]) >= 2` et `configurable.last_user_message` non vide, appeler `extract_profile_from_text` ; merger en garantissant `regex_value` n'écrase jamais `llm_value` non-null ; logger `regex_fallback_triggered` (logger.info, extra metric).
- [x] `backend/app/graph/nodes.py` -- compléter `_build_profiling_instructions` avec un bloc `EXTRACTION OBLIGATOIRE` listant les 3 exemples few-shot quand `missing_fields` est non vide.
- [x] `backend/app/api/chat.py` -- ajouter `"last_user_message": <str>` dans le dict `configurable` (ligne ~176), source = dernier `HumanMessage.content` de `initial_state["messages"]` (string vide si aucun).
- [x] `backend/tests/test_services/test_profile_extraction.py` -- couvrir : extraction complète AgriVert/EcoSolaire/TextileVert, accents `Sénégal`/`Bénin`, casse mixte, mot vide, multi-sector (premier match), texte sans pattern. **52 tests verts.**
- [x] `backend/tests/test_tools/test_profiling_tools_extraction_fallback.py` -- monkeypatch `extract_profile_from_text` ; cas : LLM-PARTIEL → fallback comble, LLM-OK → fallback non déclenché, LLM-NULL+texte vide → message « Aucun champ utile », LLM>regex priority (LLM `sector="services"` ignore regex `agriculture`). **6 tests verts.**

**Acceptance Criteria :**
- Given un message « AgriVert Sarl, Agriculture, 15 employés, Sénégal » et un LLM qui n'extrait que `employee_count=15`, when `update_company_profile` exécute, then le profil persisté contient `company_name="AgriVert Sarl"`, `sector="agriculture"`, `country="Sénégal"`, `employee_count=15` (4 champs au lieu de 1).
- Given un LLM qui extrait correctement tous les champs, when le tool s'exécute, then le fallback regex n'est PAS appelé (assert via spy/mock) et un seul appel `update_profile` côté service.
- Given `last_user_message` absent du configurable, when le tool reçoit tous args null, then retour « Aucun champ utile fourni… » sans tentative regex (rétro-compatibilité).
- Given un LLM qui passe `sector="services"` (mauvaise extraction) sur le texte « AgriVert Sarl, Agriculture », when le tool merge, then `sector="services"` (LLM gagne — à charge du LLM d'être honnête, pas du regex).

## Spec Change Log

### Iteration 1 — review post-implementation (2026-04-28)

Trois reviewers (blind hunter / edge case hunter / acceptance auditor) ont
analysé le diff. Findings classifiés `patch` (auto-fix sans loopback) ;
aucun `intent_gap` ni `bad_spec`. Patches appliqués :

- **CRITIQUE-1** — `SECTORS_FR` contenait `industrie` et `tourisme` qui ne
  sont PAS membres de `SectorEnum` (Pydantic). Pydantic aurait levé
  `ValidationError` au moment du merge. Aligné `SECTORS_FR` sur les 11
  membres de `SectorEnum` (`industrie`/`manufacture` → `autre` ;
  `tourisme`/`hotellerie`/`restaurant` → `services`). Ajout de
  `agroalimentaire`, `recyclage`, `artisanat`. Test
  `test_all_sectors_are_valid_enum_members` ajouté comme garde-fou de
  régression.
- **CRITIQUE-2** — `_COMPANY_NAME_RE` était trop greedy : capture des
  préfixes phrastiques (« Mon Entreprise AgriVert Sarl »). Limité à 1-2
  mots capitalisés avant la forme juridique.
- **ÉLEVÉ-1** — Risque ReDoS / DoS sur texte long. Ajout d'un cap
  `_MAX_INPUT_LENGTH=5000` en tête de `extract_profile_from_text` + tests
  `test_caps_input_length` et `test_no_redos_on_pathological_input`.
- **ÉLEVÉ-2** — Lookahead négatif `(?![A-Za-zÀ-ÿ])` étendu pour inclure
  les chiffres `(?![A-Za-zÀ-ÿ0-9])` (évite `SAS123` faux split).
- **ÉLEVÉ-3** — `user_id` PII en clair dans logs (RGPD). Tronqué aux 8
  premiers caractères de l'UUID.
- **ÉLEVÉ-4** — `\d{1,6}` permettait 999 999 employés alors que Pydantic
  limite `le=100_000`. Réduit à `\d{1,5}` + lookbehind/lookahead négatifs
  sur `\d` pour éviter le faux positif `500000 employes` → `00000` (= 0).
- **MOYEN-1** — Whitespace LLM non compté comme null pour le seuil.
  Helper `_is_effectively_null` ajouté ; un LLM passant 5 chaînes vides
  déclenche désormais correctement le fallback. Test
  `test_whitespace_llm_triggers_regex_fallback` ajouté.
- **MOYEN-2** — `city` retiré de `_REGEX_FALLBACK_FIELDS` (non couvert par
  `extract_profile_from_text`, il introduisait un biais permanent +1 null).
- **MOYEN-3** — Test scénario `WHITESPACE-LLM` ajouté.
- **MOYEN-4** — Test multi-sector asserte désormais explicitement le
  warning loggé.

**KEEP (à préserver lors d'une future re-dérivation) :**
- L'invariant LLM > regex (jamais d'écrasement) reste validé par
  `test_llm_sector_wins_over_regex`.
- Le pattern §4nonies (retours `str`, jamais d'exception remontée, validation
  Pydantic obligatoire) est strictement respecté.
- L'isolation : aucun changement schéma SQLAlchemy ni graph LangGraph.

**Defer** :
- Sanitisation XSS du nom extrait (responsabilité de l'escape Vue côté
  frontend, hors scope V8-AXE1).
- UX : signaler explicitement « regex a tenté de combler le champ
  manuellement édité » (futur travail UX).
- Étendre `COUNTRIES_UEMOA` aux pays CEDEAO (Ghana, Nigeria, Cap-Vert) —
  scope expansion, future story.

**Reject** :
- Fixtures `mock_db`/`mock_user_id` réputées non importées : faux, fournies
  par `tests/test_tools/conftest.py`.
- Few-shot pays/ville : exemple pédagogique intentionnel.
- Nits sur `logger.info extra=`, ordre `not text or not isinstance` —
  patterns projet existants.

## Design Notes

**Pourquoi LLM > regex en priorité ?** Le LLM peut désambiguïser (« je suis dans le solaire » → `sector="energie"` correct ; le regex match le mot « solaire » dans `SECTORS_FR["energie"]` mais le LLM peut aussi gérer des phrases comme « pas dans l'énergie » que le regex catégoriserait à tort). Le LLM est l'oracle ; le regex est la béquille.

**Pourquoi seuil ≥2 nulls et pas ≥1 ?** Avec 1 seul null, le LLM a probablement intentionnellement omis le champ (info non disponible). Avec ≥2 nulls sur un message structuré, c'est probablement un échec d'extraction massif comme observé V7.1-001. Évite les faux positifs.

**Pourquoi `last_user_message` plutôt qu'`InjectedState` ?** Plus simple, ciblé, évite de surcharger le payload state vers le tool. Pattern aligné avec `widget_response` déjà présent dans `configurable` (chat.py:181).

**Few-shot exemple canonique (à intégrer dans prompt + docstring) :**
```
User : "AgriVert Sarl, Agriculture, 15 employés, Sénégal"
→ update_company_profile(company_name="AgriVert Sarl", sector="agriculture",
                         employee_count=15, country="Sénégal")
```
(Note : champ `company_name`, pas `name` — alignement schéma Pydantic réel.)

## Verification

**Commands :**
- `cd backend && source venv/bin/activate && pytest tests/test_services/test_profile_extraction.py tests/test_tools/test_profiling_tools_extraction_fallback.py -v` -- expected : tous verts, ≥10 tests.
- `cd backend && source venv/bin/activate && pytest tests/ -q --ignore=tests/test_e2e` -- expected : aucune régression sur les ~935 tests existants.
- `ruff check backend/app/services/profile_extraction.py backend/app/graph/tools/profiling_tools.py backend/app/graph/nodes.py backend/app/api/chat.py` -- expected : 0 erreur.

**Manual checks (smoke ciblé V7.1-001) :**
- Lancer backend, créer compte test, poster en chat « AgriVert Sarl, Agriculture, 15 employés, Sénégal ».
- Vérifier `SELECT company_name, sector, employee_count, country, city FROM company_profiles WHERE user_id=…` : les 4 champs principaux (sauf city) doivent être renseignés en un seul appel tool.
- Inspecter `tool_call_logs` : un seul `update_company_profile` `status=success` (pas 4 retries).

## Suggested Review Order

**Logique de merge LLM/regex (cœur du fix)**

- Helper qui considère `None`/`""`/whitespace comme nul pour le seuil — base du fallback déclenché correctement.
  [`profiling_tools.py:36`](../../backend/app/graph/tools/profiling_tools.py#L36)

- Décision d'activation du fallback (≥ 2 nulls ET texte exploitable) — point de bascule LLM → regex.
  [`profiling_tools.py:128`](../../backend/app/graph/tools/profiling_tools.py#L128)

- Merge LLM > regex : ne comble que les trous, jamais d'écrasement.
  [`profiling_tools.py:139`](../../backend/app/graph/tools/profiling_tools.py#L139)

- Logging `regex_fallback_triggered` avec `user_id` tronqué (PII RGPD).
  [`profiling_tools.py:144`](../../backend/app/graph/tools/profiling_tools.py#L144)

**Extraction déterministe (regex)**

- Mapping secteurs → SectorEnum aligné (industrie/tourisme remappés sur autre/services).
  [`profile_extraction.py:31`](../../backend/app/services/profile_extraction.py#L31)

- Pays UEMOA, dict ordonné, normalisation accents en amont.
  [`profile_extraction.py:45`](../../backend/app/services/profile_extraction.py#L45)

- Pattern entreprise borné à 1-2 mots capitalisés + lookahead alphanum strict.
  [`profile_extraction.py:62`](../../backend/app/services/profile_extraction.py#L62)

- Pattern effectif borné `\d{1,5}` + lookbehind/lookahead `(?<!\d)`/`(?!\d)`.
  [`profile_extraction.py:73`](../../backend/app/services/profile_extraction.py#L73)

- Cap longueur input anti-DoS / ReDoS.
  [`profile_extraction.py:81`](../../backend/app/services/profile_extraction.py#L81)

**Câblage prompt et état**

- Few-shot 3 exemples injectés dans `_build_profiling_instructions` quand profil incomplet.
  [`nodes.py:441`](../../backend/app/graph/nodes.py#L441)

- Docstring tool enrichi avec mêmes exemples (vu par le LLM via tool schema).
  [`profiling_tools.py:55`](../../backend/app/graph/tools/profiling_tools.py#L55)

- `last_user_message` exposé via `RunnableConfig.configurable` au tool.
  [`chat.py:185`](../../backend/app/api/chat.py#L185)

**Tests**

- 4 cas critiques : LLM-PARTIEL, LLM-OK, texte vide, LLM > regex.
  [`test_profiling_tools_extraction_fallback.py:1`](../../backend/tests/test_tools/test_profiling_tools_extraction_fallback.py#L1)

- Scénario WHITESPACE-LLM (review MOYEN-1).
  [`test_profiling_tools_extraction_fallback.py:202`](../../backend/tests/test_tools/test_profiling_tools_extraction_fallback.py#L202)

- Garde-fou anti-régression : tous les secteurs canoniques sont membres de `SectorEnum`.
  [`test_profile_extraction.py:120`](../../backend/tests/test_services/test_profile_extraction.py#L120)

- Tests sécurité (DoS / ReDoS).
  [`test_profile_extraction.py:213`](../../backend/tests/test_services/test_profile_extraction.py#L213)
