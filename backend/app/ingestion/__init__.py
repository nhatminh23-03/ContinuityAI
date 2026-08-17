"""Ingestion: external artifacts in, normalised artifacts and evidence out."""

from .adapters import (
    artifact_id_for,
    load_declared_ownership,
    load_normalised_github_export,
    load_public_github_corpus,
    load_synthetic_corpus,
    normalise_reference,
)
from .pipeline import IngestionReport, ingest

__all__ = [
    "IngestionReport",
    "artifact_id_for",
    "ingest",
    "load_declared_ownership",
    "load_normalised_github_export",
    "load_public_github_corpus",
    "load_synthetic_corpus",
    "normalise_reference",
]
