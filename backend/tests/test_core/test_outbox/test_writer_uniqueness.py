"""Scan d'unicité du writer Outbox (INFO-10.10-2 absorbé Story 10.11).

La déclaration SQL `INSERT INTO domain_events` ne doit exister qu'au
sein de `app/core/outbox/writer.py`. Les autres modules (handlers,
services métier, migrations) doivent passer par `write_domain_event(...)`
(règle 10.5 « pas de duplication »).

Le modèle ORM `app/models/domain_event.py` contient la définition de la
table et peut mentionner `domain_events` dans les métadonnées SQLAlchemy
(chaînes `__tablename__ = "domain_events"`) — il est donc explicitement
exclu du scan.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

BACKEND_ROOT = Path(__file__).resolve().parents[3]
BACKEND_APP = BACKEND_ROOT / "app"
BACKEND_ALEMBIC = BACKEND_ROOT / "alembic" / "versions"
BACKEND_SCRIPTS = BACKEND_ROOT / "scripts"

WRITER_PATH = BACKEND_APP / "core" / "outbox" / "writer.py"
MODEL_PATH = BACKEND_APP / "models" / "domain_event.py"

_INSERT_PATTERN = re.compile(r"\bINSERT\s+INTO\s+domain_events\b", re.IGNORECASE)

# LOW-10.11-21 : scope élargi à `alembic/versions/` et `backend/scripts/` —
# un backfill SQL one-shot dans une migration ou un script ops ne doit pas
# échapper au garde-fou.
_SCAN_ROOTS: tuple[Path, ...] = (
    BACKEND_APP,
    BACKEND_ALEMBIC,
    BACKEND_SCRIPTS,
)


def test_writer_is_single_source_of_truth_for_insert_into_domain_events() -> None:
    """Le littéral `INSERT INTO domain_events` doit vivre uniquement dans
    `writer.py`, en excluant explicitement le modèle ORM `models/domain_event.py`
    (exclusion documentée — INFO-10.10-2).

    LOW-10.11-21 : scanne aussi `alembic/versions/` + `backend/scripts/`.
    """

    hits: list[Path] = []
    for root in _SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            if path == MODEL_PATH:
                # Exclusion explicite : le modèle ORM peut contenir
                # "domain_events" via __tablename__ ou metadata.
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if _INSERT_PATTERN.search(content):
                hits.append(path)

    # Strictement 0 ou 1 hit, et s'il y en a 1 il DOIT être writer.py.
    # Aujourd'hui le writer utilise l'ORM (`session.add(event)`) et non
    # un SQL littéral ; le test garantit que si quelqu'un introduit un
    # `INSERT INTO domain_events` brut, il le fait nécessairement dans
    # writer.py — jamais ailleurs.
    assert hits == [] or hits == [WRITER_PATH], (
        f"INSERT INTO domain_events doit rester confiné à writer.py ; "
        f"hit(s) trouvé(s) : {hits}"
    )
