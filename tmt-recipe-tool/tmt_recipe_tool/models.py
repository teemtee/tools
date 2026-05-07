from __future__ import annotations

from pydantic import BaseModel, Field


class Result(BaseModel, extra="allow"):
    name: str
    serial_number: int = Field(alias="serial-number")
    result: str
