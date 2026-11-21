import pytest

from evals.common import load_dataset
from tests.integration_helpers import login_session, query

SQL_CASES = load_dataset("sql_accuracy.json")
NEEDS_TAGS = {"sql-37"}


def test_dataset_sizes_match_prd() -> None:
    assert len(SQL_CASES) == 40
    assert sum(case["language"] == "hinglish" for case in SQL_CASES) == 8
    assert len(load_dataset("isolation.json")) == 20
    guardrails = load_dataset("guardrails.json")
    assert len(guardrails["bad"]) == 15 and len(guardrails["normal"]) == 15
    assert len(load_dataset("routing.json")) == 25
    assert len(load_dataset("charts.json")) == 15
    labels = load_dataset("tagging_labels.json")
    assert len(labels["feedback"]) == 40 and len(labels["complaints"]) == 20


@pytest.mark.parametrize("case", SQL_CASES, ids=[case["id"] for case in SQL_CASES])
def test_gold_sql_runs_for_its_role(case: dict) -> None:
    result = query(login_session(case["role"]), case["gold_sql"])
    assert "error" not in result, result.get("error")
    if case["id"] not in NEEDS_TAGS:
        assert result["total_rows"] > 0
