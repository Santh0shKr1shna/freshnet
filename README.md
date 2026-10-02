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
from freshnet import load_workflow, Executor

dag = load_workflow("workflow.yaml")
Executor().run(dag)  # runs extract_users, extract_orders (either order), then build_report
```

A task's work is specified as `run: "module.path:function_name"` — a plain
Python callable, resolved and invoked in-process. There's no `command:`
subprocess support (yet); keeping everything in-process is what makes this
teach DAG mechanics instead of process management.

Errors point at the actual YAML source position (`file:line:col`) instead
of a raw Python traceback — an unknown `depends_on` reference or a
dependency cycle gets a message naming exactly where in the file the
problem is.

## Status

Early scaffold: YAML parsing (`ruamel.yaml`, chosen specifically because it
preserves line/column info for error messages), schema validation, cycle
detection, and sequential topological execution. No parallel execution,
retries, or `command:` subprocess tasks yet.


## Dev

```bash
pip install -e ".[test]"
pytest
```
