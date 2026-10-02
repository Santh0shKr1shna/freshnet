from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class TaskSpec:
    name: str
    run: str
    depends_on: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class WorkflowSpec:
    name: Optional[str]
    tasks: List[TaskSpec]
