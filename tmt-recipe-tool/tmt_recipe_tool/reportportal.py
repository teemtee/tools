from __future__ import annotations

from collections.abc import Iterable
from typing import Union, cast

import requests
from tmt.recipe import _RecipePlan, _RecipeTest
from tmt.steps import _RawStepData
from tmt.utils import retry_session

from tmt_recipe_tool.filtering import matches_filter
from tmt_recipe_tool.models import ReportPortalPhase, ReportPortalResult
from tmt_recipe_tool.utils import create_tmt_logger

STATUS_FORCELIST = (
    429,  # Too Many Requests
    500,  # Internal Server Error
    502,  # Bad Gateway
    503,  # Service Unavailable
    504,  # Gateway Timeout
)


class ReportPortalError(Exception):
    """Raised when fetching results from ReportPortal fails."""


def _handle_response(response: requests.Response) -> None:
    """
    Check the endpoint response and raise an exception if needed
    """
    if not response.ok:
        raise ReportPortalError(
            f"Received non-ok status code {response.status_code} "
            f"from ReportPortal: {response.text}"
        )


def get_rp_phases(plan: _RecipePlan) -> list[ReportPortalPhase]:
    """Get the ReportPortal phases from the plan"""
    return [
        ReportPortalPhase.model_validate(phase)
        for phase in plan.report.phases
        if phase.get("how", None) == "reportportal"
    ]


def edit_rp_phases(phases: Iterable[_RawStepData]) -> list[_RawStepData]:
    """Edit the ReportPortal phases so they don't overwrite previous launches"""
    filtered_phases = []
    for phase in phases:
        if phase.get("how", None) == "reportportal":
            phase.pop("launch-url", None)  # type: ignore[typeddict-item]
            phase.pop("launch-uuid", None)  # type: ignore[typeddict-item]
            phase.pop("suite-uuid", None)  # type: ignore[typeddict-item]
            phase.pop("test-uuids", None)  # type: ignore[typeddict-item]
        filtered_phases.append(phase)
    return filtered_phases


def _get_launch_id(
    session: requests.Session,
    headers: dict[str, str],
    api_version: str,
    rp_phase: ReportPortalPhase,
) -> int:
    """Resolve the numeric launch ID from launch-uuid"""
    if not rp_phase.launch_uuid:
        raise ReportPortalError(f"ReportPortal phase '{rp_phase.name}' has missing 'launch-uuid'.")
    base_url = rp_phase.url.rstrip("/")
    url = f"{base_url}/api/{api_version}/{rp_phase.project}/launch/uuid/{rp_phase.launch_uuid}"

    response = session.get(url, headers=headers)
    _handle_response(response)
    return int(response.json()["id"])


def _fetch_rp_results(
    session: requests.Session,
    headers: dict[str, str],
    api_version: str,
    rp_phase: ReportPortalPhase,
    launch_id: int,
) -> dict[str, ReportPortalResult]:
    """Fetch the ReportPortal results for a given launch ID"""
    base_url = rp_phase.url.rstrip("/")
    results: list[ReportPortalResult] = []
    page = 1
    while True:
        response = session.get(
            f"{base_url}/api/{api_version}/{rp_phase.project}/item",
            headers=headers,
            params=cast(
                dict[str, Union[str, int]],
                {
                    "filter.eq.launchId": launch_id,
                    "filter.eq.type": "STEP",
                    "page.size": 100,
                    "page.page": page,
                },
            ),
        )
        _handle_response(response)
        data = response.json()
        results += [
            ReportPortalResult.model_validate(result) for result in data.get("content", [])
        ]
        page_info = data.get("page", {})
        if page >= page_info.get("totalPages", 1):
            break
        page += 1
    return {result.uuid: result for result in results}


def filter_tests_from_rp(
    tests: list[_RecipeTest],
    rp_phases: list[ReportPortalPhase],
    filter: str,  # noqa: A002
) -> Iterable[_RecipeTest]:
    """
    Yield tests whose ReportPortal result matches the fmf filter expression.
    """
    filtered_tests: dict[int, _RecipeTest] = {}

    for phase in rp_phases:
        with retry_session(
            status_forcelist=STATUS_FORCELIST,
            logger=create_tmt_logger(),
        ) as session:
            session.verify = phase.ssl_verify
            headers = {
                "Authorization": f"Bearer {phase.token}",
                "Accept": "*/*",
                "Content-Type": "application/json",
            }

            rp_results = _fetch_rp_results(
                session=session,
                headers=headers,
                api_version=phase.api_version,
                rp_phase=phase,
                launch_id=_get_launch_id(session, headers, phase.api_version, phase),
            )

        serial_number_to_uuids: dict[int, list[str]] = {
            serial: list(value.values()) for serial, value in phase.test_uuids.items()
        }

        for test in tests:
            # Test can have multiple results with the same serial-number
            uuids = serial_number_to_uuids.get(test.serial_number, [])
            for uuid in uuids:
                result = rp_results.get(uuid, None)
                if not result:
                    continue
                data = {
                    "name": test.name,
                    "result": result.status,
                    "defect": list(result.statistics.defects.keys()) or None,
                }
                if matches_filter(filter, data):
                    filtered_tests[test.serial_number] = test
                    break

    return filtered_tests.values()
