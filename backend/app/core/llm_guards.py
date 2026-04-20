"""Guards LLM pour les contenus persistes remis aux bailleurs (SC-T8, Risque 10).

Protege les 2 surfaces LLM actuelles :
- Resume executif ESG (reports/service.py)
- Plan d'action JSON (action_plan/service.py)

Story 9.6 / P1 #10 audit.
"""

from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from datetime import date, timedelta
from typing import Any, Awaitable, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from app.models.action_plan import ActionItemCategory, ActionItemPriority

logger = logging.getLogger(__name__)

# --- Constantes tunables (exposees pour audit + tests) ---

# Resume executif ESG
MIN_SUMMARY_LEN = 200
MAX_SUMMARY_LEN = 3000

# Plan d'action
MIN_ACTION_COUNT = 5
MAX_ACTION_COUNT = 20
MAX_COST_XOF = 10_000_000_000  # 10 milliards FCFA plafond par action
MAX_TIMEFRAME_MONTHS = 24
# Tolerance sur due_date (15 % du timeframe) pour absorber les legers
# depassements LLM : un plan 6 mois accepte jusqu'a ~6.9 mois.
DUE_DATE_TOLERANCE_RATIO = 0.15

# Derive du modele SQLAlchemy pour eviter le drift enum / guard (review 9.6).
VALID_CATEGORIES: frozenset[str] = frozenset(c.value for c in ActionItemCategory)
VALID_PRIORITIES: frozenset[str] = frozenset(p.value for p in ActionItemPriority)

# Vocabulaire interdit (responsabilite juridique, Risque 10).
# Termes normalises sans accents (la detection applique _strip_accents
# sur le texte ET sur les termes pour defense en profondeur).
# Inclut les conjugaisons actives frequentes (garantit, garantissons, ...).
FORBIDDEN_VOCAB: tuple[str, ...] = (
    "garanti",
    "garantie",
    "garantis",
    "garanties",
    "garantit",
    "garantissons",
    "garantissez",
    "garantissent",
    "certifie",
    "certifiee",
    "certifies",
    "certifiees",
    "certifions",
    "certifient",
    "valide par",
    "validee par",
    "valides par",
    "validees par",
    "homologue",
    "homologuee",
    "accredite",
    "accreditee",
    "accreditons",
    "officiellement reconnu",
    "officiellement reconnue",
)

# Detection de langue francaise (mots outils FR tres frequents,
# robuste sur textes > 100 chars). Inclut les formes elidees (l', d', qu', n').
_FR_STOPWORDS: frozenset[str] = frozenset({
    "le", "la", "les", "un", "une", "des", "de", "du",
    "et", "ou", "est", "sont", "pour", "dans", "avec",
    "sur", "par", "ce", "cette", "ces", "votre", "vos",
    "nous", "vous", "il", "elle", "ils", "elles",
    "a", "au", "aux", "en", "que", "qui", "plus", "moins",
    "son", "sa", "ses", "leur", "leurs", "mais", "donc",
    "si", "ne", "pas", "tres", "bien", "aussi",
    # Formes elidees (l'entreprise, d'une, qu'il, n'est, c'est, s'il)
    "l", "d", "qu", "n", "c", "s", "j", "m", "t",
})
MIN_FR_RATIO = 0.12  # 12 % de tokens stopword FR = seuil sain
# Seuil minimal d'analyse : en-dessous, pas assez de signal pour un verdict fiable.
# Baisse depuis 50 tokens (review 9.6) : un resume >= 200 chars contient
# typiquement 30-45 tokens, donc 50 laissait passer trop de textes.
MIN_TOKENS_FOR_LANG_CHECK = 20

# Mots-cles declencheurs d'une verification numeric_coherence en mode "%"
# (whitelist contextuelle, decision D1 review 9.6) : un "X%" isole dans le
# texte n'est verifie que si l'un de ces mots apparait a +/- 5 tokens.
_SCORE_CONTEXT_KEYWORDS: frozenset[str] = frozenset({
    "score", "scores",
    "note", "notes", "notation",
    "evaluation", "evaluations",
    "pilier", "piliers",
    "global", "globale", "globaux",
    "overall",
})
_SCORE_CONTEXT_WINDOW = 5  # tokens de part et d'autre


# --- Exception unifiee ---


class LLMGuardError(Exception):
    """Exception levee quand un guard LLM detecte une anomalie.

    Attributes:
        code: identifiant machine de la cause ("numeric_drift", "forbidden_vocab", ...)
        target: surface LLM concernee ("executive_summary", "action_plan", ...)
        details: dict libre d'infos pour audit/log (detected, expected, field, ...)
    """

    def __init__(
        self,
        code: str,
        target: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.target = target
        self.details = details or {}
        super().__init__(
            f"LLM guard failed: code={code} target={target} details={self.details}"
        )


# --- Helpers normalisation ---


def _strip_accents(text: str) -> str:
    """Retirer les accents pour la detection insensible a l'accent (vocab interdit)."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _normalize_whitespace(text: str) -> str:
    """Remplacer NBSP (U+00A0), thin space (U+202F), narrow NBSP par espace ASCII."""
    return (text or "").replace("\u00a0", " ").replace("\u202f", " ").replace("\u2009", " ")


def prompt_hash(prompt: str) -> str:
    """SHA-256 des 200 premiers chars du prompt, pour audit sans exposer le contenu."""
    sample = prompt[:200].encode("utf-8")
    return hashlib.sha256(sample).hexdigest()[:16]


# --- Free text guards (resume executif) ---


def assert_length(
    text: str,
    min_chars: int,
    max_chars: int,
    target: str,
) -> None:
    """AC4 : borner la longueur du texte LLM."""
    n = len(text or "")
    if n < min_chars:
        raise LLMGuardError(
            "too_short", target, {"length": n, "min": min_chars}
        )
    if n > max_chars:
        raise LLMGuardError(
            "too_long", target, {"length": n, "max": max_chars}
        )


def _tokenize_fr(text: str) -> list[str]:
    """Tokenizer FR : \\w+ Unicode + split sur apostrophes (elision)."""
    # Normaliser apostrophes typographiques puis splitter sur apostrophe
    # pour que "l'entreprise" -> ["l", "entreprise"] (capte le stopword "l").
    normalized = (text or "").replace("\u2019", "'").lower()
    # [^\W\d_]+ = mots Unicode sans chiffres ni underscore (meilleur que \w).
    return re.findall(r"[^\W\d_]+", normalized, flags=re.UNICODE)


def assert_language_fr(
    text: str,
    target: str,
    min_ratio: float = MIN_FR_RATIO,
) -> None:
    """AC3 : verifier la langue francaise via densite des stopwords FR.

    Implementation volontairement minimaliste (pas de langdetect obligatoire) pour
    rester deterministe. Retourne silencieusement sur textes trop courts
    (< MIN_TOKENS_FOR_LANG_CHECK) pour eviter les faux positifs.
    """
    tokens = _tokenize_fr(text)
    if len(tokens) < MIN_TOKENS_FOR_LANG_CHECK:
        return  # texte trop court pour detection fiable
    normalized = [_strip_accents(t) for t in tokens]
    fr_hits = sum(1 for t in normalized if t in _FR_STOPWORDS)
    ratio = fr_hits / len(tokens)
    if ratio < min_ratio:
        raise LLMGuardError(
            "language_drift",
            target,
            {"ratio": round(ratio, 3), "min": min_ratio, "detected_lang": "non-fr"},
        )


def assert_no_forbidden_vocabulary(
    text: str,
    target: str,
    vocab: tuple[str, ...] = FORBIDDEN_VOCAB,
) -> None:
    """AC2 : bloquer le vocabulaire interdit (insensible a la casse et aux accents).

    Les termes multi-mots acceptent n'importe quel whitespace (espaces multiples,
    NBSP, tabulations) entre les mots (ex. "valide  par", "valide\\u00a0par").
    """
    normalized_text = _strip_accents(_normalize_whitespace(text or "").lower())
    for term in vocab:
        # Defense en profondeur : normaliser aussi les termes meme si la
        # constante est deja ASCII (au cas ou un contributeur ajoute un accent).
        normalized_term = _strip_accents(term.lower())
        # Remplacer chaque espace par \s+ pour tolerer NBSP, tabs, espaces multiples.
        parts = [re.escape(p) for p in normalized_term.split(" ")]
        pattern = r"\b" + r"\s+".join(parts) + r"\b"
        if re.search(pattern, normalized_text):
            raise LLMGuardError(
                "forbidden_vocab", target, {"detected_term": term}
            )


def _closest_source(
    value: float, source_values: dict[str, float]
) -> tuple[str | None, float | None]:
    """Identifier la source la plus proche (nom, valeur) pour enrichir l'erreur."""
    best_name: str | None = None
    best_val: float | None = None
    best_dist = float("inf")
    for name, raw in source_values.items():
        if not isinstance(raw, (int, float)):
            continue
        dist = abs(float(raw) - value)
        if dist < best_dist:
            best_dist = dist
            best_name = name
            best_val = float(raw)
    return best_name, best_val


def _has_score_context(
    tokens_ascii: list[str], match_position_in_text: int, text_positions: list[int]
) -> bool:
    """Verifier qu'un mot-cle score apparait a +/- _SCORE_CONTEXT_WINDOW tokens."""
    # Trouver l'index du token le plus proche de la position du match
    match_token_idx = 0
    for i, pos in enumerate(text_positions):
        if pos > match_position_in_text:
            match_token_idx = max(0, i - 1)
            break
        match_token_idx = i
    start = max(0, match_token_idx - _SCORE_CONTEXT_WINDOW)
    end = min(len(tokens_ascii), match_token_idx + _SCORE_CONTEXT_WINDOW + 1)
    window = tokens_ascii[start:end]
    return any(tok in _SCORE_CONTEXT_KEYWORDS for tok in window)


def assert_numeric_coherence(
    text: str,
    source_values: dict[str, float],
    target: str,
    tolerance: float = 2.0,
) -> None:
    """AC1 : verifier que le texte ne mentionne pas de chiffres divergents des faits sources.

    Deux modes de detection (whitelist contextuelle, decision D1 review 9.6) :
    - Mode "strict" : tout "X/100", "X points", "X pts", "X/10" est verifie.
    - Mode "%" contextualise : un "X %" n'est verifie QUE si un mot-cle
      score/note/evaluation/pilier/global apparait a +/- 5 tokens.
      Evite les faux positifs sur "12 % du PIB", "progression de 15 %".

    Sources a zero ou None sont filtrees : leur presence fausserait la
    comparaison (tout score du texte apparaitrait drift vs 0).
    """
    if not text:
        return
    clean_text = _normalize_whitespace(text).lower()

    # Pattern strict : toujours verifie
    strict_pattern = r"\b(\d+(?:[.,]\d+)?)\s*(?:/100|\s+points?|\s+pts|/10)\b"
    # Pattern % : verifie seulement si contexte score a proximite
    pct_pattern = r"\b(\d+(?:[.,]\d+)?)\s*%"

    # Filtrer les sources : 0 et None sont ecartes (faux signal).
    source_floats = [
        float(v)
        for v in source_values.values()
        if isinstance(v, (int, float)) and v not in (0, 0.0)
    ]
    if not source_floats:
        return  # pas de source exploitable a comparer

    # Tokenisation pour la detection de contexte (mots ASCII uniquement)
    tokens_ascii: list[str] = []
    text_positions: list[int] = []
    ascii_text = _strip_accents(clean_text)
    for m in re.finditer(r"[^\W\d_]+", ascii_text, flags=re.UNICODE):
        tokens_ascii.append(m.group(0))
        text_positions.append(m.start())

    def _check(value: float) -> None:
        # Acceptable si proche (+/- tolerance) d'au moins une source
        if any(abs(value - s) <= tolerance for s in source_floats):
            return
        # Acceptable aussi si score /10 plutot que /100 (ex. "5/10" ~ 54/100)
        if any(abs(value * 10 - s) <= tolerance for s in source_floats):
            return
        closest_name, closest_val = _closest_source(value, source_values)
        raise LLMGuardError(
            "numeric_drift",
            target,
            {
                "detected_value": value,
                "expected": closest_val,
                "field": closest_name,
                "source_values": source_values,
            },
        )

    # 1. Pattern strict
    for m in re.finditer(strict_pattern, clean_text):
        value = float(m.group(1).replace(",", "."))
        _check(value)

    # 2. Pattern % avec whitelist contextuelle
    for m in re.finditer(pct_pattern, clean_text):
        if not _has_score_context(tokens_ascii, m.start(), text_positions):
            continue  # "12 % du PIB" : pas de contexte score -> ignore
        value = float(m.group(1).replace(",", "."))
        _check(value)


# --- Pydantic strict JSON guards (plan d'action) ---


class ActionPlanItemLLMSchema(BaseModel):
    """Schema strict pour UNE action generee par le LLM.

    Bornes et enums calibres sur le prompt `action_plan.py` + modele `ActionItem`.
    extra='forbid' : toute cle supplementaire (hallucination) fait echouer.

    Validation contextuelle de `due_date` via `ValidationInfo.context` :
    passer `context={"timeframe_months": <int>}` a `model_validate` pour que
    la borne max respecte l'horizon demande a l'utilisateur (decision D3).
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    title: str = Field(min_length=5, max_length=500)
    description: str | None = Field(default=None, max_length=4000)
    category: str = Field(description="Categorie normalisee")
    priority: str = Field(description="Priorite normalisee")
    due_date: str | None = Field(default=None, description="ISO 8601 YYYY-MM-DD")
    estimated_cost_xof: int | None = Field(default=None, ge=0, le=MAX_COST_XOF)
    estimated_benefit: str | None = Field(default=None, max_length=500)
    fund_id: str | None = Field(default=None, max_length=200)
    intermediary_id: str | None = Field(default=None, max_length=200)
    intermediary_name: str | None = Field(default=None, max_length=200)
    intermediary_address: str | None = Field(default=None, max_length=500)
    intermediary_phone: str | None = Field(default=None, max_length=50)
    intermediary_email: str | None = Field(default=None, max_length=200)

    @field_validator("category")
    @classmethod
    def _validate_category(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(
                f"category='{v}' not in {sorted(VALID_CATEGORIES)}"
            )
        return v

    @field_validator("priority")
    @classmethod
    def _validate_priority(cls, v: str) -> str:
        if v not in VALID_PRIORITIES:
            raise ValueError(
                f"priority='{v}' not in {sorted(VALID_PRIORITIES)}"
            )
        return v

    @field_validator("due_date")
    @classmethod
    def _validate_due_date(cls, v: str | None, info: ValidationInfo) -> str | None:
        if v is None:
            return v
        try:
            parsed = date.fromisoformat(v)
        except ValueError as e:
            raise ValueError(
                f"due_date='{v}' is not ISO 8601 (YYYY-MM-DD)"
            ) from e
        # Contexte : timeframe_months pilote la borne max (decision D3).
        # Tolerance 15 % pour absorber les legers depassements LLM.
        context = info.context or {}
        raw_tf = context.get("timeframe_months", MAX_TIMEFRAME_MONTHS)
        try:
            timeframe = int(raw_tf)
        except (TypeError, ValueError):
            timeframe = MAX_TIMEFRAME_MONTHS
        timeframe = max(1, min(timeframe, MAX_TIMEFRAME_MONTHS))
        tolerated_months = timeframe * (1 + DUE_DATE_TOLERANCE_RATIO)
        max_days = int(tolerated_months * 31)
        max_date = date.today() + timedelta(days=max_days)
        if parsed > max_date:
            raise ValueError(
                f"due_date='{v}' hors horizon ({timeframe} mois + 15 %) "
                f"max={max_date.isoformat()}"
            )
        return v


def validate_action_plan_schema(
    actions_raw: Any,
    target: str = "action_plan",
    *,
    timeframe_months: int | None = None,
) -> list[ActionPlanItemLLMSchema]:
    """AC5 : valider le schema Pydantic strict + AC6 : borner le nombre d'actions.

    Args:
        actions_raw: liste attendue (tout autre type leve schema_invalid).
        target: identifiant surface pour telemetrie.
        timeframe_months: horizon du plan courant (mois) pour borner les
            dates d'echeance. Si None, le plafond global MAX_TIMEFRAME_MONTHS
            est utilise.
    """
    if not isinstance(actions_raw, list):
        raise LLMGuardError(
            "schema_invalid",
            target,
            {"reason": "expected list", "got": type(actions_raw).__name__},
        )
    n = len(actions_raw)
    if n < MIN_ACTION_COUNT or n > MAX_ACTION_COUNT:
        raise LLMGuardError(
            "action_count_out_of_range",
            target,
            {"count": n, "expected_range": [MIN_ACTION_COUNT, MAX_ACTION_COUNT]},
        )

    context: dict[str, Any] = {}
    if timeframe_months is not None:
        context["timeframe_months"] = timeframe_months

    validated: list[ActionPlanItemLLMSchema] = []
    for idx, item in enumerate(actions_raw):
        if not isinstance(item, dict):
            raise LLMGuardError(
                "schema_invalid",
                target,
                {"index": idx, "errors": f"expected dict, got {type(item).__name__}"},
            )
        try:
            validated.append(
                ActionPlanItemLLMSchema.model_validate(item, context=context)
            )
        except Exception as e:
            raise LLMGuardError(
                "schema_invalid",
                target,
                {"index": idx, "errors": str(e)[:500]},
            ) from e

    return validated


# --- Telemetrie (AC9) ---


def log_guard_failure(
    target: str,
    guard: str,
    user_id: str,
    prompt_h: str,
    details: dict[str, Any],
    retry_attempted: bool,
    final_outcome: Literal["recovered", "failed"],
) -> None:
    """Log structure AC9 : consommable par Prometheus/Grafana (FR55 futur)."""
    logger.warning(
        "LLM guard failure target=%s guard=%s outcome=%s",
        target,
        guard,
        final_outcome,
        extra={
            "metric": "llm_guard_failure",
            "guard": guard,
            "target": target,
            "user_id": user_id,
            "prompt_hash": prompt_h,
            "retry_attempted": retry_attempted,
            "final_outcome": final_outcome,
            **{f"detail_{k}": v for k, v in details.items()},
        },
    )


# --- Orchestrateur (AC7, AC8) ---


async def run_guarded_llm_call(
    *,
    llm_call: Callable[[str], Awaitable[str]],
    guards: Callable[[str], None],
    base_prompt: str,
    hardened_prompt: str,
    target: str,
    user_id: str,
) -> str:
    """Executer un appel LLM avec garde-fous et retry unique.

    Contrat d'exceptions (decision D2 review 9.6) :

    - `LLMGuardError` (content validation) : attrapee ici. Retry unique avec
      `hardened_prompt`. Si le retry echoue aussi, transformee en
      `HTTPException(500)`. Tracee via `log_guard_failure`.
    - Erreurs transitoires infra (`httpx.TimeoutException`,
      `openai.RateLimitError`, 5xx provider) : PROPAGEES telles quelles vers
      l'appelant, qui est responsable d'un retry exterieur
      (`backend/app/core/common.py::with_retry`, NFR75). Ne PAS retry ici :
      double retry imbrique = 9 tentatives = desastre latence/cout.
    - Autres exceptions (bug, assertion) : propagees vers le handler global
      FastAPI.

    Separation claire : `with_retry` = infra resilience, `run_guarded_llm_call`
    = semantic validation. Ne pas melanger.

    Args:
        llm_call: coroutine `(prompt) -> raw_output` (async)
        guards: callable sync `(output) -> None` qui leve LLMGuardError si anomalie
        base_prompt: prompt initial
        hardened_prompt: prompt de retry (avec instruction additionnelle explicite)
        target: "executive_summary" | "action_plan"
        user_id: pour log structure AC9

    Returns:
        le contenu LLM valide (str brut)

    Raises:
        HTTPException(500): retry content-validation echoue definitivement
        Exception: toute autre erreur (infra, bug) propagee telle quelle
    """
    from fastapi import HTTPException

    ph_base = prompt_hash(base_prompt)
    try:
        output = await llm_call(base_prompt)
        guards(output)
        return output
    except LLMGuardError as err1:
        # Retry unique avec prompt renforce. Le log `recovered` est emis
        # APRES confirmation du succes du retry (review 9.6) pour ne pas
        # fausser les metriques Grafana avec des recover hypothetiques.
        try:
            output = await llm_call(hardened_prompt)
            guards(output)
        except LLMGuardError as err2:
            # Echec definitif : logger le 1er echec ET le retry rate.
            log_guard_failure(
                target=target,
                guard=err1.code,
                user_id=user_id,
                prompt_h=ph_base,
                details=err1.details,
                retry_attempted=True,
                final_outcome="failed",
            )
            log_guard_failure(
                target=target,
                guard=err2.code,
                user_id=user_id,
                prompt_h=prompt_hash(hardened_prompt),
                details=err2.details,
                retry_attempted=True,
                final_outcome="failed",
            )
            raise HTTPException(
                status_code=500,
                detail=f"Erreur generation {target} : guard LLM echoue apres retry",
            ) from err2
        # Succes du retry : logger la recuperation.
        log_guard_failure(
            target=target,
            guard=err1.code,
            user_id=user_id,
            prompt_h=ph_base,
            details=err1.details,
            retry_attempted=True,
            final_outcome="recovered",
        )
        return output
