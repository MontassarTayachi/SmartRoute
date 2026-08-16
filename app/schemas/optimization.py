from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class RegionSettingsUpdateRequest(BaseModel):
    n_clusters: int | None = Field(default=None, ge=1, description="Nombre de regions à créer")
    mode: Literal["fixe", "auto"] = Field(default="fixe", description="Mode de calcul des regions")

    @field_validator("n_clusters", mode="before")
    @classmethod
    def normalize_n_clusters(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return value


class AlgorithmActivationRequest(BaseModel):
    algorithm_name: str = Field(..., min_length=1, description="Nom de l'algorithme à activer")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Paramètres spécifiques à l'algorithme")


class RouteStrategyActivationRequest(BaseModel):
    strategy_name: str = Field(..., min_length=1, description="Nom de la stratégie de tournée à activer")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Paramètres spécifiques à la stratégie (ex. time_limit_seconds)")