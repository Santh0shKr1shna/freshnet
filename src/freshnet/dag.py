from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set

from .errors import CycleError


@dataclass(frozen=True)
class DagTask:
    name: str
    run: Callable[[], None]
    depends_on: List[str]


class Dag:
    def __init__(self, nodes: Dict[str, DagTask]):
        self.nodes = nodes

    def topological_order(self) -> List[str]:
        """Kahn's algorithm. Raises CycleError if the graph isn't a DAG."""
        in_degree = {name: 0 for name in self.nodes}
        dependents: Dict[str, List[str]] = {name: [] for name in self.nodes}
        for name, task in self.nodes.items():
            for dep in task.depends_on:
                in_degree[name] += 1
                dependents[dep].append(name)

        ready = sorted(name for name, degree in in_degree.items() if degree == 0)
        order: List[str] = []
        while ready:
            ready.sort()
            name = ready.pop(0)
            order.append(name)
            for dependent in dependents[name]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    ready.append(dependent)

        if len(order) != len(self.nodes):
            remaining = set(self.nodes) - set(order)
            raise CycleError(_find_cycle(self.nodes, remaining))

        return order


def _find_cycle(nodes: Dict[str, DagTask], remaining: Set[str]) -> List[str]:
    """DFS over the leftover (cyclic) nodes, following depends_on edges,
    until a node already on the current path is revisited."""
    stack: List[str] = []
    on_stack: Set[str] = set()
    visited: Set[str] = set()

    def visit(name: str) -> Optional[List[str]]:
        if name in on_stack:
            idx = stack.index(name)
            return stack[idx:] + [name]
        if name in visited:
            return None
        visited.add(name)
        stack.append(name)
        on_stack.add(name)
        for dep in nodes[name].depends_on:
            if dep in remaining:
                found = visit(dep)
                if found is not None:
                    return found
        stack.pop()
        on_stack.discard(name)
        return None

    for name in remaining:
        found = visit(name)
        if found is not None:
            return found
    return list(remaining)  # unreachable in practice
