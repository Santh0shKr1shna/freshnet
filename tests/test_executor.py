import pytest

from freshnet import Dag, DagTask, Executor


def make_task(name, run, depends_on=()):
    return DagTask(name=name, run=run, depends_on=list(depends_on))


def test_executor_runs_all_tasks_in_topological_order():
    runs = []
    dag = Dag(
        {
            "a": make_task("a", lambda: runs.append("a")),
            "b": make_task("b", lambda a: runs.append("b"), ["a"]),
        }
    )

    ran = Executor().run(dag)

    assert ran == ["a", "b"]
    assert runs == ["a", "b"]


def test_executor_threads_return_values_to_dependents():
    dag = Dag(
        {
            "a": make_task("a", lambda: 2),
            "b": make_task("b", lambda a: a * 10, ["a"]),
        }
    )

    executor = Executor()
    executor.run(dag)

    assert executor.results["a"] == 2
    assert executor.results["b"] == 20


def test_executor_passes_all_fan_in_inputs_by_name():
    dag = Dag(
        {
            "x": make_task("x", lambda: 1),
            "y": make_task("y", lambda: 2),
            "z": make_task("z", lambda x, y: x + y, ["x", "y"]),
        }
    )

    executor = Executor()
    executor.run(dag)

    assert executor.results["z"] == 3


def test_executor_stops_on_task_exception():
    runs = []

    def boom():
        raise RuntimeError("boom")

    dag = Dag(
        {
            "a": make_task("a", boom),
            "b": make_task("b", lambda a: runs.append("b"), ["a"]),
        }
    )

    with pytest.raises(RuntimeError, match="boom"):
        Executor().run(dag)

    assert runs == []
