"""Tests Story 10.13 — script rembed_voyage_corpus.py (AC5)."""

from __future__ import annotations

import argparse
import uuid

import pytest

from scripts import rembed_voyage_corpus as rembed


def test_parse_args_defaults():
    args = rembed._parse_args([])
    assert args.batch_size == 100
    assert args.limit is None
    assert args.resume_from is None
    assert args.dry_run is False


def test_parse_args_all_flags():
    sample_id = str(uuid.uuid4())
    args = rembed._parse_args(
        ["--batch-size", "50", "--limit", "10", "--resume-from", sample_id, "--dry-run"]
    )
    assert args.batch_size == 50
    assert args.limit == 10
    assert args.resume_from == sample_id
    assert args.dry_run is True


def test_validate_args_batch_size_out_of_bounds_min():
    args = argparse.Namespace(
        batch_size=0, limit=None, resume_from=None, dry_run=False
    )
    with pytest.raises(SystemExit, match="batch-size"):
        rembed._validate_args(args)


def test_validate_args_batch_size_out_of_bounds_max():
    args = argparse.Namespace(
        batch_size=10_000, limit=None, resume_from=None, dry_run=False
    )
    with pytest.raises(SystemExit, match="batch-size"):
        rembed._validate_args(args)


def test_validate_args_limit_zero_rejected():
    args = argparse.Namespace(
        batch_size=100, limit=0, resume_from=None, dry_run=False
    )
    with pytest.raises(SystemExit, match="limit"):
        rembed._validate_args(args)


def test_validate_args_invalid_resume_uuid():
    args = argparse.Namespace(
        batch_size=100, limit=None, resume_from="not-a-uuid", dry_run=False
    )
    with pytest.raises(SystemExit, match="resume-from"):
        rembed._validate_args(args)


def test_validate_args_valid():
    args = argparse.Namespace(
        batch_size=100,
        limit=50,
        resume_from=str(uuid.uuid4()),
        dry_run=False,
    )
    # Ne doit pas lever.
    rembed._validate_args(args)


def test_constants_are_coherent():
    """La default est dans les bornes."""
    assert rembed.BATCH_SIZE_MIN <= rembed.DEFAULT_BATCH_SIZE <= rembed.BATCH_SIZE_MAX


def test_emit_progress_serializes_event(caplog):
    """Le log JSON structuré inclut l'événement + metric."""
    import logging

    with caplog.at_level(logging.INFO, logger="rembed_voyage_corpus"):
        rembed._emit_progress({"event": "embedding_batch_progress", "processed": 3})
    joined = "\n".join(r.message for r in caplog.records)
    assert "embedding_batch_progress" in joined
    assert "\"processed\": 3" in joined
