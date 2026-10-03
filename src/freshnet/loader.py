import importlib
import inspect
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from .dag import Dag, DagTask
from .errors import CallableResolutionError, CycleError, SchemaError, YamlSyntaxError
from .spec import TaskSpec, WorkflowSpec

_yaml = YAML(typ="rt")


def parse_yaml(path) -> dict:
    path = Path(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return _yaml.load(f)
    except YAMLError as exc:
        raise YamlSyntaxError(path, exc) from exc


def _key_position(mapping, key) -> Tuple[Optional[int], Optional[int]]:
    """Position of `key` in a ruamel CommentedMap (1-indexed), or (None, None)."""
    try:
        entry = mapping.lc.data[key]
        return entry[0] + 1, entry[1] + 1
    except Exception:
        return None, None


def _item_position(seq, index) -> Tuple[Optional[int], Optional[int]]:
    """Position of item `index` in a ruamel CommentedSeq (1-indexed), or (None, None)."""
    try:
        entry = seq.lc.data[index]
        return entry[0] + 1, entry[1] + 1
    except Exception:
        return None, None


def _map_position(mapping) -> Tuple[Optional[int], Optional[int]]:
    """Position where a ruamel CommentedMap itself starts (1-indexed), or (None, None)."""
    try:
        return mapping.lc.line + 1, mapping.lc.col + 1
    except Exception:
        return None, None


def to_spec(raw, source_path=None) -> WorkflowSpec:
    if not isinstance(raw, dict):
        raise SchemaError(
            "workflow file must be a YAML mapping with a top-level 'tasks:' key",
            path=source_path,
        )

    tasks_raw = raw.get("tasks")
    if not isinstance(tasks_raw, dict) or not tasks_raw:
        line, col = _map_position(raw)
        raise SchemaError("missing or empty 'tasks:' mapping", path=source_path, line=line, col=col)

    task_names = set(tasks_raw.keys())
    tasks: List[TaskSpec] = []

    for name, body in tasks_raw.items():
        if not isinstance(body, dict):
            line, col = _key_position(tasks_raw, name)
            raise SchemaError(
                f"task '{name}' must be a mapping", path=source_path, line=line, col=col, task_name=name
            )

        run = body.get("run")
        if not isinstance(run, str) or not run:
            line, col = _map_position(body)
            if line is None:
                line, col = _key_position(tasks_raw, name)
            raise SchemaError(
                f"task '{name}' is missing a 'run:' string", path=source_path, line=line, col=col, task_name=name
            )

        depends_on_raw = body.get("depends_on") or []
        if not isinstance(depends_on_raw, list):
            line, col = _key_position(body, "depends_on")
            raise SchemaError(
                f"task '{name}' depends_on must be a list", path=source_path, line=line, col=col, task_name=name
            )

        depends_on: List[str] = []
        for idx, dep in enumerate(depends_on_raw):
            if dep not in task_names:
                line, col = _item_position(depends_on_raw, idx)
                if line is None:
                    line, col = _key_position(body, "depends_on")
                raise SchemaError(
                    f"task '{name}' depends_on unknown task '{dep}'",
                    path=source_path,
                    line=line,
                    col=col,
                    task_name=name,
                )
            depends_on.append(str(dep))

        tasks.append(TaskSpec(name=str(name), run=run, depends_on=depends_on))

    return WorkflowSpec(name=raw.get("name"), tasks=tasks)


def resolve_callable(run_str: str) -> Callable[[], None]:
    if ":" not in run_str:
        raise CallableResolutionError(run_str, ValueError("expected 'module.path:function_name'"))
    module_path, _, func_name = run_str.partition(":")
    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise CallableResolutionError(run_str, exc) from exc
    try:
        return getattr(module, func_name)
    except AttributeError as exc:
        raise CallableResolutionError(run_str, exc) from exc


def _check_signature(name: str, callable_, depends_on: List[str], source_path=None) -> None:
    """Each dependency's return value is threaded in as a same-named keyword
    argument, so the callable must be able to accept them - check this at
    build time instead of letting it surface as a TypeError mid-execution."""
    try:
        inspect.signature(callable_).bind(**{dep: None for dep in depends_on})
    except TypeError as exc:
        raise SchemaError(
            f"task '{name}' function does not accept its dependencies {depends_on} as keyword arguments: {exc}",
            path=source_path,
            task_name=name,
        ) from exc


def build_dag(spec: WorkflowSpec, source_path=None) -> Dag:
    nodes = {}
    for task in spec.tasks:
        callable_ = resolve_callable(task.run)
        _check_signature(task.name, callable_, task.depends_on, source_path)
        nodes[task.name] = DagTask(name=task.name, run=callable_, depends_on=list(task.depends_on))

    dag = Dag(nodes)
    try:
        dag.topological_order()  # validates acyclicity eagerly, at build time
    except CycleError as exc:
        exc.path = source_path
        raise
    return dag


def load_workflow(path) -> Dag:
    path = Path(path)
    raw = parse_yaml(path)
    spec = to_spec(raw, source_path=path)
    return build_dag(spec, source_path=path)
