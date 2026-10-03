from typing import Any, Dict, List

from .dag import Dag


class Executor:
    """Runs every task in a Dag exactly once, in topological order.

    Each task is called with its dependencies' return values as same-named
    keyword arguments, and its own return value is threaded to whatever
    depends on it. Final results stay available on `.results` after a run.

    Fail-fast: if a task raises, the exception propagates immediately and
    no further tasks run.
    """

    def __init__(self):
        self.results: Dict[str, Any] = {}

    def run(self, dag: Dag) -> List[str]:
        self.results = {}
        ran: List[str] = []
        for name in dag.topological_order():
            task = dag.nodes[name]
            inputs = {dep: self.results[dep] for dep in task.depends_on}
            self.results[name] = task.run(**inputs)
            ran.append(name)
        return ran
