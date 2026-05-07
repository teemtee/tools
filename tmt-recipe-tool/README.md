# tmt-recipe-tool

A command-line tool for filtering and rerunning [tmt](https://tmt.readthedocs.io/) tests based on result outcomes.

Given a [tmt recipe](https://tmt.readthedocs.io/en/stable/spec/recipe.html) and its associated [test results](https://tmt.readthedocs.io/en/stable/spec/results.html), `tmt-recipe-tool` can produce a new recipe containing only the tests that matched specific outcomes (e.g. failed or errored tests), and optionally rerun them immediately.

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
tmt-recipe-tool -i RECIPE filter-tests [--result RESULT]...
```

| Option | Default | Description |
|--------|---------|-------------|
| `--result RESULT` | `fail`, `error`, `warn` | Keep tests with this outcome (repeatable) |

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
