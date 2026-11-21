from evals.compare import results_match


def test_order_insensitive_match_with_extra_columns() -> None:
    gold = [["CSE", 10.0], ["ECE", 20.0]]
    generated = [["ECE", "Electronics", 20.004], ["CSE", "Computer", 10.0]]
    assert results_match(gold, generated, ordered=False)


def test_ordered_mismatch_fails() -> None:
    assert not results_match([[1], [2]], [[2], [1]], ordered=True)


def test_value_mismatch_fails() -> None:
    assert not results_match([["CSE", 10.0]], [["CSE", 10.5]], ordered=False)


def test_top_one_gold_accepts_ordered_list() -> None:
    assert results_match([["ME"]], [["ME", 5.0], ["CSE", 3.0]], ordered=False)


def test_empty_results() -> None:
    assert results_match([], [], ordered=False)
    assert not results_match([], [[1]], ordered=False)
