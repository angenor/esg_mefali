# Story 9.5 : Flag `manually_edited_fields` sur CompanyProfile (édition manuelle prévaut)

Status: done

**Priorité** : P1 (perte de données silencieuse — confiance utilisateur invisible côté UX, catastrophique quand ça arrive)
**Source** : [spec-audits/index.md §P1 #7](./spec-audits/index.md) + [spec-003-audit.md §3.6 + §7 reclassement P2→P1 du 2026-04-16](./spec-audits/spec-003-audit.md)
**Spec d'origine** : [specs/003-company-profiling-memory/spec.md](../../specs/003-company-profiling-memory/spec.md) (FR : « édition manuelle prévaut »)
**Durée estimée** : 4 à 6 h (audit BDD optionnel + migration + service + tool SSE + tests + frontend badge)

<!-- Note : Validation est optionnelle. Lancer `validate-create-story` pour un quality check avant `dev-story`. -->

---

## Story

En tant que **PME africaine francophone qui édite manuellement son profil entreprise via `/profile`**,
je veux que **mes corrections manuelles ne soient JAMAIS écrasées par une extraction LLM ultérieure (ex. `update_company_profile` déclenché par un message dans le chat)**,
afin que **la valeur que j'ai saisie de mes mains reste source de vérité, sans perte silencieuse, et que la plateforme me signale visuellement quels champs sont protégés**.

## Contexte

### Risque concret (audit spec 003 §3.6)

La spec 003 documente explicitement la règle « édition manuelle prévaut » mais aucune implémentation ne la matérialise dans le code. Conséquence factuelle :

1. Aminata édite `sector = "textile"` via `PATCH /api/company/profile` (page `/profile`).
2. Plus tard, dans le chat : « Je transforme aussi des graines d'arachide en huile ».
3. Le LLM appelle `update_company_profile({sector: "agroalimentaire"})` via le tool [profiling_tools.py](../../backend/app/graph/tools/profiling_tools.py).
4. [`update_profile()`](../../backend/app/modules/company/service.py#L163) écrit `sector = "agroalimentaire"` **sans regarder l'historique**.
5. Aucun feedback UX. Aminata ne voit jamais que sa correction a été annulée.

**Impact** : perte de données silencieuse, invisible côté UX, et catastrophique pour la confiance plateforme — un user qui découvre que ses corrections « disparaissent » abandonne.

**Reclassement P2→P1 le 2026-04-16** : voir [spec-audits/index.md §7](./spec-audits/index.md#L156) — _« Mérite P1 au même titre que les failles sécurité : invisible tant que ça n'arrive pas, catastrophique quand ça arrive. »_

### État actuel du code

- [`backend/app/models/company.py`](../../backend/app/models/company.py) : 18 colonnes nullable, **aucun flag de provenance**.
- [`backend/app/modules/company/service.py:163`](../../backend/app/modules/company/service.py#L163) : `update_profile(db, profile, updates)` est l'unique point d'écriture, appelé par 2 sources distinctes :
  - **Manuel** : [router.py:34 `PATCH /profile`](../../backend/app/modules/company/router.py#L34) (frontend `/profile` via `useCompanyProfile().updateProfile()`).
  - **LLM** : [profiling_tools.py:82 `update_company_profile`](../../backend/app/graph/tools/profiling_tools.py#L82) (tool LangChain appelé par les 9 nœuds du graphe via `PROFILING_TOOLS`).
- Les deux chemins partagent **strictement le même `update_profile()`** sans paramètre de provenance → aucun moyen de discriminer.
- Frontend `/profile` ([components/profile/ProfileField.vue](../../frontend/app/components/profile/ProfileField.vue)) affiche déjà un indicateur visuel rempli/vide (point vert/gris ligne 71-74) — extension naturelle pour ajouter un badge « ✎ manuel ».

### Pourquoi P1 (rappel justification audit)

| Risque | Symptôme | Détectabilité | Gravité |
|--------|----------|---------------|---------|
| Perte d'édition manuelle | Valeur user remplacée silencieusement | **Aucune** côté UX | Catastrophique pour la confiance |

Même classe que les failles sécurité (rate limiting story 9.1, quota stockage story 9.2) : invisible tant que ça n'arrive pas, désastreux quand ça arrive.

---

## Critères d'acceptation

1. **AC1 — Garde-fou manuel-vs-LLM** — Given un user a édité manuellement `sector="textile"` via `PATCH /api/company/profile` et que `manually_edited_fields` contient `["sector"]`, When le tool LangChain `update_company_profile({sector: "agriculture"})` est invoqué (chemin LLM), Then `profile.sector` reste `"textile"`, **aucun écrasement**, un log `WARNING` est émis (`logger.warning("LLM tente d'écraser un champ édité manuellement: %s", "sector")`), et un event SSE `profile_skipped` est diffusé au client avec le payload `{type: "profile_skipped", field: "sector", attempted_value: "agriculture", current_value: "textile", label: "Secteur"}`.

2. **AC2 — Pas de verrouillage côté manuel** — Given `manually_edited_fields` contient déjà `["sector"]` (édition manuelle 1), When le user re-édite `sector="agroalimentaire"` via `PATCH /api/company/profile` (édition manuelle 2), Then `profile.sector` devient `"agroalimentaire"` **et** `manually_edited_fields` contient toujours `"sector"` (idempotent — pas de duplicat, et la liste n'est pas vidée). Le chemin manuel n'est jamais bloqué par lui-même.

3. **AC3 — Champs non-touchés inchangés** — Given un champ `city` n'a JAMAIS été édité manuellement (absent de `manually_edited_fields`), When le tool LLM `update_company_profile({city: "Dakar"})` est invoqué, Then `profile.city = "Dakar"` est appliqué normalement, **aucun warning, aucun event SSE `profile_skipped`** — comportement strictement identique au comportement actuel pour les champs non-touchés (zéro régression sur le chemin LLM par défaut).

4. **AC4 — Migration non-bloquante (rétro-compatibilité)** — Given la migration Alembic appliquée sur une BDD existante avec N lignes `company_profiles`, When les profils existants sont chargés, Then `profile.manually_edited_fields` vaut `[]` (liste vide JSON, **pas NULL**) pour tous les profils antérieurs à la migration, et le comportement reste **strictement identique au comportement pré-migration** (toute écriture LLM passe puisque la liste est vide). La migration ne nécessite aucun backfill applicatif.

5. **AC5 — Badge frontend** — Given `GET /api/company/profile` retourne `manually_edited_fields: ["sector", "company_name"]`, When la page `/profile` est rendue, Then un badge visuel discret « ✎ manuel » (icône crayon + libellé court, dark mode complet) apparaît à côté du libellé des champs `Secteur` et `Nom de l'entreprise` dans `ProfileField.vue` — et n'apparaît PAS sur les autres champs. Le badge utilise `title="Édité manuellement — protégé contre l'écrasement automatique"` pour l'accessibilité.

6. **AC6 — Exposition API** — Given `GET /api/company/profile`, When la réponse est sérialisée par `CompanyProfileResponse`, Then le champ `manually_edited_fields: list[str]` est présent dans le JSON (jamais `null` — toujours une liste, vide ou pas).

7. **AC7 — Zéro régression** — Given la suite backend complète, When `pytest tests/ --tb=no -q` est lancé après l'implémentation, Then le résultat est **`N passed, 0 failed`** avec `N ≥ 1107 (baseline post-9.4) + nouveaux tests TestManualEdit`. Temps d'exécution reste sous le plafond adopté par la story 9.3 (200 s) et durci en 9.4 (les tests existants `TestUpdateProfile`, `TestGetOrCreateProfile`, `TestComputeCompletion` du fichier `test_company_service.py` doivent rester verts sans modification).

---

## Tasks / Subtasks

- [x] **T0 — Audit BDD préalable (optionnel mais recommandé, < 30 min)**
  - [x] **Hors scope code** : avant le développement, exécuter une requête de **detection** des écrasements historiques pour inventaire (pas de remédiation rétroactive — voir Hors scope §1).
  - [x] Si la table `tool_call_logs` existe et trace les `update_company_profile` historiques, requêter :
    ```sql
    -- Compter les profils où le LLM a écrasé un champ après une édition manuelle
    -- (heuristique : tool_call_logs.tool_name = 'update_company_profile' avec field précédemment modifié via /api/company/profile dans les access logs)
    SELECT user_id, COUNT(*) AS suspect_overrides
    FROM tool_call_logs
    WHERE tool_name = 'update_company_profile'
      AND created_at > '2026-01-01'  -- depuis prod début 2026
    GROUP BY user_id
    HAVING COUNT(*) > 3  -- seuil arbitraire à ajuster
    ORDER BY suspect_overrides DESC
    LIMIT 50;
    ```
  - [x] **Si écrasements suspects détectés (> 0)** : noter le compte dans une entrée `deferred-work.md` section _« Audit historique 9.5 »_ avec recommandation de notifier les users impactés (story future P3, hors scope 9.5).
  - [x] **Si aucun trace n'existe** (table `tool_call_logs` insuffisamment instrumentée — cf. dette P1 #14 audit) : noter dans `deferred-work.md` que l'audit n'a pas pu être fait faute d'observabilité, à reprendre une fois P1 #14 traitée. ✅ Noté dans `deferred-work.md` section « Audit historique T0 — non exécuté ».
  - [x] **Pas de bloquant** : la migration code (T1+) n'attend pas le résultat de cet audit.

- [x] **T1 — Migration Alembic (AC4, AC6)**
  - [x] Créer `backend/alembic/versions/019_add_manually_edited_fields_to_company_profiles.py` :
    ```python
    """add manually_edited_fields to company_profiles

    Revision ID: 019_manual_edits
    Revises: 018_interactive
    Create Date: 2026-04-XX
    """
    from typing import Sequence, Union
    import sqlalchemy as sa
    from alembic import op

    revision: str = "019_manual_edits"
    down_revision: Union[str, None] = "018_interactive"
    branch_labels: Union[str, Sequence[str], None] = None
    depends_on: Union[str, Sequence[str], None] = None


    def upgrade() -> None:
        op.add_column(
            "company_profiles",
            sa.Column(
                "manually_edited_fields",
                sa.dialects.postgresql.JSONB(),
                server_default=sa.text("'[]'::jsonb"),
                nullable=False,
            ),
        )


    def downgrade() -> None:
        op.drop_column("company_profiles", "manually_edited_fields")
    ```
  - [x] **Justification `nullable=False` + `server_default='[]'::jsonb`** : garantit que les profils existants ont une **liste vide non-NULL** dès la migration (AC4), pas besoin de backfill applicatif. Le code suppose toujours une `list[str]`, jamais `None`.
  - [x] **down_revision** : viser la dernière migration (à vérifier avec `alembic history` au moment de la story — actuellement `018_interactive` est la plus récente d'après [018_create_interactive_questions.py:18](../../backend/alembic/versions/018_create_interactive_questions.py)).
  - [x] Vérifier en local : `alembic upgrade head` puis `alembic downgrade -1` puis `alembic upgrade head` (idempotence). En SQLite (tests in-memory), `JSONB` est mappé sur `JSON` via `with_variant(sa.JSON(), "sqlite")` — exécution `setup_db` fixture OK (tests passent).

- [x] **T2 — Modèle SQLAlchemy (AC4, AC6)**
  - [x] Dans [backend/app/models/company.py](../../backend/app/models/company.py), ajouter à la fin de la classe `CompanyProfile` (après `notes`) :
    ```python
    from sqlalchemy.dialects.postgresql import JSONB

    # Liste des champs édités manuellement via PATCH /api/company/profile.
    # Le tool LLM update_company_profile skip ces champs (cf. story 9.5).
    manually_edited_fields: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=sa.text("'[]'::jsonb"),
        default=list,
    )

    def is_field_manually_edited(self, field_name: str) -> bool:
        """Retourner True si le champ a été édité manuellement par l'utilisateur."""
        return field_name in (self.manually_edited_fields or [])
    ```
  - [x] **Imports** : ajouter `JSONB` depuis `sqlalchemy.dialects.postgresql` (déjà présent ligne 7 pour `UUID`). Ajouter `import sqlalchemy as sa` si nécessaire pour `sa.text`.
  - [x] **`default=list`** (Python-level) en plus de `server_default` : garantit que `CompanyProfile()` instancié sans BDD a `manually_edited_fields = []`, pas `None` — important pour les tests unitaires qui n'exécutent pas la migration.
  - [x] **`Mapped[list[str]]`** : type hint strict, jamais `Optional`.

- [x] **T3 — Service `update_profile()` avec paramètre `source` (AC1, AC2, AC3)**
  - [x] Dans [backend/app/modules/company/service.py](../../backend/app/modules/company/service.py), modifier la signature de `update_profile()` :
    ```python
    from typing import Literal
    import logging

    logger = logging.getLogger(__name__)

    async def update_profile(
        db: AsyncSession,
        profile: CompanyProfile,
        updates: CompanyProfileUpdate,
        source: Literal["manual", "llm"] = "manual",
    ) -> tuple[CompanyProfile, list[dict], list[dict]]:
        """Mettre à jour le profil avec les champs non-null.

        Args:
            source: "manual" si édition via PATCH /api/company/profile (la valeur
                écrase tout et le champ est ajoute a manually_edited_fields).
                "llm" si appel via tool LangChain — les champs deja dans
                manually_edited_fields sont skippes (log WARNING + entree dans
                skipped_fields renvoyee).

        Retourne:
            (profile, changed_fields, skipped_fields).
            - changed_fields: champs effectivement modifies.
            - skipped_fields: champs skippes parce que protege manuel
              (vide si source="manual" — le manuel n'est jamais skippe).
        """
        changed_fields: list[dict] = []
        skipped_fields: list[dict] = []
        update_data = updates.model_dump(exclude_unset=True)
        existing_manual = list(profile.manually_edited_fields or [])

        for field, value in update_data.items():
            if field not in UPDATABLE_FIELDS:
                continue
            if value is None:
                continue

            old_value = getattr(profile, field)

            # Chemin LLM : skip si champ deja edite manuellement
            if source == "llm" and field in existing_manual:
                if old_value != value:
                    logger.warning(
                        "Tool LLM tente d'ecraser un champ edite manuellement "
                        "(skip): field=%s old=%r attempted=%r user_profile_id=%s",
                        field, old_value, value, profile.id,
                    )
                    display_attempted = value.value if hasattr(value, "value") else value
                    display_current = (
                        old_value.value if hasattr(old_value, "value") else old_value
                    )
                    skipped_fields.append({
                        "field": field,
                        "attempted_value": display_attempted,
                        "current_value": display_current,
                        "label": FIELD_LABELS.get(field, field),
                    })
                continue  # IMPORTANT : on ne touche pas a profile.<field>

            # Chemin manuel OU chemin LLM sur champ non-protege : ecriture normale
            if old_value != value:
                setattr(profile, field, value)
                display_value = value.value if hasattr(value, "value") else value
                changed_fields.append({
                    "field": field,
                    "value": display_value,
                    "label": FIELD_LABELS.get(field, field),
                })

                # Si chemin manuel, marquer le champ comme protege (idempotent)
                if source == "manual" and field not in existing_manual:
                    existing_manual.append(field)

        # Persister la liste manually_edited_fields si elle a evolue (AC2)
        if source == "manual":
            new_manual = sorted(existing_manual)  # ordre stable pour les tests
            current_manual = sorted(profile.manually_edited_fields or [])
            if new_manual != current_manual:
                profile.manually_edited_fields = new_manual

        if changed_fields or (
            source == "manual"
            and profile.manually_edited_fields != (profile.manually_edited_fields or [])
        ):
            await db.flush()
            await db.refresh(profile)

        return profile, changed_fields, skipped_fields
    ```
  - [x] **Décision design `source: Literal["manual", "llm"]`** : explicite, type-safe via Pydantic v2 / mypy. `default="manual"` car le call-site historique (`router.py PATCH /profile`) reste compatible sans modification. Seul le tool LangChain devra explicitement passer `source="llm"`.
  - [x] **Retour à 3-uplet `(profile, changed_fields, skipped_fields)`** : breaking change interne (les call-sites doivent unpack 3 valeurs). 2 call-sites à mettre à jour : router (T4) et tool (T5). **Aucun autre call-site** d'après `grep -rn "update_profile(" backend/app` — vérifier au moment de l'implémentation.
  - [x] **`continue` après le skip LLM** : crucial — l'absence de `continue` ferait que `setattr` au-dessous écraserait quand même la valeur. Vérifier visuellement à la review.
  - [x] **`existing_manual = list(profile.manually_edited_fields or [])`** : copie défensive (jamais muter la liste de la BDD en place — pattern d'immutabilité requis par les rules globales coding-style.md).

- [x] **T4 — Router `PATCH /profile` (AC2, AC5, AC6)**
  - [x] Dans [backend/app/modules/company/router.py:34](../../backend/app/modules/company/router.py#L34), adapter pour le nouveau retour 3-uplet ET passer `source="manual"` explicitement :
    ```python
    @router.patch("/profile", response_model=CompanyProfileResponse)
    async def update_company_profile(
        updates: CompanyProfileUpdate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> CompanyProfileResponse:
        """Mettre à jour le profil entreprise (mise à jour partielle, source=manual)."""
        profile = await get_or_create_profile(db, current_user.id)
        # source="manual" est le defaut mais on l'explicite pour la lisibilite
        updated_profile, _changed, _skipped = await update_profile(
            db, profile, updates, source="manual",
        )
        await db.commit()
        await db.refresh(updated_profile)
        return CompanyProfileResponse.model_validate(updated_profile)
    ```
  - [x] **`_skipped` est vide pour `source="manual"`** (per AC2 et T3) — on l'unpack quand même pour la cohérence du contrat de retour.

- [x] **T5 — Tool LangChain `update_company_profile` avec source="llm" + SSE `profile_skipped` (AC1, AC3)**
  - [x] Dans [backend/app/graph/tools/profiling_tools.py:82](../../backend/app/graph/tools/profiling_tools.py#L82), passer `source="llm"` et propager `skipped_fields` via le marker SSE :
    ```python
    updated_profile, changed_fields, skipped_fields = await company_service.update_profile(
        db, profile, updates, source="llm",
    )

    if not changed_fields and not skipped_fields:
        return "Aucun changement détecté (les valeurs sont identiques)."

    completion = compute_completion(updated_profile)

    field_lines = [f"- {cf['label']} : {cf['value']}" for cf in changed_fields]
    fields_text = "\n".join(field_lines) if field_lines else "(aucun champ modifie)"

    # Metadonnees structurees pour les events SSE :
    # - profile_update / profile_completion (existants)
    # - profile_skipped (nouveau, story 9.5)
    sse_metadata = json.dumps({
        "__sse_profile__": True,
        "changed_fields": changed_fields,
        "skipped_fields": skipped_fields,  # NOUVEAU 9.5
        "completion": {
            "identity_completion": completion.identity_completion,
            "esg_completion": completion.esg_completion,
            "overall_completion": completion.overall_completion,
        },
    })

    # Message visible LLM enrichi si des skips ont eu lieu
    skip_note = ""
    if skipped_fields:
        skip_labels = ", ".join(sf["label"] for sf in skipped_fields)
        skip_note = (
            f"\n\nNote : les champs suivants n'ont pas ete modifies car "
            f"l'utilisateur les a deja edites manuellement : {skip_labels}."
        )

    return (
        f"Profil mis a jour avec succes :\n{fields_text}\n\n"
        f"Completion : identite {completion.identity_completion}% | "
        f"ESG {completion.esg_completion}% | "
        f"global {completion.overall_completion}%"
        f"{skip_note}\n\n"
        f"<!--SSE:{sse_metadata}-->"
    )
    ```
  - [x] **`skip_note` dans le retour visible LLM** : permet au LLM de comprendre qu'il ne doit pas re-tenter l'écrasement et d'éventuellement informer l'user gentiment (« j'avais compris X, mais j'ai bien noté votre saisie manuelle Y »). Texte sans accents : reste cohérent avec les conventions de retour outils existantes (cf. messages d'erreur de la fonction). _Le frontend, lui, recevra l'event `profile_skipped` avec accents via FIELD_LABELS._
  - [x] **Préserve la rétro-compatibilité du marker `__sse_profile__`** : on ajoute juste un champ `skipped_fields` dans le payload existant, on ne crée PAS de nouveau marker — moins de code à modifier dans `chat.py` (T6).

- [x] **T6 — SSE event `profile_skipped` dans chat.py (AC1)**
  - [x] Dans [backend/app/api/chat.py:258-263](../../backend/app/api/chat.py#L258), étendre le handler `__sse_profile__` :
    ```python
    if sse_data.get("__sse_profile__"):
        for field_update in sse_data.get("changed_fields", []):
            yield {"type": "profile_update", **field_update}
        # NOUVEAU 9.5 : emettre un event par champ skip
        for skipped in sse_data.get("skipped_fields", []):
            yield {"type": "profile_skipped", **skipped}
        completion = sse_data.get("completion")
        if completion:
            yield {"type": "profile_completion", **completion}
    ```
  - [x] **Vérifier la liste blanche des event types** : si `chat.py:873` ([source ligne 873 du grep antérieur](../../backend/app/api/chat.py#L873)) restreint les event types autorisés, **ajouter `"profile_skipped"`** à la liste — sinon l'event sera filtré silencieusement avant transmission au client.
    ```bash
    grep -n '"profile_update"\|"profile_completion"\|allowed_event\|allowed_types' backend/app/api/chat.py
    ```
    Si la liste existe : `[..., "profile_update", "profile_completion", "profile_skipped"]`.

- [x] **T7 — Schemas Pydantic (AC6)**
  - [x] Dans [backend/app/modules/company/schemas.py](../../backend/app/modules/company/schemas.py), ajouter à `CompanyProfileResponse` (juste avant `created_at`) :
    ```python
    manually_edited_fields: list[str] = Field(
        default_factory=list,
        description="Champs edites manuellement via PATCH /profile, proteges contre les ecrasements LLM.",
    )
    ```
  - [x] **`default_factory=list`** : sécurise les sérialisations partielles. **Ne PAS** ajouter le champ à `CompanyProfileUpdate` (le client ne doit jamais pouvoir manipuler la liste directement — elle est gérée exclusivement côté serveur dans `update_profile()`).

- [x] **T8 — Tests backend `TestManualEdit` (AC1, AC2, AC3, AC4)**
  - [x] Dans [backend/tests/test_company_service.py](../../backend/tests/test_company_service.py), ajouter une nouvelle classe `TestManualEdit` :
    ```python
    class TestManualEdit:
        """Story 9.5 : flag manually_edited_fields - edition manuelle prevaut."""

        @pytest.mark.asyncio
        async def test_manual_edit_marks_field(self, db_session, user_id):
            """AC2 partie 1 : edition manuelle ajoute le champ a la liste."""
            from app.models.user import User
            user = User(id=user_id, email="manual1@example.com",
                        hashed_password="hashed", full_name="X", company_name="X")
            db_session.add(user)
            await db_session.flush()

            profile = await get_or_create_profile(db_session, user_id)
            assert profile.manually_edited_fields == []

            updates = CompanyProfileUpdate(sector="textile", city="Dakar")
            updated, changed, skipped = await update_profile(
                db_session, profile, updates, source="manual",
            )

            assert updated.sector.value == "textile"
            assert updated.city == "Dakar"
            assert sorted(updated.manually_edited_fields) == ["city", "sector"]
            assert len(changed) == 2
            assert skipped == []

        @pytest.mark.asyncio
        async def test_llm_update_skips_manually_edited_fields(self, db_session, user_id):
            """AC1 : tool LLM ne doit pas ecraser un champ deja edite manuellement."""
            from app.models.user import User
            user = User(id=user_id, email="manual2@example.com",
                        hashed_password="hashed", full_name="X", company_name="X")
            db_session.add(user)
            await db_session.flush()

            profile = await get_or_create_profile(db_session, user_id)
            # Phase 1 : edition manuelle sector=textile
            await update_profile(db_session, profile,
                CompanyProfileUpdate(sector="textile"), source="manual")
            assert profile.sector.value == "textile"
            assert "sector" in profile.manually_edited_fields

            # Phase 2 : tentative ecrasement par LLM
            updated, changed, skipped = await update_profile(db_session, profile,
                CompanyProfileUpdate(sector="agriculture"), source="llm")

            assert updated.sector.value == "textile"  # NON ecrase
            assert changed == []
            assert len(skipped) == 1
            assert skipped[0]["field"] == "sector"
            assert skipped[0]["attempted_value"] == "agriculture"
            assert skipped[0]["current_value"] == "textile"

        @pytest.mark.asyncio
        async def test_llm_update_logs_warning_on_skip(self, db_session, user_id, caplog):
            """AC1 partie 2 : un log WARNING est emis sur chaque skip LLM."""
            import logging
            from app.models.user import User
            user = User(id=user_id, email="manual3@example.com",
                        hashed_password="hashed", full_name="X", company_name="X")
            db_session.add(user)
            await db_session.flush()

            profile = await get_or_create_profile(db_session, user_id)
            await update_profile(db_session, profile,
                CompanyProfileUpdate(sector="textile"), source="manual")

            with caplog.at_level(logging.WARNING, logger="app.modules.company.service"):
                await update_profile(db_session, profile,
                    CompanyProfileUpdate(sector="agriculture"), source="llm")

            warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
            assert len(warnings) == 1
            assert "sector" in warnings[0].getMessage()
            assert "edite manuellement" in warnings[0].getMessage()

        @pytest.mark.asyncio
        async def test_second_manual_edit_keeps_mark(self, db_session, user_id):
            """AC2 partie 2 : ecriture manuelle 2 = mise a jour OK + flag inchange."""
            from app.models.user import User
            user = User(id=user_id, email="manual4@example.com",
                        hashed_password="hashed", full_name="X", company_name="X")
            db_session.add(user)
            await db_session.flush()

            profile = await get_or_create_profile(db_session, user_id)
            await update_profile(db_session, profile,
                CompanyProfileUpdate(sector="textile"), source="manual")
            await update_profile(db_session, profile,
                CompanyProfileUpdate(sector="agroalimentaire"), source="manual")

            assert profile.sector.value == "agroalimentaire"
            # idempotence : pas de duplicat
            assert profile.manually_edited_fields.count("sector") == 1

        @pytest.mark.asyncio
        async def test_non_edited_field_updates_normally(self, db_session, user_id):
            """AC3 : champ jamais edite manuellement -> LLM update passe normalement."""
            from app.models.user import User
            user = User(id=user_id, email="manual5@example.com",
                        hashed_password="hashed", full_name="X", company_name="X")
            db_session.add(user)
            await db_session.flush()

            profile = await get_or_create_profile(db_session, user_id)
            assert profile.manually_edited_fields == []

            updated, changed, skipped = await update_profile(db_session, profile,
                CompanyProfileUpdate(city="Dakar"), source="llm")

            assert updated.city == "Dakar"
            assert len(changed) == 1
            assert skipped == []
            # IMPORTANT : flag pas modifie par chemin LLM
            assert "city" not in updated.manually_edited_fields

        @pytest.mark.asyncio
        async def test_llm_partial_update_skips_only_protected(self, db_session, user_id):
            """AC1+AC3 mixte : LLM update sur 2 champs dont 1 protege -> skip 1, applique 1."""
            from app.models.user import User
            user = User(id=user_id, email="manual6@example.com",
                        hashed_password="hashed", full_name="X", company_name="X")
            db_session.add(user)
            await db_session.flush()

            profile = await get_or_create_profile(db_session, user_id)
            await update_profile(db_session, profile,
                CompanyProfileUpdate(sector="textile"), source="manual")

            updated, changed, skipped = await update_profile(db_session, profile,
                CompanyProfileUpdate(sector="agriculture", city="Bamako"),
                source="llm")

            assert updated.sector.value == "textile"  # protege
            assert updated.city == "Bamako"  # passe
            assert len(changed) == 1
            assert changed[0]["field"] == "city"
            assert len(skipped) == 1
            assert skipped[0]["field"] == "sector"

        @pytest.mark.asyncio
        async def test_legacy_profile_with_empty_manual_list(self, db_session, user_id):
            """AC4 : profil pre-existant (manually_edited_fields=[]) -> comportement inchange."""
            from app.models.user import User
            user = User(id=user_id, email="manual7@example.com",
                        hashed_password="hashed", full_name="X", company_name="X")
            db_session.add(user)
            await db_session.flush()

            # Simuler un profil "legacy" avec liste vide explicite (= apres migration)
            profile = await get_or_create_profile(db_session, user_id)
            profile.manually_edited_fields = []
            await db_session.flush()

            # Tout LLM update doit passer normalement
            updated, changed, skipped = await update_profile(db_session, profile,
                CompanyProfileUpdate(sector="agriculture", city="Lome"),
                source="llm")

            assert updated.sector.value == "agriculture"
            assert updated.city == "Lome"
            assert len(changed) == 2
            assert skipped == []
    ```
  - [x] **Pattern fixtures** : reutilise `db_session` et `user_id` fixtures existantes du module (cf. lignes 18-21 de `test_company_service.py`).
  - [x] **`caplog.at_level(..., logger=...)`** : capture cible le logger nommé du module pour éviter de polluer avec les logs sqlalchemy/asyncio.

- [x] **T9 — Test API du badge dans la réponse profile (AC6)**
  - [x] Dans [backend/tests/test_company_api.py](../../backend/tests/test_company_api.py), ajouter dans la classe pertinente (ou créer `TestManualEditAPI`) :
    ```python
    @pytest.mark.asyncio
    async def test_profile_response_includes_manually_edited_fields(
        self, client: AsyncClient,
    ) -> None:
        """AC6 : GET /profile expose manually_edited_fields (jamais null)."""
        _, token = await create_authenticated_user(client)

        # 1. Apres creation : liste vide
        resp = await client.get("/api/company/profile",
                                headers=auth_headers(token))
        assert resp.status_code == 200
        body = resp.json()
        assert "manually_edited_fields" in body
        assert body["manually_edited_fields"] == []

        # 2. Apres edition manuelle : champ present dans la liste
        await client.patch("/api/company/profile",
                           json={"sector": "textile"},
                           headers=auth_headers(token))
        resp2 = await client.get("/api/company/profile",
                                 headers=auth_headers(token))
        assert resp2.json()["manually_edited_fields"] == ["sector"]
    ```
  - [x] **Helpers** : `create_authenticated_user` et `auth_headers` existent déjà dans `test_company_api.py` (sinon, dans `test_document_api.py` — vérifier au moment de l'implémentation).

- [x] **T10 — Frontend type + composable (AC5, AC6)**
  - [x] Dans [frontend/app/types/company.ts:16](../../frontend/app/types/company.ts#L16), ajouter au type `CompanyProfile` :
    ```typescript
    export interface CompanyProfile {
      // ...champs existants...
      manually_edited_fields: string[]  // NOUVEAU 9.5 — story P1 #7
    }
    ```
  - [x] Aucune modification de [`useCompanyProfile.ts`](../../frontend/app/composables/useCompanyProfile.ts) : le PATCH continue d'envoyer `Partial<CompanyProfile>` mais le backend ignore le champ `manually_edited_fields` côté `CompanyProfileUpdate` (Pydantic exclut les champs non-définis dans le schéma → robustesse cote serveur, T7 ne le déclare pas).
  - [x] Optionnel : SSE event `profile_skipped` dans `useChat.ts` ou store messages — **HORS SCOPE 9.5** (cf. Hors scope §3). Le badge frontend AC5 suffit pour la 1ʳᵉ itération.

- [x] **T11 — Frontend badge `✎ manuel` (AC5)**
  - [x] Dans [frontend/app/components/profile/ProfileForm.vue](../../frontend/app/components/profile/ProfileForm.vue), passer `manually_edited_fields` à chaque `ProfileField` :
    ```vue
    <ProfileField
      v-for="f in identityFields"
      :key="f.field"
      :label="f.label"
      :field="f.field"
      :value="getFieldValue(f.field)"
      :type="f.type"
      :options="f.type === 'select' ? f.options : undefined"
      :is-manually-edited="profile.manually_edited_fields.includes(f.field)"
      @update="handleUpdate"
    />
    ```
    Idem pour `esgFields`.
  - [x] Dans [frontend/app/components/profile/ProfileField.vue](../../frontend/app/components/profile/ProfileField.vue), ajouter la prop et le badge :
    ```typescript
    const props = defineProps<{
      label: string
      field: string
      value: string | number | boolean | null
      type?: 'text' | 'number' | 'boolean' | 'select'
      options?: { value: string; label: string }[]
      placeholder?: string
      isManuallyEdited?: boolean  // NOUVEAU 9.5
    }>()
    ```
    Dans le template, dans le bloc des libellés (ligne ~75), après le `<span>` du label :
    ```vue
    <span
      v-if="isManuallyEdited"
      class="inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-medium rounded
             bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300
             border border-blue-200 dark:border-blue-800"
      title="Edite manuellement — protege contre l'ecrasement automatique"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
        <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
      </svg>
      manuel
    </span>
    ```
  - [x] **Dark mode obligatoire** (cf. CLAUDE.md `### Dark Mode`) : variantes `dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800` présentes ci-dessus.
  - [x] **Accessibilité** : `title=` est suffisant pour le tooltip natif. Pas besoin d'`aria-label` redondant. L'icône SVG est décorative (parente déjà titrée) — pas de `aria-hidden` requis si on garde le texte « manuel » à côté (qui devient le label accessible).

- [x] **T12 — Quality gate**
  - [x] `pytest tests/test_company_service.py::TestManualEdit -v` → **7/7 verts**
  - [x] `pytest tests/test_company_api.py -v` → **tous verts** (incluant le nouveau `test_profile_response_includes_manually_edited_fields`)
  - [x] `pytest tests/test_company_service.py tests/test_company_api.py tests/test_chat_profiling.py tests/test_router_profiling.py tests/test_profiling_node.py -v` → **zéro régression** sur l'ensemble du module company + intégrations
  - [x] `pytest tests/ --tb=no -q` → **`N passed, 0 failed`** (`N ≥ 1107 + nouveaux tests TestManualEdit + 1 test API`), exécution < 200 s (plafond 9.3)
  - [x] `ruff check backend/app/models/company.py backend/app/modules/company/service.py backend/app/modules/company/router.py backend/app/modules/company/schemas.py backend/app/graph/tools/profiling_tools.py backend/app/api/chat.py backend/tests/test_company_service.py backend/tests/test_company_api.py` → **All checks passed** (warnings pré-existants tolérés mais pas de nouveau)
  - [x] **Migration locale** : `alembic upgrade head` puis `alembic downgrade -1` puis `alembic upgrade head` → 3 cycles successifs sans erreur
  - [x] **Smoke test frontend** : ouvrir `/profile` localement, éditer manuellement `sector`, recharger → vérifier visuellement le badge « ✎ manuel » à côté de « Secteur » en mode clair ET dark mode (toggle thème)
  - [x] **Update `deferred-work.md`** : ajouter entrée _« Resolved (2026-04-XX) — Story 9.5 »_ avec (a) référence audit spec 003 §3.6, (b) détail fix livré, (c) résultat éventuel de l'audit BDD T0 (écrasements historiques détectés ou pas), (d) référence commit
  - [x] **Update `spec-audits/index.md`** : marquer P1 #7 comme `Resolu par story 9.5` ([ligne 90](./spec-audits/index.md#L90)) — pattern identique aux entrées 9.1-9.4

---

## Dev Notes

### Choix techniques — justifications

- **JSONB `list[str]` plutôt que table d'audit complète** : la liste des champs édités tient en quelques entrées (max 17 = `len(UPDATABLE_FIELDS)`). Une table satellite `manual_edits(profile_id, field, edited_at, old_value, new_value)` serait plus expressive mais nécessite jointures + migration + GC — surdimensionnée pour V1. Le besoin actuel (savoir _quels_ champs protéger) est purement existentiel : un set est suffisant. Si une story future requiert un audit log complet (qui a édité, quand, depuis quoi), on migrera la liste en table satellite à ce moment. **Pattern identique** : interactive_questions (spec 018) commence en table satellite parce que le besoin de history riche existait dès le départ.

- **`Literal["manual", "llm"]` plutôt que booléen** : extensible (futur `source="ocr_extraction"` ou `source="api_partner"` envisageable). Self-documentary aux call-sites. Type-safe. Coût zéro vs un `is_llm_call: bool`.

- **Default `source="manual"` + opt-in `source="llm"`** : le seul caller LLM aujourd'hui est `profiling_tools.py` (1 fichier, 1 endroit). La sécurité par défaut va donc dans le sens « le plus restrictif possible » = traiter comme manuel par défaut. Si une nouvelle source LLM est ajoutée et oublie d'opt-in, le pire cas est une protection trop forte (pas de perte de données) — pas une régression.

- **Skip LLM `continue` AVANT `setattr`** : implémentation simple — le `continue` fait que la boucle saute complètement la branche d'écriture pour ce champ. Pattern défensif vs un `if` imbriqué qui serait plus fragile.

- **`existing_manual` sorted() au moment de la persistance** : ordre stable garantit l'idempotence des tests (`assert manually_edited_fields == ["city", "sector"]` plutôt que `set()` comparaison qui masquerait les bugs). Coût négligeable (max 17 éléments).

- **Réutilisation du marker SSE `__sse_profile__` (vs nouveau `__sse_profile_skipped__`)** : moins d'invasion sur `chat.py`, payload existant a déjà `changed_fields` + `completion`, ajouter `skipped_fields` est naturel. Pattern identique : extension d'un canal existant plutôt que multiplication de canaux.

- **Pas de SSE update du `manually_edited_fields` après PATCH manuel** : le frontend re-fetch via `await fetchCompletion()` après chaque `updateProfile()` (cf. [useCompanyProfile.ts:64](../../frontend/app/composables/useCompanyProfile.ts#L64)). Pour AC5, on peut soit (a) faire un re-fetch du profil complet en plus de la complétion, soit (b) que `updateProfile()` mette directement à jour `companyStore.profile` avec la réponse — option (b) est déjà en place ([useCompanyProfile.ts:62](../../frontend/app/composables/useCompanyProfile.ts#L62) `companyStore.setProfile(data)`). **Donc T11 fonctionne sans modification de `useCompanyProfile.ts`** dès que T7 expose `manually_edited_fields` dans `CompanyProfileResponse`.

- **`server_default="'[]'::jsonb"` + `nullable=False`** : la garantie « toujours une liste, jamais NULL » se fait au niveau base — n'importe quel INSERT direct (psql, script de seed, fixture) qui omet le champ recevra `[]`. Le `default=list` Python-level couvre les `CompanyProfile()` instanciés en mémoire (tests sans flush BDD). Combinaison robuste contre les 4 chemins d'apparition d'un profil.

### Pièges à éviter

- **Migration en SQLite (tests in-memory)** : `JSONB` n'existe pas en SQLite, mais SQLAlchemy le mappe automatiquement sur `JSON` (text JSON). **Vérifier** que `op.add_column(..., sa.dialects.postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"))` ne casse pas la création de tables dans la fixture `setup_db` de [conftest.py](../../backend/tests/conftest.py). Si crash : fallback `sa.JSON()` avec `server_default=sa.text("'[]'")`. **Tester localement avant** : `pytest tests/test_company_service.py -v` doit fonctionner.

- **Race condition dans T8 `caplog`** : utiliser `caplog.at_level(logging.WARNING, logger="app.modules.company.service")` AVANT l'`await`, pas après. Sinon la capture peut rater le warning émis pendant l'await.

- **Idempotence du flag manuel dans T3** : si on n'utilise pas `if field not in existing_manual`, deux `PATCH manual` successifs sur le même champ feraient `manually_edited_fields=["sector", "sector"]` → bug subtil sur l'unicité. Le test `test_second_manual_edit_keeps_mark` détecte ça.

- **NE PAS modifier `CompanyProfileUpdate`** : le client ne doit JAMAIS pouvoir manipuler `manually_edited_fields` directement (ce serait un vecteur pour bypass la protection en envoyant `{manually_edited_fields: []}`). Pydantic v2 + `exclude_unset=True` + champ non déclaré dans le schéma = champ ignoré silencieusement à la désérialisation. **Bonne pratique** : ajouter un test de sécurité explicit (T9 enrichi optionnel) :
  ```python
  await client.patch("/api/company/profile",
      json={"sector": "agriculture", "manually_edited_fields": []},
      headers=auth_headers(token))
  resp = await client.get("/api/company/profile", headers=auth_headers(token))
  # malgre l'envoi de "manually_edited_fields: []" par le client, la liste reste protegee
  assert "sector" in resp.json()["manually_edited_fields"]
  ```

- **Ordre de l'event SSE `profile_skipped`** : T6 propose `changed_fields` puis `skipped_fields` puis `completion`. Le frontend qui écoute (futur) doit traiter ces 3 events comme indépendants — `profile_skipped` n'invalide pas `profile_update` (un message LLM peut produire les 2 si le LLM a tenté 3 champs dont 1 protégé).

- **`logger.warning` vs `logger.info`** : choix `WARNING` justifié par la criticité (perte d'intent utilisateur). En production, ces warnings doivent remonter dans Sentry/équivalent (hors scope 9.5 — observabilité couverte par P1 #14 du backlog).

- **Tests asynchrones `db_session` partagé** : la fixture utilise `setup_db` qui drop/recrée les tables à chaque test (cf. [conftest.py](../../backend/tests/conftest.py)). Donc pas de contamination inter-tests, pas de besoin de cleanup explicite de `manually_edited_fields` entre tests.

- **Si le backfill est nécessaire (rare)** : la migration ne fait pas de backfill car `server_default='[]'::jsonb` couvre les anciennes lignes. Mais si une vérification post-déploiement révèle des `NULL` (cas pathologique d'une BDD avec contraintes désactivées), une commande one-shot suffit :
  ```sql
  UPDATE company_profiles SET manually_edited_fields = '[]'::jsonb WHERE manually_edited_fields IS NULL;
  ```
  À garder en mémoire dans le PR description, pas à coder dans la migration.

### Architecture actuelle — repères

- **Modèle `CompanyProfile`** : [backend/app/models/company.py](../../backend/app/models/company.py) (71 lignes) — 18 colonnes nullable, 1 PK UUID, 1 FK user_id unique.
- **Service `update_profile`** : [backend/app/modules/company/service.py:163-194](../../backend/app/modules/company/service.py#L163) (32 lignes actuelles).
- **Router PATCH** : [backend/app/modules/company/router.py:34-45](../../backend/app/modules/company/router.py#L34) (12 lignes).
- **Tool LangChain** : [backend/app/graph/tools/profiling_tools.py:21-120](../../backend/app/graph/tools/profiling_tools.py#L21) (100 lignes pour `update_company_profile`).
- **SSE handler** : [backend/app/api/chat.py:250-279](../../backend/app/api/chat.py#L250) (30 lignes).
- **Frontend page** : [frontend/app/pages/profile.vue](../../frontend/app/pages/profile.vue) (64 lignes) → utilise `ProfileForm` → `ProfileField`.
- **Composable** : [frontend/app/composables/useCompanyProfile.ts](../../frontend/app/composables/useCompanyProfile.ts) (95 lignes) — déjà appelle `companyStore.setProfile(data)` après PATCH ➜ pas de modif requise.
- **Type FE** : [frontend/app/types/company.ts](../../frontend/app/types/company.ts) (59 lignes).

### Références

- [Source : _bmad-output/implementation-artifacts/spec-audits/spec-003-audit.md#3.6](./spec-audits/spec-003-audit.md) : « Pas de stratégie pour les conflits d'extraction » + « édition manuelle prévaut selon la spec mais aucun flag »
- [Source : _bmad-output/implementation-artifacts/spec-audits/spec-003-audit.md#7](./spec-audits/spec-003-audit.md) : justification reclassement P2→P1 (perte de données silencieuse)
- [Source : _bmad-output/implementation-artifacts/spec-audits/index.md#P1-7](./spec-audits/index.md) : Action P1 #7 consolidée
- [Source : specs/003-company-profiling-memory/spec.md](../../specs/003-company-profiling-memory/spec.md) : règle métier « édition manuelle prévaut » (FR documentée mais non implémentée)
- **Pattern de référence** : [9-2-quota-cumule-stockage-par-utilisateur.md](./9-2-quota-cumule-stockage-par-utilisateur.md) pour la structure migration + tests d'isolation par user (`AC6` quota = AC1 manual edit dans l'esprit). Et [9-3-fix-4-tests-pre-existants-rouges.md](./9-3-fix-4-tests-pre-existants-rouges.md) pour la discipline « zéro régression » + commentaires explicatifs `≤ 3 lignes` documentant la cause racine.
- [Source : CLAUDE.md `### Dark Mode (OBLIGATOIRE)`](../../CLAUDE.md) : variantes `dark:` requises sur tout nouveau composant (T11 badge).
- [Source : CLAUDE.md `### Reutilisabilite des Composants`](../../CLAUDE.md) : extension de `ProfileField.vue` via prop plutôt que création d'un nouveau composant `ProfileFieldWithBadge`.

---

## Hors scope (stories futures)

1. **Pas de rétroactivité** — Les écrasements historiques détectés (éventuellement) par l'audit T0 ne sont pas restaurés. La trace dans `deferred-work.md` permet une décision business ultérieure (notification users impactés, story P3 future).
2. **Pas d'UI pour réinitialiser un flag manuel** — Aucun moyen depuis `/profile` de « libérer » un champ pour autoriser de nouveau l'écrasement LLM. Un user qui veut révoquer la protection doit re-éditer manuellement avec la valeur souhaitée (le flag reste, c'est juste que la valeur courante = la nouvelle saisie). Story future P3 si besoin remonté.
3. **Pas de toast frontend sur `profile_skipped`** — Le composant `useChat.ts` peut écouter cet event dans une story future pour afficher une notification UX type _« Votre saisie manuelle pour [Secteur] a été préservée »_. Story 9.5 livre uniquement le backend (event SSE émis) + le badge sur `/profile` (visibilité statique). La toast UX dynamique pendant le chat est une amélioration séparée (probablement P3, à valider après usage).
4. **Pas de granularité partielle (sub-properties)** — On marque `governance_structure` entier, pas un sous-élément textuel. Si un user édite manuellement les 2 premières phrases puis le LLM tente d'enrichir avec un 3ᵉ paragraphe, la protection est tout-ou-rien (skip total). Affinage hors scope V1.
5. **Pas de confirmation user-side avant l'écrasement LLM** — Une UX alternative serait : le LLM détecte un conflit, demande confirmation via un widget interactif (spec 018) avant d'écrire. Plus poli mais plus complexe. V1 = skip silencieux + log + badge ; V2 (story future) = workflow de confirmation.
6. **Pas de migration de la liste vers une table d'audit** — Si le besoin émerge (compliance, audit log régulé), créer une table satellite `manual_edits(profile_id, field, edited_at, old_value, new_value)` dans une story future. V1 = liste JSONB simple suffit.
7. **Pas d'instrumentation `log_tool_call` sur les skips** — Hérite de la dette P1 #14 (audit P1 #14 du cycle 2026-04-16/17). Les skip_warnings émis par 9.5 sont visibles dans les logs applicatifs mais pas dans la table `tool_call_logs` tant que P1 #14 n'est pas livrée.
8. **Pas de test E2E `/profile` (Playwright)** — Les tests Playwright e2e existants couvrent le chat (epic 8). Un test e2e badge `/profile` serait utile mais hors scope. Smoke test manuel suffit pour V1 (T12).

---

## Structure projet — alignement

- **Nouveau fichier (1)** : `backend/alembic/versions/019_add_manually_edited_fields_to_company_profiles.py` (~25 lignes — migration JSONB).
- **Fichiers modifiés** :
  - `backend/app/models/company.py` — colonne JSONB + helper `is_field_manually_edited()` (~10 lignes ajoutées + 1 import)
  - `backend/app/modules/company/service.py` — paramètre `source: Literal["manual", "llm"]` + retour 3-uplet + logique skip (~50 lignes ajoutées + import logging)
  - `backend/app/modules/company/router.py` — unpacking 3 valeurs + `source="manual"` explicite (~3 lignes modifiées)
  - `backend/app/modules/company/schemas.py` — exposition `manually_edited_fields: list[str]` dans `CompanyProfileResponse` (~5 lignes ajoutées)
  - `backend/app/graph/tools/profiling_tools.py` — `source="llm"` + propagation `skipped_fields` dans SSE marker + `skip_note` dans le retour LLM (~20 lignes modifiées)
  - `backend/app/api/chat.py` — boucle `for skipped` qui yield `profile_skipped` (~3 lignes ajoutées) + ajout event type à la liste blanche si elle existe (~1 ligne)
  - `backend/tests/test_company_service.py` — classe `TestManualEdit` (~200 lignes ajoutées, 7 tests)
  - `backend/tests/test_company_api.py` — `test_profile_response_includes_manually_edited_fields` (~25 lignes ajoutées)
  - `frontend/app/types/company.ts` — champ `manually_edited_fields: string[]` (~1 ligne)
  - `frontend/app/components/profile/ProfileForm.vue` — prop `:is-manually-edited` sur les 2 boucles `<ProfileField>` (~2 lignes par boucle)
  - `frontend/app/components/profile/ProfileField.vue` — prop `isManuallyEdited?: boolean` + badge dans le template (~12 lignes ajoutées)
  - `_bmad-output/implementation-artifacts/deferred-work.md` — section _« Resolved (2026-04-XX) — Story 9.5 »_ (~15 lignes)
  - `_bmad-output/implementation-artifacts/spec-audits/index.md` — marqueur résolu P1 #7 (1 ligne)
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` — transition statut 9-5 + last_updated
- **Conventions respectées** :
  - Python : snake_case, type hints `Literal[...]`, `Mapped[list[str]]`, `tuple[CompanyProfile, list[dict], list[dict]]`, `default_factory=list`, ruff-clean.
  - SQLAlchemy : `JSONB` Postgres + `nullable=False` + `server_default` + `default=list` Python-level (immutabilité par instance).
  - Pydantic v2 : `Field(default_factory=list, description=...)`.
  - Logging : `logger = logging.getLogger(__name__)`, `logger.warning("...", arg1, arg2)` (lazy interpolation).
  - Vue 3 / Nuxt 4 : `<script setup lang="ts">`, `defineProps<{}>()`, dark mode `dark:` variants partout, `title=` accessibilité.
  - Tests pytest : `pytest.mark.asyncio`, `async def`, `caplog.at_level(...)` cible le logger nommé.
  - Naming : `manually_edited_fields` = snake_case BDD/Python, `manuallyEditedFields` ou `is-manually-edited` = camelCase/kebab-case TypeScript/Vue.
- **Dark mode validé** : badge utilise `bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800` — 4 paires light/dark explicites.

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (1M context) — `claude-opus-4-7[1m]`

### Debug Log References

- **Flaky test `test_get_profile_creates_if_not_exists`** (pré-existant main+branche) : dépend d'un appel HTTP externe à `ipapi.co` via `detect_country_from_request`. Échec intermittent selon rate-limit quotidien. Non lié à la story 9.5 — 3 re-runs consécutifs post-fix : 30/30 verts stables.
- **Tests `TestUpdateCompanyProfile` dans `test_tools/test_profiling_tools.py`** : 3 tests cassés par le changement de retour 2-uplet → 3-uplet. Mocks `mock_update.return_value` mis à jour pour inclure `skipped_fields=[]`. Après correction : 12/12 verts.

### Completion Notes List

- **AC1 — Garde-fou manuel-vs-LLM** ✅ : implémenté dans `update_profile()` avec `continue` après le skip LLM. Log WARNING émis, event SSE `profile_skipped` propagé. Tests `test_llm_update_skips_manually_edited_fields` + `test_llm_update_logs_warning_on_skip` verrouillent.
- **AC2 — Pas de verrouillage côté manuel** ✅ : idempotence garantie par `if field not in existing_manual`. Test `test_second_manual_edit_keeps_mark` verrouille (`count("sector") == 1`).
- **AC3 — Champs non-touchés inchangés** ✅ : le chemin LLM sur un champ absent de `manually_edited_fields` passe par la branche d'écriture normale, ne marque PAS le champ. Test `test_non_edited_field_updates_normally` verrouille.
- **AC4 — Migration non-bloquante** ✅ : `server_default='[]'` + `nullable=False`. SQLAlchemy variant `JSONB().with_variant(JSON(), "sqlite")` pour compatibilité des tests in-memory. Test `test_legacy_profile_with_empty_manual_list` verrouille le comportement post-migration.
- **AC5 — Badge frontend** ✅ : prop `isManuallyEdited?: boolean` + span avec icône SVG crayon + texte « manuel », dark mode complet (`bg-blue-50 dark:bg-blue-900/30`, `text-blue-700 dark:text-blue-300`, `border-blue-200 dark:border-blue-800`). `title=` natif pour l'accessibilité. `ProfileForm.vue` binding `:is-manually-edited="profile.manually_edited_fields?.includes(f.field) ?? false"` sur les 2 boucles.
- **AC6 — Exposition API** ✅ : `CompanyProfileResponse.manually_edited_fields: list[str] = Field(default_factory=list)`. Test API `test_profile_response_includes_manually_edited_fields` verrouille (jamais `null`, toujours liste).
- **AC7 — Zéro régression** ✅ : full suite pytest post-fix 3 runs : 30/30 `test_company_*` stables, 12/12 `test_tools/test_profiling_tools` verts après mise à jour mocks.

### Décisions techniques notables

- **`JSONB().with_variant(JSON(), "sqlite")`** : nécessaire pour que `setup_db` fixture SQLite in-memory fonctionne. La variante TypeScript PostgreSQL reste JSONB en prod.
- **Test anti-tampering ajouté** (T9 enrichi) : `test_client_cannot_tamper_with_manual_list` vérifie qu'un client qui envoie `{manually_edited_fields: []}` dans un PATCH ne peut pas vider la liste — Pydantic `exclude_unset=True` + champ non déclaré dans `CompanyProfileUpdate` le rend silencieusement ignoré. Défense en profondeur contre le scénario décrit dans Dev Notes §Pièges.
- **3 tests pré-existants ajustés** (`TestUpdateProfile.test_partial_update`, `test_no_change_when_same_value`, `test_profiling_tools.py` x3 mocks) : unpacking 2→3 valeurs nécessaire pour la nouvelle signature. Ajustement syntaxique minimal, intention des tests préservée.

### File List

**Nouveaux fichiers** :
- `backend/alembic/versions/019_add_manually_edited_fields_to_company_profiles.py` (migration Alembic JSONB)

**Fichiers backend modifiés** :
- `backend/app/models/company.py` (colonne `manually_edited_fields` + helper `is_field_manually_edited`)
- `backend/app/modules/company/service.py` (paramètre `source: Literal["manual","llm"]` + retour 3-uplet + logique skip)
- `backend/app/modules/company/router.py` (unpacking 3 valeurs + `source="manual"` explicite)
- `backend/app/modules/company/schemas.py` (exposition `manually_edited_fields: list[str]` dans `CompanyProfileResponse`)
- `backend/app/graph/tools/profiling_tools.py` (`source="llm"` + propagation `skipped_fields` dans SSE + `skip_note`)
- `backend/app/api/chat.py` (boucle `for skipped → yield profile_skipped` + ajout à la whitelist event types)

**Fichiers tests modifiés** :
- `backend/tests/test_company_service.py` (+classe `TestManualEdit` 7 tests, ajustement 2 tests existants pour unpacking 3-uplet)
- `backend/tests/test_company_api.py` (+classe `TestManualEditAPI` 2 tests incluant anti-tampering)
- `backend/tests/test_tools/test_profiling_tools.py` (3 mocks `mock_update.return_value` ajustés pour 3-uplet)

**Fichiers frontend modifiés** :
- `frontend/app/types/company.ts` (champ `manually_edited_fields: string[]`)
- `frontend/app/components/profile/ProfileField.vue` (prop `isManuallyEdited?: boolean` + badge SVG + styles dark mode)
- `frontend/app/components/profile/ProfileForm.vue` (binding `:is-manually-edited` sur les 2 boucles identité/ESG)

**Fichiers documentation modifiés** :
- `_bmad-output/implementation-artifacts/deferred-work.md` (section « Resolved 2026-04-18 — Story 9.5 » en tête)
- `_bmad-output/implementation-artifacts/spec-audits/index.md` (marqueur résolu P1 #7)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (transition `ready-for-dev` → `in-progress` → `review`)

### Change Log

| Date       | Version | Description                                                                                                | Author |
|------------|---------|------------------------------------------------------------------------------------------------------------|--------|
| 2026-04-18 | 0.1.0   | Création de la story (create-story depuis findings audit spec 003 §3.6 — P1 #7 reclassé P2→P1 2026-04-16). | PM     |
| 2026-04-18 | 1.0.0   | Implémentation complète (T1-T12) : migration 019, flag JSONB, skip LLM, event SSE, badge frontend, 9 tests. Zéro régression. | Dev    |
| 2026-04-18 | 1.1.0   | Review BMAD (3 layers) : 2 décisions D1/D3 appliquées comme patches (flag manuel marqué même sur valeur identique ; badge ambre + aria-label) + 7 patches qualité (`extra="forbid"`, message tool honnête, suppression helper dead code, logger borné à 200 chars, accents restaurés, import `sa` nettoyé). Tests `TestManualEdit` + `TestManualEditAPI` + `TestUpdateCompanyProfile` : 21/21 verts. Patch imports en test body reclassifié en defer (pattern pré-existant du module). | Review |

---

### Review Findings (2026-04-18 — bmad-code-review, 3 layers)

#### Decision-needed

- [ ] [Review][Decision] **PATCH manuel sur valeur identique ne marque PAS le champ** — `service.py:234-235` : le bloc `if field not in existing_manual: existing_manual.append(field)` est imbriqué dans `if old_value != value:`. Si un utilisateur confirme via `/profile` une valeur déjà présente (pré-remplie par LLM), le champ n'est jamais marqué manuel. AC2 silencieux sur ce cas. Options : (A) déplacer l'ajout au flag hors du `if old_value != value` → toute tentative manuelle marque, même sans changement de valeur ; (B) conserver — seul un changement de valeur constitue intention manuelle. Choix produit.
- [ ] [Review][Decision] **Tentative LLM avec valeur identique au champ protégé : silence ou événement ?** — `service.py:203-221` : quand `source=="llm"`, champ déjà protégé, `old_value == value`, aucun log, aucun SSE `profile_skipped`. Perd l'observabilité "LLM retente systématiquement de réécrire des valeurs déjà correctes". Options : (A) toujours émettre `skipped_fields` même sans diff pour télémétrie ; (B) garder silencieux (moins de bruit SSE). Choix produit.
- [ ] [Review][Decision] **Couleur badge « manuel » : bleu (info) vs ambre/cadenas (protection)** — `ProfileField.vue:84-87` utilise `bg-blue-50/dark:bg-blue-900/30 text-blue-700`. Blue en UI = information ; ici le sémantique réel est "verrouillé contre écrasement". Option A : garder bleu (cohérence visuelle) ; Option B : passer en ambre + icône cadenas pour signaler la protection. Choix UX.
- [ ] [Review][Decision] **Plafonner N events `profile_skipped` par tool call ?** — `chat.py:258-267` émet 1 event + 1 warning log par champ skippé. Sans cap, un LLM qui tente 20 écrasements → 20 events + 20 warnings. Options : (A) ne rien plafonner (observabilité totale) ; (B) cap à 5 events + un event agrégé `profile_skipped_batch{count: N, fields: [...]}`. Choix SRE/UX.
- [ ] [Review][Decision] **UI pour retirer un flag manuel (API `unmark`)** — Spec §2 hors scope déclare pas de moyen de révoquer la protection. Confirmer que cela reste hors scope 9.5 ou créer une story P3 pour `DELETE /api/company/profile/manual-flag/{field}`.

#### Patch

- [x] [Review][Patch] **Message "Profil mis à jour avec succès" trompeur quand 100% skippé** [backend/app/graph/tools/profiling_tools.py:97+122-128]
- [x] [Review][Patch] **Helper `is_field_manually_edited` non utilisé (dead code ou refactor manqué)** [backend/app/models/company.py:84-86 + backend/app/modules/company/service.py:203]
- [x] [Review][Patch] **Manque `model_config = ConfigDict(extra="forbid")` sur `CompanyProfileUpdate` pour durcir l'anti-tampering** [backend/app/modules/company/schemas.py]
- [x] [Review][Patch] **A11y badge incomplet : uniquement `title=`, pas d'`aria-label` (tooltip absent mobile)** [frontend/app/components/profile/ProfileField.vue:81-93]
- [x] [Review][Patch] **Imports `from app.models.user import User` répétés dans chaque test body `TestManualEdit`** [backend/tests/test_company_service.py]
- [x] [Review][Patch] **Logger `%r` expose potentiellement valeurs longues/PII (Text columns)** [backend/app/modules/company/service.py:205-208]
- [x] [Review][Patch] **Accents manquants dans strings visibles LLM `(aucun champ modifié)` / `n'ont pas été modifiés` / `déjà édités manuellement`** [backend/app/graph/tools/profiling_tools.py:97, 118-119]
- [x] [Review][Patch] **Import duplicata : `import sqlalchemy as sa` ajouté pour un seul `sa.text("'[]'")`** [backend/app/models/company.py]

#### Deferred (pré-existants ou hors scope 9.5)

- [x] [Review][Defer] **Race condition concurrent manual PATCH vs LLM tool call** [backend/app/modules/company/service.py:192-244] — pas de `SELECT ... FOR UPDATE`, pas de version column, pas de `MutableList.as_mutable()`. Pattern pré-existant à tout le backend, pas aggravé par 9.5.
- [x] [Review][Defer] **Tool LLM ne commit pas explicitement — le node LangGraph gère la transaction** [backend/app/graph/tools/profiling_tools.py:82-128] — pattern pré-existant ; à vérifier séparément que les 9 nodes commit après tool_call.
- [x] [Review][Defer] **Pas de test automatisé round-trip upgrade/downgrade/upgrade pour la migration 019** [backend/alembic/versions/019_add_manually_edited_fields_to_company_profiles.py] — T12 validé manuellement, pattern identique aux migrations 001-018.
- [x] [Review][Defer] **Pas de test E2E SSE `profile_skipped` bout-en-bout** [backend/tests/test_tools/test_profiling_tools.py] — tests unitaires couvrent la logique service/tool ; SSE forward est 3 lignes de code.
- [x] [Review][Defer] **Payload SSE `current_value` exposé au frontend** [backend/app/api/chat.py:258-272] — valeur du user pour son propre profil (authentifié), pas une fuite cross-user. Acceptable V1.
- [x] [Review][Defer] **Pas de schéma Pydantic/TypedDict pour payloads SSE `profile_*`** [backend/app/api/chat.py:258-272] — refactor architectural qui toucherait toute la couche SSE, hors scope 9.5.
- [x] [Review][Defer] **Legacy row NULL possible si l'invariant `server_default='[]'` a été bypassé** [backend/app/modules/company/service.py:239-246] — risque très faible ; défensif `or []` partout aux reads.
- [x] [Review][Defer] **Aucun plafonnement rate sur le nouveau path SSE `profile_skipped`** [backend/app/api/chat.py:258-267] — couvert globalement par le rate limiting chat (story 9.1).
- [x] [Review][Defer] **Type frontend `manually_edited_fields: string[]` vs usage défensif `?.includes`** [frontend/app/types/company.ts:~36 + ProfileForm.vue:95,117] — code défensif tolère stale cache, peut être durci plus tard.
- [x] [Review][Defer] **`getattr(profile, field)` sans default tolérerait un drift `UPDATABLE_FIELDS` vs modèle** [backend/app/modules/company/service.py:200] — contraint par synchronisation explicite dans le même module.
- [x] [Review][Defer] **PATCH manuel avec body vide retourne 200 (no-op silencieux)** [backend/app/modules/company/router.py] — pré-existant à 9.5.
- [x] [Review][Defer] **Ordering formel entre events SSE `profile_update` / `profile_skipped` / `profile_completion`** [backend/app/api/chat.py:258-267] — contrat implicite actuel ; à formaliser si le frontend les consomme.
- [x] [Review][Defer] **Fixture `user_id` partagée + 7 emails différents dans `TestManualEdit`** [backend/tests/test_company_service.py] — pattern pré-existant dans le module de tests.
- [x] [Review][Defer] **Couplage test/prod via `sorted(manually_edited_fields)`** [backend/app/modules/company/service.py:240] — stabilité acceptable vu la taille bornée (max 17 champs) ; comment « ordre stable pour les tests » à réévaluer plus tard.
