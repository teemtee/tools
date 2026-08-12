import tempfile
from pathlib import Path
from typing import Any, Optional

import click

from tmt_recipe_tool.filtering import DEFAULT_FILTER
from tmt_recipe_tool.recipe import _save_recipe, filter_recipe
from tmt_recipe_tool.utils import run_tmt_recipe


@click.command(no_args_is_help=True)
@click.version_option(package_name="tmt-recipe-tool")
@click.option(
    "-i",
    "--input",
    metavar="PATH",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to the input recipe file.",
    required=True,
)
@click.option(
    "-o",
    "--output",
    metavar="PATH",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    default=None,
    help=(
        "Path to the output recipe file. If not specified, the modified recipe will not be saved."
    ),
)
@click.option(
    "-f",
    "--filter",
    metavar="EXPRESSION",
    type=str,
    default=DEFAULT_FILTER,
    show_default=True,
    help="Keep tests matching this fmf filter expression. Available keys: name, result, defect.",
)
@click.option(
    "--use-reportportal",
    is_flag=True,
    default=False,
    help="Fetch test results from ReportPortal instead of a local results file.",
)
@click.option(
    "--run",
    is_flag=True,
    type=bool,
    default=False,
    help="Rerun the modified recipe with tmt.",
)
@click.option(
    "--feeling-safe",
    is_flag=True,
    type=bool,
    default=False,
    help="Pass --feeling-safe to tmt, allowing execution of potentially unsafe operations.",
)
@click.option(
    "--run-workdir",
    metavar="PATH",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help=(
        "Path to the tmt run workdir. Used as the base directory for resolving "
        "relative results paths."
    ),
)
def main(
    input: Path,  # noqa: A002
    output: Optional[Path],
    filter: str,  # noqa: A002
    use_reportportal: bool,
    run: bool,
    feeling_safe: bool,
    run_workdir: Optional[Path],
    **kwargs: Any,
) -> None:
    """tmt-recipe-tool - Filter and optionally rerun a tmt recipe using a filter expression."""
    recipe = filter_recipe(
        input,
        filter,
        run_workdir=run_workdir,
        use_reportportal=use_reportportal,
    )

    empty_plans = [p.name for p in recipe.plans if not p.discover.tests]
    if empty_plans:
        click.echo(
            f"Warning: No tests remaining after filtering in plan(s): {', '.join(empty_plans)}",
            err=True,
        )

    if output:
        _save_recipe(recipe, output)
        print(f"Modified recipe saved to: '{output}'")
    else:
        print("No output path provided, the modified recipe will not be saved.")

    if run:
        if not output:
            with tempfile.TemporaryDirectory(prefix="tmt_recipe_tool_") as tmp:
                output = Path(tmp) / "recipe.yaml"
                _save_recipe(recipe, output)
                run_tmt_recipe(output, feeling_safe=feeling_safe)
        else:
            run_tmt_recipe(output, feeling_safe=feeling_safe)
    elif len(empty_plans) == len(recipe.plans):
        click.echo(
            "Warning: None of the plans have any tests after filtering.",
            err=True,
        )
        raise SystemExit(3)
