"""Tests des guards LLM (story 9.6 / P1 #10)."""

from __future__ import annotations

import pytest

from app.core.llm_guards import (
    FORBIDDEN_VOCAB,
    LLMGuardError,
    MAX_COST_XOF,
    MAX_SUMMARY_LEN,
    MIN_SUMMARY_LEN,
    ActionPlanItemLLMSchema,
    assert_language_fr,
    assert_length,
    assert_no_forbidden_vocabulary,
    assert_numeric_coherence,
    prompt_hash,
    validate_action_plan_schema,
)


class TestLLMGuardsFreeText:
    """AC1-AC4 : guards texte libre."""

    # AC4 - length
    def test_too_short_raises(self) -> None:
        with pytest.raises(LLMGuardError) as exc:
            assert_length("salut", MIN_SUMMARY_LEN, MAX_SUMMARY_LEN, "test")
        assert exc.value.code == "too_short"
        assert exc.value.details["length"] == 5
        assert exc.value.target == "test"

    def test_too_long_raises(self) -> None:
        text = "a" * 5000
        with pytest.raises(LLMGuardError) as exc:
            assert_length(text, MIN_SUMMARY_LEN, MAX_SUMMARY_LEN, "test")
        assert exc.value.code == "too_long"
        assert exc.value.details["length"] == 5000

    def test_length_ok(self) -> None:
        assert_length("a" * 500, MIN_SUMMARY_LEN, MAX_SUMMARY_LEN, "test")

    # AC3 - language FR
    def test_english_drift_detected(self) -> None:
        text = (
            "Your ESG score is satisfactory. We recommend improvements in "
            "governance and social pillars. The financing options are broad. "
            "Please consider the IFC PS standards for your future applications. "
            "Overall, the analysis shows a strong position for further growth "
            "and additional investments from international donors to support green "
            "initiatives across all operational sectors."
        )
        with pytest.raises(LLMGuardError) as exc:
            assert_language_fr(text, "test")
        assert exc.value.code == "language_drift"
        assert exc.value.details["min"] == 0.12

    def test_french_ok(self) -> None:
        text = (
            "Votre score ESG est satisfaisant avec une note globale solide. "
            "Nous recommandons des ameliorations sur le pilier gouvernance et "
            "sur les aspects sociaux. Les options de financement dans la region "
            "sont larges et adaptees au secteur. Considerez les standards IFC PS "
            "pour vos futures demandes de fonds. L'analyse montre une position "
            "solide pour la croissance dans les prochaines annees."
        )
        assert_language_fr(text, "test")

    def test_short_text_not_checked(self) -> None:
        # Texte trop court (< 50 tokens) : pas de verification, pas d'exception
        assert_language_fr("Hello world short", "test")

    # AC2 - forbidden vocabulary
    @pytest.mark.parametrize(
        "text,expected_term",
        [
            ("Votre conformite est garantie par nos experts.", "garantie"),
            ("Programme certifie ISO 26000.", "certifie"),
            ("Projet valide par le GCF en 2025.", "valide par"),
            ("Votre demarche est homologuee.", "homologuee"),
            ("Entreprise accreditee par le regulateur.", "accreditee"),
        ],
    )
    def test_forbidden_vocab_detected(self, text: str, expected_term: str) -> None:
        with pytest.raises(LLMGuardError) as exc:
            assert_no_forbidden_vocabulary(text, "test")
        assert exc.value.code == "forbidden_vocab"
        assert exc.value.details["detected_term"] == expected_term

    def test_forbidden_vocab_insensitive_to_accents(self) -> None:
        # "CERTIFIE" avec accents et majuscules -> doit matcher "certifie"
        text = "Programme CERTIFIE par l'ONU en 2024 pour sa demarche ESG."
        with pytest.raises(LLMGuardError) as exc:
            assert_no_forbidden_vocabulary(text, "test")
        assert exc.value.code == "forbidden_vocab"

    def test_safe_vocab_ok(self) -> None:
        # "garantir" (infinitif) ne doit PAS matcher "garanti" (adjectif)
        text = "Nous recommandons de garantir la tracabilite des processus."
        assert_no_forbidden_vocabulary(text, "test")

    def test_forbidden_vocab_constant_exposed(self) -> None:
        # AC2 : la liste est exposee pour audit
        assert isinstance(FORBIDDEN_VOCAB, tuple)
        assert "garanti" in FORBIDDEN_VOCAB
        assert "certifie" in FORBIDDEN_VOCAB

    # AC1 - numeric coherence
    def test_score_drift_detected(self) -> None:
        text = (
            "Avec votre excellent score de 82/100 en gouvernance, "
            "vous excellez parmi vos pairs."
        )
        with pytest.raises(LLMGuardError) as exc:
            assert_numeric_coherence(
                text,
                {"governance_score": 54.0, "overall_score": 54.0},
                "test",
            )
        assert exc.value.code == "numeric_drift"
        assert exc.value.details["detected_value"] == 82.0

    def test_score_close_ok(self) -> None:
        text = "Votre score global de 54/100 montre des progres notables."
        assert_numeric_coherence(
            text,
            {"overall_score": 54.3, "governance_score": 54.0},
            "test",
            tolerance=2.0,
        )

    def test_score_on_ten_ok(self) -> None:
        # 5/10 * 10 = 50 proche de 54 avec tolerance 5
        text = "Votre score de 5/10 en gouvernance est correct."
        assert_numeric_coherence(
            text,
            {"governance_score": 54.0},
            "test",
            tolerance=5.0,
        )

    def test_no_numbers_in_text_ok(self) -> None:
        text = "Votre demarche ESG est prometteuse et s'inscrit dans la duree."
        assert_numeric_coherence(text, {"overall_score": 54.0}, "test")

    def test_prompt_hash_deterministic(self) -> None:
        h1 = prompt_hash("un prompt test")
        h2 = prompt_hash("un prompt test")
        h3 = prompt_hash("un autre prompt")
        assert h1 == h2
        assert h1 != h3
        assert len(h1) == 16


class TestLLMGuardsJSONSchema:
    """AC5-AC6 : guards JSON plan d'action."""

    def _make_valid_action(self, **overrides) -> dict:
        base = {
            "title": "Installer eclairage LED basse consommation",
            "description": "Remplacer les ampoules existantes.",
            "category": "environment",
            "priority": "high",
            "due_date": "2026-09-30",
            "estimated_cost_xof": 500_000,
        }
        base.update(overrides)
        return base

    def test_valid_plan_ok(self) -> None:
        plan = [self._make_valid_action() for _ in range(8)]
        validated = validate_action_plan_schema(plan)
        assert len(validated) == 8
        assert validated[0].category == "environment"
        assert validated[0].priority == "high"

    def test_valid_plan_model_dump(self) -> None:
        plan = [self._make_valid_action() for _ in range(6)]
        validated = validate_action_plan_schema(plan)
        dumped = [a.model_dump(mode="json") for a in validated]
        assert isinstance(dumped, list)
        assert dumped[0]["category"] == "environment"

    def test_category_out_of_enum_raises(self) -> None:
        plan = [self._make_valid_action() for _ in range(6)]
        plan[0]["category"] = "hallucinated_category"
        with pytest.raises(LLMGuardError) as exc:
            validate_action_plan_schema(plan)
        assert exc.value.code == "schema_invalid"
        assert "category" in exc.value.details["errors"]

    def test_priority_out_of_enum_raises(self) -> None:
        plan = [self._make_valid_action() for _ in range(6)]
        plan[0]["priority"] = "CRITICAL"
        with pytest.raises(LLMGuardError) as exc:
            validate_action_plan_schema(plan)
        assert exc.value.code == "schema_invalid"

    def test_cost_exceeds_cap_raises(self) -> None:
        plan = [self._make_valid_action() for _ in range(6)]
        plan[0]["estimated_cost_xof"] = MAX_COST_XOF + 1
        with pytest.raises(LLMGuardError) as exc:
            validate_action_plan_schema(plan)
        assert exc.value.code == "schema_invalid"

    def test_cost_negative_raises(self) -> None:
        plan = [self._make_valid_action() for _ in range(6)]
        plan[0]["estimated_cost_xof"] = -100
        with pytest.raises(LLMGuardError) as exc:
            validate_action_plan_schema(plan)
        assert exc.value.code == "schema_invalid"

    def test_extra_key_raises(self) -> None:
        # extra='forbid' -> cle inventee rejetee
        plan = [self._make_valid_action() for _ in range(6)]
        plan[0]["hallucinated_co2_reduction"] = 42
        with pytest.raises(LLMGuardError) as exc:
            validate_action_plan_schema(plan)
        assert exc.value.code == "schema_invalid"

    def test_date_too_far_raises(self) -> None:
        plan = [self._make_valid_action() for _ in range(6)]
        plan[0]["due_date"] = "2099-12-31"
        with pytest.raises(LLMGuardError) as exc:
            validate_action_plan_schema(plan)
        assert exc.value.code == "schema_invalid"

    def test_invalid_date_format_raises(self) -> None:
        plan = [self._make_valid_action() for _ in range(6)]
        plan[0]["due_date"] = "demain"
        with pytest.raises(LLMGuardError) as exc:
            validate_action_plan_schema(plan)
        assert exc.value.code == "schema_invalid"

    def test_title_too_short_raises(self) -> None:
        plan = [self._make_valid_action() for _ in range(6)]
        plan[0]["title"] = "X"
        with pytest.raises(LLMGuardError) as exc:
            validate_action_plan_schema(plan)
        assert exc.value.code == "schema_invalid"

    def test_too_few_actions_raises(self) -> None:
        plan = [self._make_valid_action() for _ in range(2)]
        with pytest.raises(LLMGuardError) as exc:
            validate_action_plan_schema(plan)
        assert exc.value.code == "action_count_out_of_range"
        assert exc.value.details["count"] == 2

    def test_too_many_actions_raises(self) -> None:
        plan = [self._make_valid_action() for _ in range(30)]
        with pytest.raises(LLMGuardError) as exc:
            validate_action_plan_schema(plan)
        assert exc.value.code == "action_count_out_of_range"
        assert exc.value.details["count"] == 30

    def test_non_list_raises(self) -> None:
        with pytest.raises(LLMGuardError) as exc:
            validate_action_plan_schema({"not_a_list": True})
        assert exc.value.code == "schema_invalid"

    def test_non_dict_item_raises(self) -> None:
        plan = [self._make_valid_action() for _ in range(5)]
        plan[2] = "not_a_dict"
        with pytest.raises(LLMGuardError) as exc:
            validate_action_plan_schema(plan)
        assert exc.value.code == "schema_invalid"

    def test_optional_fields_allowed_none(self) -> None:
        plan = [
            self._make_valid_action(
                description=None, due_date=None, estimated_cost_xof=None
            )
            for _ in range(5)
        ]
        validated = validate_action_plan_schema(plan)
        assert len(validated) == 5


class TestActionPlanItemLLMSchemaDirect:
    """Tests unitaires directs du schema Pydantic (bords)."""

    def test_intermediary_name_too_long_rejected(self) -> None:
        with pytest.raises(Exception):
            ActionPlanItemLLMSchema(
                title="Rencontrer intermediaire local",
                category="intermediary_contact",
                priority="medium",
                intermediary_name="x" * 201,
            )

    def test_title_strip_whitespace(self) -> None:
        item = ActionPlanItemLLMSchema(
            title="   Action valide   ",
            category="social",
            priority="low",
        )
        assert item.title == "Action valide"

    def test_all_valid_categories_accepted(self) -> None:
        for cat in [
            "environment", "social", "governance",
            "financing", "carbon", "intermediary_contact",
        ]:
            item = ActionPlanItemLLMSchema(
                title="Action test valide",
                category=cat,
                priority="medium",
            )
            assert item.category == cat


# --- Tests review 9.6 : decisions D1/D2/D3 ---


class TestScoreDetectionInPercentageContext:
    """D1 : whitelist contextuelle pour assert_numeric_coherence.

    Un "X %" n'est verifie comme score que si un mot-cle
    (score, note, evaluation, pilier, global) est a +/- 5 tokens.
    """

    def test_percentage_with_score_keyword_rejected(self) -> None:
        # "score de 88 %" + vraies sources 54/60 -> drift attendu
        text = (
            "L'analyse globale de l'entreprise aboutit a un score de 88 % "
            "particulierement satisfaisant sur tous les piliers. "
            "La gouvernance et le social sont equilibres et coherents. "
            "Nous recommandons de consolider ces acquis progressivement."
        )
        sources = {"overall": 54.0, "env": 60.0, "soc": 48.0, "gov": 54.0}
        with pytest.raises(LLMGuardError) as exc:
            assert_numeric_coherence(text, sources, "test")
        assert exc.value.code == "numeric_drift"
        assert exc.value.details["detected_value"] == 88.0
        assert exc.value.details["expected"] is not None
        assert exc.value.details["field"] is not None

    def test_percentage_without_score_keyword_ignored(self) -> None:
        # "12 % du PIB" : pas de contexte score -> accepte
        text = (
            "Le secteur textile represente 12 % du PIB national, "
            "avec une croissance de 15 % observee cette annee. "
            "Les opportunites sectorielles sont nombreuses. "
            "L'entreprise peut saisir ces tendances favorables."
        )
        sources = {"overall": 54.0, "env": 60.0}
        # Ne doit PAS lever : pas de mot-cle score pres des %
        assert_numeric_coherence(text, sources, "test") is None

    def test_strict_pattern_always_verified(self) -> None:
        # "82/100" : pattern strict, pas besoin de contexte
        text = "L'entreprise obtient 82/100 au pilier gouvernance."
        sources = {"overall": 54.0, "env": 60.0}
        with pytest.raises(LLMGuardError) as exc:
            assert_numeric_coherence(text, sources, "test")
        assert exc.value.code == "numeric_drift"
        assert exc.value.details["detected_value"] == 82.0

    def test_percentage_near_pilier_keyword_rejected(self) -> None:
        text = (
            "Le pilier environnemental ressort a 85 % sur les donnees analysees. "
            "Les scores sociaux sont egalement bons. "
            "La gouvernance necessite quelques ameliorations. "
            "Continuez sur cette dynamique positive."
        )
        sources = {"env": 60.0, "soc": 48.0}
        with pytest.raises(LLMGuardError) as exc:
            assert_numeric_coherence(text, sources, "test")
        assert exc.value.code == "numeric_drift"

    def test_coherent_score_percentage_passes(self) -> None:
        # "score de 60 %" avec source env=60 -> passe (+/- tolerance 2.0)
        text = (
            "L'evaluation globale donne un score de 60 % sur le pilier "
            "environnemental, en coherence avec les donnees fournies. "
            "Les autres piliers restent a renforcer. "
            "Gardez cette trajectoire positive."
        )
        sources = {"env": 60.0, "soc": 48.0}
        assert_numeric_coherence(text, sources, "test") is None


class TestTransientErrorsPropagateToOuterRetry:
    """D2 : les erreurs infra transitoires (timeout, rate limit) sortent
    directement sans retry interne ni log guard. `run_guarded_llm_call`
    ne gere QUE la validation semantique (LLMGuardError).
    """

    @pytest.mark.asyncio
    async def test_timeout_error_propagates_without_retry(self) -> None:
        import httpx

        from app.core.llm_guards import run_guarded_llm_call

        call_count = {"n": 0}

        async def llm_call(prompt: str) -> str:
            call_count["n"] += 1
            raise httpx.TimeoutException("infra timeout")

        def guards(text: str) -> None:
            pass

        with pytest.raises(httpx.TimeoutException):
            await run_guarded_llm_call(
                llm_call=llm_call,
                guards=guards,
                base_prompt="p",
                hardened_prompt="p+",
                target="test",
                user_id="u1",
            )
        # Pas de retry interne : un seul appel
        assert call_count["n"] == 1

    @pytest.mark.asyncio
    async def test_generic_exception_propagates_without_retry(self) -> None:
        from app.core.llm_guards import run_guarded_llm_call

        call_count = {"n": 0}

        class FakeRateLimit(Exception):
            pass

        async def llm_call(prompt: str) -> str:
            call_count["n"] += 1
            raise FakeRateLimit("429 rate limited")

        def guards(text: str) -> None:
            pass

        with pytest.raises(FakeRateLimit):
            await run_guarded_llm_call(
                llm_call=llm_call,
                guards=guards,
                base_prompt="p",
                hardened_prompt="p+",
                target="test",
                user_id="u1",
            )
        assert call_count["n"] == 1


class TestDueDateValidationWithTimeframeContext:
    """D3 : validation due_date utilise `context['timeframe_months']` + tolerance 15 %."""

    @staticmethod
    def _iso_future(days: int) -> str:
        from datetime import date as _date
        from datetime import timedelta as _td

        return (_date.today() + _td(days=days)).isoformat()

    def test_timeframe_6_months_accepts_within_tolerance(self) -> None:
        # 6 mois * 31j * 1.15 ~ 214j : date a ~6.9 mois = OK
        item = ActionPlanItemLLMSchema.model_validate(
            {
                "title": "Action dans tolerance",
                "category": "environment",
                "priority": "medium",
                "due_date": self._iso_future(210),
            },
            context={"timeframe_months": 6},
        )
        assert item.due_date is not None

    def test_timeframe_6_months_rejects_18_months(self) -> None:
        # 18 mois pour un plan 6 mois -> reject
        with pytest.raises(Exception) as exc:
            ActionPlanItemLLMSchema.model_validate(
                {
                    "title": "Action hors horizon",
                    "category": "environment",
                    "priority": "medium",
                    "due_date": self._iso_future(18 * 31),
                },
                context={"timeframe_months": 6},
            )
        assert "horizon" in str(exc.value).lower()

    def test_timeframe_12_months_accepts_13_months(self) -> None:
        # 13 mois pour un plan 12 mois (< 15 % tolerance ~13.8) -> OK
        item = ActionPlanItemLLMSchema.model_validate(
            {
                "title": "Action 13 mois sur plan 12",
                "category": "social",
                "priority": "low",
                "due_date": self._iso_future(13 * 31),
            },
            context={"timeframe_months": 12},
        )
        assert item.due_date is not None

    def test_timeframe_12_months_rejects_15_months(self) -> None:
        # 15 mois > 12 * 1.15 = 13.8 -> reject
        with pytest.raises(Exception):
            ActionPlanItemLLMSchema.model_validate(
                {
                    "title": "Action 15 mois sur plan 12",
                    "category": "social",
                    "priority": "low",
                    "due_date": self._iso_future(15 * 31),
                },
                context={"timeframe_months": 12},
            )

    def test_timeframe_24_months_accepts_near_boundary(self) -> None:
        # 24 mois * 1.15 = 27.6 mois : 26 mois OK
        item = ActionPlanItemLLMSchema.model_validate(
            {
                "title": "Action 26 mois sur plan 24",
                "category": "governance",
                "priority": "high",
                "due_date": self._iso_future(26 * 31),
            },
            context={"timeframe_months": 24},
        )
        assert item.due_date is not None

    def test_no_context_defaults_to_max_timeframe(self) -> None:
        # Sans context : fallback MAX_TIMEFRAME_MONTHS = 24
        item = ActionPlanItemLLMSchema.model_validate(
            {
                "title": "Action sans contexte",
                "category": "financing",
                "priority": "medium",
                "due_date": self._iso_future(12 * 31),
            }
        )
        assert item.due_date is not None
