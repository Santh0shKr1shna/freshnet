from typing import List, Optional


class FreshnetError(Exception):
    """Base class for all freshnet errors."""


class YamlSyntaxError(FreshnetError):
    def __init__(self, path, cause: Exception):
        self.path = path
        self.cause = cause
        super().__init__(f"Malformed YAML in {path}: {cause}")


class SchemaError(FreshnetError):
    def __init__(
        self,
        message: str,
        path=None,
        line: Optional[int] = None,
        col: Optional[int] = None,
        task_name: Optional[str] = None,
    ):
        self.message = message
        self.path = path
        self.line = line
        self.col = col
        self.task_name = task_name
        super().__init__(str(self))

    def __str__(self) -> str:
        if self.path is not None and self.line is not None and self.col is not None:
            return f"{self.path}:{self.line}:{self.col}: {self.message}"
        return self.message


class CycleError(SchemaError):
    def __init__(self, cycle: List[str], path=None, line: Optional[int] = None, col: Optional[int] = None):
        self.cycle = cycle
        rendered = " -> ".join(cycle)
        super().__init__(f"dependency cycle detected: {rendered}", path=path, line=line, col=col)


class CallableResolutionError(FreshnetError):
    def __init__(self, run_str: str, cause: Exception):
        self.run_str = run_str
        self.cause = cause
        super().__init__(f"could not resolve run: \"{run_str}\" ({cause})")
