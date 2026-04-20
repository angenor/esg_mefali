"""Helpers partagés pour tous les tools LangChain des nœuds LangGraph.

Ce module fournit trois primitives consommées par les 9 modules métier
(`profiling_tools`, `esg_tools`, `carbon_tools`, `financing_tools`,
`credit_tools`, `application_tools`, `document_tools`, `action_plan_tools`,
`chat_tools`) ainsi que par `interactive_tools` et `guided_tour_tools` :

- `get_db_and_user(config)` — extraction de la session DB + user_id depuis RunnableConfig.
- `log_tool_call(...)` — journalisation structurée dans `tool_call_logs` (FR-022).
- `with_retry(func, ...)` — wrapping avec retry exponentiel + circuit breaker (FR-021, NFR75).

Voir `backend/app/graph/tools/README.md` pour le guide d'utilisation.
"""

import asyncio
import contextlib
import json
import logging
import time
import uuid
from collections.abc import Callable
from functools import wraps
from typing import Any

from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def get_db_and_user(config: RunnableConfig) -> tuple[AsyncSession, uuid.UUID]:
    """Extraire la session DB et le user_id depuis le RunnableConfig.

    Chaque tool reçoit un RunnableConfig injecté par le handler SSE.
    Les valeurs sont stockées dans config["configurable"].

    Raises:
        ValueError: Si user_id ou db manquent dans la configuration.
    """
    configurable = (config or {}).get("configurable", {})

    db = configurable.get("db")
    if db is None:
        raise ValueError("Session DB manquante dans RunnableConfig['configurable']['db']")

    user_id_raw = configurable.get("user_id")
    if user_id_raw is None:
        raise ValueError("user_id manquant dans RunnableConfig['configurable']['user_id']")

    if isinstance(user_id_raw, str):
        user_id = uuid.UUID(user_id_raw)
    else:
        user_id = user_id_raw

    return db, user_id


async def log_tool_call(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID | None,
    node_name: str,
    tool_name: str,
    tool_args: dict[str, Any],
    tool_result: dict[str, Any] | None = None,
    duration_ms: int | None = None,
    status: str = "success",
    error_message: str | None = None,
    retry_count: int = 0,
) -> None:
    """Journaliser un appel de tool dans la table tool_call_logs.

    Appelé après chaque exécution de tool (succès, erreur, retry).
    """
    from app.models.tool_call_log import ToolCallLog

    log_entry = ToolCallLog(
        user_id=user_id,
        conversation_id=conversation_id,
        node_name=node_name,
        tool_name=tool_name,
        tool_args=tool_args,
        tool_result=tool_result,
        duration_ms=duration_ms,
        status=status,
        error_message=error_message,
        retry_count=retry_count,
    )
    db.add(log_entry)
    await db.flush()


# ---------------------------------------------------------------------------
# Classification des exceptions transientes (AC2, AC3)
# ---------------------------------------------------------------------------


_LLM_5XX_STATUS_CODES = frozenset({500, 502, 503, 504})
_TRANSIENT_HTTP_STATUS = frozenset({429, 500, 502, 503, 504})
_LLM_5XX_CLASS_NAMES = frozenset({"APIError", "InternalServerError", "APIStatusError"})


def is_transient_error(exc: BaseException) -> bool:
    """Classifier une exception comme transiente (retry possible) ou définitive.

    Transient (retry OK) :
        - asyncio.TimeoutError / builtin TimeoutError
        - ConnectionError (et sous-classes)
        - httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError
        - asyncpg.exceptions.PostgresConnectionError, CannotConnectNowError
        - Toute exception portant un attribut status_code ∈ {429, 500, 502, 503, 504}

    Non transient (pas de retry) :
        - pydantic.ValidationError, ValueError, IntegrityError, PermissionError, KeyError
        - Tout reste inconnu → False (défensif, on évite de retry trop agressivement).
    """
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True

    try:
        import httpx

        if isinstance(
            exc,
            (
                httpx.ConnectError,
                httpx.ReadTimeout,
                httpx.ConnectTimeout,
                httpx.RemoteProtocolError,
            ),
        ):
            return True
    except ImportError:  # pragma: no cover
        pass

    try:
        from asyncpg import exceptions as pgx

        if isinstance(
            exc,
            (pgx.PostgresConnectionError, pgx.CannotConnectNowError),
        ):
            return True
    except ImportError:  # pragma: no cover
        pass

    status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int) and status_code in _TRANSIENT_HTTP_STATUS:
        return True

    response = getattr(exc, "response", None)
    if response is not None:
        rsc = getattr(response, "status_code", None)
        if isinstance(rsc, int) and rsc in _TRANSIENT_HTTP_STATUS:
            return True

    return False


def _is_llm_5xx_error(exc: BaseException) -> bool:
    """Détecter si une exception transiente est un 5xx d'origine LLM (AC5)."""
    status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int) and status_code in _LLM_5XX_STATUS_CODES:
        return True

    response = getattr(exc, "response", None)
    if response is not None:
        rsc = getattr(response, "status_code", None)
        if isinstance(rsc, int) and rsc in _LLM_5XX_STATUS_CODES:
            return True

    return type(exc).__name__ in _LLM_5XX_CLASS_NAMES


# ---------------------------------------------------------------------------
# Circuit breaker module-level (AC5, NFR75)
# ---------------------------------------------------------------------------


class _CircuitBreakerState:
    """État d'un circuit breaker par clé ``(tool_name, node_name)``.

    Seuil 10 erreurs 5xx consécutives → ouverture pendant 60 s, puis bascule
    half-open implicite : `should_block` retourne False après expiration et
    la prochaine tentative reprend le cycle normal. Sur succès, reset total.
    """

    THRESHOLD = 10
    WINDOW_S = 60.0

    def __init__(self) -> None:
        self._counts: dict[tuple[str, str], int] = {}
        self._opened_at: dict[tuple[str, str], float] = {}
        self._lock = asyncio.Lock()

    def _now(self) -> float:
        """Indirection testable pour ``time.monotonic``."""
        return time.monotonic()

    async def should_block(self, tool_name: str, node_name: str) -> bool:
        """True si le breaker est ouvert et la fenêtre 60 s pas expirée."""
        key = (tool_name, node_name)
        async with self._lock:
            opened = self._opened_at.get(key)
            if opened is None:
                return False
            if self._now() - opened < self.WINDOW_S:
                return True
            self._opened_at.pop(key, None)
            self._counts.pop(key, None)
            return False

    async def record_failure(
        self,
        tool_name: str,
        node_name: str,
        *,
        is_llm_5xx: bool,
    ) -> None:
        """Incrémente le compteur si échec LLM 5xx ; ouvre le breaker au seuil."""
        if not is_llm_5xx:
            return
        key = (tool_name, node_name)
        async with self._lock:
            count = self._counts.get(key, 0) + 1
            self._counts[key] = count
            if count >= self.THRESHOLD and key not in self._opened_at:
                self._opened_at[key] = self._now()
                logger.error(
                    "Circuit breaker ouvert pour tool=%s node=%s (%d echecs 5xx)",
                    tool_name,
                    node_name,
                    self.THRESHOLD,
                    extra={
                        "metric": "circuit_breaker_open",
                        "tool_name": tool_name,
                        "node_name": node_name,
                        "consecutive_failures": self.THRESHOLD,
                    },
                )

    async def record_success(self, tool_name: str, node_name: str) -> None:
        """Reset du compteur et de l'état ouvert sur succès final."""
        key = (tool_name, node_name)
        async with self._lock:
            self._counts.pop(key, None)
            self._opened_at.pop(key, None)


_breaker = _CircuitBreakerState()


def _reset_breaker_state_for_tests() -> None:
    """Reset synchrone du breaker pour les fixtures pytest."""
    _breaker._counts.clear()
    _breaker._opened_at.clear()


# ---------------------------------------------------------------------------
# Extraction filtrée des arguments pour journalisation
# ---------------------------------------------------------------------------


_TOOL_ARGS_BLACKLIST = frozenset({"config", "db", "self"})
_STRING_ARG_MAX_LEN = 200


def _extract_tool_args(args: tuple, kwargs: dict) -> dict[str, Any]:
    """Extraire les arguments métier du tool pour la journalisation.

    Filtre les arguments techniques (``config``, ``db``, ``self``) et tronque
    les strings à 200 caractères pour éviter le gonflement des logs. Ajoute
    la dimension observabilité ``_input_size_bytes`` (AC4).
    """
    filtered: dict[str, Any] = {}
    for key, value in kwargs.items():
        if key in _TOOL_ARGS_BLACKLIST:
            continue
        if isinstance(value, str) and len(value) > _STRING_ARG_MAX_LEN:
            filtered[key] = value[:_STRING_ARG_MAX_LEN] + "..."
        else:
            filtered[key] = value

    try:
        filtered["_input_size_bytes"] = len(json.dumps(filtered, default=str))
    except (TypeError, ValueError):  # pragma: no cover
        filtered["_input_size_bytes"] = 0

    return filtered


def _build_tool_result(result: Any) -> dict[str, Any]:
    """Construire le payload ``tool_result`` journalisé (AC4)."""
    summary = str(result)[:500]
    try:
        output_size = len(str(result))
    except Exception:  # pragma: no cover
        output_size = 0
    return {"summary": summary, "_output_size_bytes": output_size}


# ---------------------------------------------------------------------------
# with_retry — wrapping retry + journalisation + circuit breaker (AC1-AC5)
# ---------------------------------------------------------------------------


_DEFAULT_BACKOFF: tuple[float, ...] = (1.0, 3.0, 9.0)


def _extract_config(args: tuple, kwargs: dict) -> RunnableConfig | None:
    """Extraire le RunnableConfig depuis les arguments (kwargs ou positionnel)."""
    cfg = kwargs.get("config")
    if cfg is not None:
        return cfg
    if args and isinstance(args[-1], dict) and "configurable" in args[-1]:
        return args[-1]
    return None


async def _safe_log(
    config: RunnableConfig | None,
    *,
    node_name: str,
    tool_name: str,
    tool_args: dict[str, Any],
    tool_result: dict[str, Any] | None,
    duration_ms: int | None,
    status: str,
    error_message: str | None,
    retry_count: int,
) -> None:
    """Journaliser sans jamais crasher (best-effort, rgle 4 du pattern)."""
    if config is None:
        return
    try:
        db, user_id = get_db_and_user(config)
        configurable = config.get("configurable", {})
        await log_tool_call(
            db,
            user_id=user_id,
            conversation_id=configurable.get("conversation_id"),
            node_name=node_name,
            tool_name=tool_name,
            tool_args=tool_args,
            tool_result=tool_result,
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
            retry_count=retry_count,
        )
    except Exception:
        # H2 (post-review 9.7) : warning au lieu de debug pour ne pas manquer
        # les pertes silencieuses de logs quand la session est en
        # PendingRollbackError (tool qui a crash en cours de transaction).
        logger.warning(
            "Echec journalisation tool %s (tool_call_log perdu, best-effort)",
            tool_name,
            exc_info=True,
            extra={"metric": "tool_log_persistence_failure", "tool_name": tool_name},
        )


def _apply_sentinel(target: Any) -> None:
    """Poser l'attribut sentinelle ``_is_wrapped_by_with_retry=True`` (AC1)."""
    try:
        object.__setattr__(target, "_is_wrapped_by_with_retry", True)
    except Exception:  # pragma: no cover
        logger.debug("Impossible de poser la sentinelle sur %r", target)


def with_retry(
    func: Any,
    *,
    max_retries: int = 2,
    node_name: str = "",
    backoff: list[float] | tuple[float, ...] | None = None,
) -> Any:
    """Wrapper resilience : retry exponentiel + journalisation + circuit breaker.

    Étend la primitive originale (spec 012 FR-021) pour converger avec NFR75
    (3 tentatives, backoff [1,3,9] s, breaker 60 s / 10 erreurs 5xx).

    Args:
        func: Fonction async ou LangChain ``BaseTool`` à wrapper. Si ``BaseTool``,
            la coroutine interne est remplacée en place (préserve l'interface
            LangChain consommée par ``ToolNode``).
        max_retries: Nombre de retries après l'essai initial (défaut 2 → 3 tentatives).
        node_name: Nom du nœud LangGraph (journalisation + clé du breaker).
        backoff: Liste des délais en secondes (défaut ``[1, 3, 9]``).
            Doit contenir au moins ``max_retries`` éléments.

    Behavior:
        - Non transient (ValueError, ValidationError, IntegrityError, KeyError,
          PermissionError…) → pas de retry, journalisation unique ``status="error"``,
          propagation sous forme ``"Erreur : {e}"`` (AC3).
        - Transient (TimeoutError, ConnectionError, httpx/asyncpg, status_code ∈
          {429, 500, 502, 503, 504}) → retry avec ``asyncio.sleep(backoff[attempt-1])``
          avant chaque tentative N>0. Dernier échec logué ``status="error"`` (AC2).
        - Succès après retry → ``status="retry_success"`` + log INFO structuré
          ``extra={"metric": "tool_retry_recovered", ...}`` (AC9).
        - Breaker 5xx → après 10 échecs 5xx consécutifs sur la clé
          ``(tool_name, node_name)``, ouverture pendant 60 s ; durant cette fenêtre
          toute invocation retourne ``"Erreur : circuit breaker ouvert"`` sans
          appeler ``func`` (ligne ``status="circuit_open"`` émise) (AC5).
    """
    backoff_seq: tuple[float, ...] = (
        tuple(backoff) if backoff is not None else _DEFAULT_BACKOFF
    )
    if len(backoff_seq) < max_retries:
        raise ValueError(
            f"backoff doit contenir au moins {max_retries} éléments, "
            f"reçu {len(backoff_seq)}."
        )

    tool_obj: Any = None
    original_coroutine: Callable | None = None
    try:
        from langchain_core.tools import BaseTool

        if isinstance(func, BaseTool):
            tool_obj = func
            original_coroutine = func.coroutine
            if original_coroutine is None:
                raise ValueError(
                    f"BaseTool {func.name} n'a pas de coroutine async — "
                    "with_retry nécessite un tool async."
                )
    except ImportError:  # pragma: no cover
        pass

    target_fn: Callable = original_coroutine if original_coroutine is not None else func
    tool_display_name = (
        tool_obj.name if tool_obj is not None else getattr(func, "__name__", "unknown_tool")
    )

    @wraps(target_fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        config = _extract_config(args, kwargs)
        tool_args_snapshot = _extract_tool_args(args, kwargs)

        # Fallback dynamique : si node_name statique vide (tool partagé tel qu'
        # INTERACTIVE_TOOLS / GUIDED_TOUR_TOOLS), utiliser active_module depuis
        # le RunnableConfig. Évite d'étiqueter les logs avec un faux node_name.
        effective_node_name = node_name
        if not effective_node_name and config is not None:
            configurable = config.get("configurable", {})
            effective_node_name = (
                configurable.get("active_module")
                or (configurable.get("active_module_data") or {}).get("module")
                or "chat"
            )

        if await _breaker.should_block(tool_display_name, effective_node_name):
            logger.warning(
                "Invocation bloquee par circuit breaker : tool=%s node=%s",
                tool_display_name,
                effective_node_name,
                extra={
                    "metric": "circuit_breaker_blocked",
                    "tool_name": tool_display_name,
                    "node_name": effective_node_name,
                },
            )
            await _safe_log(
                config,
                node_name=effective_node_name,
                tool_name=tool_display_name,
                tool_args=tool_args_snapshot,
                tool_result=None,
                duration_ms=0,
                status="circuit_open",
                error_message="circuit breaker ouvert",
                retry_count=0,
            )
            return "Erreur : circuit breaker ouvert"

        last_exc: BaseException | None = None
        for attempt in range(max_retries + 1):
            if attempt > 0:
                await asyncio.sleep(backoff_seq[attempt - 1])

            start = time.monotonic()
            try:
                result = await target_fn(*args, **kwargs)
                duration_ms = int((time.monotonic() - start) * 1000)
                await _safe_log(
                    config,
                    node_name=effective_node_name,
                    tool_name=tool_display_name,
                    tool_args=tool_args_snapshot,
                    tool_result=_build_tool_result(result),
                    duration_ms=duration_ms,
                    status="retry_success" if attempt > 0 else "success",
                    error_message=None,
                    retry_count=attempt,
                )
                await _breaker.record_success(tool_display_name, effective_node_name)

                if attempt > 0:
                    logger.info(
                        "Tool %s/%s récupéré après %d tentative(s)",
                        tool_display_name,
                        effective_node_name,
                        attempt + 1,
                        extra={
                            "metric": "tool_retry_recovered",
                            "tool_name": tool_display_name,
                            "node_name": effective_node_name,
                            "attempts": attempt + 1,
                        },
                    )
                return result

            except Exception as exc:
                duration_ms = int((time.monotonic() - start) * 1000)
                last_exc = exc
                is_transient = is_transient_error(exc)

                with contextlib.suppress(Exception):
                    await _breaker.record_failure(
                        tool_display_name,
                        effective_node_name,
                        is_llm_5xx=_is_llm_5xx_error(exc),
                    )

                if not is_transient:
                    await _safe_log(
                        config,
                        node_name=effective_node_name,
                        tool_name=tool_display_name,
                        tool_args=tool_args_snapshot,
                        tool_result=None,
                        duration_ms=duration_ms,
                        status="error",
                        error_message=str(exc)[:500],
                        retry_count=attempt,
                    )
                    logger.info(
                        "Tool %s/%s échec non-transient : %s",
                        tool_display_name,
                        effective_node_name,
                        type(exc).__name__,
                    )
                    return f"Erreur : {exc}"

                if attempt < max_retries:
                    logger.warning(
                        "Tool %s/%s échec transient (tentative %d/%d) : %s, retry...",
                        tool_display_name,
                        effective_node_name,
                        attempt + 1,
                        max_retries + 1,
                        type(exc).__name__,
                    )
                    await _safe_log(
                        config,
                        node_name=effective_node_name,
                        tool_name=tool_display_name,
                        tool_args=tool_args_snapshot,
                        tool_result=None,
                        duration_ms=duration_ms,
                        status="error",
                        error_message=str(exc)[:500],
                        retry_count=attempt,
                    )
                    continue

                await _safe_log(
                    config,
                    node_name=effective_node_name,
                    tool_name=tool_display_name,
                    tool_args=tool_args_snapshot,
                    tool_result=None,
                    duration_ms=duration_ms,
                    status="error",
                    error_message=str(exc)[:500],
                    retry_count=attempt,
                )

        return f"Erreur : {last_exc}"

    # Cas 1 : wrapping d'un BaseTool → muter la coroutine et retourner le tool
    if tool_obj is not None:
        try:
            object.__setattr__(tool_obj, "coroutine", wrapper)
        except Exception as exc:  # pragma: no cover
            raise ValueError(
                f"Impossible de rebinder la coroutine sur {tool_display_name} : {exc}"
            ) from exc
        _apply_sentinel(tool_obj)
        return tool_obj

    # Cas 2 : wrapping d'une fonction async plain → retourner le wrapper
    _apply_sentinel(wrapper)
    return wrapper
