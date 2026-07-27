from collections.abc import Iterable
from pathlib import Path
from typing import Optional, cast

import tmt
import tmt.recipe
import tmt.utils
from pydantic import ValidationError

from tmt_recipe_tool.filtering import build_filter_data, matches_filter
from tmt_recipe_tool.models import Result
from tmt_recipe_tool.reportportal import edit_rp_phases, filter_tests_from_rp, get_rp_phases
from tmt_recipe_tool.utils import create_tmt_logger, load_yaml


class RecipeError(Exception):
    """Raised when a recipe is invalid or cannot be processed."""


def _load_recipe(path: Path) -> tmt.recipe.Recipe:
    raw_recipe = tmt.utils.yaml_to_dict(path.read_text(encoding="utf-8", errors="replace"))
    try:
        return tmt.recipe.Recipe.from_spec(
            cast(tmt.recipe._RawRecipe, raw_recipe), create_tmt_logger()
        )
    except Exception as exc:
        raise RecipeError(f"Invalid recipe: '{path}'") from exc


def _save_recipe(recipe: tmt.recipe.Recipe, path: Path) -> None:
    path.write_text(tmt.utils.to_yaml(recipe.to_spec()), encoding="utf-8", errors="replace")


def _resolve_results_path(
    plan: tmt.recipe._RecipePlan,
    input_path: Path,
    run_workdir: Optional[Path] = None,
) -> Path:
    """Extract and resolve the results-path from a plan's execute step."""
    if plan.execute.results_path is None:
        raise RecipeError(f"Results file for plan '{plan.name}' not found.")

    results_path = Path(plan.execute.results_path)
    if results_path.exists():
        return results_path

    if run_workdir is not None:
        results_path = run_workdir / results_path
    else:
        results_path = input_path.parent / results_path

    if not results_path.exists():
        raise RecipeError(f"Results file for plan '{plan.name}' not found: {results_path}")

    return results_path


def _load_results(results_path: Path, plan_name: str) -> list[Result]:
    """Load and validate a results file."""
    raw = load_yaml(results_path)
    if not isinstance(raw, list):
        raise RecipeError(
            f"Results for plan '{plan_name}' must be a list, got {type(raw).__name__}."
        )
    try:
        return [Result.model_validate(r) for r in raw]
    except ValidationError as e:
        raise RecipeError(f"Invalid result entry in plan '{plan_name}': {e}") from e


def _filter_tests(
    tests: list[tmt.recipe._RecipeTest],
    results: list[Result],
    filter: str,  # noqa: A002
) -> Iterable[tmt.recipe._RecipeTest]:
    """
    Yield tests whose local result matches the fmf filter expression.
    """
    for test in tests:
        for result in results:
            if test.name != result.name or test.serial_number != result.serial_number:
                continue
            data = build_filter_data(name=test.name, result=result.result)
            if matches_filter(filter, data):
                yield test
                break


def filter_recipe(
    input_path: Path,
    filter: str,  # noqa: A002
    run_workdir: Optional[Path] = None,
    use_reportportal: bool = False,
) -> tmt.recipe.Recipe:
    """
    Load a recipe and keep only tests matching the fmf filter expression.

    Results are taken from ReportPortal when ``use_reportportal`` is set and the
    plan has a reportportal phase, otherwise from the plan's local results file.
    """
    recipe = _load_recipe(input_path)

    filtered_plans = []
    for plan in recipe.plans:
        if not plan.discover.tests:
            print(f"Plan '{plan.name}' does not contain any tests and will be skipped.")
            continue
        rp_phases = get_rp_phases(plan)
        if rp_phases and use_reportportal:
            plan.discover.tests = list(
                filter_tests_from_rp(plan.discover.tests, rp_phases, filter)
            )
            plan.report.phases = edit_rp_phases(plan.report.phases)
        else:
            results = _load_results(
                _resolve_results_path(plan, input_path, run_workdir), plan.name
            )
            plan.discover.tests = list(_filter_tests(plan.discover.tests, results, filter))
        filtered_plans.append(plan)

    recipe.plans = filtered_plans
    return recipe
