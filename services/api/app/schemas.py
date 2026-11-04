from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InventoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    part_number: str | None = Field(default=None, max_length=100)
    category: str = Field(default="uncategorized", min_length=1, max_length=80)
    quantity: int = Field(default=1, ge=0, le=1_000_000)
    condition: str = Field(default="unknown", min_length=1, max_length=40)
    storage_bin: str | None = Field(default=None, max_length=80)
    notes: str = Field(default="", max_length=10_000)


class InventoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=160)
    part_number: str | None = Field(default=None, max_length=100)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    quantity: int | None = Field(default=None, ge=0, le=1_000_000)
    condition: str | None = Field(default=None, min_length=1, max_length=40)
    storage_bin: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=10_000)


class InventoryRead(InventoryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=10_000)
    status: Literal["idea", "in_progress", "done"] = "idea"


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=10_000)
    status: Literal["idea", "in_progress", "done"] | None = None


class ProjectRead(ProjectCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
