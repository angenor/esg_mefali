"""Tests unitaires du text splitting et stockage embeddings (T043)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_split_text_into_chunks():
    """Le text splitter doit decouper le texte en segments avec overlap."""
    from app.modules.documents.service import _split_text

    text = "Premier paragraphe. " * 100 + "\n\n" + "Deuxieme paragraphe. " * 100
    chunks = _split_text(text)

    assert len(chunks) > 1
    # Chaque chunk doit etre non vide
    for chunk in chunks:
        assert len(chunk) > 0
    # Les chunks doivent etre plus petits que le texte original
    assert all(len(c) <= 1200 for c in chunks)  # chunk_size + marge


@pytest.mark.asyncio
async def test_split_short_text():
    """Un texte court ne doit produire qu'un seul chunk."""
    from app.modules.documents.service import _split_text

    text = "Texte court de test."
    chunks = _split_text(text)

    assert len(chunks) == 1
    assert chunks[0] == text


@pytest.mark.asyncio
async def test_store_embeddings_creates_chunks():
    """store_embeddings doit creer des DocumentChunk en BDD."""
    from app.modules.documents.service import store_embeddings

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()

    document_id = uuid.uuid4()
    text = "Paragraphe de test. " * 100

    # Mock l'API d'embedding
    with patch(
        "app.modules.documents.service._get_embeddings",
        new_callable=AsyncMock,
        return_value=[[0.1] * 1536] * 5,
    ):
        chunks_count = await store_embeddings(mock_db, document_id, text)

    assert chunks_count > 0
    assert mock_db.add.called


@pytest.mark.asyncio
async def test_search_similar_chunks():
    """search_similar_chunks doit retourner des resultats."""
    from app.modules.documents.service import search_similar_chunks

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Mock l'API d'embedding pour la query
    with patch(
        "app.modules.documents.service._get_embeddings",
        new_callable=AsyncMock,
        return_value=[[0.1] * 1536],
    ):
        results = await search_similar_chunks(
            mock_db, uuid.uuid4(), "question test",
        )

    assert isinstance(results, list)
