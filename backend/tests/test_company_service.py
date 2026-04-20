"""Tests unitaires du service company."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import CompanyProfile
from app.modules.company.schemas import CompanyProfileUpdate
from app.modules.company.service import (
    compute_completion,
    get_or_create_profile,
    get_profile,
    update_profile,
)


@pytest.fixture
def user_id() -> uuid.UUID:
    """ID utilisateur de test."""
    return uuid.uuid4()


# ── compute_completion ──────────────────────────────────────────────


class TestComputeCompletion:
    """Tests pour le calcul de complétion."""

    def test_empty_profile_has_country_default(self) -> None:
        """Un profil avec uniquement country rempli a 12.5% identité."""
        profile = CompanyProfile(user_id=uuid.uuid4(), country="Côte d'Ivoire")
        result = compute_completion(profile)

        assert result.identity_completion == 12.5
        assert result.esg_completion == 0.0
        assert result.overall_completion == 6.2  # (12.5 + 0) / 2 arrondi
        assert "country" in result.identity_fields.filled
        assert "company_name" in result.identity_fields.missing

    def test_full_identity_completion(self) -> None:
        """Tous les champs identité remplis = 100%."""
        profile = CompanyProfile(
            user_id=uuid.uuid4(),
            company_name="EcoPlast",
            sector="recyclage",
            sub_sector="plastique",
            employee_count=15,
            annual_revenue_xof=50_000_000,
            year_founded=2018,
            city="Abidjan",
            country="Côte d'Ivoire",
        )
        result = compute_completion(profile)

        assert result.identity_completion == 100.0
        assert len(result.identity_fields.missing) == 0

    def test_full_esg_completion(self) -> None:
        """Tous les champs ESG remplis = 100%."""
        profile = CompanyProfile(
            user_id=uuid.uuid4(),
            has_waste_management=True,
            has_energy_policy=False,
            has_gender_policy=True,
            has_training_program=False,
            has_financial_transparency=True,
            governance_structure="Conseil d'administration",
            environmental_practices="Tri sélectif",
            social_practices="Emploi local",
        )
        result = compute_completion(profile)

        assert result.esg_completion == 100.0
        # Booléens False comptent comme remplis
        assert "has_energy_policy" in result.esg_fields.filled

    def test_overall_is_average(self) -> None:
        """La complétion globale est la moyenne identité + ESG."""
        profile = CompanyProfile(
            user_id=uuid.uuid4(),
            company_name="Test",
            sector="agriculture",
            city="Bamako",
            country="Mali",
            # 4/8 identity = 50%
            has_waste_management=True,
            has_energy_policy=True,
            # 2/8 ESG = 25%
        )
        result = compute_completion(profile)

        assert result.identity_completion == 50.0
        assert result.esg_completion == 25.0
        assert result.overall_completion == 37.5  # (50 + 25) / 2

    def test_empty_string_not_counted(self) -> None:
        """Une chaîne vide n'est pas considérée comme remplie."""
        profile = CompanyProfile(
            user_id=uuid.uuid4(),
            governance_structure="",
            country="Côte d'Ivoire",
        )
        result = compute_completion(profile)

        assert "governance_structure" in result.esg_fields.missing


# ── get_or_create_profile ───────────────────────────────────────────


class TestGetOrCreateProfile:
    """Tests pour la création/récupération du profil."""

    @pytest.mark.asyncio
    async def test_creates_profile_if_not_exists(
        self, db_session: AsyncSession, user_id: uuid.UUID
    ) -> None:
        """Crée un profil initialisé avec le company_name de l'utilisateur."""
        # Créer un utilisateur d'abord
        from app.models.user import User

        user = User(
            id=user_id,
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            company_name="Test Co",
        )
        db_session.add(user)
        await db_session.flush()

        profile = await get_or_create_profile(db_session, user_id)

        assert profile.user_id == user_id
        # Le country n'est plus hardcodé : il est déterminé à l'inscription
        # via géolocalisation IP (ou saisi par l'utilisateur).
        assert profile.country is None
        # Le company_name est backfillé depuis User.company_name pour que
        # le LLM ait accès au nom de l'entreprise dès la première conversation.
        assert profile.company_name == "Test Co"

    @pytest.mark.asyncio
    async def test_returns_existing_profile(
        self, db_session: AsyncSession, user_id: uuid.UUID
    ) -> None:
        """Retourne le profil existant sans en créer un nouveau."""
        from app.models.user import User

        user = User(
            id=user_id,
            email="test2@example.com",
            hashed_password="hashed",
            full_name="Test User",
            company_name="Test Co",
        )
        db_session.add(user)
        await db_session.flush()

        profile1 = await get_or_create_profile(db_session, user_id)
        profile1.company_name = "EcoPlast"
        await db_session.flush()

        profile2 = await get_or_create_profile(db_session, user_id)
        assert profile2.id == profile1.id
        assert profile2.company_name == "EcoPlast"


# ── update_profile ──────────────────────────────────────────────────


class TestUpdateProfile:
    """Tests pour la mise à jour partielle du profil."""

    @pytest.mark.asyncio
    async def test_partial_update(
        self, db_session: AsyncSession, user_id: uuid.UUID
    ) -> None:
        """Seuls les champs non-null sont mis à jour."""
        from app.models.user import User

        user = User(
            id=user_id,
            email="test3@example.com",
            hashed_password="hashed",
            full_name="Test",
            company_name="Test",
        )
        db_session.add(user)
        await db_session.flush()

        profile = await get_or_create_profile(db_session, user_id)

        updates = CompanyProfileUpdate(
            company_name="EcoPlast", sector="recyclage"
        )
        # Story 9.5 : update_profile retourne un 3-uplet (profile, changed, skipped).
        updated_profile, changed, _skipped = await update_profile(
            db_session, profile, updates
        )

        assert updated_profile.company_name == "EcoPlast"
        assert updated_profile.sector.value == "recyclage"
        # country reste tel qu'il était (None dans ce contexte de test)
        assert updated_profile.country is None
        assert len(changed) == 2
        assert any(c["field"] == "company_name" for c in changed)

    @pytest.mark.asyncio
    async def test_no_change_when_same_value(
        self, db_session: AsyncSession, user_id: uuid.UUID
    ) -> None:
        """Pas de changement quand la valeur est identique."""
        from app.models.user import User

        user = User(
            id=user_id,
            email="test4@example.com",
            hashed_password="hashed",
            full_name="Test",
            company_name="Test",
        )
        db_session.add(user)
        await db_session.flush()

        profile = await get_or_create_profile(db_session, user_id)
        profile.city = "Abidjan"
        await db_session.flush()

        updates = CompanyProfileUpdate(city="Abidjan")
        # Story 9.5 : update_profile retourne un 3-uplet (profile, changed, skipped).
        _, changed, _skipped = await update_profile(db_session, profile, updates)

        assert len(changed) == 0


# ── get_profile ─────────────────────────────────────────────────────


class TestGetProfile:
    """Tests pour la récupération du profil."""

    @pytest.mark.asyncio
    async def test_returns_none_if_not_exists(
        self, db_session: AsyncSession
    ) -> None:
        """Retourne None si le profil n'existe pas."""
        result = await get_profile(db_session, uuid.uuid4())
        assert result is None


# ── Story 9.5 — TestManualEdit (P1 #7) ──────────────────────────────


class TestManualEdit:
    """Story 9.5 : flag manually_edited_fields — edition manuelle prevaut.

    Couvre AC1 (skip LLM + log WARNING + event skip), AC2 (pas de verrou manuel,
    idempotence du flag), AC3 (champ non-touche = comportement normal), AC4
    (retro-compatibilite liste vide).
    """

    @pytest.mark.asyncio
    async def test_manual_edit_marks_field(
        self, db_session: AsyncSession, user_id: uuid.UUID
    ) -> None:
        """AC2 partie 1 : edition manuelle ajoute le champ a la liste protegee."""
        from app.models.user import User

        user = User(
            id=user_id, email="manual1@example.com",
            hashed_password="hashed", full_name="X", company_name="X",
        )
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
    async def test_llm_update_skips_manually_edited_fields(
        self, db_session: AsyncSession, user_id: uuid.UUID
    ) -> None:
        """AC1 : tool LLM ne doit pas ecraser un champ deja edite manuellement."""
        from app.models.user import User

        user = User(
            id=user_id, email="manual2@example.com",
            hashed_password="hashed", full_name="X", company_name="X",
        )
        db_session.add(user)
        await db_session.flush()

        profile = await get_or_create_profile(db_session, user_id)
        # Phase 1 : edition manuelle sector=textile
        await update_profile(
            db_session, profile,
            CompanyProfileUpdate(sector="textile"), source="manual",
        )
        assert profile.sector.value == "textile"
        assert "sector" in profile.manually_edited_fields

        # Phase 2 : tentative ecrasement par LLM
        updated, changed, skipped = await update_profile(
            db_session, profile,
            CompanyProfileUpdate(sector="agriculture"), source="llm",
        )

        assert updated.sector.value == "textile"  # NON ecrase
        assert changed == []
        assert len(skipped) == 1
        assert skipped[0]["field"] == "sector"
        assert skipped[0]["attempted_value"] == "agriculture"
        assert skipped[0]["current_value"] == "textile"
        assert skipped[0]["label"] == "Secteur"

    @pytest.mark.asyncio
    async def test_llm_update_logs_warning_on_skip(
        self, db_session: AsyncSession, user_id: uuid.UUID, caplog
    ) -> None:
        """AC1 partie 2 : un log WARNING est emis sur chaque skip LLM."""
        import logging

        from app.models.user import User

        user = User(
            id=user_id, email="manual3@example.com",
            hashed_password="hashed", full_name="X", company_name="X",
        )
        db_session.add(user)
        await db_session.flush()

        profile = await get_or_create_profile(db_session, user_id)
        await update_profile(
            db_session, profile,
            CompanyProfileUpdate(sector="textile"), source="manual",
        )

        with caplog.at_level(logging.WARNING, logger="app.modules.company.service"):
            await update_profile(
                db_session, profile,
                CompanyProfileUpdate(sector="agriculture"), source="llm",
            )

        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warnings) == 1
        assert "sector" in warnings[0].getMessage()
        assert "edite manuellement" in warnings[0].getMessage()

    @pytest.mark.asyncio
    async def test_second_manual_edit_keeps_mark(
        self, db_session: AsyncSession, user_id: uuid.UUID
    ) -> None:
        """AC2 partie 2 : edition manuelle 2 = mise a jour OK + flag idempotent."""
        from app.models.user import User

        user = User(
            id=user_id, email="manual4@example.com",
            hashed_password="hashed", full_name="X", company_name="X",
        )
        db_session.add(user)
        await db_session.flush()

        profile = await get_or_create_profile(db_session, user_id)
        await update_profile(
            db_session, profile,
            CompanyProfileUpdate(sector="textile"), source="manual",
        )
        await update_profile(
            db_session, profile,
            CompanyProfileUpdate(sector="agroalimentaire"), source="manual",
        )

        assert profile.sector.value == "agroalimentaire"
        # Idempotence : le champ n'apparait qu'une seule fois
        assert profile.manually_edited_fields.count("sector") == 1

    @pytest.mark.asyncio
    async def test_non_edited_field_updates_normally(
        self, db_session: AsyncSession, user_id: uuid.UUID
    ) -> None:
        """AC3 : champ jamais edite manuellement -> LLM update passe normalement."""
        from app.models.user import User

        user = User(
            id=user_id, email="manual5@example.com",
            hashed_password="hashed", full_name="X", company_name="X",
        )
        db_session.add(user)
        await db_session.flush()

        profile = await get_or_create_profile(db_session, user_id)
        assert profile.manually_edited_fields == []

        updated, changed, skipped = await update_profile(
            db_session, profile,
            CompanyProfileUpdate(city="Dakar"), source="llm",
        )

        assert updated.city == "Dakar"
        assert len(changed) == 1
        assert skipped == []
        # IMPORTANT : le chemin LLM ne doit PAS marquer le champ comme manuel
        assert "city" not in updated.manually_edited_fields

    @pytest.mark.asyncio
    async def test_llm_partial_update_skips_only_protected(
        self, db_session: AsyncSession, user_id: uuid.UUID
    ) -> None:
        """AC1+AC3 mixte : LLM update sur 2 champs dont 1 protege -> skip 1, applique 1."""
        from app.models.user import User

        user = User(
            id=user_id, email="manual6@example.com",
            hashed_password="hashed", full_name="X", company_name="X",
        )
        db_session.add(user)
        await db_session.flush()

        profile = await get_or_create_profile(db_session, user_id)
        await update_profile(
            db_session, profile,
            CompanyProfileUpdate(sector="textile"), source="manual",
        )

        updated, changed, skipped = await update_profile(
            db_session, profile,
            CompanyProfileUpdate(sector="agriculture", city="Bamako"),
            source="llm",
        )

        assert updated.sector.value == "textile"  # protege
        assert updated.city == "Bamako"  # passe
        assert len(changed) == 1
        assert changed[0]["field"] == "city"
        assert len(skipped) == 1
        assert skipped[0]["field"] == "sector"

    @pytest.mark.asyncio
    async def test_legacy_profile_with_empty_manual_list(
        self, db_session: AsyncSession, user_id: uuid.UUID
    ) -> None:
        """AC4 : profil pre-existant (manually_edited_fields=[]) -> comportement inchange."""
        from app.models.user import User

        user = User(
            id=user_id, email="manual7@example.com",
            hashed_password="hashed", full_name="X", company_name="X",
        )
        db_session.add(user)
        await db_session.flush()

        # Simuler un profil « legacy » avec liste vide explicite (post-migration)
        profile = await get_or_create_profile(db_session, user_id)
        profile.manually_edited_fields = []
        await db_session.flush()

        # Tout LLM update doit passer normalement
        updated, changed, skipped = await update_profile(
            db_session, profile,
            CompanyProfileUpdate(sector="agriculture", city="Lome"),
            source="llm",
        )

        assert updated.sector.value == "agriculture"
        assert updated.city == "Lome"
        assert len(changed) == 2
        assert skipped == []
