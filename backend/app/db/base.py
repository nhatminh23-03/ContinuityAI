"""Declarative base for every persistence model."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared metadata holder.

    Persistence models are deliberately allowed to differ from the API DTOs in
    `app/schemas/` (docs/ARCHITECTURE.md section 15). Anything stored here that the
    contract does not carry — evidence aggregates, fired-rule reason codes, index
    modifier breakdowns — exists so a conclusion can be explained after the fact.
    """
