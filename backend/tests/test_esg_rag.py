"""Tests de la recherche RAG par critere ESG."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.esg.service import search_relevant_chunks


@pytest.fixture
def mock_db():
    """Session DB mockee."""
    db = AsyncMock()
    return db


@pytest.fixture
def fake_user_id():
    return uuid.uuid4()


@pytest.fixture
def fake_chunks():
    """Chunks simules avec contenu pertinent."""
    chunk1 = MagicMock()
    chunk1.content = "L'entreprise a mis en place un programme de tri des dechets depuis 2022."
    chunk1.document_id = uuid.uuid4()
    chunk1.chunk_index = 0

    chunk2 = MagicMock()
    chunk2.content = "Le rapport RSE mentionne une reduction de 15% des emissions carbone."
    chunk2.document_id = uuid.uuid4()
    chunk2.chunk_index = 3

    return [chunk1, chunk2]


class TestSearchRelevantChunks:
    """Tests de la recherche vectorielle par critere ESG."""

    @pytest.mark.asyncio
    async def test_returns_formatted_results(self, mock_db, fake_user_id, fake_chunks):
        """La recherche retourne des resultats formates avec content et source."""
        with patch(
            "app.modules.esg.service._search_chunks_by_query",
            new_callable=AsyncMock,
            return_value=fake_chunks,
        ):
            results = await search_relevant_chunks(
                db=mock_db,
                criteria_code="E1",
                user_id=fake_user_id,
                limit=5,
            )

        assert isinstance(results, list)
        assert len(results) == 2
        assert "content" in results[0]
        assert "document_id" in results[0]

    @pytest.mark.asyncio
    async def test_returns_empty_on_no_chunks(self, mock_db, fake_user_id):
        """Retourne une liste vide si aucun chunk pertinent."""
        with patch(
            "app.modules.esg.service._search_chunks_by_query",
            new_callable=AsyncMock,
            return_value=[],
        ):
            results = await search_relevant_chunks(
                db=mock_db,
                criteria_code="E1",
                user_id=fake_user_id,
            )

        assert results == []

    @pytest.mark.asyncio
    async def test_uses_criteria_label_as_query(self, mock_db, fake_user_id):
        """La recherche utilise le libelle du critere pour construire la requete."""
        with patch(
            "app.modules.esg.service._search_chunks_by_query",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_search:
            await search_relevant_chunks(
                db=mock_db,
                criteria_code="E1",
                user_id=fake_user_id,
            )

        call_args = mock_search.call_args
        query = call_args[1].get("query") or call_args[0][1]
        # La requete doit contenir des termes lies au critere E1 (Gestion des dechets)
        assert "dechets" in query.lower() or "gestion" in query.lower()

    @pytest.mark.asyncio
    async def test_handles_unknown_criteria_code(self, mock_db, fake_user_id):
        """Retourne une liste vide pour un code critere inconnu."""
        results = await search_relevant_chunks(
            db=mock_db,
            criteria_code="X99",
            user_id=fake_user_id,
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_respects_limit_parameter(self, mock_db, fake_user_id, fake_chunks):
        """Le parametre limit est respecte."""
        with patch(
            "app.modules.esg.service._search_chunks_by_query",
            new_callable=AsyncMock,
            return_value=fake_chunks[:1],
        ) as mock_search:
            await search_relevant_chunks(
                db=mock_db,
                criteria_code="E1",
                user_id=fake_user_id,
                limit=1,
            )

        call_args = mock_search.call_args
        # Verifier que limit est passe
        assert call_args[1].get("limit") == 1 or (len(call_args[0]) > 3 and call_args[0][3] == 1)

    @pytest.mark.asyncio
    async def test_handles_search_error_gracefully(self, mock_db, fake_user_id):
        """Retourne une liste vide en cas d'erreur de recherche."""
        with patch(
            "app.modules.esg.service._search_chunks_by_query",
            new_callable=AsyncMock,
            side_effect=Exception("Embedding API error"),
        ):
            results = await search_relevant_chunks(
                db=mock_db,
                criteria_code="E1",
                user_id=fake_user_id,
            )

        assert results == []
