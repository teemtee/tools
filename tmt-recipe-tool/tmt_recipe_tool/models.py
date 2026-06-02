from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Result(BaseModel, extra="allow"):
    name: str
    serial_number: int = Field(alias="serial-number")
    result: str


class ReportPortalPhase(BaseModel, extra="allow"):
    name: str
    how: Literal["reportportal"]
    url: str
    project: str
    token: str
    launch_uuid: Optional[str] = Field(None, alias="launch-uuid")
    launch_url: Optional[str] = Field(None, alias="launch-url")
    ssl_verify: bool = Field(True, alias="ssl-verify")
    test_uuids: dict[int, dict[Optional[str], str]] = Field(default_factory=dict, alias="test-uuids")
    api_version: str = Field(alias="api-version")


class ReportPortalResult(BaseModel, extra="allow"):
    uuid: str
    status: str
