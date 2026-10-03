# freshnet

A bare-metal YAML-to-DAG workflow parser and executor.

Define tasks and their dependencies declaratively in a YAML file, and freshnet
parses it into a validated dependency graph and runs each task exactly once,
in topological order.



## Example

```yaml
# workflow.yaml
name: sample_pipeline

tasks:
  extract_users:
    run: "tasks:extract_users"
  extract_orders:
    run: "tasks:extract_orders"
  build_report:
    depends_on: [extract_users, extract_orders]
    run: "tasks:build_report"
```

```python
# tasks.py
def extract_users():
    return ["alice", "bob"]

def extract_orders():
    return [101, 102, 103]

def build_report(extract_users, extract_orders):
    return f"{len(extract_users)} users, {len(extract_orders)} orders"
```

```python
from freshnet import load_workflow, Executor

dag = load_workflow("workflow.yaml")
executor = Executor()
executor.run(dag)  # runs extract_users, extract_orders (either order), then build_report
executor.results["build_report"]  # "2 users, 3 orders"
```

A task's work is specified as `run: "module.path:function_name"` — a plain
Python callable, resolved and invoked in-process. Each task's return value
is threaded to whatever depends on it, as a same-named keyword argument
(`build_report` above receives `extract_users` and `extract_orders` by
name) — a task needing several values from one dependency just returns a
dict. Signature mismatches (a task that doesn't accept its own
dependencies) are caught at load time, not mid-run. There's no `command:`
subprocess support (yet) — everything runs in-process.

Errors point at the actual YAML source position (`file:line:col`) instead
of a raw Python traceback — an unknown `depends_on` reference or a
dependency cycle gets a message naming exactly where in the file the
problem is.

## Status

YAML parsing (`ruamel.yaml`, chosen specifically because it preserves
line/column info for error messages), schema validation, cycle detection,
build-time signature checking, and sequential topological execution with
return values threaded between tasks. No parallel execution, retries, or
`command:` subprocess tasks yet.


## Dev

```bash
pip install -e ".[test]"
pytest
```
