from src.models.classify_check import classify_gap, is_near_mro


def test_classify_all_brief_durations():
    assert classify_gap(2, True, False)[0] == "A-check"
    assert classify_gap(4, False, False)[0] == "B-check"
    assert classify_gap(29, False, False)[0] == "C-check"
    assert classify_gap(89, False, False)[0] == "D-check"


def test_mro_hub_detection():
    assert is_near_mro("EPWA") is True
    assert is_near_mro("KJFK") is False
