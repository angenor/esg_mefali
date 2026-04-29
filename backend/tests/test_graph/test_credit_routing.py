"""Tests routing déterministe credit (BUG-V8-002).

Vérifie que `_detect_credit_request` reconnaît les déclencheurs du forçage
`_FORCE_CREDIT_RE` du `credit_node`. Sans cet alignement (V8 initial), la
phrase « évalue ma solvabilité » échouait à matcher `_CREDIT_PATTERNS` et le
router routait vers chat_node, contournant le forçage déterministe AXE3.
"""

from __future__ import annotations

import pytest

from app.graph.nodes import _detect_credit_request


class TestDetectCreditRequestV8:
    """BUG-V8-002 : alignement router ↔ forçage credit_node."""

    @pytest.mark.parametrize(
        "text",
        [
            "évalue ma solvabilité",
            "évalue ma solvabilité maintenant",
            "evalue ma solvabilite",
            "calcule mon score",
            "calcule mon score crédit vert",
            "génère mon score crédit",
            "donne-moi mon score de solvabilité",
            "fais mon scoring de crédit",
            "mon score crédit",
            "scoring crédit vert",
        ],
    )
    def test_detects_credit_request(self, text: str):
        assert _detect_credit_request(text) is True

    @pytest.mark.parametrize(
        "text",
        [
            "bonjour",
            "comment ça va",
            "explique-moi le bilan carbone",
            "quel est mon plan d'action",
            "",
        ],
    )
    def test_rejects_non_credit_request(self, text: str):
        assert _detect_credit_request(text) is False
