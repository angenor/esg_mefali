"""Tests IAM policies granulaires (Story 10.7 AC4 — absorbe LOW-10.6-2).

Parse le HCL du module iam via `python-hcl2` et assert :
    - Rôle app : **pas** de `s3:DeleteObject` (soft-delete applicatif only)
    - Rôle admin : condition `aws:MultiFactorAuthPresent == "true"` obligatoire
    - Anti-wildcard : aucun `Resource = "*"` dans tout le module iam
"""

from __future__ import annotations

import json
from pathlib import Path

import hcl2
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent
IAM_MAIN_TF = REPO_ROOT / "infra" / "terraform" / "modules" / "iam" / "main.tf"


@pytest.fixture(scope="module")
def iam_module() -> dict:
    """Parse le HCL une fois par module."""
    assert IAM_MAIN_TF.is_file(), f"Missing IAM module: {IAM_MAIN_TF}"
    with IAM_MAIN_TF.open("r", encoding="utf-8") as f:
        return hcl2.load(f)


def _extract_policy_statements(module: dict, policy_name: str) -> list[dict]:
    """Récupère les Statement d'une `aws_iam_policy` par son nom logique."""
    for resource in module.get("resource", []):
        if "aws_iam_policy" in resource:
            for logical_name, policy_def in resource["aws_iam_policy"].items():
                if logical_name == policy_name:
                    # Terraform wrap les blocks dans des listes
                    policy_json_expr = policy_def["policy"]
                    # python-hcl2 retourne l'expression jsonencode brute
                    # On cherche le dict statement dans l'expression
                    return policy_def
    raise AssertionError(f"Policy {policy_name} not found in IAM module")


def test_app_policy_has_no_delete_action(iam_module: dict):
    """Rôle app : `s3:DeleteObject` et `s3:DeleteObjectVersion` interdits.

    Leçon LOW-10.6-2 absorbée — app ne fait que soft-delete applicatif.
    """
    # Recherche brute dans le texte du module (plus robuste que HCL AST parsing
    # complexe de `jsonencode` expressions imbriquées)
    text = IAM_MAIN_TF.read_text(encoding="utf-8")

    # Split en sections aws_iam_policy
    app_section_start = text.find('resource "aws_iam_policy" "app_s3_read_write"')
    admin_section_start = text.find('resource "aws_iam_policy" "admin_s3_delete_mfa"')
    assert app_section_start != -1, "app_s3_read_write policy not found"
    assert admin_section_start != -1, "admin_s3_delete_mfa policy not found"

    # La policy app est avant la policy admin
    app_section_end = text.find('resource "aws_iam_policy"', app_section_start + 1)
    app_section = text[app_section_start:app_section_end]

    assert "s3:DeleteObject" not in app_section, (
        "Rôle app ne DOIT PAS avoir s3:DeleteObject — "
        "AC4 absorption LOW-10.6-2 (soft-delete applicatif uniquement)"
    )
    assert "s3:DeleteObjectVersion" not in app_section


def test_admin_policy_requires_mfa(iam_module: dict):
    """Rôle admin : `aws:MultiFactorAuthPresent == "true"` condition obligatoire."""
    text = IAM_MAIN_TF.read_text(encoding="utf-8")

    admin_section_start = text.find('resource "aws_iam_policy" "admin_s3_delete_mfa"')
    admin_section_end = text.find("\nresource ", admin_section_start + 1)
    if admin_section_end == -1:
        admin_section_end = len(text)
    admin_section = text[admin_section_start:admin_section_end]

    assert "aws:MultiFactorAuthPresent" in admin_section, (
        "Rôle admin DOIT avoir Condition MFA obligatoire (AC4)"
    )
    assert '"true"' in admin_section or "= true" in admin_section, (
        "MFA condition doit égaler 'true'"
    )


import re

# Patterns wildcard strictement interdits (review MEDIUM-10.7-3 + MEDIUM-10.7-4).
# Regex par vecteur — évite logique OR fragile sur proximité texte.
# Un wildcard scopé à un bucket (`arn:aws:s3:::mefali-prod/*`) est autorisé car
# le `*` final porte uniquement sur les OBJETS du bucket (scope strict).
_FORBIDDEN_WILDCARD_PATTERNS: dict[str, re.Pattern[str]] = {
    "resource_star_scalar":  re.compile(r'Resource"?\s*[:=]\s*"\*"'),
    "resource_star_array":   re.compile(r'Resource"?\s*[:=]\s*\[\s*"\*"'),
    "action_star_scalar":    re.compile(r'Action"?\s*[:=]\s*"\*"'),
    "action_star_array":     re.compile(r'Action"?\s*[:=]\s*\[\s*"\*"'),
    "action_s3_star":        re.compile(r'"s3:\*"'),
    "bucket_arn_star":       re.compile(r'"arn:aws:s3:::\*"'),
    "all_services_star":     re.compile(r'"arn:aws:\*"'),
    "single_service_star":   re.compile(r'"arn:aws:[a-z0-9-]+:\*"'),
    # Wildcard dans NOM de bucket (ex. `arn:aws:s3:::xyz*`) — dangereux car
    # le `*` porte sur la globalité du compte. Autorisé uniquement après `/`
    # (scope strict objets : `arn:aws:s3:::mefali-prod/*`).
    "bucket_name_star":      re.compile(r'"arn:aws:s3:::[^"/]*\*[^"/]*"'),
}


def _scan_iam_text(text: str) -> dict[str, list[tuple[int, str]]]:
    """Retourne {pattern_name: [(line_no, match), ...]} pour tout wildcard."""
    hits: dict[str, list[tuple[int, str]]] = {}
    for name, pattern in _FORBIDDEN_WILDCARD_PATTERNS.items():
        for match in pattern.finditer(text):
            line_no = text[: match.start()].count("\n") + 1
            hits.setdefault(name, []).append((line_no, match.group(0)))
    return hits


def test_no_wildcard_resource_in_iam_module():
    """Anti-wildcard strict — 8 patterns testés, aucun toléré.

    Refonte review MEDIUM-10.7-4 : supprime l'assertion OR fragile. Chaque match
    fail immédiatement avec la ligne exacte (audit trail PR review).
    """
    text = IAM_MAIN_TF.read_text(encoding="utf-8")
    hits = _scan_iam_text(text)
    assert hits == {}, (
        f"Wildcards IAM interdits détectés (MEDIUM-10.7-3 + AC4): "
        f"{ {name: locs for name, locs in hits.items()} }"
    )


@pytest.mark.parametrize(
    "adversarial_snippet,expected_match",
    [
        ('Resource = "*"',                                  "resource_star_scalar"),
        ('Resource = ["*"]',                                "resource_star_array"),
        ('Action = "s3:*"',                                 "action_s3_star"),
        ('Resource = "arn:aws:s3:::xyz*"',                  "bucket_name_star"),  # wildcard dans nom bucket
        ('Resource = ["arn:aws:s3:::my-bucket/*"]',         None),  # ← SCOPE STRICT, autorisé
        ('Action = ["*"]',                                  "action_star_array"),
        ('Resource = "arn:aws:*"',                          "all_services_star"),
        ('Resource = "arn:aws:dynamodb:*"',                 "single_service_star"),
    ],
)
def test_adversarial_wildcard_detection(adversarial_snippet: str, expected_match: str | None):
    """Tests adversariaux — vérifie que la batterie regex attrape les vecteurs
    connus ET ne fait pas faux positif sur scope strict bucket/objects.
    """
    hits = _scan_iam_text(adversarial_snippet)
    if expected_match is None:
        # Scope strict `arn:aws:s3:::bucket/*` → PAS de hit (objets du bucket OK)
        assert hits == {}, (
            f"Faux positif sur scope strict: {adversarial_snippet} → {hits}"
        )
    else:
        assert expected_match in hits, (
            f"Pattern {expected_match} devait matcher {adversarial_snippet!r}, "
            f"hits={hits}"
        )


def test_app_policy_resource_scoped_to_bucket():
    """Rôle app : Resource scopé à `arn:aws:s3:::${bucket}/*`, pas `*`."""
    text = IAM_MAIN_TF.read_text(encoding="utf-8")

    # Cherche la policy app
    app_section_start = text.find('resource "aws_iam_policy" "app_s3_read_write"')
    app_section_end = text.find("\nresource ", app_section_start + 1)
    app_section = text[app_section_start:app_section_end]

    # Doit référencer local.bucket_arn ou local.bucket_objects (scope strict)
    assert "local.bucket_arn" in app_section or "local.bucket_objects" in app_section, (
        "App policy doit scoper Resource sur bucket_arn/bucket_objects (pas wildcard)"
    )
