# tmt-recipe-tool

A command-line tool for filtering and rerunning [tmt](https://tmt.readthedocs.io/) tests based on result attributes.

Given a [tmt recipe](https://tmt.readthedocs.io/en/stable/spec/recipe.html) and its associated test results, `tmt-recipe-tool` can produce a new recipe containing only the tests that match a filter expression, and optionally rerun them immediately.

Results can be sourced either from a local tmt [results file](https://tmt.readthedocs.io/en/stable/spec/results.html) or from a [ReportPortal](https://tmt.readthedocs.io/en/stable/plugins/report.html#reportportal) instance when the recipe's report phase is configured with `how: reportportal`.

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
tmt-recipe-tool [OPTIONS]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `-i, --input PATH` | | Path to the input recipe file (required) |
| `-o, --output PATH` | | Path to save the modified recipe (if omitted, the recipe is not saved) |
| `-f, --filter EXPRESSION` | `result: fail, error, failed` | Keep tests matching this filter expression |
| `--use-reportportal` | `false` | Fetch test results from ReportPortal instead of a local results file |
| `--run` | | Rerun the modified recipe with tmt after processing |
| `--feeling-safe` | | Pass `--feeling-safe` to tmt, allowing potentially unsafe operations |
| `--run-workdir PATH` | | Path to the tmt run workdir, used as the base directory for resolving relative results paths |
| `--version` | | Show version and exit |

### Filter expression

Filtering uses [fmf](https://fmf.readthedocs.io/en/stable/modules.html#fmf.filter) expression syntax internally. Matching is case-insensitive; values are regular expressions matched against the whole field.

| Operator | Meaning |
|----------|---------|
| `&` | AND |
| `\|` | OR |
| `key: -value` | NOT |
| `key: a, b` | OR within the same key (`key: a \| key: b`) |

Parentheses are not supported. Use disjunctive normal form instead (`A & C \| B & C` for `(A \| B) & C`). Precedence is negation, then `&`, then `|`.

Supported fields:

| Field | Description |
|-------|-------------|
| `name` | Test name |
| `result` | Result status (see below) |
| `defect` | ReportPortal defect type (`product_bug`, `automation_bug`, `system_issue`, `no_defect`, `to_investigate`). Set to `none` for local results and for ReportPortal items with no defects. |

### Result statuses

Statuses are **not** mapped between sources. Use the values from the source you are filtering:

| Source | `result` values |
|--------|-----------------|
| tmt results | `pass`, `fail`, `warn`, `error`, `info`, `skip`, `pending` |
| ReportPortal results | `passed`, `failed`, `skipped` |

The default filter includes both `fail`/`error` (tmt) and `failed` (ReportPortal) so it works with either source.

### ReportPortal

When `--use-reportportal` is used, results are fetched from any report phase in the recipe that has `how: reportportal`. The phase must include `launch-uuid` and `test-uuids` (populated automatically by the tmt [ReportPortal](https://tmt.readthedocs.io/en/stable/plugins/report/reportportal.html) plugin after a run finishes). The `launch-uuid` and `test-uuids` fields are stripped from the output recipe so that a subsequent run creates a new ReportPortal launch. Plans that do not have a `reportportal` report phase always fall back to their local `results.yaml` file, even when `--use-reportportal` is passed.

### Examples

Filter a recipe with the default expression (failed and errored tests), saving the result:

```bash
tmt-recipe-tool -i recipe.yaml -o filtered.yaml
```

Keep only tests that passed:

```bash
tmt-recipe-tool -i recipe.yaml -o passed.yaml -f 'result: pass'
```

Keep failed tests with a specific defect type (ReportPortal):

```bash
tmt-recipe-tool -i recipe.yaml -o bugs.yaml --use-reportportal \
  -f 'result: failed & defect: product_bug'
```

Keep failed tests, or tests whose name matches a pattern:

```bash
tmt-recipe-tool -i recipe.yaml -o subset.yaml -f 'result: fail | name: .*/smoke.*'
```

Filter and immediately rerun:

```bash
tmt-recipe-tool -i recipe.yaml --run
```

Rerun with `--feeling-safe`:

```bash
tmt-recipe-tool -i recipe.yaml --run --feeling-safe
```

Filter using ReportPortal results:

```bash
tmt-recipe-tool -i recipe.yaml -o filtered.yaml --use-reportportal
```

Fetch failures from ReportPortal and rerun them:

```bash
tmt-recipe-tool -i recipe.yaml --run --use-reportportal -f 'result: failed'
```
