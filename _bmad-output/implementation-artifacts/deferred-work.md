# Deferred Work

## Deferred from BUG-V5-003 ESG pillar validation runtime (2026-04-25)

- **DEF-BUG-V5-3-1 — Validation des bornes de `score` dans batch_save_esg_criteria** — Le tool persiste `score` tel quel ; un LLM aberrant peut envoyer -5, 100, `None`, `"7"`, `7.5` et corrompre `compute_overall_score`. Pré-existant au patch BUG-V5-003 mais surfacé par la review. **Path** : ajouter une validation Pydantic `int` 0≤score≤10 dans le schéma de tool, ou défensive dans `_validate_pillar_completeness`. Coût : 30 min. [backend/app/graph/tools/esg_tools.py]
- **DEF-BUG-V5-3-2 — Critère persisté avec score corrompu compté comme "complet"** — `_validate_pillar_completeness` utilise uniquement `evaluated_criteria` (présence du code) ; un E1 persisté avec `score=-1` passe la validation et fausse la finalisation. **Path** : croiser avec `criteria_scores` et exiger un score valide pour considérer le critère "complet". Coût : 30 min. [backend/app/graph/tools/esg_tools.py]
- **DEF-BUG-V5-3-3 — Race condition lecture/écriture sur `evaluated_criteria`** — Deux appels concurrents (réessais LLM, onglets parallèles) peuvent perdre des codes via last-write-wins au niveau ligne. **Path** : ajouter un verrou applicatif (`SELECT ... FOR UPDATE`) ou versioning optimiste sur ESGAssessment. Coût : 1-2 h. [backend/app/modules/esg/service.py]
- **DEF-BUG-V5-3-4 — `MAX_TOOL_CALLS_PER_TURN=5` peut bloquer une finalisation longue** — Si le LLM échoue 3 fois sur un pilier puis tente E+S+G dans le même tour, le 5e appel est coupé. **Path** : passer la limite à 8 ou logger un avertissement quand le quota est atteint dans un nœud ESG en `in_progress`. Coût : 15 min. [backend/app/graph/graph.py]
- **DEF-BUG-V5-3-5 — `current_pillar` basé sur `criteria[-1]` ignore les piliers mixtes** — Un appel multi-pilier finissant sur S marque `current_pillar=social` même si G n'est pas encore commencé. **Path** : déduire `current_pillar` du dernier pilier non encore terminé (ordre E→S→G). Coût : 15 min. [backend/app/graph/tools/esg_tools.py]
- **DEF-BUG-V5-3-6 — Pas de gestion explicite de `KeyError` sur clés manquantes du dict criterion** — Si le LLM omet `criterion_code`, `score` ou `justification`, `KeyError` est rejoué 3× par `with_retry` puis renvoyé brut au LLM. **Path** : valider la structure de chaque dict avant le helper et retourner un message d'erreur explicite. Coût : 20 min. [backend/app/graph/tools/esg_tools.py]
- **DEF-BUG-V5-3-7 — Pas de test verrouillant la cohérence prompt ↔ format d'erreur** — Le prompt ESG cite `ERREUR : pilier X incomplet (N/10)` ; si la chaîne change dans le tool, le LLM peut ne plus reconnaître le pattern. **Path** : ajouter un test golden qui vérifie que la chaîne d'erreur du tool est citée dans le prompt. Coût : 15 min. [backend/tests/test_prompts/]

## Deferred from BUG-V5-001/002 ESG finalize + chat scroll (2026-04-24)

- **DEF-BUG-V5-1 — Détection scroll utilisateur via `wheel`/`touchstart`/`pointerdown`** — Le flag `isProgrammaticScroll` (timer 1200ms) couvre la majorité des cas mais laisse une fenêtre où un scroll utilisateur authentique pendant l'animation smooth est ignoré. **Path** : ajouter listeners `wheel`/`touchstart`/`pointerdown` sur `messagesContainer` qui forcent `userScrolledUp=true` indépendamment du flag — distingue intent utilisateur réel vs scroll programmatique avec certitude. Coût estimé : 30 min. **Trigger** : feedback utilisateur sur perte de scroll user pendant streaming long. [frontend/app/components/copilot/FloatingChatWidget.vue]
- **DEF-BUG-V5-2 — Test runtime LLM-mock pour `esg_scoring_node`** — Les 4 tests V5 sont statiques (inspection source). Un test runtime mockant le LLM pour inspecter `chat_messages[0].content` (`SystemMessage`) et vérifier la présence de l'UUID concret renforcerait la garantie AC #1/#2. Nécessite mock async DB session + LLM. Coût estimé : 1h. **Trigger** : si une régression future invalide la chaîne de propagation `esg_assessment.assessment_id → state → prompt`. [backend/tests/test_graph/]
- **DEF-BUG-V5-3 — Listener `scrollend` event pour reset précis du flag** — Plus robuste que le timer 1200ms : `messagesContainer.addEventListener('scrollend', ...)` réinitialise `isProgrammaticScroll` exactement à la fin du scroll smooth. Support : Chrome 114+, Firefox 109+, Safari 17.6+ (à vérifier). Fallback timer toujours nécessaire pour vieux Safari. Coût estimé : 20 min. **Trigger** : compatibilité navigateurs cible confirmée stable sur `scrollend`. [frontend/app/components/copilot/FloatingChatWidget.vue]

## Deferred from BUG-V4-001/002 widget cycle + spinbutton (2026-04-24)

- **DEF-BUG-V4-1 — Fenêtre fixe `+ 1200` chars dans `test_esg_scoring_transition.py`** — Les tests `test_esg_prompt_transition_mentions_ask_interactive_question` et `test_esg_prompt_transition_forbids_text_only` scannent une sous-chaîne de 1200 caractères après « TRANSITION PILIER ». Fragile si la section grossit au-delà. **Path** : remplacer par un découpage sur la prochaine section `##` ou sur la fin de la séquence numérotée. Coût estimé : 10 min.
- **DEF-BUG-V4-2 — Couverture frontend du nouveau handler `interactive_question_resolved` dans `submitInteractiveAnswer` et du garde-fou `finally`** — Pas de test unitaire côté frontend (vitest/jest absent du harness actuel). **Path** : ajouter des tests vitest une fois le harness configuré ; ou test E2E Playwright couvrant la transition ESG E→S. Coût estimé : 1-2 h.

## Deferred from: BUG-011 fix — langue MiniMax (2026-04-23)

- **DEF-BUG-011-1 — `LANGUAGE_INSTRUCTION` absente des 6 builders spécialistes** — `build_esg_prompt`, `build_carbon_prompt`, `build_financing_prompt`, `build_credit_prompt`, `build_application_prompt`, `build_action_plan_prompt` n'incluent pas `LANGUAGE_INSTRUCTION`. MiniMax peut toujours répondre en chinois dans les modules spécialistes. Fix : prepend `LANGUAGE_INSTRUCTION` dans chaque builder (ou via `build_prompt` du registre). Hors scope BUG-011 par contrainte utilisateur (ne pas modifier les autres nœuds). Coût estimé : 30 min.

## Deferred from: code review of 10-17-ui-badge-tokens-semantiques (2026-04-22)

- **DEF-10.17-1 — `@ts-expect-error` non-spécifique dans Badge.test-d.ts** — Les 14 directives `@ts-expect-error` peuvent silencieusement catcher une erreur TS non-voulue (mauvais champ, narrowing différent). Migration recommandée vers `expectTypeOf<Bad>().not.toMatchTypeOf<BadgeProps>()` ou pattern TS 5.6+ `// @ts-expect-error description-matcher`. Amélioration méthodo transposable à Button/Input/Textarea/Select.test-d.ts. Coût estimé : 45 min (5 fichiers × ~10 assertions).
- **DEF-10.17-2 — AC7 seuil admin `dark:` pile 6 (marge 0)** — Badge.vue:100-104 contient exactement 6 `dark:` classes admin (3 states × 2 axes bg/text). Tout refactor factorisant `dark:bg-admin-*` et `dark:text-admin-*` dans un sélecteur arbitraire ferait chuter le count sous le plancher sans changer le rendu. Ajouter un test statique comptage `dark:` par famille dans `test_no_hex_hardcoded_badge.test.ts` (extension scope) ou fichier dédié. Coût estimé : 15 min.
- **DEF-10.17-3 — Documentation piège #27 : tests consommateurs `onMounted` slow-path `nextTick`** — Badge.vue:144-150 émet `console.warn` après `nextTick()` si label vide. Les tests consommateurs mesurant ce warn doivent `await flushPromises()` post-mount sinon faux négatifs non-déterministes. Ajouter piège #27 `ui-primitives.md` §5 avec snippet correct. Coût estimé : 10 min.

## Deferred from: story 10.16 (2026-04-22)

## Deferred from: code review of story-10.21 (2026-04-23)

Items tracés post code-review Story 10.21 `ui/EsgIcon.vue`. Pour contexte complet, voir `_bmad-output/implementation-artifacts/10-21-code-review-2026-04-23.md` + patches Option 0 Fix-All.

- **DEF-10.21-1 — Successeur DEF-10.15-1 Button spinner migration Lucide** — le spinner `Button.vue:145-160` reste un SVG inline `<svg class="animate-spin h-4 w-4"><circle opacity-25/><path opacity-75/></svg>` (style anneau tournant). Lucide `Loader2` rend un simple trait rotatif sans l'effet pulse opacity-25/75 composé. **Investigation 10.21 review M-5** : un wrapper `<span class="opacity-25"><EsgIcon name="loader" class="animate-spin h-4 w-4" /></span>` modifie l'opacity GLOBALE du SVG entier (pas le `<circle>` + `<path>` distinctement) → rendu dégradé visible. **Options Epic 11+** : (a) créer SVG custom `esg-button-spinner.svg` reproduisant circle opacity-25 + path opacity-75 — ajouter à registry `esg-*` prefix ; (b) introduire une prop Lucide `Loader2Compose` via wrapper dédié ; (c) accepter l'apparence Lucide standard dans un refactor design system global. **Trigger** : refonte spinner Button lors d'une story UI design system unifiée ou upgrade Lucide v1.x+ si compose natif. Impact fonctionnel 0 (animate-spin préservé, `prefers-reduced-motion` délégué `<style scoped>`). [frontend/app/components/ui/Button.vue:145-160]

- **DEF-10.21-2 — CI gate tree-shaking automatique (L31 §4octies)** — bundle delta Lucide mesuré 3.3 KB isolé post-10.21 mais risque régression silencieuse future si pattern d'import change (ex. `import * as Lucide`, `import Lucide from` default). **Path Epic 11+** : ajouter à `.github/workflows/ci.yml` step `rg "import \* as.*(lucide|lodash|date-fns|heroicons|react-icons)" frontend/app --count` → fail si > 0 + mesure bundle delta `du -sb storybook-static/assets/*.js` avec seuil 50 KB hard fail sur la PR. Coût 10 min. **Trigger** : sprint CI hardening. [frontend/ + .github/workflows/]

- **DEF-10.21-3 — Coverage thresholds Vitest enforced CI (L-4 10.21 review)** — `@vitest/coverage-v8` installé mais aucun script `test:coverage` ni `coverage.thresholds` dans `vitest.config.ts`. La couverture 100 % EsgIcon est mesurée narrativement, pas enforcée. **Path** : ajouter `coverage: { provider: 'v8', thresholds: { lines: 80, branches: 75, functions: 80, statements: 80 } }` + script `test:coverage`. **Trigger** : premier faux positif de régression coverage sur une story Epic 11+. Coût 15 min. [frontend/vitest.config.ts + package.json]

- **DEF-10.16-1 — Reka UI `SelectRoot` wrapper pour `ui/Select`** — L'Epic 10 AC5 prévoyait initialement un wrapper Reka UI `SelectRoot` stylé Tailwind pour `ui/Select.vue`. **Q3 Story 10.16 verrouillée** en faveur du `<select>` natif MVP car : (a) a11y système ChromeVox/VoiceOver battle-tested sans code custom, (b) 0 dépendance Reka UI ajoutée (Reka UI Combobox livré Story 10.19 pour le besoin typeahead/recherche qui justifie vraiment le portail), (c) touch target iOS picker wheel + Android bottom sheet natifs gratuits, (d) livraison M 1h30 préservée. **Cible reprise** : Phase Growth uniquement si besoin custom styling cross-browser uniforme (Firefox flèche native masquée ok mais pas de portail pour liste > viewport) OU feature avancée (grouping options avec `optgroup` stylé, virtualisation > 500 options). Coût estimé : 2-3 h.
- **DEF-10.16-2 — Remplacement stubs SVG inline par Lucide icons** — 3 composants (`Input.vue` : `AlertCircle` pour error / `Textarea.vue` : `AlertCircle` / `Select.vue` : `ChevronDown` + `AlertCircle`) utilisent aujourd'hui des SVG inline commentés `<!-- STUB: remplace par <LucideX /> Lucide Story 10.21 -->`. Une fois `lucide-vue-next` installé par Story 10.21 (`ui/EsgIcon.vue` + pile Lucide), remplacer mécaniquement les 4 SVG par les imports Lucide correspondants. **Traçage** : 4 locations identifiables via `rg 'STUB.*Lucide' frontend/app/components/ui/`. Coût estimé : 15 min.

## Deferred from: code review of story-10.14 (2026-04-21)

- **LOW-10.14-6 — CI `storybook:test` divergent du spec AC5** — [.github/workflows/storybook.yml:62-68] La CI lance `http-server` + `wait-on` + `test-storybook --url http://127.0.0.1:6006` alors que le spec AC5 prévoyait `test-storybook -- --ci --url file://…`. Le pattern `file://` crashe sur certaines ressources relatives Vite build, donc http-server est plus robuste. **Décision** : défer — modification > 15 min (documenter rationale, mettre à jour spec, valider CI sur PR test). **Cible drive-by** Story 10.15 quand ajout step CI `ui/Button`. Coût estimé : 15-20 min.
- **INFO-10.14-1 — Flaky pré-existant `useGuidedTour.resilience`** — [frontend/tests/composables/useGuidedTour.resilience.test.ts:362] Test « emits one message per skipped step when multiple steps are absent » échoue ~50% du temps (async timing). **Hors scope 10.14** (pré-existant Story 7.1). À traiter par une mini-story « stabilisation useGuidedTour » ou drive-by Epic 12 (UI). Filet : test ne bloque pas la CI car isolé dans sa suite.
- **INFO-10.14-2 — Pattern UX Patterns Dialog/Drawer/Popover capitalisé** — codemap `docs/CODEMAPS/storybook.md` §UX Patterns documente la règle de décision ARIA role selon bloquant/parallèle. Réutilisable Stories 10.15-10.21 (`ui/Dialog`, `ui/Drawer`, `ui/Popover`). Pas de travail déféré, juste trace méthodologique.

## Resolved in Story 10.14 code-review patches (2026-04-21)

- ✅ **HIGH-10.14-1 — Phantom dep `@storybook/test`** : déclaré explicitement dans `frontend/package.json:devDependencies` `^8.6.18`. Plus de dépendance transitive fragile via `@storybook/addon-interactions`.
- ✅ **HIGH-10.14-2 — `SourceCitationDrawer` role drawer complementary** : refactor de `DialogRoot`/`DialogContent` vers `<Teleport to="body"><aside role="complementary" aria-label="Sources documentaires">` avec `ScrollAreaRoot` Reka UI, bouton fermeture explicite, Escape key bonus (listener `document.keydown` opt-in, pas focus trap). Doc UX Patterns ajoutée codemap §UX Patterns. Stories mises à jour (`OpenWithLongContent`). 4 tests Vitest nouveaux (role assert, pas aria-modal, v-if closed, Escape émet close).
- ✅ **MEDIUM-10.14-1 — Tests rendu SignatureModal/SourceCitationDrawer dégradés** : assertions DOM réelles ajoutées (`document.body.querySelector('[role="dialog"]')` + `aria-modal`, `aria-labelledby`). 9 tests `test_each_component_renders` (vs 7).
- ✅ **MEDIUM-10.14-2 — Duplication tokens verdict ≡ brand** : Option B découplage. `verdict-pass/fail/reported` = Tailwind 600 (emerald-600 `#059669`, red-600 `#DC2626`, amber-600 `#D97706`), brand-* reste 500. Commentaire explicatif `main.css`. Rationale : un rebrand ne doit pas modifier la perception sémantique pass/fail. Scan `test_no_hex_hardcoded` toujours vert (tokens @theme only).
- ✅ **MEDIUM-10.14-3 — A11y runtime non prouvé localement** : couverture jest-axe étendue à SignatureModal + SourceCitationDrawer (6 tests a11y vs 4). `nextTick` ×2 après mount pour laisser Teleport matérialiser. 0 violation WCAG AA confirmée en Vitest + addon-a11y CI runtime.
- ✅ **MEDIUM-10.14-4 — CI sans tsc --noEmit stories** : step `Type-check Storybook stories` ajouté dans `.github/workflows/storybook.yml` avant `storybook:build`. TS strict AC2 enforcé sur `.storybook/**/*.ts` + stories.
- ✅ **MEDIUM-10.14-5 — Upgrade path reka-ui 3.0 non documenté** : section « Upgrade strategy » ajoutée `docs/CODEMAPS/storybook.md` avec table primitives utilisées × breaking à surveiller, procédure step-by-step upgrade Reka 3.0 + Storybook 9.
- ✅ **LOW-10.14-1 — Commentaire viteFinal `.storybook/main.ts`** : rationale pivot `@vitejs/plugin-vue` inline devant `viteFinal` + lien codemap §5.
- ✅ **LOW-10.14-2 — Hex hardcodés preview.ts backgrounds** : commentaires inline `// === var(--color-surface-bg)` et `// === var(--color-surface-dark-bg)` pour garantir synchro lors d'un rebrand (Storybook backgrounds n'évaluent pas les CSS vars dans l'iframe).
- ✅ **LOW-10.14-3 — `:disabled` + `:aria-disabled` redondant** : `SectionReviewCheckpoint.vue:112` — `:aria-disabled` retiré, `disabled` HTML natif suffit.
- ✅ **LOW-10.14-4 — Touch target `SgesBetaBanner` bouton** : `py-1` → `py-2 min-h-[44px]` pour respecter cible mobile WCAG.
- ✅ **LOW-10.14-5 — `aria-live` manquant `ImpactProjectionPanel` published** : ajouté `aria-live="polite"` sur bloc `role="status"` état publié pour annonce lecteur d'écran.

**Baseline frontend patches round 1** : tests gravity 23 → **26 passed** (+3 : 4 drawer tests - 1 remplacé). Full baseline `vitest --run` : 383 passed + 1 flaky pré-existant (`useGuidedTour.resilience`, INFO-10.14-1). Zéro régression sur 60 composants brownfield. Stories runtime : 37 + 1 (`OpenWithLongContent`) = 38.

## Deferred from: story 10.13 — dev-story discovery (2026-04-21)

- **HIGH-10.13-1 — Re-bench 5 tools canoniques Phase 1 post-Epic 13** — Le bench Story 10.13 Livrable B utilise 5 **proxies Phase 0** (Spec 005/006/008/011) car les tools canoniques (`query_cube_4d` cube 4D, `derive_verdicts_multi_ref` ESG 3 couches, `generate_formalization_plan` Aminata niveau 0 Copilot) ne sont pas livrés MVP. Cible Epic 13.X Phase 1. Re-bench à conduire quand les tools canoniques émergent pour confirmer/ajuster la recommandation provider primaire. Coût remédiation : ~3-4h (exécution bench 150 samples + rédaction report update).

- ✅ **HIGH-10.13-2 RÉSOLU 2026-04-21 (code review patch round 1)** — Migration `financing/service.py:170` + `financing/seed.py:851` vers `get_embedding_provider()` livrée. Nouvelle migration Alembic `032_add_financing_chunks_embedding_v2_voyage.py` ajoute `financing_chunks.embedding_vec_v2 Vector(1024)` + index HNSW v2 parallèle v1. Modèle ORM `FinancingChunk.embedding_vec_v2` exposé. `search_financing_chunks` lit désormais v2 (cohérent `document_chunks`). Scan règle 10.5 post-fix : 0 hit `OpenAIEmbeddings(` hors `app/core/embeddings/` (test `test_financing_service_uses_embedding_provider` enforce). Corpus RAG homogène Voyage en production.

- ✅ **MEDIUM-10.13-1 RÉSOLU 2026-04-21 (code review patch round 1)** — Shim `backend/app/graph/nodes.py::get_llm()` branché sur `get_llm_provider().get_chat_llm(streaming=True)` (pattern shim legacy 10.6, signature publique inchangée). Les 8 nœuds LangGraph consomment désormais l'abstraction `LLMProvider`. `LLMProvider.get_chat_llm` étendue avec flag `streaming` pour préserver le comportement historique. Tests : `test_get_llm_shim_delegates_to_provider`, `test_get_llm_shim_anthropic_when_configured`, `test_provider_streaming_toggle_isolated_instances`. AC10 effectivement tenu.

- **MEDIUM-10.13-2 — Migration 032 drop colonne v1 `embedding vector(1536)`** — Coexistence v1+v2 Q2 tranchée garantit rollback non-destructif. Post-validation qualité prod ≥ 3 mois, migration 032 dédiée droppera `embedding`, droppera `ix_document_chunks_embedding_hnsw`, renommera `embedding_vec_v2 → embedding`. Cible Story 20.X Phase 1. Coût : 30 min.

- **MEDIUM-10.13-3 — Exécution effective du bench 150 échantillons** — Story 10.13 Livrable B livre l'infrastructure bench mais **n'exécute pas** le bench live. Dev lead local doit faire tourner `BENCH_LLM_CHECK=1 + ANTHROPIC_API_KEY + OPENROUTER_API_KEY python scripts/bench_llm_providers.py` pour remplir les tables `_tbd_` de `docs/bench-llm-providers-phase0.md` §3-4 et hardcoder le winner dans `Settings.llm_provider` default. Cible Sprint 1 kickoff. Coût : 1h.

- **LOW-10.13-1 — Coverage `openai.py` 46 %** — chemins `_get_client()` lazy init + `aembed_documents` non-testés (nécessitent mock LangChain profond). Acceptable MVP (legacy fallback), à augmenter si openai.py devient plus utilisé. Cible opportuniste drive-by.

## Resolved in Story 10.13 code-review patches (2026-04-21)

- ✅ **CRITICAL-10.13-1 — Corpus golden 50 chunks + test durci** : `backend/tests/test_core/fixtures/embeddings_quality_corpus.json` complété à **50 chunks réels** (10 thèmes × 5 FR ESG + 5 EN EUDR multilingue). Les 5 queries EN EUDR pointent sur c-41..c-45 avec permutations d'ordre (test robustesse ranking). `test_corpus_structure_is_valid` durci : assert `len(chunks) == 50`, ids uniques, **chaque `expected_top5_chunk_ids` référence un chunk réel** (fail-fast désynchronisation). Pattern "corpus + expected_ids validation" documenté `docs/CODEMAPS/rag.md §6`.
- ✅ **HIGH-10.13-A — `bench-results.json` gitignored** : ajout `bench-results*.json` + `bench-report-*.json` + `/tmp/bench-*.json` dans `.gitignore` racine. Pas de fichier déjà committé (`git ls-files` vide).
- ✅ **HIGH-10.13-B — Modèle Anthropic Sonnet 4.6** : 5 locations updated de `claude-sonnet-4-20250514` (Sonnet 4.0 obsolète) vers `claude-sonnet-4-5-20251022` (Sonnet 4.6 GA 2025-10-22). `bench_constants.py` + `llm/provider.py` + `bench_llm_providers.py` + `config.py` + `.env.example`. Pricing URL sources + snapshot date ajoutées (MEDIUM-4).
- ✅ **HIGH-10.13-2 — Financing embeddings migrés Voyage** (cf. section précédente).
- ✅ **HIGH-10.13-C — Exceptions OpenAI vendor explicites** : `openai.py:86-116` catche désormais `openai.RateLimitError`, `APITimeoutError`, `APIConnectionError`, `APIError` par type. Substring match `"rate" in msg` supprimé. Test `test_no_generic_except_in_embeddings_module` durci `offenders == []`. 3 tests vendor ajoutés (`test_openai_provider_maps_{rate_limit,api_timeout,api_error}`).
- ✅ **MEDIUM-10.13-1 — get_llm shim branché** (cf. section précédente).
- ✅ **MEDIUM-10.13-2 (MEDIUM-2) — breaker key test** : `test_embedding_breaker_key_is_separate_from_tool_breakers` valide l'isolation des clés `(embedding, voyage)` vs `(tool_name, node_name)` LangGraph (scan défensif du registry tools/).
- ✅ **MEDIUM-10.13-3 (MEDIUM-3) — voyageai surface compat test** : `test_voyageai_sdk_surface_compat` vérifie présence `voyageai.Client`, `voyageai.AsyncClient` (optional), `voyageai.error.RateLimitError/APIError`. Fail-fast au prochain bump SDK.
- ✅ **MEDIUM-10.13-4 (MEDIUM-4) — Pricing URLs sources** : `PRICING_PER_1M_TOKENS` annoté par entrée avec URL officielle (anthropic.com/pricing, openrouter.ai/anthropic, openrouter.ai/minimax) + snapshot date + taux USD→EUR ECB.
- ✅ **MEDIUM-10.13-5 (MEDIUM-5) — Validator `anthropic_api_key`** : `Settings._validate_anthropic_api_key_when_selected` (model_validator) fail-fast boot si `llm_provider` ou `llm_fallback_provider` == `anthropic_direct` et clé absente ou format invalide (<40 chars ou pas `sk-ant-*`).
- ✅ **MEDIUM-10.13-6 (MEDIUM-6) — AC7 `tool_call_logs` partiel** : log structuré `metric=embedding_provider.embed` émis par `VoyageEmbeddingProvider.embed()` + `OpenAIEmbeddingProvider.embed()` (duration_ms + batch_size + provider + model + status). Persistence DB `tool_call_logs` réelle reste déférée (requiert `db` + `user_id` propagés — à Phase 1 via décorateur DB-aware).
- ✅ **LOW-10.13-2 — Migration 031 downgrade cosmétique** : commentaire documentant que `postgresql_with`/`_ops` sont ignorés par `drop_index` (symétrie visuelle seule).
- ✅ **LOW-10.13-3 — `fake_result` inutilisé supprimé** dans `test_voyage_embed_returns_1024_dim_vectors`.
- ⬜ **MEDIUM-10.13-3 (bench live exécution)** — reste déféré Sprint 1 kickoff (dev lead local avec API keys).
- ⬜ **LOW-10.13-1 (coverage openai.py 46%)** — reste déféré.

**Baseline patches round 1** : 1668 → **1678 passed** (+10), 1760 → **1770 collected** (+10). Zéro régression sur les 1668 baselinés.

## Deferred from: code review of story-10.12 (2026-04-21)

- **MEDIUM-10.12-4 — Signature `record_audit_event` typée Enum mais accepte `str` par duck-typing** — [backend/app/modules/admin_catalogue/service.py:122-158] La signature déclare `action: CatalogueActionEnum` / `workflow_level: WorkflowLevelEnum`, mais le body normalise `isinstance(...) else str(action)`. Fonctionnel mais divergence type hint / comportement. **Cible Epic 13 S1** : les premiers callers typés Enum trancheront entre (A) élargir signature publique à `CatalogueActionEnum | str`, (B) convertir `CatalogueActionEnum(action_str)` côté router et garder service typé Enum strict. Coût remédiation : 5-10 min.
- **LOW-10.12-1 — SlowAPI backend in-memory mono-worker MVP** — [backend/app/modules/admin_catalogue/audit_constants.py:94-99] Le marqueur `_RATE_LIMIT_BACKEND_PHASE_GROWTH_TODO` documente la limitation : multi-worker uvicorn verrait la limite effective × N workers. **Cible Epic 20.2 Phase Growth** : migrer vers Redis backend partagé (`Limiter(storage_uri="redis://...")`). Cohérent LOW-9.1-1 Story 9.1. Déclencheur : activation multi-worker uvicorn (`--workers N`) ou déploiement Kubernetes multi-pod.
- **LOW-10.12-2 — `and_(*clauses) if clauses else True` dupliqué 3×** — [backend/app/modules/admin_catalogue/router.py:388,474,534] Extraire helper `_apply_filters(stmt, clauses) -> Select`. Cosmétique, coût ~5 min. **Cible drive-by** lors de la prochaine modification de `admin_catalogue/router.py` (Epic 13.1+ wiring callers POST).
- **INFO-10.12-1 — Pattern pytest+FastAPI limiter override à capitaliser** — le workaround documenté Completion Notes 10.12 (injecter limiter via dépendance FastAPI overridable au lieu de monkeypatcher la constante résolue à l'import SlowAPI) est un piège récurrent. **Cible** : skill BMAD dédiée `test-fastapi-limiter-override` OU bullet dans un `docs/CODEMAPS/test-fastapi-patterns.md` futur. Candidat lors de la prochaine story 10.13+ touchant rate limiting.
- **INFO-10.12-6 — Index composite `(ts DESC, id DESC)` keyset dédié à observer** — [backend/alembic/versions/026_create_admin_catalogue_audit_trail.py] Migration 026 livre 3 index composites `entity_ts`, `actor_ts`, `level_ts`. Le keyset pur sans filtre `entity_type`/`actor` tombe sur tri + scan. Observer en prod quand `admin_catalogue_audit_trail` > 10k rows. **Cible Epic 20 Ops** si latence dégrade — ajouter `CREATE INDEX idx_catalogue_audit_ts_id_desc ON admin_catalogue_audit_trail (ts DESC, id DESC)`.

## Deferred from: code review of story-10.11 (2026-04-21)

- **INFO-10.11-3 — Extension Phase 1 Catalogue Annexe F** : `ANNEXE_F_SOURCES` seed 22 sources Phase 0 ≠ exhaustivité PRD §Annexe F. Manquent : BSCI / amfori, 8 conventions OIT individuelles (C29, 87, 98, 100, 105, 111, 138, 182), UN Global Compact, Charte RSE Sénégal, Plateforme RSE Côte d'Ivoire, Label CGECI, IFC Performance Standards PS1-PS8 séparément, EUDR Règlement UE 2023/1115, RSPO huile de palme, BCEAO textes officiels, UEMOA taxonomie verte. ~15-20 sources supplémentaires à tracer pour Epic 13 Story 13.8 (admin N3).
- **INFO-10.11-4 — AC8 spec obsolète** : spec écrit « baseline 1527 → cible ≥ 1537 » mais la baseline réelle était 1601 et le réalisé est 1633. Mettre à jour la spec 10.11 pour éviter confusion future (doc-only, pas de code à patcher).
- **INFO-10.11-5 — Mini-story activation nightly** : Task 11 smoke post-merge différée par design car nécessite secret `STAGING_DATABASE_URL_READ_ONLY` + user BDD `mefali_reader` provisionnés manuellement. Créer une mini-story dédiée « provisionner secret staging + smoke workflow_dispatch + vérifier issue GitHub créée correctement » avant d'activer le cron nocturne. Combiné à H2 résolu (fail-fast + rapport minimal), le risque de silent break est fortement mitigé.
- **LOW-10.11-10 — Rapport JSON : « première table gagne » sur dedup cross-table** : comportement documenté, acceptable Phase 0. Si plusieurs tables référencent la même URL (ex: `funds.source_url = intermediaries.source_url = https://foo`), le rapport indique une seule origine. Refactor vers `dict[url, list[table]]` quand un admin aura besoin de tracer l'usage multi-table.
- **LOW-10.11-11 — `max_redirects=3` configurable** : default 3 potentiellement trop bas pour sites à chain locale `www → https → /fr/ → /fr-fr/`. Configurable via `--max-redirects`, donc acceptable. Réévaluer après un mois d'observation des `redirect_excess` en production.
- **LOW-10.11-12 — `last_valid_at = None` si KO** : par design (rapport instantané, historique en BDD `sources.last_verified_at`). Documenter plus clairement dans CODEMAPS `source-tracking.md §3`.
- **LOW-10.11-15 — Downgrade migration 030 = `pass`** : choix défensif documenté (éviter de supprimer les sources ajoutées par admin N3 entre-temps). Non strictement réversible — à revoir si la table `sources` doit être rollback-clean pour tests d'intégration (typiquement jamais).
- **LOW-10.11-19 — `--dry-run` sur fixture factice** : la fixture `dry_run_fixture.json` contient 3 URLs `example.test/*`. Ajouter un `--dry-run-seed` qui utilise `ANNEXE_F_SOURCES` comme fixture implicite pour un smoke local plus réaliste (nice-to-have).
- **LOW-10.11-4 / 7 / 8 / 9 / 23, INFO-10.11-1 / 2 / 6** : defer, cosmetic ou acceptable par design (voir `10-11-code-review-2026-04-21.md` pour détails).

## Resolved in Story 10.11 drive-by (2026-04-21)

- ✅ **INFO-10.10-2 — Scan CI unicité writer = 2 hits attendu 1** : résolu par `backend/tests/test_core/test_outbox/test_writer_uniqueness.py` qui scanne `backend/app/**/*.py` via `Path.rglob` et **exclut explicitement** `app/models/domain_event.py` (le modèle ORM contient `__tablename__ = "domain_events"` légitimement). Assertion `hits in ([], [writer.py])` — strict 0 ou 1, jamais 2.
- ✅ **INFO-10.10-4 — `_SavepointRollbackSignal` non documenté** : résolu par ajout du bullet #13 dans `docs/CODEMAPS/outbox.md §5 Pièges` — référence le pattern correctif HIGH-10.10-1 et prévient qu'un futur dev retire cette exception interne (« semble inutilisée » mais c'est le seul mécanisme d'isolation SQL par event).
- ✅ **LOW-10.10-4 — Redondance filtre `status='pending'` + `processed_at IS NULL`** : conservation **documentée** (pas de suppression). Ajout bullet #12 `§5 Pièges` expliquant que la double condition est un garde-fou anti-régression défense-en-profondeur, pas une duplication à éliminer — si un futur terminal state oublie `processed_at = now()`, le filtre pending empêche le retraitement involontaire.

## Resolved in Story 10.10 code-review patches (2026-04-21)

- ✅ **HIGH-10.10-1 — Session partagée batch : `PendingRollbackError` si handler SQL raise après écriture partielle** : résolu par patch savepoint par event (`async with db.begin_nested():` + `_SavepointRollbackSignal` dans `backend/app/core/outbox/worker.py::_process_single_event`). Nouveau test E2E `test_worker_savepoint_isolates_handler_sql_failure` vérifie que l'écriture SQL partielle d'un handler en échec est rollback, et que les autres events du batch sont traités normalement. Absorbe pré-requis bloquant Epic 13 S1.
- ✅ **MEDIUM-10.10-1 — `BACKOFF_SCHEDULE[2]=600s` dead code** : résolu par correction check `retry_count > MAX_RETRIES` (était `>=`) + filtre query `retry_count <= MAX_RETRIES` (était `<`). Les 3 entrées `BACKOFF_SCHEDULE=(30,120,600)` sont maintenant utilisées successivement (retry 1/2/3) avec `MAX_RETRIES=3` → 3 retries + dead-letter sur 4ᵉ échec, aligné §D11 architecture. Assert module `len(BACKOFF_SCHEDULE) == MAX_RETRIES` comme invariant. Nouveau test `test_worker_uses_full_backoff_schedule_30_120_600`.
- ✅ **MEDIUM-10.10-2 — Purge `prefill_drafts` mono-batch** : résolu par refactor `purge_expired_prefill_drafts` en boucle `while` bornée (`MAX_PURGE_ITERATIONS=20` × batch 500 = 10 000 lignes/tick max). Ajout alerting `prefill_drafts_purge_backlog_high` si backlog > 10 000 + log `saturated=True` si cap itérations atteint.

## Resolved in Story 10.10 (2026-04-21)

- ✅ **MEDIUM-10.1-14 — `domain_events.next_retry_at` pour backoff exponentiel** : livré via migration `backend/alembic/versions/029_add_next_retry_at_to_domain_events.py` (colonne `TIMESTAMPTZ NULL` additive, down_revision `028_audit_tamper`). Le filtre `next_retry_at IS NULL OR next_retry_at <= now()` vit dans la query worker (pas dans le DDL de l'index — `now()` non-IMMUTABLE refusé par PostgreSQL). Logique applicative `BACKOFF_SCHEDULE = (30, 120, 600)` dans `backend/app/core/outbox/worker.py::_process_single_event`. Évite le hot-loop retry immédiat.
- ✅ **MEDIUM-10.1-5 — Purge `prefill_drafts` expirés** : livrée via 2ᵉ job APScheduler `purge_expired_prefill_drafts` (intervalle 1 h, batch 500, `DELETE ... WHERE expires_at < now()`) co-localisé dans `backend/app/core/outbox/worker.py`. Scheduler unique dans `lifespan` pour éviter 2 schedulers concurrents (anti-race).
- ⚠️ **LOW (nouvelle deferred) — Contrainte CHECK enum sur `domain_events.status`** : non ajoutée par 10.10 (Q3 tranchée — 4 valeurs `pending|processed|failed|unknown_handler` garanties par le code applicatif). À évaluer lors d'un drive-by sur la table `domain_events` ou Epic 20 Ops hardening (`ALTER TABLE domain_events ADD CONSTRAINT ck_domain_events_status CHECK (status IN (...))`). Risque : une valeur hors enum insérée par un bug applicatif resterait invisible au schéma. Mitigé par les tests unit `dispatch_event` + E2E postgres `test_worker_marks_failed/processed/unknown_handler`.

## Deferred from: code review of story-10.10 (2026-04-21)

- **MEDIUM-10.10-3 — Test `FOR UPDATE SKIP LOCKED` multi-process réel manquant** — [backend/tests/test_core/test_outbox/test_worker_e2e.py:88-128] Test actuel `test_worker_skip_locked_allows_concurrent_processing` utilise `asyncio.gather` : 2 coroutines **même event loop, même connection pool, même process**. Scénario prod (2 workers gunicorn × N replicas) non couvert — le pattern PostgreSQL reste correct par construction mais donne fausse confiance dans la couverture. **Remédiation** : test avec `multiprocessing.Pool` + 2 engines indépendants OU docker-compose 2 conteneurs FastAPI. **Cible Story 20.2 load testing** (Phase 0 benchmarks).
- **LOW-10.10-1 — `scheduler.shutdown(wait=True)` bloque event loop au shutdown** — [backend/app/core/outbox/worker.py:310-315] APScheduler `AsyncIOScheduler.shutdown()` est synchrone, bloque l'event loop pendant la finalisation des jobs (potentiellement plusieurs secondes). Acceptable MVP (moment unique, pas de trafic concurrent). **Cible Epic 20 Ops** si observé en prod. Alternative : `shutdown(wait=False)` + timeout observation via monitoring.
- **LOW-10.10-2 — `db=None` toléré dans tests `test_handlers.py`** — [backend/tests/test_core/test_outbox/test_handlers.py:74-108] Passe `db=None` à `dispatch_event`. Fonctionne car `noop_handler` / chemin `unknown_handler` ne touchent pas `db`, mais fragile si un test futur ajoute un handler SQL sans fournir de session. **Cible Epic 13 S1** (premier handler métier) : revoir les fixtures tests pour utiliser une vraie session systématiquement.
- **LOW-10.10-3 — `ck_domain_events_status CHECK status IN (...)` absent** — [backend/app/models/domain_event.py:72-74] Q3 tranchée (4 valeurs garanties côté code applicatif). Acceptable MVP, mitigé par tests unit + E2E. **Cible Epic 20 Ops hardening** (drive-by `domain_events`). Coût : migration additive + 1 ALTER TABLE.
- **LOW-10.10-4 — Redondance filtre `status == "pending"` + `processed_at IS NULL`** — [backend/app/core/outbox/worker.py:110-112] Les 4 états finaux (`processed` / `failed` / `unknown_handler`) mettent `processed_at` non-NULL. La clause `processed_at IS NULL` implique déjà `status == "pending"`. Défense en profondeur acceptable (coût négligeable). **Cible drive-by opportuniste** (retirer doublon OU conserver pour lisibilité défensive — à trancher Story 10.11).
- **LOW-10.10-5 — `purge_expired_prefill_drafts` raw SQL vs ORM `PrefillDraft`** — [backend/app/core/outbox/worker.py:253-263] Pas de modèle `PrefillDraft` ORM encore livré → raw `text()`. **Cible Epic 16 Story 16.5** (livraison copilot deep-link fallback qui introduira `app.models.prefill_draft.PrefillDraft`) : remplacer `text(...)` par `delete(PrefillDraft).where(...)`.
- **INFO-10.10-1 — `noop.test` handler en registry production** — [backend/app/core/outbox/handlers.py:82-118] Test-only documenté, acceptable MVP. **Cible Epic 20 Ops** : skip l'enregistrement si `settings.env_name == "prod"` (réduire surface). Coût : 2 lignes de garde.
- **INFO-10.10-2 — Scan CI unicité writer = 2 hits attendu 1** — `rg "INSERT INTO domain_events|DomainEvent\("` matche `writer.py` **et** `models/domain_event.py` (référence ORM via docstring). Scan CI devrait exclure `backend/app/models/*` pour 1 hit strict. **Cible drive-by Story 10.11** (ajouter `--glob '!backend/app/models/*'` dans le scan CI).
- **INFO-10.10-3 — AsyncIOScheduler vs APScheduler sync — choix justifié implicite** — [docs/CODEMAPS/outbox.md §1] choix dicté par stack async (AsyncSession, FastAPI lifespan). Documentation pourrait être explicitée (§1 ajouter 1 bullet « pourquoi async scheduler »). **Cosmétique**, cible prochaine itération outbox.md.
- **INFO-10.10-4 — `_SavepointRollbackSignal` exception interne non-propagée documentée** — [backend/app/core/outbox/worker.py] Pattern correctif HIGH-10.10-1. Ajouter un bullet dans outbox.md §5 Pièges référençant ce signal (évite qu'un dev futur le retire en pensant que c'est du mort). **Cible drive-by** après vérification tests verts.
- **INFO-10.10-5 — Alerting backlog purge via metric `prefill_drafts_purge_backlog_high`** — [backend/app/core/outbox/worker.py] Seuil 10 000 hardcodé. **Cible Epic 17 Story 17.5** (dashboard monitoring admin) : remonter le seuil en Settings Pydantic si besoin prod, créer panel dashboard « backlog purge ».

## Deferred from: code review of story-10.9 (2026-04-21)

- **LOW-10.9-1 — `FORBIDDEN` AC4 incomplète : absente `split-io`, `growthbook`, `flagsmith`, `statsig`, `posthog`, `devcycle`** — le `frozenset` actuel couvre 8 noms (flipper-client/flipper/unleash-client/unleash/launchdarkly-server-sdk/launchdarkly-api/gitlab-feature-flag/configcat-client) mais omet des librairies feature-flag courantes 2025-2026. Risque faible (Clarification 5 défense en profondeur affaiblie) mais dérive possible par `pip install opportuniste`. **Remédiation** : élargir à 12-14 noms OU scanner `dist.metadata["Summary"]` pour mots-clés `"feature flag"/"feature toggle"/"feature gate"` (détection par description). **Drive-by opportuniste** sur la prochaine story touchant `feature_flags.py` OU `test_feature_flags.py`. [backend/tests/test_core/test_feature_flags.py:119-130 + _bmad-output/implementation-artifacts/10-9-code-review-2026-04-21.md#low-10.9-1]
- **LOW-10.9-2 — Regex `^def check_project_model_enabled\b` manque re-définitions indentées (nested/class method)** — l'ancre `^` ne match que les définitions module-level (colonne 0). Une re-définition en méthode de classe ou nested ne serait pas détectée par `test_no_duplicate_check_project_model_enabled_definition`. Risque très faible (anti-pattern évident en review). **Remédiation** : passer à `^\s*def check_project_model_enabled\b` (tolère indentation). Correction triviale 1 caractère. **Drive-by** sur prochaine modification de `test_feature_flags.py`. [backend/tests/test_core/test_feature_flags.py:207 + _bmad-output/implementation-artifacts/10-9-code-review-2026-04-21.md#low-10.9-2]
- **LOW-10.9-3 — Coercion Pydantic `ENABLE_PROJECT_MODEL="garbage"` → `ValidationError` non testée en CI** — l'AC2 clause 2 mentionne « Pydantic coerce garbage → erreur de boot explicite » mais cette assertion n'est vérifiée **que manuellement** (Task 4.2). Si Pydantic v2 change son comportement de coercion bool dans une montée mineure (v2.11 → v2.12), la régression ne serait pas détectée. **Remédiation** : ajouter `test_settings_rejects_garbage_bool_value(monkeypatch)` avec `pytest.raises(ValidationError)` (6 lignes). **Candidat hardening Epic 20** (ou patch batch LOW si opportunité). [backend/tests/test_core/test_feature_flags.py + _bmad-output/implementation-artifacts/10-9-code-review-2026-04-21.md#low-10.9-3]
- **LOW-10.9-4 — Naming `Settings.enable_project_model` trompeur (pas de signal « informationnel »)** — le nom de champ suggère qu'il doit être consommé au runtime, mais Q1 tranche qu'il est informationnel. Mitigations actives : (a) test enforcement `test_no_applicative_caller_reads_settings_enable_project_model` scan 0 hit, (b) commentaire bloc config.py:105-111, (c) Field description explicite. Friction DX résiduelle. **Options** : renommer `enable_project_model_informational_do_not_read` (trop verbeux) OU ajouter `ClassVar` marker OU ligne commentaire `# NOTE: informational only — use app.core.feature_flags.is_project_model_enabled() at runtime` au-dessus direct du field (visible survol IDE). **Cosmétique**, mitigé par test enforcement. [backend/app/core/config.py:112-119 + _bmad-output/implementation-artifacts/10-9-code-review-2026-04-21.md#low-10.9-4]

## Deferred from: code review of story-10.5 (2026-04-20)

- **LOW-10.5-1 — Bypass SUPERUSER PG sur REVOKE + triggers non documenté** — un compte PostgreSQL avec attribut `SUPERUSER` ou propriétaire de table peut désactiver les triggers tamper-proof via `ALTER TABLE admin_access_audit DISABLE TRIGGER ...` et bypasser le `REVOKE UPDATE, DELETE FROM PUBLIC`. Mitigation : accès SUPERUSER réservé ops/DBA ; rôle `app_user` NOINHERIT pour tous les services applicatifs. **Documenté** dans `docs/CODEMAPS/security-rls.md §6` (Limitations connues #5 + note §5.2). À encadrer dans **runbook incident_response** Epic 20 Ops (ségrégation credentials + audit accès SUPERUSER via pg_log / Cloud SQL audit). [docs/CODEMAPS/security-rls.md §6]
- **LOW-10.5-2 — REVOKE `UPDATE/DELETE` sur `admin_access_audit` non testé isolément** — les 6 tests `test_audit_tamper_proof.py` reposent sur un `sync_engine` connecté en superuser de migration où le REVOKE PUBLIC n'a aucun effet ; seul le trigger bloque. Si demain quelqu'un retire le `CREATE TRIGGER` en laissant le REVOKE, les 6 tests passeraient faussement (en superuser, REVOKE sans trigger = pas de blocage). Gap de défense en profondeur, risque régressif spécifique très faible. Ajouter `test_revoke_blocks_non_superuser_update` (SET LOCAL ROLE app_user + UPDATE → "permission denied" AVANT trigger) lors d'une future story security hardening (candidat Epic 20). [backend/tests/test_security/test_audit_tamper_proof.py]
- **LOW-10.5-3 — `ERRCODE = '42501'` (insufficient_privilege) sémantiquement ambigu** — le code SQLSTATE `42501` est émis par notre trigger PL/pgSQL alors qu'il signifie normalement « privilège insuffisant » (ex. REVOKE non-superuser). Un observateur SIEM pourrait confondre les deux signaux. Alternative envisageable : `'P0001'` (raise_exception générique) ou code custom classe `XX`/préfixe `ME` (Mefali). À arbitrer Epic 20 Ops avec l'équipe SRE (coût : rebuild migration 028 OU migration complémentaire + mise à jour assertions tests). [backend/alembic/versions/028_tamper_proof_audit_tables.py:53-54]
- **LOW-10.5-4 — `conn.execute(text("RESET ROLE"))` redondant ligne 245 test_rls_enforcement.py** — `SET LOCAL ROLE app_user` est automatiquement réinitialisé à la fin de la transaction par PostgreSQL. La ligne explicite `RESET ROLE` obscurcit la lecture — un reviewer futur pourrait la croire nécessaire. Gain purement cosmétique, à supprimer lors du prochain drive-by sur ce fichier. [backend/tests/test_security/test_rls_enforcement.py:245]
- **LOW-10.5-5 — `apply_rls_context` : 2 `set_config` séparés au lieu d'un seul** — cas pathologique théorique : si la 1ʳᵉ query réussit et la 2ᵉ échoue (perte réseau transient), la session reste dans `(user_id=<valide>, role=<stale>)`. Risque effectif très faible (transience + chemin non-authentifié simultanés). Optimisation : 1 seul `SELECT set_config(...), set_config(...)` (1 roundtrip au lieu de 2, + atomicité garantie). À appliquer lors d'un prochain drive-by sur `app/core/rls.py` — pas de changement sémantique. [backend/app/core/rls.py:131-138]
- **INFO-10.5-1 — `register_admin_access_listener(engine)` ne consomme pas `engine`** — le paramètre est conservé pour cohérence API architecture §D7 mais non utilisé (le listener est attaché sur la classe `AsyncSession.sync_session_class`, pas sur l'engine). Pattern voulu (1 seul appel au startup suffit). À documenter plus clairement dans la docstring ou renommer en `register_admin_access_listener(_: AsyncEngine | Engine | None = None)` pour signaler l'absence d'effet. [backend/app/core/admin_audit_listener.py:94-107]
- **INFO-10.5-2 — Aucune couverture ORM pour `facts`** — le modèle métier de la table `facts` (Couche 1 ESG 3 layers, migration 022) n'est pas encore livré (déféré à Epic 13). Le listener `before_flush` filtre par `__tablename__ in RLS_TABLE_NAMES` donc il couvrirait le modèle le jour où il sera ajouté ; en attendant, les tests E2E listener (`test_admin_audit_listener.py`) utilisent un ORM `_FactForTest` local isolé dans un `DeclarativeBase` de test. Quand Epic 13 livrera `app.models.fact.Fact`, remplacer l'ORM local du test par l'import de production. [backend/tests/test_security/test_admin_audit_listener.py + Epic 13]
- **INFO-10.5-3 — `security-rls.md` dépasse AC7 (8 sections vs 6 prescrites)** — la doc livre 8 sections (ajout « Fichiers clés » + « Incidents type ») contre 6 prescrites par l'AC7. Extension bénéfique (pas d'item à défer). [docs/CODEMAPS/security-rls.md]

## Deferred from: code review of story-10.4 (2026-04-20)

- **LOW-10.4-1 — Pattern `status_code=201` + raise 501** — `backend/app/modules/admin_catalogue/router.py:72-121` déclare `status_code=201` sur les 4 POST stubs (criteria, referentials, packs, rules) mais raise 501 tant qu'Epic 13 n'est pas livré. Conservation volontaire (pattern 10.2 INFO-10.2-1 + 10.3 LOW-10.3-1). Epic 13.1/13.2/13.3/13.1bis livreront les 201 effectifs avec `CriterionResponse`/`ReferentialResponse`/`PackResponse`/`CriterionDerivationRuleResponse`. [_bmad-output/implementation-artifacts/10-4-code-review-2026-04-20.md#low-10.4-1]
- **LOW-10.4-2 — Endpoints POST typés `-> dict` jamais retournent dict** — les 4 endpoints POST annotent `-> dict` mais leur seul chemin d'exécution est `raise HTTPException(501)`. Harmoniser vers `-> CriterionResponse | None` (intention future) ou `-> None` lors de la livraison Epic 13. Cosmétique. [_bmad-output/implementation-artifacts/10-4-code-review-2026-04-20.md#low-10.4-2]
- **LOW-10.4-3 — Import `admin_catalogue_router` hors ordre alphabétique dans `main.py`** — [backend/app/main.py:106-125] — l'import et l'`include_router` sont placés entre `maturity_router` et `reports_router` (Cluster A → A' → admin_catalogue → reports) plutôt qu'en ordre alpha strict. Conservation volontaire, pas d'impact runtime (préfixes disjoints). [_bmad-output/implementation-artifacts/10-4-code-review-2026-04-20.md#low-10.4-3]
- **LOW-10.4-4 — `_is_admin_mefali_email` parse env var à chaque appel** — `backend/app/modules/admin_catalogue/dependencies.py:22-30` lit + parse `ADMIN_MEFALI_EMAILS` à chaque requête admin. Micro-perf négligeable MVP (~µs, volume admin Mefali faible). Un cache module-level est **interdit** pour permettre `monkeypatch.setenv`. Résolu naturellement Epic 18 avec `User.role` + MFA FR61 (colonne BDD indexée). [_bmad-output/implementation-artifacts/10-4-code-review-2026-04-20.md#low-10.4-4]

## Deferred from: code review of story-10.3 (2026-04-20)

- **LOW-10.3-1 — Pattern `status_code=201` + raise 501** — `backend/app/modules/maturity/router.py:45-55` déclare `status_code=201` sur `POST /declare` mais raise 501 tant qu'Epic 12 n'est pas livré. Conservation volontaire (pattern 10.2 INFO-10.2-1). Epic 12.1 livrera le 201 effectif avec `FormalizationPlanResponse`. [_bmad-output/implementation-artifacts/10-3-code-review-2026-04-20.md#low-10.3-1]
- **LOW-10.3-2 — Import `maturity_router` hors ordre alphabétique dans `main.py`** — [backend/app/main.py:106-122] — l'import et l'`include_router` sont placés entre `projects_router` et `reports_router` (Cluster A → A' → reports) plutôt qu'en ordre alpha strict. Conservation volontaire, pas d'impact runtime (préfixes disjoints). [_bmad-output/implementation-artifacts/10-3-code-review-2026-04-20.md#low-10.3-2]
- **LOW-10.3-4 — Exposition future `country` en logs Epic 12.3** — quand Epic 12.3 `FormalizationPlanCalculator.generate(country: str)` sera livré, le `country` sera journalisé dans `tool_call_logs.tool_args`. Pas de risque PII (pays = public), mais à noter pour Epic 12.3 review. [_bmad-output/implementation-artifacts/10-3-code-review-2026-04-20.md#low-10.3-4]
- **Test `test_module_route_flags_coherence.py` (hérité 10.2)** — dette défensive restée ouverte depuis review 10.2 (option A « test de cohérence `_MODULE_ROUTE_FLAGS` ↔ nodes tool-loop »). Les 2 TODO `_MODULE_ROUTE_FLAGS` + `module_labels` documentent la dette pour **Epic 11 S1** (project) et **Epic 12 S1** (maturity). Implémentation conjointe lorsque l'un des deux routings sera activé. [_bmad-output/implementation-artifacts/10-3-code-review-2026-04-20.md#info-10.3-9]
- **Capitalisation pattern NFR66 country-data-driven** — le scan `assert_no_country_literals` a fait ses preuves dès la première itération 10.3 (détection `"Senegal"` dans docstring `service.py`). À extraire en helper `backend/tests/test_architecture/helpers.py::assert_no_country_literals(path, banned_list)` OU en skill BMAD `country-data-driven-scan` pour Epic 12.3, Story 10.11 (sourcing Annexe F) et futures extensions CEDEAO. [_bmad-output/implementation-artifacts/10-3-code-review-2026-04-20.md#info-10.3-10]
- **Déplacer `test_events_module_exposes_event_types`** — le test de présence des 3 constantes `events.py` est actuellement dans `backend/tests/test_maturity/test_service.py:65-77`. Cosmétique (hérité pattern 10.2 identique). À déplacer vers un `test_events.py` dédié lors de la prochaine drive-by (appliquer aussi à 10.2 pour cohérence). [_bmad-output/implementation-artifacts/10-3-code-review-2026-04-20.md#info-10.3-14]

## Deferred from: code review of story-10.2 (2026-04-20)

- **MEDIUM-10.2-1 — Migration Cluster A : `CompanyProfile` → `Company`** — les deux modèles coexistent temporairement : `app.models.company.CompanyProfile` (table `company_profiles`, spec 003 MVP) + `app.modules.projects.models.Company` (table `companies`, squelette Cluster A Story 10.2). **Story 11-1** migrera les usages métier MVP vers `Company` (relations, services, validations complètes). **Story 20.1** dépréciera `CompanyProfile` en fin de Phase 0. Docstring de traçabilité posée dans `backend/app/modules/projects/models.py::Company` (2026-04-20 patch). [_bmad-output/implementation-artifacts/10-2-code-review-2026-04-20.md#medium-10.2-1]
- **MEDIUM-10.2-2 — Checklist 4 points cohérence `_MODULE_ROUTE_FLAGS` ↔ `project_node`** — Epic 11 S1 doit activer 4 points avant d'activer le routing projet, sous peine de trap latent (classification LLM avec libellé brut `"project"`, routing introuvable) :
  1. Ajouter `"project": "_route_project"` dans `_MODULE_ROUTE_FLAGS` (`backend/app/graph/nodes.py:166-173`).
  2. Ajouter `"project": "Module projet"` dans `module_labels` (`backend/app/graph/nodes.py:181-190`).
  3. Ajouter `_route_project` dans `_route_after_router` (`backend/app/graph/graph.py`).
  4. Ajouter `"project"` dans le `conditional_edges` dict de `router` (`backend/app/graph/graph.py`).
  TODO explicite posé au-dessus des 2 dicts concernés (2026-04-20 patch). [_bmad-output/implementation-artifacts/10-2-code-review-2026-04-20.md#medium-10.2-2]
- **LOW-10.2-1 — Renommage `state` → `initial_status` dans tool `create_project`** — le nommage `state` dans la signature du tool est confusable avec `ConversationState` LangGraph. À renommer `initial_status` (aligné avec `service.create_project(status=...)`) **lors de Epic 11 Story 11-1** au moment de la vraie implémentation. [backend/app/graph/tools/projects_tools.py:24-28]
- **LOW-10.2-2 — Coercion `"idée"` → `ProjectStatusEnum.idea` + tests variantes orthographiques** — le tool accepte `state="idée"` (français accentué) alors que l'enum attend `"idea"` (anglais). Epic 11 devra gérer les variantes `"idéation"`, `"idee"`, `"en projet"`, etc. ou changer la signature pour accepter l'enum directement. À traiter **Epic 11 Story 11-1**. [backend/app/graph/tools/projects_tools.py:26 + backend/app/modules/projects/enums.py:15]
- **LOW-10.2-3 — Test `flag OFF + no auth` défensif** — vérifier que l'ordre `Depends(get_current_user)` → `Depends(check_project_model_enabled)` renvoie 401 (pas 404) même quand `ENABLE_PROJECT_MODEL=false`. Non bloquant (comportement garanti par l'ordre de résolution FastAPI), mais test 5 lignes précieux comme garde-fou. À ajouter **Story 10.9** (wrapper feature flag complet). [backend/tests/test_projects/test_router.py:58-68]
- **LOW-10.2-4 — Coordination allowlist `_TOOL_ARGS_BLACKLIST` ↔ tools projects Epic 11** — le blacklist actuel (`common.py:_TOOL_ARGS_BLACKLIST`) est trop permissif et logge `name`/`state` en clair. Quand Epic 11 ajoutera `description: str | None` (texte libre utilisateur, potentiellement nom projet confidentiel ou coordonnées bancaires), coordonner avec Story 9.7 M1 (blacklist/allowlist) **avant** d'ajouter des tools manipulant du texte libre > 50 chars. [backend/app/graph/tools/common.py:_TOOL_ARGS_BLACKLIST + 10-2-code-review-2026-04-20.md#low-10.2-4]
- **LOW-10.2-6 — Test `test_migration_enum_values_match_python_enum`** — ajouter un test défensif qui compare les strings hardcodées dans `sa.Enum(...)` de la migration 020 avec les valeurs de `ProjectStatusEnum` / `ProjectRoleEnum`. Évite qu'un refactor futur (`idea → ideation`) casse la cohérence migration ↔ enum sans alerte. À ajouter lors du prochain drive-by sur `backend/tests/test_projects/test_models.py`. [backend/alembic/versions/020_create_projects_schema.py:84-94 ↔ backend/app/modules/projects/enums.py:12-19]

## Deferred from: story-10.1 migrations Alembic 020-027 (2026-04-20)

- **Cleanup feature flag `ENABLE_PROJECT_MODEL`** (arbitrage Q1) — déplacé vers **Story 20.1** : retrait code applicatif uniquement (pas de migration Alembic supplémentaire). La migration 027 reste dédiée à `domain_events` + `prefill_drafts` (micro-Outbox D11). [_bmad-output/planning-artifacts/epics/epic-10.md#story-101]
- **Load test `REFRESH MATERIALIZED VIEW CONCURRENTLY` sur `mv_fund_matching_cube`** (arbitrage Q4) — reporté **Story 20.4** benchmark Phase 0. La vue est créée ici, le benchmark p95 ≤ 2 s sera mesuré sous charge réaliste avec des données seedées. [backend/alembic/versions/022_create_esg_3_layers.py]
- **Modèles SQLAlchemy ORM pour les 30+ nouvelles tables** — livrés en parallèle par **Stories 10.2** (`projects`), **10.3** (`maturity`), **10.4** (`admin_catalogue`). Story 10.1 livre uniquement le schéma SQL — les tests CRUD utilisent raw SQL. [backend/app/models/]
- ✅ **RÉSOLU Story 10.5 (2026-04-20)** — **Event listener SQLAlchemy pour `admin_access_audit`** : livré via `backend/app/core/admin_audit_listener.py` (pattern `before_flush` sur `AsyncSession.sync_session_class`, enregistré au startup dans `main.py::lifespan`). Voir section `## Resolved in Story 10.5` ci-dessous.
- **Worker APScheduler `domain_events` + purge `prefill_drafts`** — livré **Story 10.10** : consommation outbox via `FOR UPDATE SKIP LOCKED` 30 s + nettoyage `prefill_drafts.expires_at < now()`. Infra prête ici. [backend/alembic/versions/027_create_outbox_and_prefill_drafts.py]

## Deferred from: code review of story-10.1 (2026-04-20)

- ✅ **RÉSOLU Story 10.5 (2026-04-20)** — **HIGH-10.1-11 — Audit tables tamper-proofing (D6/D7)** : livré via migration `backend/alembic/versions/028_tamper_proof_audit_tables.py` (`REVOKE UPDATE, DELETE ... FROM PUBLIC` + fonction `audit_table_is_immutable()` + 2 triggers `BEFORE UPDATE OR DELETE` sur `admin_access_audit` et `admin_catalogue_audit_trail`). 6 tests d'attaque validant que UPDATE/DELETE → `ProgrammingError: audit table is immutable (D6/D7)`. Voir section `## Resolved in Story 10.5` ci-dessous.
- **MEDIUM-10.1-6 — Refresh policy `mv_fund_matching_cube`** — à trancher **Story 10.10** (worker APScheduler qui lancera également `REFRESH MATERIALIZED VIEW CONCURRENTLY mv_fund_matching_cube` sur événement `fund.updated`/`intermediary.updated` consommé via domain_events). Sans ce worker, la MV reste stale après le seed initial. [backend/alembic/versions/022_create_esg_3_layers.py:354]
- **MEDIUM-10.1-7 — FR44 NO BYPASS codes hardcodés** — remplacer la CHECK constraint `ck_no_bypass_human_review` (liste `('sges_beta','esia','stakeholder_engagement_plan')` inline) par une table de référence `high_risk_section_codes(code UNIQUE)` + trigger BEFORE INSERT/UPDATE sur `reusable_sections` qui force `human_review_required=true`. Prévu **Story 10.4** (module admin_catalogue) ou **Story 15.x** (moteur livrables). [backend/alembic/versions/023_create_deliverables_engine.py:107]
- **MEDIUM-10.1-8 — Timestamps manquants** (`created_at`/`updated_at` absents de `project_role_permissions`, `criterion_referential_map`, `referential_versions`, `atomic_blocks`) — cohérence D6 audit. Ajouter dans une migration dédiée lors de la livraison des modèles ORM (Stories 10.2/10.3/15.x). Non bloquant MVP.
- **MEDIUM-10.1-13 — Garde-fou backfill `fund_applications.project_id`** — ajouter un check pré-`SET NOT NULL` qui lève une `RuntimeError` explicite si des lignes restent NULL (cas user_id orphelin). À intégrer dans la prochaine révision de 020 ou via script pré-upgrade `backend/scripts/preflight_020_backfill.py`. [backend/alembic/versions/020_create_projects_schema.py:328]
- **MEDIUM-10.1-14 — `domain_events.next_retry_at` pour backoff exponentiel** — ajouter une colonne `next_retry_at TIMESTAMPTZ NULL` + adapter `idx_domain_events_pending` pour `WHERE processed_at IS NULL AND retry_count < 5 AND (next_retry_at IS NULL OR next_retry_at <= now())`. Livré **Story 10.10** (worker APScheduler) en même temps que la logique de backoff applicative. Sans ce champ, le worker actuel ne peut faire qu'un retry immédiat → risque de hot-loop. [backend/alembic/versions/027_create_outbox_and_prefill_drafts.py:44]
- **MEDIUM-10.1-15 — Mermaid erDiagram : liens audit→tables** — ajouter dans `docs/CODEMAPS/data-model-extension.md` des annotations visuelles reliant `admin_access_audit.table_accessed` aux 4 tables RLS. Cosmétique, à faire lors de la prochaine itération documentation.
- **LOW-10.1-10 — `funds.sectors_eligible` type `json` vs `jsonb`** — la colonne legacy (008_financing) est `sa.JSON()` → `json` natif. L'index GIN du MV utilise un cast `::jsonb` qui fonctionne mais n'est pas optimal. Migration future `ALTER TABLE funds ALTER COLUMN sectors_eligible TYPE jsonb USING sectors_eligible::jsonb` — prévu **Story 20.4** (load test cube 4D). [backend/alembic/versions/022_create_esg_3_layers.py:378]
- **LOW-10.1-16 — Runbook 6 rollback Alembic 🟡 squelette** — compléter avec smoke-tests précis, template message users, drill annotation. Prochaine itération documentation (pas d'échéance dure, Story Growth ops). [docs/runbooks/README.md#6-rollback-migration-alembic-nfr32-trimestriel]

## Deferred from: story-planning of 9-7-observabilite-with-retry-log-tool-call (2026-04-19)

- **AC4 dimensions stockées dans `tool_args` JSONB au lieu de colonnes séparées** — Story 9.7 AC4 livre `_input_size_bytes` / `_output_size_bytes` via clés JSON dans `tool_args` et `tool_result` pour éviter une migration Alembic dédiée dans le scope. Workaround accepté MVP mais complexifie les queries Prometheus futures (JSON extract sur JSONB au lieu de colonnes indexées) quand Story 17.5 dashboard monitoring admin arrivera. **Migration dédiée différée Phase Growth** : ajouter colonnes `tool_call_logs.input_size_bytes INTEGER` + `output_size_bytes INTEGER` indexables pour queries agrégées rapides. [backend/app/graph/tools/common.py:log_tool_call + backend/app/models/tool_call_log.py]
- **Circuit breaker seuil 10 erreurs 5xx consécutives** — cohérent NFR75 architecture mais potentiellement tardif en pratique (les 9 premières erreurs 5xx remontent brutes aux users avant ouverture du breaker). À surveiller en prod post-Phase 0 : si volume d'erreurs observées avant ouverture breaker impacte UX, ajuster NFR75 à seuil plus bas (5 ou 7 erreurs). [architecture.md §NFR75]

## Deferred from: code review of story-9.6 (2026-04-19)

- `date.today()` non-déterministe dans `_validate_due_date` — injection de temps demande refacto plus large (clock abstraction globale). [backend/app/core/llm_guards.py:_validate_due_date]
- `MAX_ACTION_COUNT=20` vs prompt action_plan existant « 10-15 actions » — contradiction d'instructions au LLM, demande édition du prompt base hors scope 9.6. [backend/app/prompts/action_plan.py]
- `HTTPException(500)` opaque côté utilisateur — message générique sans contexte guard, amélioration UX non critique à traiter dans une story dédiée gestion des erreurs guards. [backend/app/core/llm_guards.py:run_guarded_llm_call]
- `prompt_hash` sur 200 premiers chars produit collisions cross-user — design choice documenté dans spec AC9 (PII avoidance) ; amélioration future via hash intégral après scrub PII. [backend/app/core/llm_guards.py:prompt_hash]
- `assert_numeric_coherence` branche `/10` utilise la même tolérance que `/100` — edge case de conversion d'échelle asymétrique, demande design dédié (tolérance relative vs absolue). [backend/app/core/llm_guards.py:assert_numeric_coherence]

## Resolved in Story 10.5 (2026-04-20)

### Fix livré

- **HIGH-10.1-11 — Audit tables tamper-proofing (D6/D7)** — migration additive `backend/alembic/versions/028_tamper_proof_audit_tables.py` (revision `028_audit_tamper`, `down_revision = "027_outbox_prefill"`) :
  - `REVOKE UPDATE, DELETE ON admin_access_audit FROM PUBLIC`
  - `REVOKE UPDATE, DELETE ON admin_catalogue_audit_trail FROM PUBLIC`
  - Fonction PL/pgSQL partagée `audit_table_is_immutable()` qui `RAISE EXCEPTION 'audit table is immutable (D6/D7)'` avec `ERRCODE = '42501'` (insufficient_privilege).
  - 2 triggers `BEFORE UPDATE OR DELETE` : `trg_admin_access_audit_immutable` + `trg_admin_catalogue_audit_trail_immutable` (idempotents via `DO $$ IF NOT EXISTS ... END $$`).
  - `downgrade()` restaure : `DROP TRIGGER` + `DROP FUNCTION` + `GRANT UPDATE, DELETE ... TO PUBLIC` (cohérence NFR32 drill rollback trimestriel).
- **INSERT reste autorisé** sur les 2 tables (nécessaire pour l'event listener admin_audit_listener + catalogue audit trail Story 10.4). Seuls UPDATE/DELETE sont bloqués.
- **6 tests d'attaque** dans `backend/tests/test_security/test_audit_tamper_proof.py` (`@pytest.mark.postgres`) : INSERT ok + UPDATE ProgrammingError + DELETE ProgrammingError × 2 tables.

- **Event listener SQLAlchemy `admin_access_audit`** — fichier `backend/app/core/admin_audit_listener.py` (~150 lignes) avec :
  - `register_admin_access_listener(engine)` enregistré au startup dans `backend/app/main.py::lifespan`.
  - Listener `before_flush` attaché sur `AsyncSession.sync_session_class` qui inspecte `session.new | session.dirty | session.deleted` et insère une ligne `admin_access_audit` pour chaque objet muté parmi les 4 tables sensibles (`companies`, `fund_applications`, `facts`, `documents`) si le contexte session est admin.
  - Anti-récursion via filtre table (skip `admin_access_audit` + `admin_catalogue_audit_trail`) + flag `session.info[_SESSION_AUDIT_FLAG]`.
  - Atomicité : l'INSERT audit partage la transaction métier (rollback cohérent).
  - Limitation SELECT documentée (déférée Story 18.x).

- **Couche applicative RLS** — fichier `backend/app/core/rls.py` (~130 lignes) :
  - `apply_rls_context(db, user)` : positionne `app.current_user_id` + `app.user_role` via `set_config(..., false)` avec bind params.
  - `reset_rls_context(db)` : appelé dans `get_db::finally` pour éviter fuite cross-requête via pool asyncpg.
  - `resolve_user_role(user)` : réutilise `_is_admin_mefali_email` (Story 10.4) + nouvelle whitelist `ADMIN_SUPER_EMAILS` (fail-closed).
  - `ADMIN_ROLES = frozenset({"admin_mefali", "admin_super"})` (source unique).
  - Intégration dans `backend/app/api/deps.py::get_current_user` (appel automatique post-auth) + `backend/app/core/database.py::get_db` (reset en finally).

### Fichiers livrés

**Créations (9)** :
- `backend/app/core/rls.py`
- `backend/app/core/admin_audit_listener.py`
- `backend/alembic/versions/028_tamper_proof_audit_tables.py`
- `backend/tests/test_security/test_resolve_user_role.py` (7 tests, unit)
- `backend/tests/test_security/test_rls_pool_reuse.py` (3 tests, PG)
- `backend/tests/test_security/test_rls_enforcement.py` (16 tests, PG, matrice 4×4)
- `backend/tests/test_security/test_audit_tamper_proof.py` (6 tests, PG)
- `docs/CODEMAPS/security-rls.md`
- `_bmad-output/implementation-artifacts/10-5-rls-postgresql-4-tables-sensibles.md` (story spec)

**Modifications (5)** :
- `backend/app/core/database.py` (ajout `try/finally` + `reset_rls_context` dans get_db)
- `backend/app/api/deps.py` (appel `apply_rls_context(db, user)` post-auth)
- `backend/app/main.py` (import + appel `register_admin_access_listener(engine)` au lifespan startup)
- `backend/.env.example` (section « Admin Whitelists » avec `ADMIN_MEFALI_EMAILS=` + `ADMIN_SUPER_EMAILS=`)
- `docs/runbooks/README.md` (référence `docs/CODEMAPS/security-rls.md`)

### Tests

- **Baseline pré-10.5** : 1331 passed + 35 skipped.
- **Baseline post-10.5 (sans PG)** : 1338 passed + 60 skipped (+7 tests `resolve_user_role` verts, +25 tests PG skippés — 16 matrice + 3 pool + 6 tamper).
- **Delta total** : +32 tests collectés dans `backend/tests/test_security/` (6 → 38).
- **Zéro régression** sur les 1331 tests pré-existants.

### Scopes déférés (non bloquants)

- **SELECT admin non capturés** par le listener `before_flush` — déféré Story 18.x si besoin concret émerge. Mitigation MVP : un admin qui exfiltre doit persister (INSERT audité).
- **Rôle `auditor` effectif** (lecture cross-tenant read-only) — Epic 18 avec FR61 (colonne `User.role` + MFA step-up).
- **Whitelist email transitoire** — remplacée par `User.role` Epic 18.

---

## Resolved (2026-04-19) — Story 9.6 : guards LLM persistes documents bailleurs (P1 #10)

### Fix livré

- **Reference audit** : [spec-audits/index.md §P1 #10](./spec-audits/index.md) + [PRD §Risque 10](../planning-artifacts/prd.md) + [PRD §SC-T8](../planning-artifacts/prd.md)
- **Module partagé `backend/app/core/llm_guards.py`** (~440 lignes) — exception unifiée `LLMGuardError(code, target, details)` + 4 free-text guards (`assert_length`, `assert_language_fr`, `assert_no_forbidden_vocabulary`, `assert_numeric_coherence`) + schéma Pydantic strict `ActionPlanItemLLMSchema` (`extra="forbid"` + enums + bornes) + `validate_action_plan_schema` (min 5, max 20 actions) + orchestrateur `run_guarded_llm_call` (retry unique + HTTPException 500) + télémétrie `log_guard_failure` (metric `llm_guard_failure`) + `prompt_hash` (SHA-256[:16] pour audit sans PII).
- **Surface 1 — Résumé exécutif ESG** : `backend/app/modules/reports/service.py:63` refacto avec 4 guards séquentiels (length → langue FR → vocab interdit → cohérence numérique) + retry unique prompt renforcé + param `user_id: str | None`.
- **Surface 2 — Plan d'action JSON** : `backend/app/modules/action_plan/service.py:171` refacto avec schéma Pydantic strict (6 catégories enum, 3 priorités enum, coût ≤ 10 Md FCFA, due_date bornée `MAX_TIMEFRAME_MONTHS + 90j`) + bornes 5-20 actions + retry unique + défense en profondeur via `_safe_*` helpers avec log `pydantic_drift`.
- **Fiche de préparation financing** : **hors scope 9.6** — aucun LLM actuellement (100 % Jinja2 template). Point d'ancrage documenté pour story future P3.
- **43 nouveaux tests** : 37 unitaires `test_core/test_llm_guards.py` (19 free-text + 15 JSON schema + 3 Pydantic direct) + 3 intégration pipeline résumé exécutif + 3 intégration pipeline plan d'action. Coverage `app/core/llm_guards.py` = **99 %** (≥ 90 % seuil PRD).
- **Zéro régression** : 1159 tests backend verts (184 s < 200 s plafond). Adaptation de 3 fixtures `test_action_plan/test_service.py` existantes (passage de 4/1/1 actions à 5 actions pour respecter `MIN_ACTION_COUNT`).

### Scopes renvoyés à stories futures

- **FR40** (signature électronique utilisateur obligatoire avant export bailleur) — story future P1.
- **FR41** (blocage export > 50 000 USD tant que revue section par section non cochée) — story future P1.
- **FR44** (SGES/ESMS BETA NO BYPASS — revue humaine obligatoire) — story future.
- **FR55** (dashboard admin_mefali monitoring `metric=llm_guard_failure`) — story future P1 Phase 0 infra.
- **FR56** (alerting automatique Sentry/alert manager sur échecs guards) — story future Phase Growth.
- **Guards LLM sur chat live non persisté** (9 nœuds LangGraph) — P2/P3 à évaluer.
- **Test contenu PDF bout-en-bout** (P2 #20 audit : parser PDF WeasyPrint généré) — P2 séparé.
- **Pydantic strict narratifs applications** (spec 009, surface `"application_narrative"`) — hors scope.
- **`langdetect` / `spaCy`** — décision post-déploiement. T11 vérifié : `langdetect` ABSENT de `requirements.txt` → heuristique stopwords conservée seule.
- **Tuning des bornes** — constantes exposées (`MIN_SUMMARY_LEN`, `MAX_SUMMARY_LEN`, `MIN_ACTION_COUNT`, `MAX_ACTION_COUNT`, `MAX_COST_XOF`, `FORBIDDEN_VOCAB`, `VALID_CATEGORIES`, `VALID_PRIORITIES`).
- **Anti-prompt injection dans champs utilisateurs passés au LLM** (NFR9 PRD) — story future sécurité.

### Fichiers modifiés (résumé)

- `backend/app/core/llm_guards.py` (nouveau, ~440 lignes)
- `backend/app/modules/reports/service.py` (refacto `generate_executive_summary` + call-site)
- `backend/app/modules/action_plan/service.py` (refacto `generate_action_plan` + logs drift dans `_safe_*`)
- `backend/tests/test_core/__init__.py` (nouveau, vide)
- `backend/tests/test_core/test_llm_guards.py` (nouveau, 37 tests)
- `backend/tests/test_report_guards.py` (nouveau, 3 tests intégration)
- `backend/tests/test_action_plan/test_service.py` (3 fixtures adaptées + classe `TestActionPlanGuardsIntegration` avec 3 tests)
- `_bmad-output/implementation-artifacts/spec-audits/index.md` (marqueur résolu P1 #10)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (transition `in-progress` puis `review`)

### Commit fix

- Voir `git log` sur la branche `main` (date 2026-04-19) — `<short-sha>` à ajouter au commit de clôture.

---

## Deferred from: code review of story-9.5 (2026-04-18)

- **Race condition concurrent manual PATCH vs LLM tool call** — `backend/app/modules/company/service.py:192-244` : pas de `SELECT ... FOR UPDATE`, pas de version column, pas de `MutableList.as_mutable()`. Pattern pré-existant à tout le backend, pas aggravé par 9.5. Story future P2 "Locking optimiste sur CompanyProfile".
- **Tool LLM ne commit pas explicitement** — `backend/app/graph/tools/profiling_tools.py:82-128` : le node LangGraph parent gère la transaction. Pattern pré-existant ; audit séparé nécessaire pour valider que les 9 nodes commit après chaque tool_call.
- **Pas de test automatisé round-trip upgrade/downgrade/upgrade pour la migration 019** — `backend/alembic/versions/019_add_manually_edited_fields_to_company_profiles.py` : T12 validé manuellement, pattern identique aux migrations 001-018. Story infra future.
- **Pas de test E2E SSE `profile_skipped` bout-en-bout** — `backend/tests/test_tools/test_profiling_tools.py` : tests unitaires couvrent la logique service/tool ; SSE forward est 3 lignes de code. Rattachable à l'épic 8 (tests E2E parcours).
- **Payload SSE `current_value` exposé au frontend** — `backend/app/api/chat.py:258-272` : valeur du user pour son propre profil (authentifié), pas une fuite cross-user. Acceptable V1, à revoir si la plateforme devient multi-tenant/multi-collaborateur par profil.
- **Pas de schéma Pydantic/TypedDict pour payloads SSE `profile_*`** — `backend/app/api/chat.py:258-272` : refactor architectural qui toucherait toute la couche SSE (profile_update / profile_completion / profile_skipped / interactive_question / etc.), hors scope 9.5.
- **Legacy row NULL possible si l'invariant `server_default='[]'` a été bypassé** — `backend/app/modules/company/service.py:239-246` : risque très faible (server default couvre tous les INSERT ORM + DDL) ; défensif `or []` partout aux reads. One-shot UPDATE disponible dans la spec Dev Notes §"Si le backfill est nécessaire (rare)".
- **Aucun plafonnement rate sur le nouveau path SSE `profile_skipped`** — `backend/app/api/chat.py:258-267` : couvert globalement par le rate limiting chat de la story 9.1. À ré-évaluer si des abus ciblés apparaissent.
- **Type frontend `manually_edited_fields: string[]` vs usage défensif `?.includes`** — `frontend/app/types/company.ts` + `frontend/app/components/profile/ProfileForm.vue:95,117` : code défensif tolère stale cache Pinia, peut être durci plus tard en rendant le type `string[] | undefined` ou en garantissant le hydrate.
- **`getattr(profile, field)` sans default tolérerait un drift `UPDATABLE_FIELDS` vs modèle** — `backend/app/modules/company/service.py:200` : contraint par synchronisation explicite dans le même module. Ajouter un test de cohérence `UPDATABLE_FIELDS ⊆ CompanyProfile.__table__.columns` serait une belle défense en profondeur.
- **PATCH manuel avec body vide retourne 200 (no-op silencieux)** — `backend/app/modules/company/router.py` : pré-existant à 9.5. À corriger avec un 400 ou 422 si l'UX remonte de la confusion.
- **Ordering formel entre events SSE `profile_update` / `profile_skipped` / `profile_completion`** — `backend/app/api/chat.py:258-267` : contrat implicite actuel (ordre d'émission dans la boucle). À formaliser si le frontend les consomme et qu'une race pose problème.
- **Fixture `user_id` partagée + 7 emails différents dans `TestManualEdit`** — `backend/tests/test_company_service.py` : pattern pré-existant dans le module. Factory pytest dédiée à introduire dans un chantier refactoring tests.
- **Couplage test/prod via `sorted(manually_edited_fields)`** — `backend/app/modules/company/service.py:240` : stabilité acceptable vu la taille bornée (max 17 champs) ; commentaire « ordre stable pour les tests » à réévaluer — remplacer par comparaison sur sets ou introduire un ordering métier serait plus propre à long terme.
- **Pas d'API de retrait de flag manuel (« revert to AI »)** — confirmé hors scope §2 story 9.5 ; créer une story P3 si besoin produit remonté (UI pour réinitialiser les champs individuellement).

---

## Resolved (2026-04-18) — Story 9.5 : flag `manually_edited_fields` sur CompanyProfile (P1 #7)

### Fix livré

- **Reference audit** : [spec-audits/index.md §P1 #7](./spec-audits/index.md) + [spec-audits/spec-003-audit.md §3.6](./spec-audits/spec-003-audit.md)
- **Colonne JSONB** `manually_edited_fields: list[str]` ajoutée sur `company_profiles` via migration Alembic `019_manual_edits` (default `'[]'` non-NULL, rétro-compatibilité AC4 sans backfill).
- **Paramètre `source: Literal["manual", "llm"]`** sur `update_profile(db, profile, updates, source)` — retour 3-uplet `(profile, changed_fields, skipped_fields)`. Le chemin LLM skippe les champs déjà marqués manuels avec `logger.warning(...)`.
- **Event SSE `profile_skipped`** (marker `__sse_profile__` étendu avec `skipped_fields`) + whitelist `backend/app/api/chat.py` mise à jour.
- **Badge frontend `✎ manuel`** sur `ProfileField.vue` (dark mode complet), binding `:is-manually-edited` dans `ProfileForm.vue`.
- **9 nouveaux tests backend** (7 `TestManualEdit` service + 2 `TestManualEditAPI` incluant un test anti-tampering). Zero régression.

### Audit historique T0 — non exécuté

La table `tool_call_logs` existe (migration `54432e29b7f3`) mais son instrumentation actuelle ne trace pas le **champ** visé par chaque appel `update_company_profile` — uniquement le nom du tool et les arguments agrégés. Sans cette granularité, identifier les écrasements suspects « après édition manuelle » nécessiterait un cross-join avec les access logs HTTP `PATCH /profile` indisponibles en BDD actuelle.

**À reprendre** une fois la dette P1 #14 (instrumentation complète `tool_call_logs`) traitée. Non bloquant : la protection à partir du 2026-04-18 est effective pour tous les nouveaux cas.

### Fichiers modifiés (résumé)

- `backend/alembic/versions/019_add_manually_edited_fields_to_company_profiles.py` (nouveau)
- `backend/app/models/company.py`, `backend/app/modules/company/{service,router,schemas}.py`
- `backend/app/graph/tools/profiling_tools.py`, `backend/app/api/chat.py`
- `backend/tests/test_company_service.py`, `backend/tests/test_company_api.py`, `backend/tests/test_tools/test_profiling_tools.py`
- `frontend/app/types/company.ts`, `frontend/app/components/profile/{ProfileField,ProfileForm}.vue`
- `_bmad-output/implementation-artifacts/spec-audits/index.md` (marqueur résolu P1 #7)

### Commit fix

- Voir `git log` sur la branche `main` (date 2026-04-18) — `<short-sha>` à ajouter au commit de clôture.

---

## Deferred from: code review of 9-4-ocr-bilingue-fr-eng-documents-anglophones (2026-04-18, second pass)

Items nouveaux identifiés lors d'une **deuxième passe** `bmad-code-review` le 2026-04-18 (Blind + Edge Case + Acceptance Auditor indépendants de la 1ʳᵉ passe). La majorité des findings sont déjà couverts par la section 1ʳᵉ passe ci-dessous ; seuls les items inédits sont listés ici.

- **`SystemExit` / `BaseException` non attrapés par `except Exception` du lifespan OCR** [backend/app/main.py:66-72] — si une future version de pytesseract lance `SystemExit` (hypothétique mais documenté dans son code source pour certaines erreurs de version Tesseract < 3.05), le worker Uvicorn crashe au startup au lieu de logger un WARNING non bloquant. Action : à traiter avec le narrowing `except` déjà déféré en 1ʳᵉ passe, en ajoutant explicitement `(Exception, SystemExit)` ou en gardant `BaseException` uniquement ciblé sur le bloc OCR.
- **`pytesseract.get_languages()` invoque `subprocess.run` sans `timeout=`** — distinct du « bloquant event loop async » déjà listé : ici, risque de **hang infini** au startup si le binaire tesseract bloque (disque saturé, traineddata corrompue, init lent NFS). Action : wrapper `asyncio.wait_for(asyncio.to_thread(get_languages), timeout=5.0)` pour borner le startup.
- **Placeholder `<short-sha>` dans `deferred-work.md:55`** — bien annoté « (a ajouter apres commit) » mais dépend d'une action opérateur hors diff ; à substituer au commit de clôture story (non bloquant, traçable).
- **`set(pytesseract.get_languages(config=""))` plante si `get_languages` retourne `None`** — cas des wrappers pytesseract forkés (Tesseract-ARM custom, certains builds Alpine). `TypeError` absorbée par `except Exception` avec message trompeur « Tesseract introuvable » alors que le binaire fonctionne. Hypothétique mais zéro coût à guarder (`languages = set(get_languages(config="") or [])`).
- **`pytesseract.image_to_string` sans `timeout=` dans `service.py:270-278` → DoS potentiel** — un attaquant upload un PDF scanné de plusieurs centaines de pages, l'OCR séquentiel bloque un worker pendant plusieurs minutes. Hors scope 9.4 (service.py intouché par la story), mais opportunité manquée — story sécurité/Ops dédiée à ouvrir.
- **`.strip()` asymétrique entre branches PDF et image de `_extract_text_ocr`** [backend/app/modules/documents/service.py:274,278] — branche image : `image_to_string(img).strip()` ; branche PDF : `"\n".join(text_parts).strip()` (chaque `text_parts[i]` conserve son whitespace). Un PDF avec page blanche produit `"\n\n\n"` là où une image blanche produit `""`. Pré-existant, hors scope 9.4.
- **Pas de `logger.debug("OCR lang=... file=...")` dans `service.py`** — impossible en prod de distinguer « lang bien `fra+eng` mais `eng.traineddata` absent » vs « lang downgradé silencieusement ». Combiné au `except Exception` qui wrap en `ValueError` opaque (ligne 285), perte totale d'observabilité per-requête. Hors scope 9.4 (service.py intouché), amélioration observabilité.

---

## Deferred from: code review of 9-4-ocr-bilingue-fr-eng-documents-anglophones (2026-04-18)

Items différés suite à la revue adversariale 3-couches du 2026-04-18 (Blind Hunter + Edge Case Hunter + Acceptance Auditor). Ces items sont réels mais pré-existants à 9.4 ou hors périmètre ; ils ne bloquent pas la fermeture de la story.

- **AC7 temps d'exécution global 390 s > 200 s** — pré-existant, delta 185→390 s accumulé entre 9.3 et 9.4, indépendant du scope OCR. Action : story P3 future — profiler les tests lents et isoler en `@pytest.mark.slow`.
- **YAML `last_updated: '2026-04-17' (Story ...)` non parseable** — pattern pré-existant (même forme pour 9.1–9.3). Action : normaliser en un seul commit (déplacer le commentaire sur une ligne `#` dédiée).
- **Branche PDF de `_extract_text_ocr` (`pdf2image.convert_from_path`) jamais testée** — les 4 tests 9.4 couvrent uniquement la branche image directe (`PIL.Image.open`). Action : ajouter 2 tests PDF à une story future pour fermer la couverture.
- **`pytesseract.get_languages()` bloquant l'event loop async au startup** — acceptable pour un check one-shot, mais théoriquement à wrapper via `asyncio.to_thread` si profilage montre un impact sur le healthcheck Docker.
- **Lifespan duplication sur multi-workers (Gunicorn/Uvicorn)** — log WARNING émis N fois (1 par worker). Non bloquant mais peut polluer les logs prod. Action : gate par `app.state.ocr_checked` lors de la prochaine intervention sur le lifespan.
- **Aucun test unitaire n'invoque `lifespan` pour vérifier l'émission du WARNING** — le bloc OCR de `main.py` est uniquement validé par smoke-test local. Action : ajouter `test_lifespan_warns_when_eng_missing` avec `caplog` dans `tests/test_main_lifespan.py` (à créer).
- **Docker build validation absente** : pas de test ARM64 vs x86_64, pas d'épinglage de version `tesseract-ocr-eng`, pas d'invalidation de cache layer, pas de `tesseract --list-langs | grep -q eng` post-install. Action : story Ops dédiée à la CI/CD.
- **TESSDATA_PREFIX non validé/logué au startup** — si la variable d'env est absente ou incorrecte, `get_languages()` renvoie [] silencieusement. Action : logger explicitement la valeur au startup (ops concern).
- ~~**Assertion `len(found) >= 2` dans `test_ocr_english_document_extracts_keywords` permet silencieusement 4 mots-clés manquants sur 6**~~ — ✅ **RÉSOLU 2026-04-18 par code-review 2ᵉ passe** : assertion renforcée à `len(found) >= 4` (marge de 2 mots-clés sur 6).
- **`.strip()` (probable) du résultat de `image_to_string` non testé** — edge case whitespace non couvert, refactor silencieux possible.
- **Aucun test ne simule `pytesseract.image_to_string` levant `TesseractError`** — le wrap `try/except` de `service.py:285` n'est jamais exercé par la suite. Action : ajouter `test_ocr_tesseract_error_wrapped_as_value_error`.
- **Edge cases `get_languages` non gérés** : liste vide (binaire OK, aucune traineddata), `'osd'` seul (Tesseract sans langue réelle), variantes locales `_old`/`_best` (filtrage préfixe requis), versions pytesseract < 0.3.7 sans `get_languages` (AttributeError absorbée par `except Exception` générique, message trompeur). Action : durcir le check startup avec des branches ciblées.
- **`pytesseract` absent en CI runner** → ajouter `pytest.importorskip("pytesseract")` en tête de `TestOCRBilingual` pour un skip propre au lieu d'une erreur d'import.
- **Story P3 future : `TestOCRBilingualIntegration @pytest.mark.integration`** — vraies fixtures PNG/PDF (1 FR rapport ESG signé, 1 EN GCF Funding Proposal, 1 mixte RFP partiellement traduit), exécution Tesseract réelle en CI nightly avec container Docker contenant `fra+eng` installés. Les tests unitaires actuels (classe `TestOCRBilingual`) verrouillent le contrat ; ceux d'intégration valideraient la capacité réelle de Tesseract à extraire les mots-clés. Résolution decision 2/2 choix 4b code-review 9.4.
- **`except Exception as exc` trop large au startup OCR [backend/app/main.py:66-72]** — le narrowing proposé (catcher spécifiquement `pytesseract.TesseractNotFoundError`, `FileNotFoundError`, `PermissionError`) a été différé du batch 9.4 : risque de laisser passer silencieusement `TypeError`/`AttributeError` sur incompatibilité de version pytesseract < 0.3.7 (alors que l'un des buts du check startup est justement de rendre visible ce type de problème d'env). Action : traiter avec des tests lifespan dédiés (`tests/test_main_lifespan.py` — cf. item « Aucun test unitaire n'invoque `lifespan` » ci-dessus) qui permettent de valider chaque branche d'erreur avant de narrow le except. Hors scope 9.4.

---

## Resolved (2026-04-17) — Story 9.4 : OCR bilingue FR+EN pour documents de bailleurs anglophones

### Ecart audit / realite — faux positif partiel du spec 004 §3.6

- **Constat audit** : spec-004-audit.md §3.6 supposait `pytesseract` configure en `lang='fra'` uniquement (hypothese : _« pytesseract configure **probablement** en `fra` »_).
- **Realite code** : `grep "lang=" backend/app/modules/documents/service.py` confirme `lang="fra+eng"` depuis le commit initial du module (`86ece82 Feature 004 — Document Upload & Analysis`). Le code a **toujours** ete bilingue.
- **Lecon methodo** : un audit par lecture de la spec sans verification du code produit des faux positifs. Ajouter systematiquement une passe `grep` sur le repo avant de classer une dette.

### Vrais manques operationnels corriges par 9.4

- **Dockerfile.prod incoherent** : installait `tesseract-ocr-fra` mais pas `tesseract-ocr-eng`. En prod, `pytesseract.image_to_string(img, lang="fra+eng")` levait `TesseractError: Error opening data file eng.traineddata` sur tout document anglophone, transforme en `ValueError` opaque par le try/except du service. **Fix : ajout de `tesseract-ocr-eng` a la liste `apt-get install` + commentaire bilingue actualise.**
- **Pas de check startup** : l'absence de `eng.traineddata` n'etait detectee qu'au premier upload, avec un message d'erreur non actionnable. **Fix : validation `pytesseract.get_languages()` dans le `lifespan` FastAPI (app/main.py), log WARNING explicite si `fra` ou `eng` manque (non bloquant pour garder la DX en dev).**
- **Pas de test de contrat bilingue** : les tests OCR existants mockaient `_extract_text_ocr` ou `pytesseract.image_to_string` sans asserter sur `kwargs["lang"]`. Un refactor revertant a `lang="fra"` passait la CI. **Fix : nouvelle classe `TestOCRBilingual` (4 tests) qui verrouille le contrat (assertion `kwargs["lang"] == "fra+eng"` + regression FR + extraction EN + extraction mixte FR+EN).**

### Fichiers modifies

- `backend/Dockerfile.prod` (ligne 8 commentaire + ajout `tesseract-ocr-eng`) — +2 lignes nettes.
- `backend/app/main.py` (lifespan : ~33 lignes de check OCR non bloquant apres init LangGraph).
- `backend/tests/test_document_extraction.py` (nouvelle classe `TestOCRBilingual`, ~115 lignes / 4 tests).
- `_bmad-output/implementation-artifacts/deferred-work.md` (cette section).
- `_bmad-output/implementation-artifacts/spec-audits/index.md` (marqueur `Resolu par story 9.4` sous §P1 #8).

### Validation post-fix

- `pytest tests/test_document_extraction.py::TestOCRBilingual -v` → 4/4 verts (0.19 s).
- `pytest tests/test_document_extraction.py -v` → 11/11 verts (1.12 s), zero regression sur les 4 classes existantes.
- Smoke-test lifespan : `asyncio.run(lifespan(app))` logue `INFO: Tesseract OCR : langues fra+eng disponibles` sur poste local — startup check fonctionnel.
- Negative-control : simulation `lang="fra"` declenche bien l'assertion de contrat → regression detectable.
- `grep "lang=" backend/app/modules/documents/service.py` → 2 occurrences `lang="fra+eng"` (inchangees, confirmation que service.py n'a pas ete touche).
- Item P1 #8 de spec-audits/index.md marque `Resolu par story 9.4`.
- **Commit fix** : `<short-sha>` (a ajouter apres commit).

## Resolved (2026-04-17) — Story 9.3 : fix 4 tests pre-existants rouges

### 3 tests `test_guided_tour_*` casses par le commit `8c71101` (2026-04-15)

- **Root cause** : le commit `8c71101 fix(guided-tour): documenter les cles context par tour_id` a (1) etendu `GUIDED_TOUR_INSTRUCTION` de ~1600 caracteres (5600 → 7190, depassant la borne `<= 7000` du test `test_guided_tour_instruction_unchanged`), (2) renomme la section « Apres un module (proposition) » en « Proposition de guidage (post-module OU en cours d'echange) » (cassant l'ancre du helper `_post_module_section` utilise par 2 tests de `test_guided_tour_consent_flow.py`).
- **Correctif** : borne du test adaptive_frequency relevee a `<= 8000` (+~14 % marge vs l'ancienne borne 7000, commentaire actualise avec reference commit). Helper `_post_module_section` mis a jour pour accepter les 2 variantes de wording (retro-compat pre- et post-commit 8c71101) avec fallback deterministe sur la premiere ancre trouvee. Les 2 tests metier restent inchanges (leur logique est valide des que le helper localise la section).
- **Fichiers** : `backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py` + `backend/tests/test_prompts/test_guided_tour_consent_flow.py`.

### `test_rate_limit_resets_after_60s` (introduit par story 9.1, jamais passe)

- **Root cause** : le test utilisait `freezegun.freeze_time` + `frozen.tick(delta=61)` pour simuler le passage de 60 s, mais cela ne fonctionne pas avec SlowAPI / `limits.storage.memory.MemoryStorage`. Le `MemoryStorage` demarre un `threading.Timer(0.01, __expire_events)` au constructor qui tourne dans un thread separe avec le vrai `time.time()`. Consequence : les cles d'expiration du storage sont evaluees avec le temps reel (hors freezegun), les compteurs peuvent etre effaces prematurement, et le test etait instable / faux positif selon le timing (`assert response.status_code == 429` recevait 200).
- **Correctif** : remplacement de `freeze_time + tick` par un appel explicite a `limiter.reset()` entre les 2 phases du test. Equivalent semantique (« la fenetre est reinitialisee »), determinisme preserve, zero dependance a freezegun sur ce test. Commentaire du test documente la subtilite de coexistence avec la fixture autouse `reset_rate_limiter`.
- **Fichier** : `backend/tests/test_chat.py` — methode `TestRateLimit.test_rate_limit_resets_after_60s`.

### Validation post-fix

- `pytest tests/ --tb=no -q` → **1103 passed, 0 failed** (baseline 1099 passed / 4 failed avant fix).
- Temps d'execution : **~185 s** (baseline ~163 s, plafond AC6 = 200 s — marge OK).
- `pytest tests/test_chat.py::TestRateLimit -v` → 6/6 verts, aucun skip.
- `pytest tests/test_prompts/test_guided_tour_adaptive_frequency.py tests/test_prompts/test_guided_tour_consent_flow.py -v` → tous verts, aucun skip.
- Principe « Zero failing tests on main » restaure — toute regression future est detectable.

## Deferred from: code review of 9-3-fix-4-tests-pre-existants-rouges (2026-04-17)

- **Mock `session.execute` retourne inconditionnellement `None`** — `scalar_one_or_none=None` pour toutes les queries dans `TestRateLimit._make_mock_session_factory`. L'endpoint `/messages` fonctionne par coïncidence car aucune branche ne déclenche un 404 sur conversation introuvable. Rendre le mock explicite par query (side_effect séquentiel ou mock par appelant). [backend/tests/test_chat.py:449-452] — hors scope 9.3 (code issu de 9.1 non committée).
- **Mock `session.refresh` écrase `id` à chaque appel** — `side_effect=lambda m: setattr(m, "id", uuid.uuid4())` attribue un nouvel UUID à chaque refresh, y compris sur un même objet. Masquerait un bug de refetch ou double-refresh. [backend/tests/test_chat.py:446-448] — hors scope 9.3 (code issu de 9.1 non committée).
- **Dépendance implicite à la fixture autouse `reset_rate_limiter`** — `TestRateLimit` repose sur la fixture de `conftest.py:43-53` sans import explicite. Si la fixture est renommée ou supprimée, les 6 tests deviennent flaky en silence (compteurs partagés entre tests). Rendre la dépendance explicite par un argument de fixture nommé. [backend/tests/test_chat.py — classe `TestRateLimit` entière].
- **Section « Resolved 2026-04-17 » non liée au hash git** — aucun référencement du commit qui applique le fix (les changements sont uncommitted au moment de la review). Dès qu'un commit existe, ajouter une ligne « Commit fix : `<short-sha>` » pour la traçabilité audit. [`_bmad-output/implementation-artifacts/deferred-work.md` §Resolved 2026-04-17].
- **Fragilité pytest-xdist** — `limiter.reset()` partage le storage `MemoryStorage` entre workers parallèles SlowAPI. Si la suite est un jour exécutée avec `pytest -n auto`, des flakes inter-workers apparaîtront sur `test_rate_limit_resets_after_60s` et `test_rate_limit_isolated_per_user`. À adresser si xdist est activé. [backend/tests/test_chat.py:571] — xdist non actif actuellement.
- **`limiter.reset()` est `MemoryStorage`-only** — si le projet passe à Redis pour multi-worker en prod (cf. dette 9.1 déjà tracée), `limiter.reset()` ne videra pas les compteurs distants. Le test `test_rate_limit_resets_after_60s` deviendra silencieusement faux. Ajouter à la checklist de migration Redis. [backend/tests/test_chat.py:571] — V1 in-memory explicite.
- **Bug cosmétique « 2 règles numérotées 5 »** dans `GUIDED_TOUR_INSTRUCTION` — le prompt actuel a deux règles `5` (Separation guidage + Securite context), hérité du commit `8c71101`. La section Resolved 2026-04-17 ne le mentionne pas. À tracer dans une micro-story P3 future (toilettage prompt guided_tour). [backend/app/prompts/guided_tour.py:118,124] — explicite dans Hors scope 9.3 §1.

## Deferred from: code review of 9-2-quota-cumule-stockage-par-utilisateur (2026-04-17)

- **Race condition TOCTOU sur uploads concurrents** — deux uploads parallèles du même utilisateur peuvent tous deux lire `bytes_used < limit` avant que l'un ne flush, dépassant le quota. Acceptable V1 (1 worker uvicorn en dev/staging per Dev Notes §Pièges à éviter). Story future requise si multi-worker activé en prod : `SELECT ... FOR UPDATE` sur agrégat ou compteur Redis atomique. Références : `backend/app/modules/documents/service.py` — `check_user_storage_quota` + check dans `upload_document`.

- **Orphelins disque lors d'un rejet batch multi-fichiers** — `_save_file_to_disk` écrit avant le commit BDD. Si un fichier tardif du batch lève `QuotaExceededError`, les fichiers précédents restent sur disque malgré le rollback BDD. Pre-existing spec 004, explicitement noté « hors scope story 9.2 » dans le code (`service.py` commentaire au-dessus de `_save_file_to_disk`). Dette liée à la décision batch-semantics soulevée en review (D2). Fix futur : pré-calculer le total prospectif avant toute écriture OU cleanup compensatoire sur erreur.

- **`file_size` paramètre trusté sans validation contre `len(content)`** — un appelant de `upload_document(...)` peut déclarer `file_size=1` et fournir 50 MB de content, contournant le check quota (le check utilise `file_size`, pas `len(content)`). Pre-existing spec 004 — tous les validators amont (`_validate_file_size`, quota) utilisent le paramètre déclaré. À adresser dans une story P2 « durcissement upload » (aligner sur `len(content)` ou rejeter si divergence).

- **`check_user_storage_quota` comptabilise documents de tous les `status` (incl. `failed`, `error`)** — la quota inclut les docs en erreur de traitement/OCR, alors qu'ils peuvent ne pas correspondre à du stockage réel. Non spécifié par 9.2 ; comportement à clarifier dans une story future selon la politique produit (quota stockage disque vs quota BDD).

## Deferred from: 019-guided-tour-post-fix-debts validation live (2026-04-15)

- **BUG-1 resolu partiellement** — mon fix du prompt (commit 8c71101) permet
  desormais au LLM d'appeler `trigger_guided_tour(tour_id, context={sector, total_tco2, top_category, top_category_pct})`
  avec les 4 bonnes cles (validation live `tool_call_logs` 2026-04-15 02:14:51+).
  MAIS les valeurs numeriques restent `None` (seul `sector` est resolu depuis
  le profil entreprise). Cause : le chat_node ne recoit ni les stats carbone
  ni le resume du bilan dans son prompt, et le router garde le message
  « Montre-moi mes resultats carbone » dans chat_node au lieu de transitionner
  vers carbon_node (qui lui aurait acces a `get_carbon_summary`). Consequence :
  popovers affichent « Votre empreinte est de  tCO2e. [...] represente % du total. »
  (placeholders vides au lieu de valeurs). Fix avale : soit router vers
  carbon_node sur intent « resultats/bilan/empreinte + page /carbon/results »,
  soit injecter un resume carbon dans le system_prompt chat_node quand
  `current_page == '/carbon/results'`. Deterministique, hors scope du fix
  surface du 2026-04-15.

## Resolved (2026-04-15)

### [BUG] feature 019 — event SSE `guided_tour` silencieusement drop par la whitelist de `send_message`

- **Feature d'origine** : 019-floating-copilot-guided-nav (story 6.1)
- **Revele par** : test live `agent-browser --headed` sur `fatou1@gmail.com` page `/carbon/results`, message « Montre-moi mes resultats carbone ». Backend logue `trigger_guided_tour` avec `status=success` dans `tool_call_logs`, mais driver.js ne lance jamais le parcours cote front : `document.querySelector('.driver-popover')` retourne null, UI figee, aucun message systeme. Instrumentation temporaire (`[GT-TRACE]`) dans `handleGuidedTourEvent` et `startTour` revele que le handler n'est JAMAIS appele — le SSE `guided_tour` n'arrive pas au frontend.
- **Cause racine** : la fonction `generate_sse` (closure interne a `send_message` dans `backend/app/api/chat.py`) filtre les events yielded par `stream_graph_events` via un elif explicite. La whitelist contenait `token`, `tool_call_start/end/error`, `interactive_question`, `interactive_question_resolved`, `error` — mais **PAS `guided_tour`**. Consequence : `stream_graph_events` extrait correctement le marker `<!--SSE:{"__sse_guided_tour__":true,...}-->` du `on_tool_end` et yield `{type: "guided_tour", tour_id, context}` (lignes 270-276 apres story 6.1), mais `generate_sse` (ligne 865) ne le forward pas. Event silencieusement drop. Aucun log, aucune erreur — bug tres difficile a diagnostiquer sans instrumentation ciblee.
- **Correctif** (1 ligne) : ajouter `"guided_tour"` dans la whitelist du elif a `backend/app/api/chat.py:865-868`.
- **Validation live** : reproduction initiale + fix confirme via `agent-browser --headed` sur `fatou1@gmail.com` page `/carbon/results`. Apres fix : `popoverCount=1`, `overlayCount=1`, `highlightedSelector="carbon-donut-chart"`, popover « Etape 1/3 — Repartition de vos emissions » visible.
- **Tests** : nouveau test anti-regression `backend/tests/test_api/test_sse_event_whitelist.py` qui verrouille la whitelist par inspection de source (tous les types emis par `stream_graph_events` doivent etre presents dans `send_message`). Bug de cette classe difficile a attraper en integration (filtrage muet), test statique defensif plus pragmatique. 15 tests existants (`test_sse_tool_events.py`, `test_guided_tour_toolnode_registration.py`) toujours verts.
- **Dettes secondaires** (hors scope) :
  - `context` passe a `null` cote backend dans l'appel LLM actuel → placeholders `{{total_tco2}}`, `{{top_category}}`, `{{top_category_pct}}` non interpoles dans le popover (« Votre empreinte est de tCO2e »). A corriger dans une story dediee (enrichir le prompt `GUIDED_TOUR_INSTRUCTION` pour que le LLM remplisse le dict `context` avec les valeurs de la page courante).
  - `profile_update` et `profile_completion` sont emis par `stream_graph_events` (lignes 258-262) mais eux aussi absents de la whitelist `generate_sse`. Meme classe de bug, non investiguee : si la fonctionnalite marche aujourd'hui c'est via une autre voie ; sinon, verifier si elle est cassee depuis la migration tool-calling (feature 012).
- **Note sur le bug precedent (LLM hallucine "outil indisponible")** : deja resolu ce matin (cf. plus bas dans cette section « Resolved 2026-04-15 »). Le present bug etait la *couche suivante* cachee sous celui-la : backend-cote-tool OK → backend-cote-endpoint drop.

### [BUG] feature 019 — LLM hallucine « trigger_guided_tour temporairement inaccessible »

- **Feature d'origine** : 019-floating-copilot-guided-nav (stories 6.1 et suivantes)
- **Revele par** : test live `agent-browser --headed` sur compte `fatou1@gmail.com`, message « Montre-moi mes resultats carbone sur l'ecran ». Le LLM repondait « Le guidage visuel interactif n'est pas disponible pour le moment — l'outil de navigation vers la page /carbon/results n'est pas accessible dans cette session ». Cette phrase n'existe nulle part dans le code : hallucination pure.
- **Cause racine** (trouvee via logs instrumentes dans chat_node) :
  1. `GUIDED_TOUR_TOOLS` etait bien binde cote LLM dans 6 noeuds (chat, esg_scoring, carbon, financing, credit, action_plan) via `llm.bind_tools(...)`.
  2. MAIS `GUIDED_TOUR_TOOLS` etait **absent de la liste `tools=` passee a `create_tool_loop(...)` dans `app/graph/graph.py`** (lignes 132-138). Les ToolNodes ne contenaient pas le tool.
  3. Consequence : le LLM emettait `tool_calls=['trigger_guided_tour']` au 1er tour, mais le ToolNode ne trouvait pas le tool a executer et ne produisait pas de ToolMessage exploitable. Au 2e tour LLM, le modele generait un texte hallucinant l'indisponibilite de l'outil — aggrave par l'historique polue (les conversations precedentes contenaient deja des hallucinations similaires, perpetuees via `context_memory` et les summaries).
- **Correctif** (3 volets, diff minimal) :
  1. **Fix principal** [backend/app/graph/graph.py] — ajouter `GUIDED_TOUR_TOOLS` dans les 6 appels `create_tool_loop` des noeuds qui le bindent cote LLM (exclusion : `application_node` qui ne le bind pas). Import du module ajoute dans la section des imports paresseux.
  2. **Defense en profondeur contre la recidive** [backend/app/chains/summarization.py] — renforcement de `SUMMARY_PROMPT` : interdiction explicite de persister dans les resumes des formulations comme « outil indisponible », « hors service », « pas accessible dans cette session ». Les hallucinations qui passent le tool-calling ne doivent plus contaminer les sessions futures.
  3. **Nettoyage des summaries legacy** [backend/app/prompts/system.py `_format_memory_section`] — ajout d'un paragraphe neutralisant : toute affirmation d'indisponibilite d'outil dans les resumes injectes via `context_memory` est declaree INVALIDE et a IGNORER (protege contre les summaries deja en base chez d'autres users, non nettoyes).
- **Nettoyage BDD** : 9 `conversations.summary` contamines (tous users confondus) remis a NULL via script one-shot (seront regeneres au prochain summarization avec le nouveau prompt durci).
- **Tests** : 8 tests anti-regression ajoutes dans `tests/test_graph/test_guided_tour_toolnode_registration.py` qui verrouillent la coherence `bind_tools` ↔ `ToolNode` pour `trigger_guided_tour` dans les 7 modules (6 avec + 1 sans). 241 tests suites (prompts + graph + chat) verts, zero regression.
- **Validation live** : reproduction initiale + fix confirme via `agent-browser --headed` sur `fatou1@gmail.com` page /carbon/results. Avant : assistant generait le texte hallucine. Apres : `tool_call_logs` contient `trigger_guided_tour` avec `status=success` et la reponse assistant est vide (conforme a `GUIDED_TOUR_INSTRUCTION` « pas de texte apres l'appel »).
- **Note sur le declenchement front du tour** : l'event SSE `guided_tour` est emis correctement, mais le driver.js n'a pas lance visuellement le parcours lors du test (aucun `.driver-popover` dans le DOM). Probablement lie au guard `currentInteractiveQuestion` residuel dans `useChat.ts` (cf. dette 6-4 : edge case orphan-state). Symptome secondaire, hors scope du bug LLM. A investiguer dans une story de suivi.
- **Commit** : voir `git log` sur la branche `main` (date 2026-04-15).

## Resolved (2026-04-14)

### [BUG] carbon_node — lecture de bilan carbone retourne "Aucun bilan" alors qu'une entree existe

- **Feature d'origine** : 007-carbon-footprint-calculator
- **Revele par** : test live feature 019 (parcours Fatou) avec `agent-browser` sur compte `fatou1@gmail.com`
- **Cause racine** : `carbon_node` et le tool `get_carbon_summary` n'utilisaient que `get_resumable_assessment` (filtre `status = in_progress`). Lorsque l'utilisateur n'a que des bilans `completed`, le fallback retournait None et le LLM pensait qu'aucun bilan n'existait. Dans le meme temps, `create_carbon_assessment` detectait bien le bilan existant (contrainte d'unicite user_id + year), d'ou la reponse contradictoire.
- **Correctif** :
  1. Ajout de `get_latest_assessment(db, user_id)` dans `backend/app/modules/carbon/service.py` — retourne le bilan le plus recent quel que soit le statut.
  2. Mise a jour de `get_carbon_summary` dans `backend/app/graph/tools/carbon_tools.py` — fallback sur `get_latest_assessment` quand aucun bilan `in_progress`.
  3. Mise a jour de `carbon_node` dans `backend/app/graph/nodes.py` — charge egalement les bilans `completed` dans l'etat injecte au prompt (annee, statut, assessment_id reels) + nouvel en-tete de contexte "BILAN CARBONE EXISTANT (finalise, disponible en consultation)".
- **Tests** : 4 tests ajoutes (3 service + 1 tool). 1072 tests backend verts, zero regression.
- **Commit** : voir `git log` sur la branche `main` (date 2026-04-14).
- **Note sur la journalisation `tool_call_logs`** : symptome non lie au bug. Les tools metier (carbon, esg, etc.) n'instrumentent pas actuellement `log_tool_call` ; seuls `interactive_tools` et `guided_tour_tools` le font. Dette d'observabilite a traiter separement.

## Deferred from: code review of story-8-1 (2026-04-14)

- Imports `../../../app/types/carbon` sans path alias dans les fixtures E2E — a refactorer globalement avec un alias Vitest/Playwright (hors scope 8.1). [frontend/tests/e2e/fixtures/mock-backend.ts:666]
- `testMatch` ambiguite : un `.test.ts` sous `tests/e2e/` serait silencieusement skip par Vitest ET ignore par Playwright (qui matche `.spec.ts`). Documenter la convention dans `tests/e2e/README.md`. [frontend/vitest.config.ts:66 ; frontend/playwright.config.ts:97]
- Pas de header `X-Accel-Buffering: no` sur la reponse SSE fabriquee — inutile tant que la reponse est single-shot, a ajouter si un futur patch active le vrai streaming chunke. [frontend/tests/e2e/fixtures/sse-stream.ts:581]
- `route.continue()` appele sur les methodes non-POST dans plusieurs endpoints mockes (`:772, 1007, 1028, 1065`) — en environnement e2e full-mock, ceci laisse passer les requetes vers un backend qui n'existe pas. Le catch-all 404 couvre deja le cas ; a nettoyer avec une passe de harmonisation. [frontend/tests/e2e/fixtures/mock-backend.ts:772]

## Deferred from: code review of story-7-2 (2026-04-14)

- `refreshPromise` module-level dans `useAuth.ts` risque de partage entre requetes SSR — composable client-only en pratique mais pas de guard `import.meta.client` explicite. [frontend/app/composables/useAuth.ts:49]
- `useCarbon.fetchBenchmark` et `useEsg.fetchBenchmark` avalent toutes les erreurs non-session-expirée et retournent `null` — UI ne peut pas distinguer 404 vs 500. Comportement pre-existant, a traiter globalement. [frontend/app/composables/useCarbon.ts:93-98, useEsg.ts:90-96]
- Tests manquants : cycle 401 sur `apiFetchBlob` (fiche de preparation PDF), `/auth/me` (fetchUser), echec d'import dynamique dans `handleAuthFailure`. Scenarios principaux couverts par les 19 tests existants. [frontend/tests/composables/useAuth.refresh.test.ts]
- Composables non migres vers `apiFetch` (`useApplications`, `useCreditScore`, `useActionPlan`, `useReports`, `useDocuments`, `useCompanyProfile`, `useChat`) ne beneficient pas de l'intercepteur 401. Dette technique deja documentee dans la story, future story `X-Y-migration-composables-vers-apifetch` proposee.

## Deferred from: code review of story-3-1 (2026-04-13)

- Pas d'annotation reducer pour `current_page` dans ConversationState — le champ pourrait ne pas se propager si un noeud LangGraph retourne un state partiel. Risque latent pour Story 3.2 quand les noeuds liront activement cette valeur. [backend/app/graph/state.py:36]
- `invoke_graph` n'accepte pas `current_page` — inconsistance latente avec `stream_graph_events`. Verifier si cette fonction est encore utilisee et la mettre a jour ou la supprimer. [backend/app/api/chat.py:56]

## Deferred from: code review of story-3-2 (2026-04-13)

- Checkpointer LangGraph et `current_page` — aucun nœud ne retourne `current_page` dans son `return {}`, risque théorique d'écrasement par le checkpoint. Risque quasi nul car toujours re-injecté dans `initial_state` et read-only. [backend/app/graph/nodes.py]
- `send_message_json` passe toujours `current_page=None` — endpoint de compatibilité, pas utilisé par le frontend actuel. Ajouter le support ou documenter la limitation. [backend/app/api/chat.py:938]
- Routes dynamiques (`/financing/123`) tombent sur la branche générique du prompt — nécessite un design de prefix matching pour extraire les descriptions contextuelles des pages avec paramètres. [backend/app/prompts/system.py:138]
- Valeur initiale `"/"` dans `uiStore.currentPage` envoyée au backend comme page inconnue — initialiser à `null` ou ajouter `"/"` à `PAGE_DESCRIPTIONS`. [frontend/app/stores/ui.ts:17]
- Tests ne couvrent pas le chemin complet nœud → prompt pour 5 des 6 spécialistes (carbon, financing, application, credit, action_plan) — couverture indirecte via tests prompts directs. [backend/tests/test_graph/test_current_page.py]

## Deferred from: code review of story-4-1 (2026-04-13)

- Pas de `timeout` sur `requestIdleCallback` dans `prefetchDriverJs()` — sous charge CPU le prefetch peut ne jamais se declencher avant le premier guidage. Le fallback `loadDriver()` gere ce cas mais avec latence supplementaire. [frontend/app/composables/useDriverLoader.ts:25]
- Couleurs hexadecimales hardcodees en mode clair dans les overrides Driver.js CSS — incohérence avec le dark mode qui utilise des variables CSS du design system. Pattern pre-existant dans le projet. [frontend/app/assets/css/main.css]

## Deferred from: code review of story-4-2 (2026-04-13)

- `countdown` sans borne min/max — accepte 0, négatif, NaN. Ajouter validation dans le moteur `useGuidedTour` (Story 5.1). [frontend/app/types/guided-tour.ts]
- `lib/` pas dans les dirs auto-import Nuxt — import manuel requis. Choix d'architecture, documenter si nécessaire. [frontend/nuxt.config.ts]
- `tsconfig.json` étend `.nuxt/tsconfig.json` — tests TypeScript cassent avant `nuxt prepare` en clone frais. Setup pré-existant. [frontend/tsconfig.json]
- `route` field non contraint dans `GuidedTourStep` — un typo de route échoue silencieusement au runtime. Validation croisée à ajouter dans Story 5.1. [frontend/app/types/guided-tour.ts]
- `TourContext = Record<string, unknown>` sans contrat entre les placeholders attendus et le contexte fourni — risque d'affichage de `{{variable}}` brut si clé manquante. Design d'interpolation à prévoir dans Story 5.1. [frontend/app/types/guided-tour.ts]

## Deferred from: code review of story-4-3 (2026-04-13)

- Route mismatch `show_esg_results` : registre declare `route: '/esg'` mais `esg-score-circle` est sur `/esg/results`. Corriger dans `registry.ts:22` la route en `/esg/results`. [frontend/app/lib/guided-tours/registry.ts:22]
- 8 elements `data-guide-target` dans des blocs `v-if` (esg-strengths-badges, esg-recommendations, carbon-donut-chart, carbon-benchmark, carbon-reduction-plan, action-plan-timeline, credit-score-gauge, dashboard cards pendant loading). Le moteur `useGuidedTour` (Story 5.1) devra gerer les elements absents du DOM via skip, attente ou fallback. [multiple pages]

## Deferred from: code review of story-5-1 (2026-04-13)

- Delai transition `complete → idle` hardcode a 1000ms — AC5 mentionne un delai configurable. Exposer une constante ou un parametre optionnel dans `startTour`. [frontend/app/composables/useGuidedTour.ts:162-166]
- Element DOM peut etre supprime entre le retour de `waitForElement` et l'appel `highlight` — fenetre de timing tres courte. Limitation architecturale, impact negligeable en conditions normales. [frontend/app/composables/useGuidedTour.ts:112-124]

## Deferred from: code review of story-6-1 (2026-04-13)

- Pas d'allowlist serveur pour `tour_id` — AC4 delegue explicitement la validation au registre frontend (par conception du spec). Hardening defense-en-profondeur possible plus tard. [backend/app/graph/tools/guided_tour_tools.py]
- `context` dict sans limite de taille/profondeur — un LLM pourrait envoyer un context enorme. Pre-existant aux autres tools qui acceptent des dicts LLM-controlled. [backend/app/graph/tools/guided_tour_tools.py:24]
- Marker SSE split entre chunks de streaming — parser actuel dans `stream_graph_events` suppose un `on_tool_end` avec output complet. Limitation partagee avec les markers `__sse_profile__` et `__sse_interactive_question__`. [backend/app/api/chat.py:212-239]
- Plusieurs markers SSE dans un seul output ne sont pas tous parses — `index()` ne trouve que le premier `-->`, les markers suivants sont ignores. Pre-existant. [backend/app/api/chat.py:213-217]

## Deferred from: code review of story-6-2 (2026-04-13)

- Couplage STYLE_INSTRUCTION / GUIDED_TOUR_INSTRUCTION : meme branche conditionnelle `_has_minimum_profile` dans `build_system_prompt`. Un futur changement de seuil du style concis deplacera silencieusement le guidage. Extraire un helper dedie ou ajouter un test d'independance. [backend/app/prompts/system.py:211-217]
- Aucune assertion positionnelle sur l'ordre `WIDGET_INSTRUCTION` → `GUIDED_TOUR_INSTRUCTION` dans les 5 prompts specialises — les tests verifient la presence (`in`) mais pas l'ordre. Un swap futur ne declencherait aucune erreur. [backend/tests/test_prompts/test_guided_tour_instruction.py]
- Chemins frontend listes dans la docstring `GUIDED_TOUR_INSTRUCTION` (`/esg/results`, `/action-plan`, etc.) non epingles contre le registre Nuxt reel (`frontend/app/lib/guided-tours/registry.ts`). Divergence silencieuse possible (cosmetique, le tool_call utilise le `tour_id` qui lui est valide). Test cross-stack a creer. [backend/app/prompts/guided_tour.py:12-17]

## Deferred from: code review of story-6-3 (2026-04-14)

- T-AC2 / T-AC6 court-circuitent `useGuidedTour` via mock statique — le test ne valide pas que `handleGuidedTourEvent` emprunte le code path runtime reel. Couverture d'integration plus realiste a prevoir en epic 8 (e2e). [frontend/tests/composables/useChat.guided-tour-consent.test.ts]
- Plancher `count("GUIDED_TOUR_TOOLS") >= 12` dans T11 conflate shape et correctness. Un refactor legitime (liste partagee, spread) casse le test. Herite 6.2. [backend/tests/test_prompts/test_guided_tour_instruction.py]
- T-AC3 (refus consent) ne prouve pas le respect du refus — test passe car backend n'emet pas `guided_tour`, pas parce que `no` est honore. Si le backend emettait a tort un guided_tour apres refus, le frontend n'a pas de guard `yes`-only. Test d'alignement backend/frontend a ajouter (hors scope prompt-only). [frontend/tests/composables/useChat.guided-tour-consent.test.ts]
- `GUIDED_TOUR_INSTRUCTION` injecte inconditionnellement (y compris pour sessions anonymes / sans profil) — bloat tokens par requete. Decision architecturale a valider globalement ou gated. [backend/app/prompts/system.py:213-220]
- Aucun test cross-file alignant les 6 `tour_id` entre `guided_tour.py` (prompt), `registry.ts` (frontend), `guided_tour_tools.py` (backend tool enum). Renommage silencieux possible. Test de contrat pour story 7.x ou 8.x. [multi-file]
- Validation serveur `tour_id` (tool-level) et validation `context` dans `handleGuidedTourEvent` — hors scope story 6.3 (story 6.1 pour le tool, `useChat.ts` NE PAS TOUCHER pour le handler). [backend/app/graph/tools/guided_tour_tools.py, frontend/app/composables/useChat.ts:682-700]

## Deferred from: code review of story 6-4-frequence-adaptative-des-propositions-de-guidage (2026-04-14)

- Decroissance / cap global sur `acceptance_count` et `refusal_count` — actuellement saturation indefinie apres ~5 acceptations (plancher 3s permanent). Decision produit a arbitrer : cap dur vs decay temporel. [frontend/app/composables/useGuidedTour.ts]
- `send_message_json` (endpoint fallback JSON) ne transmet pas `guidance_stats` au graphe — volontaire par spec ; acceptable car le fallback est hors-parcours principal. Extension Chrome / integrations externes (story 8.x) devront explicitement opter pour la modulation. [backend/app/api/chat.py:~976]
- Perte de precision au-dela de `Number.MAX_SAFE_INTEGER` dans `loadGuidanceStats` — limite JS native ; mitigable par plafond serveur (cf. patch P8 meme review). [frontend/app/composables/useGuidedTour.ts]
- Race theorique entre `currentInteractiveQuestion` lu avant `await import(...)` et evenement SSE `interactive_question_resolved` concurrent — fenetre temporelle minime, impact pratique negligeable. [frontend/app/composables/useChat.ts]
- SSE `guided_tour` arrivant pendant une question interactive `pending` laisse un etat orphelin (refus deja comptabilise sur la question precedente, acceptance non comptabilisee sur le tour). Path early-return existant avec message systeme ; edge rare. [frontend/app/composables/useChat.ts:~730-733]
- `test_guided_tour_instruction_unchanged` verifie seulement une plage de longueur (3500-6000 chars) — ne constitue pas un vrai verrou anti-regression semantique. A renforcer avec snapshot au prochain refactor 6.2. [backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py:~894-903]
- `try { ... } catch {}` silencieux autour de l'import dynamique + increment dans `useChat.ts` — swallow des erreurs non-critiques mais sans observabilite. A envisager dans story tooling/observability. [frontend/app/composables/useChat.ts:464-466]
- Migration de la cle localStorage `esg_mefali_guidance_stats` vers un scope par utilisateur (prefixe `user_id:` ou deplacement backend `user_guidance_stats`). Status quo accepte pour story 6.4. A revisiter au demarrage du module 7 (multi-utilisateurs admin/collaborateur/lecteur). Ajouter un TODO inline en meme temps que les patchs 6.4. [frontend/app/composables/useGuidedTour.ts]

## Deferred from: code review of story 7-1-gestion-des-elements-dom-absents-et-timeout-de-chargement (2026-04-14)

- `Date.now()` non-monotone dans `waitForElementExtended` — une bascule NTP/DST peut fausser le calcul d'elapsedMs. Preferer `performance.now()` pour les mesures de duree. [frontend/app/composables/useGuidedTour.ts:179,183,189]
- `setTimeout(..., 500)` dans `interruptTour`/`cancelTour` (transition `interrupted`→`idle`) jamais annule — leak mineur de timers sur cancels repetes. [frontend/app/composables/useGuidedTour.ts:250-252,662-666]
- `cancelled` non reinitialise sur le chemin de succes de `startTour` — etat residuel possible entre deux parcours consecutifs sans cancel entre les deux. [frontend/app/composables/useGuidedTour.ts:278]
- `cancelTour` re-entre pendant la transition `interrupted`→`idle` cree des timeouts dupliques — ajouter `'interrupted'` a la garde de retour anticipe. [frontend/app/composables/useGuidedTour.ts:~635]
- Cleanup du catch global a placer dans un `finally` au lieu d'apres le catch — robustesse face a un throw interne au catch (ex. import dynamique qui throw lui-meme). [frontend/app/composables/useGuidedTour.ts:~590-627]
- `addSystemMessage` peut etre silencieusement drop si aucune conversation active cote `useChat` — limitation pre-existante ; AC4 suppose que l'utilisateur voit toujours le message empathique. A renforcer avec un fallback toast si pas de conversation active. [frontend/app/composables/useGuidedTour.ts:598-600, frontend/app/composables/useChat.ts:739-744]
- Strings FR hardcodees ("Je n'ai pas pu pointer cet element...", "La page met trop de temps a charger...", "Le guidage a rencontre un probleme...") non extraites en MAP de constantes module-level — conforme aux conventions actuelles du projet mais nuit a une future i18n ou a un edit global. [frontend/app/composables/useGuidedTour.ts:424,504,~418,~509,~600]

## Deferred from: code review of story 7-3-resilience-sse-et-indicateur-de-reconnexion (2026-04-14)

- Classification HTTP par substring francais `'erreur lors de'` : tous les throws actuels matchent mais tout nouveau message en englais ou reformule tombe dans `'other'`. Refactor en sentinel `class HttpError extends Error` ou en drapeau typed recommande a terme. [frontend/app/composables/useChat.ts:70]
- `throw new Error('Réponse sans body...')` classifie en `'other'` et pollue `error.value` meme pendant un parcours guide. Scenario rare (200 OK sans body). AC3 autorise explicitement ce comportement pour non-network, mais incoherent avec l'intention de masquer les erreurs reseau pendant un tour. [frontend/app/composables/useChat.ts:264, 659]
- `DOMException` non-Abort mid-stream (`NetworkError`, `InvalidStateError`) classifie en `'other'`. Readers modernes throw `TypeError` donc impact < 1 % du trafic (Safari legacy). Documente en spec Dev Notes. [frontend/app/composables/useChat.ts:62-72]
- `useUiStore()` appele dans le catch block — risque Pinia-not-ready dans contextes edge. Impossible dans flow UI reel. Refactor optionnel : hoister en haut de `useChat()`. [frontend/app/composables/useChat.ts:504, 776]
- Test invariant AC8 fragile au cwd : `path.resolve(process.cwd(), 'app/composables/useGuidedTour.ts')` fonctionne si vitest lance depuis `frontend/`. Robustesse : `new URL(..., import.meta.url)`. [frontend/tests/composables/useChat.connection.test.ts:831-838]
- bfcache : listeners survivent mais `isConnected` stale au `pageshow`. Edge case rare (page cachee offline puis restauree online sans event). Handler `pageshow` a ajouter a terme. [frontend/app/composables/useChat.ts:77-85]
- Fetches concurrents (`sendMessage` + `submitInteractiveAnswer`) : si l'un succeed et flip a true puis l'autre fail en network, la bascule a false ecrase le signal de reprise. Peu probable dans l'UX normale (serialisation par `abortController`). [frontend/app/composables/useChat.ts:289, 683, 503, 775]

## Deferred from: code review of 8-3-tests-e2e-parcours-aminata (2026-04-15)

- Semantique exacte de `agent-browser close` (sans `--session`) : bloque sur la documentation upstream de la CLI agent-browser 0.8.5 ; le `cleanup()` actuel appelle `agent-browser --headed close` sans session nommee et swallow la sortie. A tracker via issue CLI si comportement imprevu observe [frontend/tests/e2e-live/8-3-parcours-aminata.sh:1175, 1264].
- Driver.js popover i18n : textes hardcoded FR + fallback EN (Suivant/Next, Terminer/Done/Fermer). Aucune couverture pour ES/DE/etc. Hors scope 8.3 ; a reprendre dans une story dediee si Driver.js expose des builds i18n ou si on force la locale applicative [frontend/tests/e2e-live/8-3-parcours-aminata.sh:1328-1358].
- Flag `--session aminata-e2e` absent des invocations `agent-browser` (la spec AC3–AC8 l'impose, le dev utilise la var d'env `AGENT_BROWSER_SESSION` a la place). Defere le 2026-04-16 par Angenor : « la simulation marche, on laisse comme ca pour le moment ». A reprendre si on observe des collisions de session ou si 8.4/8.5/8.6 introduisent du parallelisme [frontend/tests/e2e-live/8-3-parcours-aminata.sh + lib/env.sh:50].

## Deferred from: code review of 9-1-rate-limiting-fr013-chat-endpoint (2026-04-17)

- Pas de limiter Redis multi-worker (in-memory SlowAPI) — explicitement hors scope V1. A reprendre quand le déploiement passera à >1 worker uvicorn. [backend/app/core/rate_limit.py]
- Pas de log/métrique émis sur les 429 : pour un contrôle sécurité (abuse prevention), on a besoin de savoir QUI hit la limite et COMBIEN pour distinguer misconfig d'une attaque. SlowAPI default handler ne log rien. [backend/app/main.py]
- Import du symbole privé `from slowapi import _rate_limit_exceeded_handler` : underscore = surface non stable. Un minor bump SlowAPI peut renommer/supprimer sans breaking semver. Wrap dans un handler local ou pin narrow (`slowapi>=0.1.9,<0.2`). [backend/app/main.py:9]
- Upload de fichier volumineux : le 429 ne tire qu'après consommation du body multipart. Un attaquant peut gaspiller bande passante/disque par requête même en étant limité. Décisionner : rate-limit hors décorateur (middleware cible) ou capper `content-length` amont. [backend/app/api/chat.py:send_message]
- Rate-limit avant validation d'input : 30 requêtes avec `content=None` ou payload invalide consomment le quota. Comportement standard (rate-limit d'abord) mais à confirmer vs le cas « spam de 4xx ». [backend/app/api/chat.py:send_message]
- Déconnexion client mid-SSE : quota déjà décompté, pas de refund. Si le client retry après disconnect, il hit la limite plus vite qu'attendu. Documenter explicitement le comportement côté UX. [backend/app/api/chat.py:976-983]
- Double-clic pendant la fenêtre 429 : pas de cooldown côté client (pas de `rateLimitedUntil` timestamp). L'utilisateur peut spam le bouton send, chaque click se prend un 429 supplémentaire. Ajouter un backoff UI. [frontend/app/composables/useChat.ts:279-289]
- Nettoyage partiel sur 429 côté frontend : `documentProgress`, `activeToolCall`, `abortController` ne sont pas explicitement réinitialisés. Le `finally` existant couvre `isStreaming`. Risque d'état fantôme d'une tentative précédente persistant après un 429. [frontend/app/composables/useChat.ts:279-289]
- Input utilisateur perdu sur 429 : AC5 spécifie l'idempotence (retrait du message refusé), mais le contenu tapé n'est pas préservé dans le composer pour un retry. UX sub-optimale pour messages longs. [frontend/app/composables/useChat.ts:287]
- Headers `X-RateLimit-Remaining` / `X-RateLimit-Limit` émis (via `headers_enabled=True`) mais ignorés côté frontend. Le composable pourrait afficher « Il vous reste X messages » pour une UX proactive. [frontend/app/composables/useChat.ts]

## Deferred from: Story 10.6 Storage abstraction (2026-04-20)

### Opportunités Phase Growth — 4 modules PDF in-memory vers storage.put()

Ces modules génèrent actuellement du PDF **in-memory** via
`HTML(...).write_pdf()` → `bytes` streamés directement via
`FastAPI Response`. Aucune écriture disque, aucun audit trail, aucun
caching. Intérêt de les câbler à `storage.put()` en Phase Growth :
persistance pour audit réglementaire (ESG/financement/crédit) + cache
1re génération = 0 CPU sur re-download, + possibilité de signed_url si
le PDF devient accessible par plusieurs intervenants.

- `backend/app/modules/credit/certificate.py:56` — certificat de scoring crédit vert.
- `backend/app/modules/financing/preparation_sheet.py:108` — fiche de préparation financement.
- `backend/app/modules/applications/export.py:149` — export dossier candidature.
- `backend/app/modules/applications/prep_sheet.py:135` — fiche de préparation candidature.

### Adaptateur tempfile pour libs d'extraction en mode S3

PyMuPDF, pytesseract, docx2txt et openpyxl attendent un **path
filesystem** (pas un BinaryIO). En mode `STORAGE_PROVIDER=s3`,
`documents.service.analyze_document` doit télécharger la clé dans un
`tempfile.NamedTemporaryFile` avant d'appeler les extracteurs. Pattern
déferré à la story de migration Phase Growth (hors 10.6 qui reste
`NotImplementedError` si S3 actif + extraction demandée).
[backend/app/modules/documents/service.py:analyze_document]

### Script `scripts/migrate_local_to_s3.py`

Phase Growth — déplace récursivement `backend/uploads/documents/*` et
`backend/uploads/reports/*` vers le bucket S3, en conservant les clés
opaques **identiques** (aucune migration BDD nécessaire car
`Document.storage_path` et `Report.file_path` stockent déjà la clé
portable depuis Story 10.6). À écrire + tester avant la bascule
`STORAGE_PROVIDER=s3` en prod. [scripts/migrate_local_to_s3.py (à créer)]

### `download_document` endpoint bascule signed_url

`backend/app/modules/documents/router.py:355-380` utilise toujours
`FileResponse(path=...)` pour servir les fichiers. En mode S3 Phase
Growth, il faudra détecter `isinstance(storage, S3StorageProvider)` et
renvoyer `RedirectResponse(await storage.signed_url(key, ttl=900))`.
Pattern identique à `reports/router.py:download_report` (déjà migré
Story 10.6). [backend/app/modules/documents/router.py]

### Pagination `list()` > 1000 keys

`S3StorageProvider.list(max_keys > 1000)` lève `NotImplementedError`.
Nécessaire pour audit catalogue multi-tenant (NFR66) à partir de ~500
utilisateurs actifs. À implémenter avec `ContinuationToken` boto3.
[backend/app/core/storage/s3.py:list]

### SSE-KMS en lieu de SSE-S3 pour compliance renforcée

SSE-S3 AES256 est gratuit + suffisant pour NFR25 MVP. SSE-KMS (clé
managée par Mefali, rotation automatique, audit CloudTrail) sera
exigé si compliance UEMOA/BCEAO renforcée. Coût : ~0,03 $/10k
requêtes. [backend/app/core/storage/s3.py:put]

## Deferred from: code review of story-10.6 (2026-04-20)

Issus du rapport `10-6-code-review-2026-04-20.md` — 6 LOW consolidés,
non bloquants pour le merge, chacun mappé à un epic/story cible de
livraison pour éviter perte de traçabilité.

- **LOW-10.6-1 — Filename PII dans la clé opaque** — `storage_key_for_document`
  inclut le filename utilisateur (sanitisé mais "humain" — ex.
  `contrat_mhamadou_sgbs_2026.pdf`). Visible dans CloudTrail logs,
  Access Analyzer, logs FastAPI de retry → PII (nom client) exposé
  côté ops AWS + ops Mefali. Proposition : option `opaque_filename=True`
  qui hash SHA256[:16] + extension. **Cible** : **Epic 18 FR65 RGPD**
  (droit à l'oubli + minimisation logs) OU **Story 10.7** avant bascule
  Phase Growth. [backend/app/core/storage/keys.py:19-30]
  [10-6-code-review-2026-04-20.md#low-10.6-5]

- **LOW-10.6-2 — IAM `s3:DeleteObject` trop large** — ✅ **RÉSOLU Story 10.7
  AC4** (absorbed). Module `infra/terraform/modules/iam/main.tf` crée 2 rôles
  distincts per-env : (a) `mefali-<env>-app` (ECS Fargate task) — actions
  `s3:GetObject` + `s3:PutObject` + `s3:ListBucket`, **pas** `DeleteObject` —
  soft-delete applicatif via `Document.deleted_at` ; (b) `mefali-<env>-admin`
  (assumé par IAM user Angenor avec MFA) — `s3:DeleteObject` scopé
  `arn:aws:s3:::mefali-<env>/*` avec `Condition.aws:MultiFactorAuthPresent=true`.
  Anti-wildcard garanti par CI guard (`rg 'Resource.*"\*"' infra/terraform/`
  dans `.github/workflows/deploy-*.yml`). Tests :
  `backend/tests/test_infra/test_iam_policies.py` (4 tests).
  Documentation : `docs/CODEMAPS/storage.md §7 IAM granulaire`.

- **LOW-10.6-3 — `LocalStorageProvider.exists()` silencieux sur path-traversal** —
  en capturant `StoragePermissionError` et retournant False, l'implémentation
  respecte le contrat ABC mais masque un signal d'attaque. Un futur endpoint
  qui exposerait `exists(user_controlled_key)` serait vulnérable à
  l'énumération silencieuse. Proposition : logger `WARNING` avant return
  False. **Cible** : **Epic 18 Security hardening** (durcissement défense
  en profondeur). [backend/app/core/storage/local.py:168-174]
  [10-6-code-review-2026-04-20.md#low-10.6-7]

- **LOW-10.6-4 — Bucket versioning + MFA delete + Object Lock non documentés** —
  ✅ **RÉSOLU Story 10.7 AC7** (absorbed). Nouvelle section
  `docs/CODEMAPS/storage.md §6 Propriétés bucket Phase Growth` documente :
  (§6.1) Versioning activé MVP via Terraform `aws_s3_bucket_versioning`
  (prérequis CRR AC6) + lifecycle rule `NoncurrentVersionExpiration` 30 jours ;
  (§6.2) MFA Delete procédure root-only via `aws s3api put-bucket-versioning`
  + MFA serial (limitation AWS — pas activable via Terraform) ; (§6.3) Object
  Lock WORM différé Phase Growth (nécessite création bucket avec
  `object_lock_enabled_for_bucket=true`, audit bailleur SGES trigger). Runbook
  4 enrichi avec « Prerequisites ops Phase Growth » + checklist trimestrielle.
  Test documentaire : `backend/tests/test_docs/test_runbook_4_has_mfa_section.py`
  (6 tests — Versioning, MFA Delete, Object Lock, CRR, ANONYMIZATION_SALT).

- **LOW-10.6-5 — `ThrottlingException` dans `_TRANSIENT_ERROR_CODES` (code mort)** —
  canonique pour DynamoDB/Lambda/API Gateway mais jamais émis par S3
  (qui utilise `SlowDown`). Inclusion défensive mais inutile, induit en
  erreur lors d'un audit du retry policy. Proposition : retirer OU
  renommer la constante `_TRANSIENT_AWS_ERROR_CODES` si le module doit
  servir d'autres services AWS un jour. **Cible** : **Epic 18
  observabilité** (audit retry policies + métriques fines par
  provider). [backend/app/core/storage/s3.py:41-50]
  [10-6-code-review-2026-04-20.md#low-10.6-9]

- **LOW-10.6-6 — `signed_url` délègue `generate_presigned_url` à `asyncio.to_thread`** —
  `generate_presigned_url` est purement local (signature HMAC ~50 μs),
  aucun round-trip réseau. Le thread-pool ajoute ~0.3-0.8 ms overhead
  sans bénéfice. Impact : +0.05-0.1 vCPU permanent sous 100 req/s en
  Phase Growth, négligeable MVP. Proposition : inline direct si profiling
  Phase Growth montre saturation thread pool. **Cible** : **optimisation
  Phase Growth** (micro-optim post-10.7). [backend/app/core/storage/s3.py:269-275]
  [10-6-code-review-2026-04-20.md#low-10.6-10]


## Deferred from: story-10.7

Les items ci-dessous ont été identifiés comme hors scope MVP dans la Story 10.7 (tranchés Q1-Q4) et sont référencés pour traçabilité Phase Growth.

- **DEF-10.7-1 — Object Lock WORM pour bucket SGES dédié** — rétention 10 ans
  immuable pour documents réglementaires SGES/audits bailleurs. **Non activable
  post-création** (nécessite bucket créé avec `object_lock_enabled_for_bucket=true`).
  **Cible** : **Phase Growth** — trigger = 1er bailleur exigeant rétention WORM
  dans son audit. Path : nouveau bucket dédié `mefali-sges-worm` + routage
  applicatif via `StorageProvider.upload_document(key="sges/...")`.
  [docs/CODEMAPS/storage.md §6.3]

- **DEF-10.7-2 — NER spaCy `fr_core_news_lg` pour anonymisation texte libre** —
  Q2 tranchée Story 10.7 → regex-only MVP (15 patterns PII FR/AO couvrent 95%
  des identifiants structurés). Le module `fr_core_news_lg` (500 MB) alourdit
  image Docker et CI time +2-3 min/run. **Trigger Phase Growth** : fuite PII
  détectée dans un pilote PME (nom propre en commentaire libre non-formaté
  dans `bio` ou `contact_person`). **Path** : modèle `fr_core_news_sm` (15 MB
  plus léger) + cache `actions/cache@v4` sur `~/.cache/spacy/` + image Docker
  pré-loadée. [backend/app/core/anonymization.py — PII_PATTERNS name_composed]

- **DEF-10.7-3 — AWS EventBridge cron trigger refresh STAGING** — Q4 tranchée
  Story 10.7 → GitHub Actions `schedule: cron '0 2 1 * *'` MVP (observabilité
  unifiée, coût zéro). **Trigger Phase Growth** : coordination avec events AWS
  (ex. post-backup RDS auto trigger refresh). **Path** : créer CloudWatch
  Events Rule + Lambda triggerer + IAM role dédié. Coût ~0.5 €/mois mais
  complexité ajoutée (2 resources AWS à manager hors Terraform workflows).

- **DEF-10.7-4 — Cross-account role separation admin/ops** — MVP : 1 IAM user
  Angenor avec MFA + assume-role. **Phase Growth** : compte AWS séparé
  `mefali-security` avec role `admin` assumé cross-account pour isoler
  credentials production des credentials dev solo. Trigger = 2ᵉ dev rejoint
  le projet ou audit SOC 2.

- **DEF-10.7-5 — Terragrunt bootstrap remote state automatisé** — MVP :
  procédure manuelle 3 étapes dans `infra/terraform/README.md` (bucket state
  + DynamoDB lock + init). **Phase Growth** : Terragrunt pour automatiser
  bootstrap + gérer envs multiples avec moins de duplication HCL. Trigger
  = 4ᵉ env (ex. `prod-eu-west-2` DR failover). Absorbe LOW-10.7-8 (duplication
  staging/prod main.tf ~90%).

## Deferred from: code review of story-10.7 (2026-04-20)

Findings **non bloquants** tracés lors du patch round 1. HIGH + 5 MEDIUM déjà traités (HIGH-10.7-1 workflow anonymize-refresh.yml, MEDIUM-10.7-1 CRR depends_on policy attach, MEDIUM-10.7-2 confused deputy replication, MEDIUM-10.7-3 regex wildcard stricte 9 patterns, MEDIUM-10.7-4 test assertions strictes + adversariaux, MEDIUM-10.7-5 state bucket isolé staging/prod).

- **LOW-10.7-1 — `test_failfast_raises_on_residual_pii` marqué `@pytest.mark.postgres` à tort** — le test utilise uniquement `tmp_path` + fichiers SQL locaux, aucun accès PG réel. Le marker le fait skipper en CI quick mode. **Drive-by** : retirer le marker lors de la prochaine passe sur ce fichier (test restera vert sans PG). [backend/tests/test_scripts/test_anonymize_prod_to_staging.py:142-166]

- **LOW-10.7-2 — `test_cli_requires_salt_env` teste une fonction privée `_require_salt`** — couplage fort à l'implémentation (underscore = privé). API internal acceptable MVP (le CLI CLI lui-même est testé via la fonction publique `anonymize_dump`). **Drive-by** : convertir en test subprocess E2E quand le CLI gagne des commandes supplémentaires. [backend/tests/test_scripts/test_anonymize_prod_to_staging.py:174-184]

- **LOW-10.7-3 — Bucket PROD sans `lifecycle { prevent_destroy = true }`** — un `terraform destroy` accidentel sur PROD supprime le bucket S3. Protection actuelle : `deletion_protection = true` sur RDS + MFA Condition sur delete objets S3. **Cible** : **Epic 20 Release Engineering hardening** — ajouter `prevent_destroy = true` conditionnel via module `s3_protected/` ou workflow force override contrôlé. **Important — à ne pas oublier avant premier client PROD**. [infra/terraform/modules/s3/main.tf:13-22]

- **LOW-10.7-4 — `container_image` accepte tag mutable (pas digest immuable)** — actuellement `ghcr.io/.../backend:staging-${sha}`. Rollback ECS non bit-exact si la tag est repoussée. **Cible** : **Phase Growth supply chain hardening** — digest `@sha256:...` exporté post-docker-push via `docker inspect --format='{{.RepoDigests}}'`. Aligné avec SLSA Level 2 roadmap. [infra/terraform/modules/ecs/main.tf:42-43]

- **LOW-10.7-5 — `SystemExit` sans exit code explicite dans `_require_salt`** — actuellement `raise SystemExit(f"...")` string → exit code 1 (Python default), confondu avec I/O error. **Drive-by** : `raise SystemExit(3)` pour salt missing + JSON audit log stderr. Mettre à jour docstring CLI. Trivial 5 lignes. [backend/scripts/anonymize_prod_to_staging.py:50-57]

- **LOW-10.7-6 — `phone_cedeao` exige `+` obligatoire (perd numéros locaux sans préfixe)** — compromis documenté Debug Log story (évite faux positifs sur hash SHA256 tronqué). Risque faux négatifs PII sur dumps qui stockent `77 123 45 67` sans `+221`. **Absorption** : **DEF-10.7-2 NER spaCy** couvrira les téléphones contextualisés (champ `mobile_local` détecté par NER) + ajout pattern `phone_local_sn` stricte opérateurs SN 70/77/78/76 sur premier dump PROD si régression détectée. [backend/app/core/anonymization.py:50-52]

- **LOW-10.7-7 — `name_composed` liste fermée 16 prénoms FR/AO** — absents fréquents CEDEAO : Marieme, Rokhaya, Awa, Binta, Bakary, Demba, Pape. Faux négatifs PII sur vrais dumps. **Absorption** : **DEF-10.7-2 NER spaCy** couvrira entity NER `PER` naturellement. **Entre-temps** : élargir à 30+ prénoms via review utilisateur pilote AO (drive-by trivial) ou constituer un dictionnaire étendu via dataset open source prénoms africains. [backend/app/core/anonymization.py:71-75]

- **LOW-10.7-8 — Duplication `staging/main.tf` ↔ `prod/main.tf` ~90%** — 109 lignes quasi-identiques (diff sur task_count/multi_az/crr_destination uniquement). Risque d'oubli backport (ex. ajout container_env en staging non répliqué prod). **Absorption** : **DEF-10.7-5 Terragrunt bootstrap** — factorisation native. **Entre-temps** : ajouter test `test_env_parity` qui compare les clés `container_env` des 2 fichiers (drive-by +1 test). [infra/terraform/envs/staging/main.tf ↔ infra/terraform/envs/prod/main.tf]

## Deferred from: code review of story-10-8-framework-injection-prompts-ccc9 (2026-04-21)

- **MEDIUM-10.8-4** — `build_prompt` ne pré-valide pas l'agrégat des `required_vars` manquantes. Boucle s'arrête à la 1ʳᵉ variable absente au lieu d'agréger toutes les manquantes. Pas critique aujourd'hui (`required_vars=()` pour les 3 instructions) — à reprendre quand une instruction utilisera des variables. [backend/app/prompts/registry.py:161-177]
- **LOW-10.8-1** — Type hint `vars_map: dict[str, str]` cohérence vs signature `Mapping[str, str]`. Pas de bug, à clarifier ou simplifier (inférence). [backend/app/prompts/registry.py:154]
- **LOW-10.8-3** — Duplication structure `_MODULE_BUILDERS` entre `_capture_golden.py` et `test_golden_snapshots.py`. DRY mineur — à factoriser dans `_canonical_profile.py`. [backend/tests/test_prompts/]
- **LOW-10.8-4** — `INSTRUCTION_REGISTRY: Final[tuple[...]]` ne protège pas contre `monkeypatch.setattr` sur le module (immutabilité runtime du tuple seulement, pas du binding). À documenter dans le docstring. [backend/app/prompts/registry.py:85]


## Story 10.8 — Patch round 1 (2026-04-21) — résolutions

- **HIGH-10.8-1 RESOLU** — `build_system_prompt` passe desormais par `build_prompt(module="chat", exclude_names=...)` via `exclude_names` ajoute au registre. `WIDGET_INSTRUCTION` n'est plus injecte manuellement dans `nodes.py:1197`. Promesse CCC-9 « 1-ligne » tient pour 7/7 modules.
- **HIGH-10.8-2 RESOLU** — `test_no_duplicate_imports.py` etend a `BACKEND_APP.rglob("*.py")` avec set `DOCUMENTED_DEBT_EXEMPTIONS` actuellement vide + meta-test anti-rot.
- **MEDIUM-10.8-1 RESOLU** — Marker `unit:` enregistre dans `pytest.ini`.
- **MEDIUM-10.8-3 RESOLU** — `_capture_golden.py` exige `--force` pour ecraser des goldens existants.
- **MEDIUM-10.8-2 N/A** — Bypass `system.py` resolu par HIGH-10.8-1, pas de dette a tracer.
- **LOW-10.8-2 RESOLU** — Story file corrige `build_esg_scoring_prompt` → `build_esg_prompt`.


## Deferred from: code review of story-10.15 (2026-04-22)

Items tracés post code-review Story 10.15 `ui/Button.vue`. Pour contexte complet, voir `_bmad-output/implementation-artifacts/10-15-code-review-2026-04-22.md`.

- **DEF-10.15-1 — Lucide Loader2 migration (spinner)** — **FERMÉ PARTIELLEMENT 10.21** : pile `lucide-vue-next` installée + `<EsgIcon name="loader" />` (Lucide `Loader2`) disponible. La migration mécanique du SVG inline de `Button.vue:145-160` a été **volontairement différée** post-investigation (cf. M-5 code review 10.21 + DEF-10.21-1 successeur ci-dessous). Le pattern `animate-spin` générique est équivalent visuellement, mais l'effet pulse opacity-25 (cercle) + opacity-75 (path) custom — qui donne au spinner Button son rendu "anneau tournant" distinct du simple trait rotatif Loader2 — n'est pas reproductible sans wrapper. **Ref succession** : DEF-10.21-1.

- **DEF-10.15-2 — Tokens `--color-brand-green-hover` / `-red-hover` dédiés** — Q5 Story 10.15 tranchée « pas de tokens hover dédiés MVP, `hover:opacity-90` suffit ». **Trigger Phase Growth** : pattern réutilisé > 2 fois hors `opacity-90` (par exemple si brand-blue/purple gagnent des hover différents, ou si design system évolue vers Material Ripple). **Path** : `main.css` ajouter `--color-brand-*-hover: <hex plus sombre>` pour chaque brand-*, puis remplacer `hover:opacity-90` par `hover:bg-brand-*-hover` dans `Button.vue` variant switches. [frontend/app/assets/css/main.css + frontend/app/components/ui/Button.vue:37,43]

- **DEF-10.15-3 — Loading button focusable AAA** — actuellement `Button.vue:100` bind `:disabled="isInactive"` où `isInactive = disabled || loading`. En HTML natif, `<button disabled>` n'est pas focusable au clavier, ce qui empêche l'utilisateur d'explorer l'état loading. Les ARIA Authoring Practices 1.2 recommandent `aria-busy="true"` + bouton **focusable** + intercepter le click via event handler (pattern déjà en place dans `handleClick`). **Impact MVP** : acceptable (WCAG AA non violé), mais best practice. **Trigger** : Story 10.21 refactor spinner Lucide + revue a11y approfondie. **Path** : changer bind à `:disabled="disabled && !loading"` + `:aria-disabled="isInactive ? 'true' : undefined"` + `:aria-busy="loading ? 'true' : undefined"`. [frontend/app/components/ui/Button.vue:100-103]

- **DEF-10.15-4 — Upgrade a11y harness vers Storybook runtime** — code review HIGH-2 a identifié que jest-axe en happy-dom ne résout pas `color-contrast` (retourne `incomplete`). Les 8 audits actuels sur 4 variants × 2 states ne couvrent donc pas AC7 contraste AA. **Trigger** : Story 10.16+ ou job CI dédié. **Path** : activer `npm run storybook:test -- --ci` en CI qui lance un navigateur réel avec Tailwind compilé + axe-core complet. Alternative : script Node dédié qui calcule WCAG contrast ratio sur tous les tokens `@theme` brand-*/verdict-* + fail si < 4,5:1 en normal text. [frontend/tests/components/ui/test_button_a11y.test.ts]


## Deferred from: code review of story-10.16 (2026-04-22)

Items tracés post code-review Story 10.16 `ui/{Input,Textarea,Select}`. Pour contexte complet, voir `_bmad-output/implementation-artifacts/10-16-code-review-2026-04-22.md`.

- **DEF-10.16-3 — Textarea prop `resize: 'y' | 'none' | 'both'` exposée** — Phase Growth. `Textarea.vue:144` hardcode `resize-y` ; piège #12 codemap acknowledge le layout risk mobile iOS landscape (keyboard + drag handle hors écran). MVP : consommateur contourne via classe externe (collision Tailwind merge). **Trigger** : > 2 contextes où resize-none est requis (carte compacte admin). **Path** : ajouter prop `resize?: 'y' | 'none' | 'both'` avec default `'y'`, 10 lignes. [frontend/app/components/ui/Textarea.vue:144]

- **DEF-10.16-4 — Coverage c8 batched 10.15+10.16+10.17** — AC9 Story 10.16 exige coverage ≥85 % non mesurée lors du dev (Task 8.8 reporte post-merge pattern 10.15). **Trigger** : avant close Story 10.17 Badge (ou job CI dédié). **Path** : `npm run test:coverage -- --reporter=json-summary` + parser dans script dédié + fail si < 85 % sur `app/components/ui/**`. Alternative : ajouter au package.json `"coverage:ui"` avec threshold Vitest coverage-c8. [frontend/vitest.config.ts + scripts/]

- **LOW-10.16-1 — `autocomplete: string` whitelist type** — `Input.vue:38` accepte chaîne arbitraire ; piège #14 codemap documente tokens MDN mais type ne contraint pas. Union template-literal des 60+ tokens trop ugly pour MVP. **Trigger** : > 2 bugs où custom token casse password manager en QA. **Path** : union prefix-based `'off' | 'on' | 'email' | 'username' | \`current-password\` | …` minimale 15 tokens. [frontend/app/components/ui/Input.vue:38]

- **LOW-10.16-2 — Select placeholder non-reselectable** — `Select.vue:126` rend `<option value="" disabled>` pour le placeholder ; user ne peut pas revenir à état vide après sélection. Limitation native MVP. **Trigger** : Story 10.19 Combobox (Reka UI expose clear button natif). **Path** : déplacement vers wrapper Reka UI `SelectRoot` (DEF-10.16-1 déjà tracé). [frontend/app/components/ui/Select.vue:126]

- **LOW-10.16-3 — `read-only:` variant Tailwind test visuel** — `Input.vue:161` + `Textarea.vue:142` utilisent `read-only:bg-gray-50` ; aucun test visuel (screenshot / Storybook) n'assert la classe appliquée. Runtime Tailwind v3.2+ OK. **Trigger** : régression visuelle non détectée sur un futur upgrade Tailwind. **Path** : ajouter story `Input.ReadonlyShowcase` + screenshot Chromatic baseline. [frontend/app/components/ui/Input.vue:161, Textarea.vue:142]

## Deferred from BUG-002/007/008 batch (2026-04-23)

- **MEDIUM-BUG002-1 — `isAuthenticated` sans expiry JWT** — `frontend/app/stores/auth.ts:10` calcule `isAuthenticated` via `!!accessToken.value` sans valider le claim `exp` du JWT. Un token expiré en localStorage passe le guard middleware → API retourne 401 sur tous les calls. **Trigger** : utilisateur avec token expiré voit des 401 en cascade sans redirection login. **Path** : décoder le JWT côté client (sans vérification signature) et comparer `exp * 1000` vs `Date.now()` dans `isAuthenticated` ou dans `loadFromStorage` → appel `clearAuth()` si expiré. Priorité avant mise en production.

- **LOW-BUG002-2 — Token JWT en `localStorage` (XSS surface)** — `frontend/app/stores/auth.ts:19` stocke les tokens en `localStorage` accessible à tout script injecté. Choix d'architecture connu pour les SPA sans SSR. **Path** : migration vers `httpOnly` cookies (requiert changement backend + nuxt.config runtimeConfig) — Story dédiée Epic 11+.

- **LOW-BUG008-1 — `financingStore.error` partagé entre 3 fetches** — Le champ `error` dans le store financement est écrasé par le dernier fetch ayant échoué. Si `fetchFunds` et `fetchMatches` échouent simultanément, seule l'erreur de `fetchFunds` sera visible. **Path** : créer des champs d'erreur distincts par fetch (`matchesError`, `fundsError`, `intermediariesError`) dans le store financement — refactoring Story Epic 11.

## Deferred from BUG-V2-001/002 chat regressions (2026-04-23)

- **DEF-BUG-V2-001-1 — Rappel linguistique « RAPPEL FINAL » absent des 6 nœuds spécialistes** — ✅ **RÉSOLU 2026-04-23** (spec `spec-bug-v2-batch-regressions-ux.md`). Pattern `"\n\nRAPPEL FINAL — " + LANGUAGE_INSTRUCTION` appendé en queue de `full_prompt` dans les 6 nœuds `esg_scoring_node`, `carbon_node`, `financing_node`, `credit_node`, `application_node`, `action_plan_node` dans `backend/app/graph/nodes.py`. Tests d'invariant statique : `tests/test_graph/test_specialists_language_reminder.py` (8 tests verts).
