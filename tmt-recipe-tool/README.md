# tmt-recipe-tool

A command-line tool for filtering and rerunning [tmt](https://tmt.readthedocs.io/) tests based on result outcomes.

Given a [tmt recipe](https://tmt.readthedocs.io/en/stable/spec/recipe.html) and its associated test results, `tmt-recipe-tool` can produce a new recipe containing only the tests that matched specific outcomes (e.g. failed or errored tests), and optionally rerun them immediately.

Results can be sourced either from a local tmt [results file](https://tmt.readthedocs.io/en/stable/spec/results.html) or from a [ReportPortal](https://reportportal.io/) instance when the recipe's report phase is configured with `how: reportportal`.

## Requirements

- Python 3.9+

## Installation

```bash
pip install .
```

For development:

```bash
uv sync --group dev
```

## Usage

```
tmt-recipe-tool [OPTIONS] COMMAND [ARGS]...
```

### Global options

| Option | Description |
|--------|-------------|
| `-i, --input PATH` | Path to the input recipe file |
| `-o, --output PATH` | Path to save the modified recipe (if omitted, the recipe is not saved) |
| `--run` | Rerun the modified recipe with tmt after processing |
| `--feeling-safe` | Pass `--feeling-safe` to tmt, allowing potentially unsafe operations |
| `--run-workdir PATH` | Path to the tmt run workdir, used as the base directory for resolving relative results paths |
| `--version` | Show version and exit |

### Commands

#### `filter-tests`

Filter recipe tests by their result outcome, keeping only those that match.

```
tmt-recipe-tool -i RECIPE filter-tests [--use-reportportal] [--result RESULT]...
```

| Option | Default | Description |
|--------|---------|-------------|
| `--result RESULT` | `fail`, `error`, `warn` | Keep tests with this outcome (repeatable) |
| `--use-reportportal` | `false` | Fetch test results from ReportPortal instead of a local results file |

When `--use-reportportal` is used, results are fetched from any report phase in the recipe that has `how: reportportal`. The phase must include `launch-uuid` and `test-uuids` (populated automatically by the tmt [ReportPortal](https://tmt.readthedocs.io/en/stable/plugins/report/reportportal.html) plugin after a run finishes). The `launch-uuid` and `test-uuids` fields are stripped from the output recipe so that a subsequent run creates a new ReportPortal launch. Plans that do not have a `reportportal` report phase always fall back to their local `results.yaml` file, even when `--use-reportportal` is passed.

Because ReportPortal only has three result statuses (`PASSED`, `FAILED`, `SKIPPED`), tmt outcomes are mapped before filtering:

| tmt outcome | ReportPortal status |
|-------------|---------------------|
| `pass` | `PASSED` |
| `fail` | `FAILED` |
| `warn` | `FAILED` |
| `error` | `FAILED` |
| `info` | `SKIPPED` |
| `skip` | `SKIPPED` |
| `pending` | `SKIPPED` |

As a result, `fail`, `warn`, and `error` are indistinguishable when filtering via ReportPortal, and all three will select tests with status `FAILED`. Similarly, `info`, `skip`, and `pending` will all select tests with status `SKIPPED`.

### Examples

Filter a recipe to keep only failed and errored tests, saving the result:

```bash
tmt-recipe-tool -i recipe.yaml -o filtered.yaml filter-tests
```

Keep only tests that passed:

```bash
tmt-recipe-tool -i recipe.yaml -o passed.yaml filter-tests --result pass
```

Filter and immediately rerun the failing tests:

```bash
tmt-recipe-tool -i recipe.yaml --run filter-tests
```

Rerun with `--feeling-safe` to allow potentially unsafe tmt operations:

```bash
tmt-recipe-tool -i recipe.yaml --run --feeling-safe filter-tests
```

Combine multiple result filters:

```bash
tmt-recipe-tool -i recipe.yaml -o subset.yaml filter-tests --result fail --result error
```

Filter using ReportPortal results (requires the recipe to have a `reportportal` report phase with `launch-uuid` and `test-uuids`):

```bash
tmt-recipe-tool -i recipe.yaml -o filtered.yaml filter-tests --use-reportportal
```

Fetch failures from ReportPortal and rerun them immediately:

```bash
tmt-recipe-tool -i recipe.yaml --run filter-tests --use-reportportal --result fail
```
