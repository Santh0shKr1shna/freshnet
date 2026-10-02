from typing import List

from .dag import Dag


class Executor:
    """Runs every task in a Dag exactly once, in topological order.

    Fail-fast: if a task raises, the exception propagates immediately and
    no further tasks run.
    """

    def run(self, dag: Dag) -> List[str]:
        ran: List[str] = []
        for name in dag.topological_order():
            dag.nodes[name].run()
            ran.append(name)
        return ran
