from pathlib import Path
from typing import Any, Union, cast

import tmt
from ruamel.yaml import YAML

YamlType = Union[dict[str, Any], list[dict[str, Any]]]


def create_tmt_logger() -> "tmt.log.Logger":
    logger = tmt.log.Logger.create()
    logger.add_console_handler()
    logger._logger.propagate = False
    return logger


def load_yaml(path: Path) -> YamlType:
    """Load and parse a YAML file from the given path."""
    yaml = YAML()
    with path.open() as file:
        return cast("YamlType", yaml.load(file))


def save_yaml(data: YamlType, path: Path) -> None:
    """Serialize data to a YAML file at the given path."""
    yaml = YAML()
    yaml.default_flow_style = False
    with path.open("w") as file:
        yaml.dump(data, file)


def run_tmt_recipe(recipe_path: Path, *, feeling_safe: bool = False) -> None:
    """Execute a tmt recipe."""
    import tmt.cli._root

    print("Running modified recipe with tmt.")

    args = ["run", "--recipe", str(recipe_path)]
    if feeling_safe:
        args = ["--feeling-safe", *args]

    tmt.cli._root.main(args)
