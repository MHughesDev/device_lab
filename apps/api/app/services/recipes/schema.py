"""Recipe YAML schema using Pydantic."""
from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field


class RecipeInput(BaseModel):
    type: Literal["string", "integer", "boolean", "secret_ref"] = "string"
    required: bool = False
    default: Any = None
    ref: str | None = None   # for secret_ref type


class RecipeStep(BaseModel):
    id: str
    action: str
    params: dict[str, Any] = Field(default_factory=dict)
    dangerous: bool = False
    description: str = ""


class RecipeArtifact(BaseModel):
    capture_screenshot: str | None = None   # "after_each_step" | "on_failure"
    capture_logs: str | None = None         # "on_failure" | "always"


class RecipeCleanupStep(BaseModel):
    action: str
    params: dict[str, Any] = Field(default_factory=dict)


class RecipeSchema(BaseModel):
    name: str
    version: int = 1
    families: list[str] = Field(default_factory=list)
    min_devicelab_version: str = "0.1.0"
    inputs: dict[str, RecipeInput] = Field(default_factory=dict)
    steps: list[RecipeStep] = Field(default_factory=list)
    artifacts: list[RecipeArtifact] = Field(default_factory=list)
    cleanup: list[RecipeCleanupStep] = Field(default_factory=list)
