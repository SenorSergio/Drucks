"""Request/response schemas for the API."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    template: str = Field(..., description="Vorlagen-ID, z. B. 'box'")
    params: dict[str, Any] = Field(default_factory=dict)
    material: str | None = "pla_nx2"
    printer: str | None = "mk3s"
    color: str | None = None            # German colour name, for the spec/order
    precise: bool = False               # run the real slicer instead of the heuristic
