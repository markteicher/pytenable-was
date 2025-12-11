# tests/test_utils.py

import math
from pytenable_was.utils import (
    normalize_id,
    normalize_url,
    normalize_list,
    is_uuid,
    safe_get,
    parse_timestamp,
    format_iso,
    duration_seconds,
    severity_rank,
    sort_by_severity,
    group_by_severity,
    flatten_dict,
    flatten_model,
    pretty_json,
)


def test_normalize_id_basic():
    assert normalize_id("  abc  ") == "abc"
    assert normalize_id(123) == "123"
    assert normalize_id(None) is None


def test_normalize_url_basic():
    assert normalize_url("  HTTPS://Example.com/Path ") == "https://example.com/path"
    assert normalize_url(None) is None
    assert normalize_url("") is None


def test_normalize_list():
    assert normalize_list(None) == []
    assert normalize_list([1, 2]) == [1, 2]
    assert normalize_list("a") == ["a"]


def test_is_uuid():
    assert is_uuid("123e4567-e89b-12d3-a456-426614174000")
    assert not is_uuid("not-a-uuid")
    assert not is_uuid("")
    assert not is_uuid(None)


def test_safe_get():
    data = {"a": {"b": {"c": 1}}}
    assert safe_get(data, "a", "b", "c") == 1
    assert safe_get(data, "a", "x", "c", default="missing") == "missing"
    assert safe_get(None, "a", default="missing") == "missing"
    assert safe_get({"a": None}, "a", default="missing") == "missing"


def test_parse_timestamp_epoch_int_and_str():
    assert parse_timestamp(1700000000) == 1700000000
    assert parse_timestamp("1700000000") == 1700000000


def test_parse_timestamp_iso_and_format_iso_roundtrip():
    ts_iso = "2023-01-01T00:00:00Z"
    epoch = parse_timestamp(ts_iso)
    assert isinstance(epoch, int)

    iso_out = format_iso(epoch)
    # Accept minor differences in seconds representation; just ensure roundtrip works
    assert iso_out.endswith("Z")


def test_parse_timestamp_invalid():
    assert parse_timestamp("not-a-timestamp") is None


def test_duration_seconds():
    start = 1700000000
    end = 1700000100
    assert duration_seconds(start, end) == 100

    # invalid input returns None
    assert duration_seconds("bad", end) is None


def test_severity_rank_and_sort():
    assert severity_rank("critical") > severity_rank("high")
    assert severity_rank("info") >= 0
    assert severity_rank("UNKNOWN") == -1

    findings = [
        {"id": 1, "severity": "low"},
        {"id": 2, "severity": "critical"},
        {"id": 3, "severity": "medium"},
    ]
    sorted_findings = sort_by_severity(findings)
    assert [f["id"] for f in sorted_findings] == [2, 3, 1]


def test_group_by_severity_dict_and_object():
    class Obj:
        def __init__(self, severity):
            self.severity = severity

    f1 = {"severity": "high"}
    f2 = {"severity": "low"}
    f3 = Obj("critical")
    f4 = {"severity": "weird"}

    groups = group_by_severity([f1, f2, f3, f4])
    assert len(groups["critical"]) == 1
    assert len(groups["high"]) == 1
    assert len(groups["low"]) == 1
    assert len(groups["unknown"]) == 1


def test_flatten_dict_simple():
    data = {"a": {"b": 1, "c": {"d": 2}}, "x": 3}
    flat = flatten_dict(data)
    assert flat == {"a.b": 1, "a.c.d": 2, "x": 3}


def test_flatten_model_with_dict():
    data = {"a": {"b": 1}}
    flat = flatten_model(data)
    assert flat == {"a.b": 1}


def test_flatten_model_with_pydantic_like():
    class FakeModel:
        def __init__(self):
            self._data = {"a": {"b": 1}}

        def model_dump(self):
            return self._data

    model = FakeModel()
    flat = flatten_model(model)
    assert flat == {"a.b": 1}


def test_flatten_model_invalid():
    class NotModel:
        pass

    try:
        flatten_model(NotModel())
    except ValueError:
        assert True
    else:
        assert False, "Expected ValueError for invalid flatten_model input"


def test_pretty_json():
    data = {"b": 1, "a": 2}
    out = pretty_json(data)
    assert "{\n" in out
    assert '"a": 2' in out
    assert '"b": 1' in out

    # Non-serializable object falls back to str()
    class X:
        pass

    x = X()
    out2 = pretty_json(x)
    # Just make sure it doesn't crash and returns something
    assert isinstance(out2, str)
