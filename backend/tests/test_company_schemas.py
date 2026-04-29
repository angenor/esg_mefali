"""Tests unitaires des validators Pydantic du schema CompanyProfileUpdate.

Couvre BUG-V7-002 / V7.1-002 : `_strip_or_reject_blank` rejette les chaines
whitespace-only ou empty cote REST (defense en profondeur, le tool LLM
update_company_profile etait deja durci par BUG-V6-011).
"""

import pytest
from pydantic import ValidationError

from app.modules.company.schemas import CompanyProfileUpdate


class TestStripOrRejectBlank:
    """Validator _strip_or_reject_blank sur les champs string optionnels."""

    @pytest.mark.parametrize(
        "field",
        [
            "company_name",
            "sub_sector",
            "city",
            "country",
            "governance_structure",
            "environmental_practices",
            "social_practices",
            "notes",
        ],
    )
    def test_whitespace_only_raises_validation_error(self, field: str) -> None:
        """`"   "` doit lever une erreur de validation (HTTP 422 cote REST)."""
        with pytest.raises(ValidationError) as exc_info:
            CompanyProfileUpdate(**{field: "   "})
        assert "vide" in str(exc_info.value).lower() or "espaces" in str(exc_info.value).lower()

    @pytest.mark.parametrize(
        "field",
        [
            "company_name",
            "sub_sector",
            "city",
            "country",
            "governance_structure",
            "environmental_practices",
            "social_practices",
            "notes",
        ],
    )
    def test_empty_string_raises_validation_error(self, field: str) -> None:
        """`""` (empty string) doit lever une erreur de validation."""
        with pytest.raises(ValidationError):
            CompanyProfileUpdate(**{field: ""})

    def test_padded_value_is_trimmed(self) -> None:
        """`"  AgriVert  "` doit etre normalise en `"AgriVert"`."""
        result = CompanyProfileUpdate(company_name="  AgriVert Sarl  ")
        assert result.company_name == "AgriVert Sarl"

    def test_none_passes_through(self) -> None:
        """`None` (champ omis) doit rester `None` sans erreur."""
        result = CompanyProfileUpdate(company_name=None)
        assert result.company_name is None

    def test_normal_value_unchanged(self) -> None:
        """Valeur normale sans espaces externes preservee telle quelle."""
        result = CompanyProfileUpdate(city="Dakar")
        assert result.city == "Dakar"

    def test_mixed_payload_trim_and_none(self) -> None:
        """Payload mixte : un champ trim, un autre None, autres absents."""
        result = CompanyProfileUpdate(
            company_name="  AgriVert  ",
            city=None,
        )
        assert result.company_name == "AgriVert"
        assert result.city is None
        # Champs non fournis doivent rester `None` par defaut.
        assert result.country is None
        assert result.sub_sector is None

    def test_tab_and_newline_only_rejected(self) -> None:
        """Whitespace divers (`\\t\\n  `) doit etre rejete."""
        with pytest.raises(ValidationError):
            CompanyProfileUpdate(company_name="\t\n  ")

    def test_employee_count_unaffected_by_string_validator(self) -> None:
        """Le validator string ne doit pas casser le coerce_int_strings existant."""
        result = CompanyProfileUpdate(employee_count="42")
        assert result.employee_count == 42

    @pytest.mark.parametrize(
        "ch_name,ch",
        [
            ("ZWS", "​"),
            ("ZWNJ", "‌"),
            ("ZWJ", "‍"),
            ("WJ", "⁠"),
            ("BOM", "﻿"),
        ],
    )
    def test_zero_width_unicode_rejected(self, ch_name: str, ch: str) -> None:
        """V8-AXE5 review : zero-width / BOM ne doivent pas passer (R3-1)."""
        with pytest.raises(ValidationError):
            CompanyProfileUpdate(company_name=ch)

    def test_mixed_invisible_and_whitespace_rejected(self) -> None:
        """Combinaison d'espaces standards + invisibles : rejet."""
        with pytest.raises(ValidationError):
            CompanyProfileUpdate(company_name="  ​⁠﻿  ")
