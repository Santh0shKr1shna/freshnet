import pytest

from freshnet import CycleError, Dag, DagTask


def make_task(name, depends_on=()):
    return DagTask(name=name, run=lambda: None, depends_on=list(depends_on))


def test_topological_order_respects_dependencies():
    dag = Dag(
        {
            "a": make_task("a"),
            "b": make_task("b", ["a"]),
            "c": make_task("c", ["b"]),
        }
    )

    assert dag.topological_order() == ["a", "b", "c"]


def test_topological_order_handles_fan_in():
    sources = ["extract_users", "extract_orders", "extract_inventory"]
    nodes = {name: make_task(name) for name in sources}
    nodes["build_report"] = make_task("build_report", depends_on=sources)
    dag = Dag(nodes)

    order = dag.topological_order()

    for source in sources:
        assert order.index("build_report") > order.index(source)


def test_topological_order_handles_fan_out():
    dependents = ["load_users", "load_orders", "load_inventory"]
    nodes = {"extract": make_task("extract")}
    nodes.update({name: make_task(name, depends_on=["extract"]) for name in dependents})
    dag = Dag(nodes)

    order = dag.topological_order()

    for dependent in dependents:
        assert order.index(dependent) > order.index("extract")


def test_cycle_raises_cycle_error():
    dag = Dag(
        {
            "a": make_task("a", ["b"]),
            "b": make_task("b", ["a"]),
        }
    )

    with pytest.raises(CycleError) as exc_info:
        dag.topological_order()

    assert "a" in exc_info.value.cycle
    assert "b" in exc_info.value.cycle


def test_self_dependency_raises_cycle_error():
    dag = Dag({"a": make_task("a", ["a"])})

    with pytest.raises(CycleError) as exc_info:
        dag.topological_order()

    assert exc_info.value.cycle == ["a", "a"]
