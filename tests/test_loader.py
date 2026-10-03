import pytest

from freshnet import (
    CallableResolutionError,
    SchemaError,
    YamlSyntaxError,
    load_workflow,
    resolve_callable,
)


def make_fixture_module(tmp_path, monkeypatch):
    (tmp_path / "fixture_tasks.py").write_text(
        "calls = []\n"
        "def task_a():\n"
        "    calls.append('a')\n"
        "def task_b(a=None):\n"
        "    calls.append('b')\n"
    )
    monkeypatch.syspath_prepend(str(tmp_path))


def write_workflow(tmp_path, lines):
    path = tmp_path / "workflow.yaml"
    path.write_text("\n".join(lines) + "\n")
    return path


def test_load_workflow_builds_dag_with_expected_tasks(tmp_path, monkeypatch):
    make_fixture_module(tmp_path, monkeypatch)
    workflow = write_workflow(
        tmp_path,
        [
            "tasks:",
            "  a:",
            '    run: "fixture_tasks:task_a"',
            "  b:",
            "    depends_on: [a]",
            '    run: "fixture_tasks:task_b"',
        ],
    )

    dag = load_workflow(workflow)

    assert set(dag.nodes) == {"a", "b"}
    assert dag.nodes["b"].depends_on == ["a"]


def test_resolve_callable_imports_function(tmp_path, monkeypatch):
    make_fixture_module(tmp_path, monkeypatch)

    fn = resolve_callable("fixture_tasks:task_a")
    fn()

    import fixture_tasks

    assert fixture_tasks.calls == ["a"]


def test_resolve_callable_raises_on_missing_module():
    with pytest.raises(CallableResolutionError, match="no_such_module"):
        resolve_callable("no_such_module:fn")


def test_resolve_callable_raises_on_missing_attr(tmp_path, monkeypatch):
    make_fixture_module(tmp_path, monkeypatch)

    with pytest.raises(CallableResolutionError, match="does_not_exist"):
        resolve_callable("fixture_tasks:does_not_exist")


def test_unknown_depends_on_raises_schema_error_with_line_info(tmp_path, monkeypatch):
    make_fixture_module(tmp_path, monkeypatch)
    workflow = write_workflow(
        tmp_path,
        [
            "tasks:",
            "  a:",
            '    run: "fixture_tasks:task_a"',
            "  b:",
            "    depends_on: [ghost]",
            '    run: "fixture_tasks:task_b"',
        ],
    )

    with pytest.raises(SchemaError) as exc_info:
        load_workflow(workflow)

    err = exc_info.value
    assert err.task_name == "b"
    assert err.line == 5
    assert err.col == 18


def test_signature_mismatch_raises_schema_error(tmp_path, monkeypatch):
    (tmp_path / "bad_tasks.py").write_text("def task_a():\n    pass\ndef task_b():\n    pass\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    workflow = write_workflow(
        tmp_path,
        [
            "tasks:",
            "  a:",
            '    run: "bad_tasks:task_a"',
            "  b:",
            "    depends_on: [a]",
            '    run: "bad_tasks:task_b"',
        ],
    )

    with pytest.raises(SchemaError, match="does not accept"):
        load_workflow(workflow)


def test_missing_run_raises_schema_error(tmp_path):
    workflow = write_workflow(tmp_path, ["tasks:", "  a:", "    depends_on: []"])

    with pytest.raises(SchemaError, match="missing a 'run:'"):
        load_workflow(workflow)


def test_malformed_yaml_raises_yaml_syntax_error(tmp_path):
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text("tasks:\n  a:\n\trun: bad-tab-indent\n")

    with pytest.raises(YamlSyntaxError):
        load_workflow(workflow)


def test_missing_tasks_key_raises_schema_error(tmp_path):
    workflow = write_workflow(tmp_path, ["name: empty_workflow"])

    with pytest.raises(SchemaError, match="tasks"):
        load_workflow(workflow)
