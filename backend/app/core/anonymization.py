"""Anonymisation déterministe PII AO (Story 10.7 AC5 — D8.2).

Pipeline PROD→STAGING :
    1. Dump PROD (pg_dump filtré par `EXCLUDED_TABLES` — BLOB docs/reports hors scope).
    2. Scan ligne-par-ligne du dump SQL, substitution `PII_PATTERNS` par
       `anonymize_deterministic(value, salt)`.
    3. Re-scan post-anonymisation : `AnonymizationPatternViolation` levée
       + exit ≠ 0 si ≥ 1 pattern matche encore (fail-fast architecture §D8.2).

15 patterns PII FR/AO :
    - Identifiants entreprises : RCCM OHADA, NINEA SN, IFU CI/BF/BJ/TG, NIF ML/NE.
    - Identifiants personnels : email, phone CEDEAO, CNI SN.
    - Financiers : IBAN, BIC, amount_fcfa_precise.
    - Coordonnées : address_precise.
    - Dates : date_birth_iso.
    - Noms : name_composed (préfixes FR/AO fréquents — fallback NER différé
      Phase Growth, Q2 tranchée).
    - Réseau : ipv4 (logs embarqués).

Contraintes héritées :
    - C1 (9.7) : 3 exceptions canoniques — pas de `except Exception`.
    - C2 (9.7) : testable sur vrai dump fixture, pas mock regex engine.
    - Règle d'or 10.5 : effet observable (scan_for_pii post-anonymisation).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

# 15 patterns PII FR/AO — validation fail-fast (architecture.md §D8.2).
# Ordre important : les plus spécifiques d'abord (anti-overlap).
PII_PATTERNS: dict[str, re.Pattern[str]] = {
    # --- Identifiants entreprises OHADA ---
    # RCCM : RC, RCC, RCM ou RCCM — suivi du format OHADA standard.
    "rccm_ohada":    re.compile(r"\bRCC?M?\s+[A-Z]{2,3}\s+[A-Z]{3}\s+\d{4}-[A-Z]-\d+\b"),
    "ninea_sn":      re.compile(r"\b\d{7,9}\s+[A-Z]\s+\d\b"),
    "ifu_ci":        re.compile(r"\b\d{10,13}[A-Z]\b"),
    "ifu_bf_bj_tg":  re.compile(r"\bIFU[-\s:]*\d{7,12}\b", re.IGNORECASE),
    "nif_ml_ne":     re.compile(r"\bNIF[-\s:]*\d{8,11}[A-Z]?\b", re.IGNORECASE),
    # --- Identifiants personnels ---
    # Exclut les domaines déjà anonymisés (éviter re-anonymisation infinie)
    "email_real":    re.compile(
        r"\b[\w.+-]+@(?!anonymized\.test\b|example\.(?:com|org)\b)[\w.-]+\.\w{2,}\b"
    ),
    # Téléphones CEDEAO : +221/+225/+226/+227/+228/+229. `+` obligatoire
    # pour éviter les faux positifs sur les hashes anonymisés (séquences
    # numériques aléatoires 221/225 dans SHA256 tronqué).
    "phone_cedeao":  re.compile(
        r"\+22[1-9][\s.-]?\d{2,3}[\s.-]?\d{2,3}[\s.-]?\d{2,3}[\s.-]?\d{0,3}"
    ),
    # CNI Sénégal 13 chiffres (formats 1/2 + 4 blocs)
    "cni_sn":        re.compile(r"\b[12][\s-]?\d{3}[\s-]?\d{4}[\s-]?\d{5}\b"),
    # --- Financier ---
    "iban":          re.compile(r"\b[A-Z]{2}\d{2}(?:[\s-]?\d{4}){3,7}[\s-]?\d{0,4}\b"),
    "bic_swift":     re.compile(r"\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b"),
    "amount_fcfa_precise": re.compile(
        r"\b\d{1,3}(?:[  .]\d{3}){2,}\s*(?:F\s?CFA|XOF|XAF)\b"
    ),
    # --- Coordonnées ---
    "address_precise": re.compile(
        r"\b\d{1,4}\s+(?:rue|avenue|av\.|bd|boulevard|route|impasse|allée|all\.)"
        r"\s+[\w\s\-']+",
        re.IGNORECASE,
    ),
    # --- Dates sensibles ---
    # ⚠️ Large : à scope à champs PII uniquement en prod (bio, birth_date, etc.)
    "date_birth_iso": re.compile(r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b"),
    # --- Noms composés FR/AO (fallback regex — NER différé Phase Growth Q2) ---
    "name_composed": re.compile(
        r"\b(?:M\.|Mme|Dr|Pr|El\s*Hadj|Seydou|Aminata|Mariam|Fatou|Moussa|"
        r"Ibrahima?|Aissatou|Mamadou|Ousmane|Abdoulaye|Cheikh|Fatima)"
        r"\s+[A-ZÀ-Ý][a-zà-ÿ]+(?:\s+[A-ZÀ-Ý][a-zà-ÿ]+)?\b"
    ),
    # --- Réseau ---
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}

# Tables exclues du dump anonymisé (BLOB binaires — filtrés en amont par
# `pg_dump --exclude-table`, pas anonymisées après). Listées pour audit.
EXCLUDED_TABLES: frozenset[str] = frozenset({
    "documents",   # file_content_bytes BYTEA
    "reports",     # pdf_bytes BYTEA
})

# Env var name for deterministic salt (fail-fast au boot du CLI)
ANONYMIZATION_SALT_ENV = "ANONYMIZATION_SALT"


class AnonymizationError(Exception):
    """Base class pour toutes les erreurs du pipeline anonymisation.

    Hiérarchie explicite — permet `except AnonymizationError` granulaire
    côté ops sans tomber dans `except Exception` (leçon C1 9.7).
    """


class AnonymizationPatternViolation(AnonymizationError):
    """Un pattern PII est détecté APRÈS anonymisation (fail-fast D8.2).

    L'ops doit enrichir `PII_PATTERNS` ou corriger le filtrage amont avant
    de rejouer le pipeline. Bloque systématiquement la restauration STAGING.
    """


class AnonymizationDumpError(AnonymizationError):
    """Lecture/écriture du dump SQL a échoué (I/O, encoding, ...)."""


class AnonymizationRestoreError(AnonymizationError):
    """Restauration du dump anonymisé vers STAGING a échoué (DB down, etc.)."""


@dataclass(frozen=True)
class AnonymizationResult:
    """Trace d'une substitution PII — consommé par audit log JSON."""

    pattern_name: str
    value_before: str
    value_after: str


def anonymize_deterministic(value: str, salt: str) -> str:
    """Mapping déterministe : même valeur → même anonymisation.

    Préserve les jointures SQL post-anonymisation (un email qui apparaît
    dans 3 tables reste unique dans ces 3 tables après transformation).

    Algorithme : SHA256(value + salt) → hex → 12 premiers caractères.
    Préfixe `anonymized-` pour marquer visuellement les valeurs synthétiques
    (et fournir au pattern `email_real` un domaine à exclure du re-scan).

    Args:
        value: valeur PII brute détectée dans le dump.
        salt: secret 32+ bytes lu depuis `ANONYMIZATION_SALT` env var,
              jamais commité. Rotation manuelle Phase Growth si leak.

    Returns:
        chaîne `anonymized-<hash12>` stable pour une paire (value, salt).
    """
    if not salt:
        raise AnonymizationError(
            f"{ANONYMIZATION_SALT_ENV} must be non-empty (deterministic mapping)"
        )
    digest = hashlib.sha256((value + salt).encode("utf-8")).hexdigest()[:12]
    return f"anonymized-{digest}"


def scan_for_pii(text: str) -> list[tuple[str, str]]:
    """Scan exhaustif : retourne [(pattern_name, matched_value), ...].

    Utilisé (a) pour remplacer les PII au premier passage,
    (b) pour re-scanner le dump anonymisé et fail-fast si résiduel.

    Args:
        text: contenu brut du dump SQL (potentiellement plusieurs MB).

    Returns:
        liste vide si aucun PII détecté (cas attendu post-anonymisation).
    """
    violations: list[tuple[str, str]] = []
    for name, pattern in PII_PATTERNS.items():
        for match in pattern.finditer(text):
            violations.append((name, match.group(0)))
    return violations


def anonymize_text(text: str, salt: str) -> tuple[str, list[AnonymizationResult]]:
    """Substitue toutes les occurrences de `PII_PATTERNS` dans `text`.

    Args:
        text: contenu SQL brut (ligne ou bloc).
        salt: secret déterministe.

    Returns:
        (text anonymisé, trace des substitutions pour audit log).
    """
    results: list[AnonymizationResult] = []
    current = text
    for name, pattern in PII_PATTERNS.items():
        def _replace(match: re.Match[str]) -> str:
            original = match.group(0)
            replacement = anonymize_deterministic(original, salt)
            results.append(
                AnonymizationResult(
                    pattern_name=name,
                    value_before=original,
                    value_after=replacement,
                )
            )
            return replacement

        current = pattern.sub(_replace, current)
    return current, results
