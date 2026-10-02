import pytest

from freshnet import Dag, DagTask, Executor


def make_task(name, run, depends_on=()):
    return DagTask(name=name, run=run, depends_on=list(depends_on))


def test_executor_runs_all_tasks_in_topological_order():
    runs = []
    dag = Dag(
        {
            "a": make_task("a", lambda: runs.append("a")),
            "b": make_task("b", lambda: runs.append("b"), ["a"]),
        }
    )

    ran = Executor().run(dag)

    assert ran == ["a", "b"]
    assert runs == ["a", "b"]


def test_executor_stops_on_task_exception():
    runs = []

    def boom():
        raise RuntimeError("boom")

    dag = Dag(
        {
            "a": make_task("a", boom),
            "b": make_task("b", lambda: runs.append("b"), ["a"]),
        }
    )

    with pytest.raises(RuntimeError, match="boom"):
        Executor().run(dag)

    assert runs == []
