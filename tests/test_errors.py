from freshnet import SchemaError


def test_schema_error_str_includes_position_when_known():
    err = SchemaError("bad thing", path="workflow.yaml", line=5, col=3)
    assert str(err) == "workflow.yaml:5:3: bad thing"


def test_schema_error_str_falls_back_gracefully_without_position():
    err = SchemaError("bad thing")
    assert str(err) == "bad thing"

    err_partial = SchemaError("bad thing", path="workflow.yaml")
    assert str(err_partial) == "bad thing"
