# Story 9.3 : Fixer les 4 tests pré-existants rouges détectés en revue story 9.2

Status: done

**Priorité** : P1 (gouvernance qualité — findings méthodologiques audit 2026-04-16/17)
**Source** : [spec-audits/index.md §Findings méthodologiques « Zero failing tests on main »](./spec-audits/index.md) + [9-2 Debug Log ligne 324](./9-2-quota-cumule-stockage-par-utilisateur.md)
**Durée estimée** : 1 à 2 h (diagnostic + fix + validation)

<!-- Note : Validation est optionnelle. Lancer `validate-create-story` pour un quality check avant `dev-story`. -->

---

## Story

En tant que **responsable qualité de la plateforme Mefali**,
je veux que **les 4 tests pré-existants rouges (3 `test_guided_tour_*` + 1 `test_rate_limit_resets_after_60s`) soient fixés ou explicitement skippés avec un ticket**,
afin d'**honorer le principe « Zero failing tests on main » adopté par le cycle d'audit 2026-04-16/17 et restaurer la capacité de détecter les vraies régressions** (avec 4 échecs tolérés en baseline, une vraie régression future passe inaperçue : on ne peut plus distinguer un nouveau bug d'un vieux échec connu).

## Contexte

- La revue 2026-04-17 de la story 9.2 (quota stockage) a observé un état `1099 passed, 4 failed` sur `pytest tests/` ([9-2 Debug Log](./9-2-quota-cumule-stockage-par-utilisateur.md#L324)) — 3 échecs guided_tour déjà documentés comme baseline depuis 9.1 + 1 échec rate_limit **introduit par 9.1 elle-même et jamais fixé**.
- Les findings méthodologiques du cycle d'audit (spec-audits/index.md §Findings méthodologiques) stipulent : _« tolérer des tests rouges sur main normalise la dette technique et rend impossible la détection de vraies régressions »_. Règle adoptée : **zero failing tests on main**.
- Les 4 tests rouges actuels sur `main` (baseline mesuré le 2026-04-17 dans le venv Python 3.14) :
  1. `tests/test_chat.py::TestRateLimit::test_rate_limit_resets_after_60s` — `assert response.status_code == 429` échoue avec 200. Introduit par story 9.1, jamais passé.
  2. `tests/test_prompts/test_guided_tour_adaptive_frequency.py::test_guided_tour_instruction_unchanged` — `assert 3500 <= len(GUIDED_TOUR_INSTRUCTION) <= 7000` échoue avec `len = 7190`. Cassé par commit `8c71101` (2026-04-15, « fix(guided-tour): documenter les cles context par tour_id ») qui a étendu le prompt de ~1600 chars.
  3. `tests/test_prompts/test_guided_tour_consent_flow.py::test_ask_interactive_question_before_trigger_in_post_module_section` — `AssertionError: Ancre « Apres un module (proposition) » introuvable`. Même commit `8c71101` a renommé la section en « Proposition de guidage (post-module OU en cours d'echange) ».
  4. `tests/test_prompts/test_guided_tour_consent_flow.py::test_post_module_section_links_yes_to_trigger_guided_tour` — même root cause que #3 (helper `_post_module_section` qui cherche l'ancre disparue).
- Les 3 tests guided_tour ont été **explicitement tolérés** dans le baseline des stories 9.1 et 9.2 (cf. `T8 quality gate` des 2 stories : _« 3 échecs pré-existants sur guided_tour tolérés »_). Cette tolérance a accumulé 1 échec supplémentaire (rate_limit) → 4 échecs. La règle « zero failing » exige de fermer cette porte avant d'accumuler davantage.

---

## Critères d'acceptation

1. **AC1** — Given la suite de tests backend actuelle, When on exécute `pytest tests/ --tb=no -q`, Then le résultat final est **`1103 passed, 0 failed`** (ou équivalent selon le décompte exact après les fixes — aucune ligne `FAILED`, aucune ligne `ERROR`). Les warnings de deprecation (`DeprecationWarning` sur `asyncio.iscoroutinefunction`, `HTTP_413_REQUEST_ENTITY_TOO_LARGE`, etc.) restent tolérés (hors scope).

2. **AC2** — Given la cause racine identifiée sur chacun des 4 tests, When on lit le fichier de test corrigé, Then une **courte note explicative** (commentaire ≤ 3 lignes) documente la cause racine et la stratégie de fix appliquée (ex : _« Borne relevée suite à l'ajout de la section "Cles context par tour_id" dans le commit 8c71101 — prompt légitimement étendu »_). Objectif : éviter la perte de contexte lors d'une future régression.

3. **AC3** — Given le test `test_guided_tour_instruction_unchanged`, When il est corrigé, Then il **conserve son rôle de garde-fou anti-dérive** (une borne max réaliste, pas infinie) — pas de `@pytest.mark.skip` silencieux. Nouvelle borne acceptable : **`3500 <= len(GUIDED_TOUR_INSTRUCTION) <= 8000`** (7190 actuels + ~10 % de marge pour les micro-ajustements futurs). Le message d'assertion reste descriptif.

4. **AC4** — Given le helper `_post_module_section` de `test_guided_tour_consent_flow.py`, When il est corrigé pour la nouvelle ancre, Then il **couvre les 2 variantes de wording observées** (ancien : `"Apres un module (proposition)"` pour rétro-compat, nouveau : `"Proposition de guidage (post-module"` — accepter la première ancre trouvée), afin qu'un futur refactor partiel du prompt ne recasse pas les 2 tests à nouveau. Les 2 tests concernés (`test_ask_interactive_question_before_trigger_in_post_module_section` + `test_post_module_section_links_yes_to_trigger_guided_tour`) passent tous deux après le fix.

5. **AC5** — Given `test_rate_limit_resets_after_60s`, When il est corrigé, Then il **valide effectivement la sémantique de reset de fenêtre** (pas un skip). Le fix peut utiliser :
   - **Option A (recommandée)** : remplacer la simulation temporelle par `freezegun` par un appel explicite à `limiter.reset()` entre les 2 phases (avec un commentaire expliquant pourquoi `freezegun` seul ne suffit pas avec `MemoryStorage` de SlowAPI — cf. Dev Notes §Root cause #1).
   - **Option B (alternative)** : patcher directement `limits.storage.memory.time.time` via `monkeypatch.setattr` pour synchroniser le storage avec l'heure gelée.
   - **Interdit** : `@pytest.mark.skip(reason="freezegun incompatible with SlowAPI")` sans issue trackée — le principe « zero failing » exige un fix ou un skip tracké par un ticket explicite dans `deferred-work.md`.

6. **AC6** — Given la baseline actuelle `1099 passed, 4 failed`, When on ré-exécute `pytest tests/ --tb=no -q` après le fix, Then le temps d'exécution **reste sous 200 s** (baseline 163 s observé le 2026-04-17) — un fix qui ralentirait significativement la suite (ex : un `time.sleep(61)` littéral) est refusé.

7. **AC7** — Given le principe « Zero failing tests on main », When la story est clôturée, Then une **entrée dédiée est ajoutée à `deferred-work.md`** (section _« Resolved (2026-04-17) »_) documentant les 4 fixes avec référence aux commits source des régressions (`8c71101` pour les 3 guided_tour, story 9.1 pour le rate_limit). Cette trace sert de référence si des régressions similaires apparaissent.

---

## Tasks / Subtasks

- [x] **T1 — Fix `test_guided_tour_instruction_unchanged` (AC1, AC2, AC3)**
  - [x] Dans [backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py](../../backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py) ligne 172, remplacer `assert 3500 <= len(GUIDED_TOUR_INSTRUCTION) <= 7000` par `assert 3500 <= len(GUIDED_TOUR_INSTRUCTION) <= 8000`.
  - [x] Maj le commentaire ligne 168-171 pour refléter la nouvelle borne :
    ```python
    # Valeur de reference au moment de la story 6.3 — toute derive > 15 %
    # indique une modification non intentionnelle du contrat cible par les
    # 16+17 tests existants. Relevee a 8000 le 2026-04-17 pour accueillir
    # la section « Cles context par tour_id » (commit 8c71101 post-fix BUG-1)
    # qui a legitimement etendu le prompt de ~1600 chars.
    ```
  - [x] Vérifier : `pytest tests/test_prompts/test_guided_tour_adaptive_frequency.py::test_guided_tour_instruction_unchanged -v` → **vert**.

- [x] **T2 — Fix helper `_post_module_section` pour nouvelle ancre (AC1, AC2, AC4)**
  - [x] Dans [backend/tests/test_prompts/test_guided_tour_consent_flow.py](../../backend/tests/test_prompts/test_guided_tour_consent_flow.py) lignes 24-41, modifier le helper `_post_module_section` pour accepter les 2 variantes de wording :
    ```python
    def _post_module_section(text: str) -> str:
        """Extrait la section post-module du prompt.

        Supporte 2 ancres (pre- et post-commit 8c71101 du 2026-04-15) :
        - Ancienne : « Apres un module (proposition) »
        - Nouvelle : « Proposition de guidage (post-module »
        On cherche la premiere ancre presente. L'ancre de fin reste
        « Sur demande explicite (declenchement direct) » (inchangee).
        """
        anchors = [
            "Proposition de guidage (post-module",  # post-2026-04-15
            "Apres un module (proposition)",         # pre-2026-04-15 (retro-compat)
        ]
        start = -1
        for anchor in anchors:
            start = text.find(anchor)
            if start != -1:
                break
        assert start != -1, (
            "Aucune ancre de section post-module trouvee "
            f"(essaye: {anchors}) — la section normative de consentement "
            "a ete renommee au-dela des variantes supportees."
        )
        end = text.find("Sur demande explicite (declenchement direct)", start)
        assert end != -1, (
            "Ancre « Sur demande explicite (declenchement direct) » introuvable — "
            "verifier l'integrite de la section normative."
        )
        return text[start:end]
    ```
  - [x] **Ne pas modifier les 2 tests eux-mêmes** (`test_ask_interactive_question_before_trigger_in_post_module_section`, `test_post_module_section_links_yes_to_trigger_guided_tour`) : leur logique reste valide dès que le helper trouve la section.
  - [x] Vérifier : `pytest tests/test_prompts/test_guided_tour_consent_flow.py -v` → **tous les tests verts** (ces 2 + les 10 autres déjà verts de la même classe).

- [x] **T3 — Fix `test_rate_limit_resets_after_60s` (AC1, AC2, AC5, AC6)**
  - [x] Dans [backend/tests/test_chat.py](../../backend/tests/test_chat.py) lignes 534-569, remplacer l'usage combiné `freeze_time + frozen.tick(delta=61)` par un reset explicite du limiter :
    ```python
    async def test_rate_limit_resets_after_60s(self, client: AsyncClient) -> None:
        """AC2 — Apres reinitialisation de la fenetre de rate limiting, le
        message suivant passe. On simule le « apres 60s » par un reset
        explicite du storage SlowAPI car freezegun ne peut pas patcher
        time.time() dans le thread `threading.Timer` de `MemoryStorage`
        (voir Dev Notes §Root cause #1 de la story 9.3).
        """
        from app.core.rate_limit import limiter

        _, token = await create_authenticated_user(client)
        create_resp = await client.post(
            "/api/chat/conversations", json={}, headers=auth_headers(token)
        )
        conv_id = create_resp.json()["id"]

        with (
            patch("app.api.chat.stream_graph_events", side_effect=self._mock_stream),
            patch("app.api.chat.async_session_factory", self._make_mock_session_factory()),
        ):
            # Phase 1 : saturer la fenetre (30 messages OK + 1 refuse)
            for i in range(30):
                status_code = await self._send_one_message(client, conv_id, token, f"m{i}")
                assert status_code == 200

            response = await client.post(
                f"/api/chat/conversations/{conv_id}/messages",
                data={"content": "depassement"},
                headers=auth_headers(token),
            )
            assert response.status_code == 429

            # Phase 2 : reset explicite du limiter (equivalent « 60s passes »)
            limiter.reset()

            status_code = await self._send_one_message(
                client, conv_id, token, "apres fenetre"
            )

        assert status_code == 200
    ```
  - [x] Retirer l'import `from freezegun import freeze_time` dans cette fonction (ne plus nécessaire ici — les autres tests de la classe ne l'utilisent pas non plus).
  - [x] **Attention au reset_rate_limiter autouse fixture** : `reset_rate_limiter` dans [conftest.py:43-53](../../backend/tests/conftest.py) appelle déjà `limiter.reset()` avant CHAQUE test. Dans ce test précis, on doit appeler `limiter.reset()` **au milieu** du test (pas avant/après), d'où l'appel explicite. Conserver le commentaire qui explique cette subtilité.
  - [x] Vérifier : `pytest tests/test_chat.py::TestRateLimit -v` → **6/6 verts** (les 5 autres tests de la classe ne doivent pas régresser). _Note dev : la classe compte 6 méthodes `test_*`, pas 7 — rectification par rapport à l'estimation initiale._

- [x] **T4 — Documentation dans `deferred-work.md` (AC7)**
  - [x] Ajouter dans [_bmad-output/implementation-artifacts/deferred-work.md](./deferred-work.md) une section « Resolved (2026-04-17) » en haut du fichier (avant « Deferred from: code review of 9-2 ... ») :
    ```markdown
    ## Resolved (2026-04-17) — Story 9.3 : fix 4 tests pre-existants rouges

    ### 3 tests `test_guided_tour_*` cassés par le commit `8c71101` (2026-04-15)

    - **Root cause** : le commit `8c71101 fix(guided-tour): documenter les cles context par tour_id` a (1) etendu `GUIDED_TOUR_INSTRUCTION` de ~1600 caracteres (5600 → 7190, depassant la borne `<=7000` du test `test_guided_tour_instruction_unchanged`), (2) renomme la section « Apres un module (proposition) » en « Proposition de guidage (post-module OU en cours d'echange) » (cassant l'ancre du helper `_post_module_section` utilise par 2 tests de `test_guided_tour_consent_flow.py`).
    - **Correctif** : borne du test adaptive_frequency relevee a `<=8000` (+~10 % marge). Helper `_post_module_section` mis a jour pour accepter les 2 variantes de wording (retro-compat pre- et post-commit 8c71101).
    - **Fichiers** : `backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py` + `backend/tests/test_prompts/test_guided_tour_consent_flow.py`.

    ### `test_rate_limit_resets_after_60s` (introduit par story 9.1, jamais passe)

    - **Root cause** : le test utilisait `freezegun.freeze_time` + `frozen.tick(delta=61)` pour simuler le passage de 60s, mais cela ne fonctionne pas avec SlowAPI/`limits.storage.memory.MemoryStorage`. Le `MemoryStorage` demarre un `threading.Timer(0.01, __expire_events)` au constructor qui tourne dans un thread separe avec le vrai `time.time()`. Consequence : les cles d'expiration du storage sont evaluees avec le temps reel (hors freezegun), les compteurs peuvent etre effaces prematurement, et le test est instable/faux positif selon le timing.
    - **Correctif** : remplacement de `freeze_time + tick` par un appel explicite a `limiter.reset()` entre les 2 phases du test. Equivalent semantique (« la fenetre est reinitialisee »), determinisme preserve, zero dependance a freezegun sur ce test.
    - **Fichier** : `backend/tests/test_chat.py` — methode `TestRateLimit.test_rate_limit_resets_after_60s`.

    ### Validation post-fix
    - `pytest tests/` → **1103 passed, 0 failed** (baseline 1099/4 avant fix)
    - Temps d'execution : ~185 s (baseline ~163 s, plafond AC6 = 200 s — marge OK)
    - Principe « Zero failing tests on main » restaure — toute regression future est detectable.
    ```
  - [x] Valider le formatage Markdown (indentation des blocs, backticks autour des noms de fichiers/commits).

- [x] **T5 — Quality gate (AC1, AC6)**
  - [x] `pytest tests/ --tb=no -q` → **`1103 passed, 0 failed`** (décompte exact, zero warning supplémentaire vs baseline).
  - [x] `time pytest tests/ --tb=no -q` → **185.60 s** (baseline 163 s, marge OK sous le plafond 200 s).
  - [x] `pytest tests/test_chat.py::TestRateLimit -v` → **6/6 verts**, aucun skip.
  - [x] `pytest tests/test_prompts/test_guided_tour_adaptive_frequency.py tests/test_prompts/test_guided_tour_consent_flow.py -v` → **tous verts**, aucun skip.
  - [x] `ruff check tests/test_chat.py tests/test_prompts/test_guided_tour_adaptive_frequency.py tests/test_prompts/test_guided_tour_consent_flow.py` → 2 warnings F401 **pré-existants** (confirmés par `git stash + ruff check` sur HEAD pre-9.3, lignes 336 et 378 — tests distincts de ceux modifiés par 9.3). **Zero régression ruff introduite.**
  - [x] `git diff` : **3 fichiers de tests** (`test_chat.py` + `test_guided_tour_adaptive_frequency.py` + `test_guided_tour_consent_flow.py`) + `deferred-work.md` + fichier story + sprint-status.yaml. **Aucun fichier `app/` modifié** — story 100 % test-only confirmée.

---

## Dev Notes

### Root cause #1 — `test_rate_limit_resets_after_60s` : incompatibilité `freezegun` / `MemoryStorage.__expire_events`

Le storage par défaut de SlowAPI, `limits.storage.memory.MemoryStorage`, démarre au constructor un `threading.Timer(0.01, self.__expire_events)` qui tourne dans un **thread séparé** (cf. [limits/storage/memory.py source](https://github.com/alisaifee/limits/blob/main/limits/storage/memory.py)). Ce thread utilise le vrai `time.time()` et nettoie les clés dont `expirations[key] <= time.time()`.

Quand un test fait `freeze_time('2026-04-17 10:00:00')` puis envoie 30 messages, le storage écrit des clés avec `expirations[key] = time.time() + 60 = T0_freeze + 60`. Mais le thread `__expire_events` (hors freezegun) compare avec le temps réel (plus tardif que T0_freeze dans la plupart des contextes de test), et peut donc effacer les compteurs **avant** le 31ᵉ message. Résultat : le 31ᵉ message passe en 200 alors qu'il devrait être 429. Test non déterministe / faux positif.

**Fix adopté** : supprimer la dépendance à freezegun dans ce test. Remplacer la simulation temporelle par `limiter.reset()` entre les phases — équivalent sémantique (« la fenêtre est réinitialisée »), entièrement déterministe, 0 thread.

**Alternative rejetée** : `monkeypatch.setattr(limits.storage.memory.time, 'time', lambda: ...)` — fragile car dépend du nom de l'attribut interne du module `limits`, qui peut changer en mineur.

**Alternative rejetée** : `time.sleep(61)` — ralentit la suite de 61 s, viole AC6.

### Root cause #2 — `GUIDED_TOUR_INSTRUCTION` étendu par le commit `8c71101`

Le commit `8c71101` (2026-04-15, `fix(guided-tour): documenter les cles context par tour_id dans GUIDED_TOUR_INSTRUCTION`) a ajouté **25 lignes** dans [backend/app/prompts/guided_tour.py](../../backend/app/prompts/guided_tour.py), apportant 2 changements qui cassent 3 tests :

1. **Nouvelle section « Cles `context` par tour_id »** (lignes 53-76 actuelles) + nouvelle règle 5 « Separation guidage vs segmentation metier » + durcissement de la règle 1 (« EXACTEMENT 2 options, PAS PLUS »). Total : +~1600 caractères, portant `len(GUIDED_TOUR_INSTRUCTION)` de ~5600 à 7190 — **dépasse la borne max 7000** du test `test_guided_tour_instruction_unchanged`.

2. **Renommage de la règle 1** de `« Apres un module (proposition) »` en `« Proposition de guidage (post-module OU en cours d'echange) »` (ligne 91 actuelle). **Casse l'ancre** utilisée par le helper `_post_module_section` dans `test_guided_tour_consent_flow.py` — 2 tests rouges en cascade (les 2 qui appellent ce helper).

Ces 2 changements sont **légitimes** (ils documentent un contrat devenu critique avec la feature 019 guided-tour) et ne doivent pas être reverted. Le fix concerne uniquement les tests qui verrouillaient un état ancien du prompt.

### Stratégie de fix retenue — pourquoi pas un skip ?

Le principe « Zero failing tests on main » (findings méthodologiques 2026-04-17) exige soit un fix actif, soit un skip explicite avec ticket tracké. Ici, **les 4 tests sont tous fixables en < 10 lignes chacun** — pas de justification pour skipper. Les tests conservent leur rôle d'anti-régression après fix :

- `test_guided_tour_instruction_unchanged` reste un garde-fou de dérive (borne max relevée, pas supprimée).
- `_post_module_section` helper accepte les 2 wordings — rétro-compat si le prompt change à nouveau.
- `test_rate_limit_resets_after_60s` valide désormais la **sémantique de reset** (ce qui était l'intention originale) plutôt que la **simulation temporelle freezegun** (qui était un moyen, pas une fin).

### Pièges à éviter

- **Ne pas ajouter `@pytest.mark.skip` silencieux** : viole le principe zero failing + complique le suivi. Si un test est vraiment infixable, créer une entrée `deferred-work.md` AVEC ticket et justification — pas le cas ici, les 4 tests sont fixables.
- **Ne pas modifier `GUIDED_TOUR_INSTRUCTION`** : le prompt est correct, ce sont les tests qui doivent s'adapter. Modifier le prompt reverted le commit `8c71101` et casserait la feature 019.
- **Ne pas toucher à la fixture `reset_rate_limiter`** de [conftest.py:43-53](../../backend/tests/conftest.py) : elle est autouse et appelée AVANT chaque test. Dans le test `test_rate_limit_resets_after_60s`, on appelle `limiter.reset()` **au milieu** — ne pas confondre. Documenter cette subtilité dans le commentaire du test.
- **Ne pas changer la borne min (3500) du test adaptive_frequency** : elle sert à détecter une **suppression accidentelle massive** du prompt (ex : un refactor qui aurait viré 70 % du contenu). Seule la borne max change.
- **`freezegun` reste utilisable ailleurs** : la story 9.1 fonctionne avec freezegun sur les autres tests (pas de `MemoryStorage` actif). C'est **uniquement** l'interaction `freezegun` + `threading.Timer` de SlowAPI qui pose problème. Ne pas généraliser une interdiction de freezegun.
- **Attention aux 2 règles « 5 »** dans `guided_tour.py` : le prompt actuel a 2 règles numérotées `5` (Separation guidage + Securite context) — bug cosmétique du commit 8c71101 mais **hors scope** de cette story (9.3 = tests seulement). Ne pas corriger le prompt, noter la dette dans `deferred-work.md` si besoin.

### Architecture actuelle — repères

- **Tests concernés** (3 fichiers, 4 tests) :
  - [backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py:163-173](../../backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py) — `test_guided_tour_instruction_unchanged` (10 lignes, une assertion de longueur).
  - [backend/tests/test_prompts/test_guided_tour_consent_flow.py:24-41](../../backend/tests/test_prompts/test_guided_tour_consent_flow.py) — helper `_post_module_section` (17 lignes). Utilisé par les tests lignes 63-80 et 83-106.
  - [backend/tests/test_chat.py:534-569](../../backend/tests/test_chat.py) — `test_rate_limit_resets_after_60s` (35 lignes, avec freezegun).
- **Prompt impliqué** : [backend/app/prompts/guided_tour.py](../../backend/app/prompts/guided_tour.py) (174 lignes, constante `GUIDED_TOUR_INSTRUCTION`). **Ne pas modifier**.
- **Limiter SlowAPI** : [backend/app/core/rate_limit.py](../../backend/app/core/rate_limit.py) — `limiter.reset()` appelable, utilise `MemoryStorage` par défaut.
- **Fixture autouse** : [backend/tests/conftest.py:43-53](../../backend/tests/conftest.py) `reset_rate_limiter` — s'exécute avant chaque test, ne pas modifier.
- **Python 3.14.2** (venv), pytest 9.0.2, pytest-asyncio 1.3.0 en mode `auto` (cf. [pytest.ini](../../backend/pytest.ini)).

### Références

- [Source : _bmad-output/implementation-artifacts/spec-audits/index.md §Findings méthodologiques « Zero failing tests on main »](./spec-audits/index.md)
- [Source : _bmad-output/implementation-artifacts/9-2-quota-cumule-stockage-par-utilisateur.md#L324](./9-2-quota-cumule-stockage-par-utilisateur.md) : baseline `1099 passed, 4 failed`
- [Source : _bmad-output/implementation-artifacts/9-1-rate-limiting-fr013-chat-endpoint.md](./9-1-rate-limiting-fr013-chat-endpoint.md) : origine du test `test_rate_limit_resets_after_60s`
- **Commit source des régressions guided_tour** : `8c71101 fix(guided-tour): documenter les cles context par tour_id dans GUIDED_TOUR_INSTRUCTION` (2026-04-15) — légitime, à conserver.
- **Pattern de référence** : [9-2 §T8 quality gate](./9-2-quota-cumule-stockage-par-utilisateur.md) pour la structure « test-only story + validation baseline ».
- [Source : docs SlowAPI — Limiter.reset()](https://slowapi.readthedocs.io/en/latest/#reset) : `reset()` vide le storage global, à appeler manuellement au milieu d'un test pour simuler un passage de fenêtre.

---

## Hors scope (stories futures)

- **Bug cosmétique : 2 règles numérotées `5`** dans `GUIDED_TOUR_INSTRUCTION` (lignes 118 et 124 actuelles) — hérité du commit `8c71101`. Trivial à fixer mais **hors scope 9.3** (test-only). À adresser dans une micro-story P3 de toilettage du prompt guided_tour.
- **Décision produit sur la taille max de `GUIDED_TOUR_INSTRUCTION`** : on relève à 8000 mais le prompt continuera probablement à grandir. Décider si on veut un snapshot strict (checksum, `pytest-snapshot`) ou accepter des bornes larges.
- **Audit systématique de tous les usages `freezegun` dans la suite** : éviter que la même classe de bug (freezegun + lib externe utilisant `threading.Timer` ou `time.monotonic()`) ne revienne ailleurs. Hors scope 9.3.
- **Protection de branche GitHub « Zero failing tests on main »** : la règle est documentée dans les findings méthodologiques mais pas encore enforcée via `.github/workflows/` ou GitHub branch protection. À ajouter dans une story gouvernance (P1 #29 du backlog audit).
- **Nettoyage des `DeprecationWarning`** de Python 3.14 (`asyncio.iscoroutinefunction`, `HTTP_413_REQUEST_ENTITY_TOO_LARGE`, etc.) : hors scope, pas bloquant.

---

## Structure projet — alignement

- **Aucun fichier de production modifié** — 100 % test-only + doc.
- **Fichiers modifiés** :
  - `backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py` — ajustement borne max + commentaire (~4 lignes modifiées).
  - `backend/tests/test_prompts/test_guided_tour_consent_flow.py` — helper `_post_module_section` accepte 2 ancres (~15 lignes modifiées).
  - `backend/tests/test_chat.py` — refactor `test_rate_limit_resets_after_60s` : retirer `freeze_time`, utiliser `limiter.reset()` (~20 lignes modifiées, dont commentaire).
  - `_bmad-output/implementation-artifacts/deferred-work.md` — nouvelle section « Resolved (2026-04-17) — Story 9.3 » (~25 lignes ajoutées).
- **Conventions respectées** :
  - Python PEP 8, `ruff` clean sur les diffs.
  - Type annotations conservées (rien à ajouter — les tests n'en ont pas eu besoin).
  - Commentaires en français avec accents (é, è, à, ç) selon CLAUDE.md.
  - Messages d'assertion descriptifs (helpers pour `AssertionError`).
  - Aucun `@pytest.mark.skip` silencieux ajouté.
- **Dark mode non-impacté** : aucune UI dans cette story.
- **Pas de migration BDD** : aucun changement de schéma.
- **Pas de changement d'API** : zéro endpoint touché.

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (1M context) — `claude-opus-4-7[1m]` — via workflow `/bmad-dev-story` (2026-04-17).

### Debug Log References

- **Baseline RED confirmée** (2026-04-17) :
  ```
  pytest tests/test_prompts/test_guided_tour_adaptive_frequency.py::test_guided_tour_instruction_unchanged \
         tests/test_prompts/test_guided_tour_consent_flow.py::test_ask_interactive_question_before_trigger_in_post_module_section \
         tests/test_prompts/test_guided_tour_consent_flow.py::test_post_module_section_links_yes_to_trigger_guided_tour \
         tests/test_chat.py::TestRateLimit::test_rate_limit_resets_after_60s
  ```
  → `4 failed, 3 warnings in 2.06s` — root causes identiques à celles documentées dans les Dev Notes (borne 7190 > 7000, ancre « Apres un module » renommée, freezegun/MemoryStorage non-déterministe).

- **Ruff baseline pré-9.3** (via `git stash push -- backend/tests/test_chat.py && ruff check`) : **2 F401 pré-existants** (`AsyncMock` ligne 336, `test_session_factory` ligne 378) — **confirmés comme dettes hors scope**, non introduits par 9.3.

- **Validation post-fix (T1+T2+T3)** : les 4 tests ciblés passent individuellement après correctif. Puis suite complète :
  ```
  pytest tests/ --tb=no -q  →  1103 passed, 0 failed, 16 warnings in 185.60s
  ```
  — pytest full < 200 s (AC6 OK), 0 failed (AC1 OK), 16 warnings pré-existants uniquement (DeprecationWarning asyncio / HTTP_413_REQUEST_ENTITY_TOO_LARGE / SwigPyPacked / Pydantic v2 — tous hors scope 9.3).

### Completion Notes List

- **T1** résolu : borne max relevée de 7000 à 8000 (marge +~10 %) sur `test_guided_tour_instruction_unchanged`. Commentaire actualisé (référence commit `8c71101`, date 2026-04-17, dérive tolérée 15 %). La borne min 3500 reste inchangée — elle garde son rôle anti-régression de suppression massive.
- **T2** résolu : helper `_post_module_section` refactoré pour tester 2 ancres en cascade (nouvelle d'abord, ancienne en fallback). Les 2 tests métier (`test_ask_interactive_question_before_trigger_in_post_module_section` + `test_post_module_section_links_yes_to_trigger_guided_tour`) passent sans modification. Docstring et message d'assertion actualisés pour refléter le support des 2 wordings.
- **T3** résolu : `test_rate_limit_resets_after_60s` ré-écrit pour utiliser `limiter.reset()` entre les 2 phases (au lieu de `freeze_time` + `frozen.tick`). Suppression de l'import `freezegun` (local à la méthode). Nouveau commentaire docstring documente (a) la root cause `MemoryStorage.__expire_events` + `threading.Timer` / `time.time()`, (b) la coexistence avec la fixture autouse `reset_rate_limiter`. Création utilisateur/conversation extraite du `with` pour simplifier la structure (pas de contrainte `freeze_time` sur l'issuance JWT). 6/6 `TestRateLimit` verts en 7.73 s.
- **T4** résolu : section « Resolved (2026-04-17) — Story 9.3 » ajoutée en tête de `deferred-work.md` avec 3 sous-sections (guided_tour ×3 / rate_limit / Validation post-fix). Référence explicite au commit `8c71101` comme source des 3 régressions guided_tour + story 9.1 comme source de la régression rate_limit.
- **T5** résolu : quality gate complet passé — 1103 tests verts en 185.60 s, ruff zéro régression, scope 100 % test-only + doc validé (aucun fichier `app/` touché par 9.3).
- **Hors scope respecté** : le prompt `GUIDED_TOUR_INSTRUCTION` n'a pas été modifié (contrat feature 019 préservé). Le bug cosmétique « 2 règles 5 » dans `guided_tour.py` reste ouvert pour une micro-story P3 future. Aucun `@pytest.mark.skip` silencieux ajouté.

### File List

Fichiers modifiés par la story 9.3 (relatif à la racine du repo) :

- `backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py` — ajustement borne max + commentaire (5 lignes modifiées).
- `backend/tests/test_prompts/test_guided_tour_consent_flow.py` — helper `_post_module_section` refactoré (liste d'ancres + fallback + docstring actualisée, 27 lignes modifiées).
- `backend/tests/test_chat.py` — refactor `test_rate_limit_resets_after_60s` uniquement (~38 lignes modifiées au titre de 9.3 : suppression `freeze_time`/`frozen.tick`, ajout `limiter.reset()` explicite, docstring enrichie). **Note** : le `git diff` brut affiche ~231 lignes ajoutees car la classe `TestRateLimit` entiere (6 methodes) vient de la story 9.1 non committee et apparait dans le diff. Seule la methode `test_rate_limit_resets_after_60s` est le fix 9.3 a proprement parler.
- `_bmad-output/implementation-artifacts/deferred-work.md` — nouvelle section « Resolved (2026-04-17) — Story 9.3 » (25 lignes ajoutées en tête).
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — transition `ready-for-dev` → `in-progress` → `review` + `last_updated`.
- `_bmad-output/implementation-artifacts/9-3-fix-4-tests-pre-existants-rouges.md` — Status + cases Tasks/Subtasks + Dev Agent Record + File List + Change Log.

**Aucun fichier `backend/app/` modifié.** Aucune migration Alembic. Aucun endpoint touché.

### Change Log

| Date       | Version | Description                                                                             | Author  |
|------------|---------|-----------------------------------------------------------------------------------------|---------|
| 2026-04-17 | 0.1.0   | Création de la story (create-story depuis findings audit 2026-04-16/17).                | PM      |
| 2026-04-17 | 1.0.0   | Implémentation 9.3 — fix 4 tests pré-existants rouges (T1–T4) + quality gate T5 passé. | dev agent |
| 2026-04-17 | 1.1.0   | Code review : 8 patches appliqués (aread manquants, commentaire 14 %, test_401_not_429 × 31 req, alignements doc). 7 defers tracés. 25/25 tests affectés verts. Status → done. | reviewer |

### Review Findings (code review 2026-04-17)

**Patches (8) — corrections non ambiguës à appliquer :**

- [x] [Review][Patch] Commentaire obsolète : dit « dérive > 15 % » alors que la nouvelle fenêtre 3500-8000 correspond à ~14 % de marge vs l'ancienne 7000 — harmoniser le chiffre [backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py:168-171]
- [x] [Review][Patch] `test_rate_limit_unauthenticated_returns_401_not_429` n'exerce pas réellement le limiter : une seule requête sans token suffit à valider AC7 mais ne prouve pas que le 401 précède bien le rate-limit. Envoyer 31 requêtes sans token pour démontrer qu'aucune ne bascule en 429 [backend/tests/test_chat.py:647-657]
- [x] [Review][Patch] `await response.aread()` manquant sur les réponses 429 finales des tests `test_rate_limit_trips_at_31st_message` et `test_rate_limit_on_json_fallback_endpoint` — potentielle fuite HTTPX/connexion non fermée en cas de croissance de la suite [backend/tests/test_chat.py:132-136, 278-284]
- [x] [Review][Patch] Incohérence doc : `deferred-work.md` affirme « ~10 % marge » alors que la borne passe de 7000 à 8000, soit +14 % effectif [_bmad-output/implementation-artifacts/deferred-work.md:13]
- [x] [Review][Patch] `File List` de la story sous-évalue la taille de `test_chat.py` (« ~38 lignes modifiées » déclarées vs 231 lignes ajoutées au diff). Clarifier que l'essentiel provient de la classe `TestRateLimit` de la story 9.1 non committée, et que seule la méthode `test_rate_limit_resets_after_60s` est le fix 9.3 à proprement parler [_bmad-output/implementation-artifacts/9-3-fix-4-tests-pre-existants-rouges.md:317]
- [x] [Review][Patch] Section « Validation post-fix » de `deferred-work.md` : rappelle « 0 failed » mais omet le décompte complet « 1103 passed » demandé par T4 [_bmad-output/implementation-artifacts/deferred-work.md:22]
- [x] [Review][Patch] Section « Validation post-fix » de `deferred-work.md` : omet la ligne « Temps d'exécution : ~185 s (baseline ~163 s, plafond 200 s) » pourtant demandée par T4 [_bmad-output/implementation-artifacts/deferred-work.md:22-27]
- [x] [Review][Patch] Divergence interne au spec : T4 §Validation post-fix mentionne « ~165 s » attendu alors que T5 observe « 185.60 s ». Aligner la valeur citée par T4 sur la mesure réelle [_bmad-output/implementation-artifacts/9-3-fix-4-tests-pre-existants-rouges.md:169 vs 176]

**Defer (7) — pré-existant ou hors scope strict 9.3 :**

- [x] [Review][Defer] Mock `session.execute` retourne inconditionnellement `scalar_one_or_none=None`. L'endpoint `/messages` fonctionne par coïncidence si aucune branche lookup ne 404. Rendre le mock explicite sur chaque query [backend/tests/test_chat.py:449-452] — deferred, code 9.1 non committé
- [x] [Review][Defer] Mock `session.refresh` écrase l'`id` à chaque appel (`setattr(m, "id", uuid.uuid4())`). Un même objet refraîchi 2× reçoit 2 ids différents, masquant un bug de refetch [backend/tests/test_chat.py:446-448] — deferred, code 9.1 non committé
- [x] [Review][Defer] Dépendance implicite à la fixture autouse `reset_rate_limiter` non tracée par import dans `TestRateLimit`. Si la fixture disparaît ou est renommée, tous les tests deviennent flaky en silence [backend/tests/test_chat.py:TestRateLimit] — deferred, robustesse fixture
- [x] [Review][Defer] Section « Resolved 2026-04-17 » de `deferred-work.md` n'est pas liée au hash git du commit de fix. Casse la traçabilité audit [_bmad-output/implementation-artifacts/deferred-work.md:3] — deferred, commit inexistant car changements uncommitted
- [x] [Review][Defer] Fragilité `pytest-xdist` : `limiter.reset()` partage le storage entre workers parallèles, pourrait provoquer des flakes si xdist est activé [backend/tests/test_chat.py:571] — deferred, xdist non actif actuellement
- [x] [Review][Defer] `limiter.reset()` est `MemoryStorage`-only ; casserait silencieusement sur un Redis futur (hors scope V1 explicite) [backend/tests/test_chat.py:571] — deferred, V1 in-memory documentée
- [x] [Review][Defer] Bug cosmétique « 2 règles numérotées 5 » dans `guided_tour.py` non mentionné dans la section Resolved 2026-04-17. Spec Hors scope §1 parle d'une « micro-story P3 future » — au moins tracer un bullet explicite [backend/app/prompts/guided_tour.py:118,124] — deferred, micro-story P3 future

**Dismissed (20)** — bruit, faux positifs, ou explicitement couverts par le spec (Hors scope, AC5 Option A `limiter.reset` sémantique acceptée, AC3 borne 8000 validée par spec, duplication tests 9.1 hors scope, imports locaux cosmétiques, typo « precéder » dans code 9.1, ancre tronquée choisie délibérément, docstring 8 lignes vs commentaire inline, vérification contenu prompt hors portée du test, etc.).
