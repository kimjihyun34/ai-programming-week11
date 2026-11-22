# test_scores.py
# 원본 함수를 scores.py에 저장한 뒤 실행: pytest -v
#
# 테스트 기준:
# - find_max: 마지막 원소를 포함한 전체 점수 중 최댓값을 반환한다.
# - count_pass: cutoff 이상인 점수를 합격으로 센다.
# - 빈 목록: find_max는 IndexError, count_pass는 0을 반환한다.
#
# 현재 구현에서는 마지막 원소가 최댓값인 경우와
# 점수가 cutoff와 같은 경우의 테스트가 실패한다.

import pytest

from scores import count_pass, find_max


# ── find_max: 정상 입력 ──────────────────────────────────────

@pytest.mark.parametrize(
    "scores, expected",
    [
        pytest.param([70, 95, 60, 85], 95, id="maximum-in-middle"),
        pytest.param([95, 85, 60, 70], 95, id="maximum-at-start"),
        pytest.param([70, 85, 60, 95], 95, id="maximum-at-end"),
        pytest.param([-30, -10, -20], -10, id="negative-scores"),
        pytest.param([70.5, 85.5, 60.5], 85.5, id="float-scores"),
        pytest.param([95, 70, 95, 60], 95, id="duplicate-maximum"),
    ],
)
def test_find_max_normal(scores, expected):
    assert find_max(scores) == expected


# ── find_max: 경계값 ─────────────────────────────────────────

@pytest.mark.parametrize(
    "scores, expected",
    [
        pytest.param([70], 70, id="single-element"),
        pytest.param([60, 95], 95, id="two-elements-last-is-maximum"),
        pytest.param([95, 60], 95, id="two-elements-first-is-maximum"),
        pytest.param([60, 60, 60], 60, id="all-equal"),
        pytest.param([0, 0], 0, id="all-zero"),
        pytest.param([-10, -5, 0], 0, id="zero-at-end"),
    ],
)
def test_find_max_boundary(scores, expected):
    assert find_max(scores) == expected


# ── find_max: 예외 ───────────────────────────────────────────

def test_find_max_empty_list_raises_index_error():
    with pytest.raises(IndexError):
        find_max([])


@pytest.mark.parametrize(
    "scores",
    [
        pytest.param(None, id="none-input"),
        pytest.param(70, id="non-sequence-input"),
        pytest.param([70, "85", 60], id="incomparable-string"),
        pytest.param([70, None, 60], id="incomparable-none"),
    ],
)
def test_find_max_invalid_input_raises_type_error(scores):
    with pytest.raises(TypeError):
        find_max(scores)


# ── count_pass: 정상 입력 ────────────────────────────────────

@pytest.mark.parametrize(
    "scores, cutoff, expected",
    [
        pytest.param([70, 85, 50, 95], 60, 3, id="mixed-scores"),
        pytest.param([70, 85, 95], 60, 3, id="all-pass"),
        pytest.param([10, 30, 59], 60, 0, id="all-fail"),
        pytest.param([70, 85, 90, 95], 80, 3, id="custom-cutoff"),
        pytest.param([-10, -5, 1], 0, 1, id="negative-scores"),
        pytest.param([59.5, 60.5, 80.5], 60, 2, id="float-scores"),
    ],
)
def test_count_pass_normal(scores, cutoff, expected):
    assert count_pass(scores, cutoff=cutoff) == expected


def test_count_pass_uses_default_cutoff():
    assert count_pass([59, 61, 90]) == 2


# ── count_pass: 경계값 ───────────────────────────────────────

@pytest.mark.parametrize(
    "scores, cutoff, expected",
    [
        pytest.param([], 60, 0, id="empty-list"),
        pytest.param([59], 60, 0, id="just-below-cutoff"),
        pytest.param([60], 60, 1, id="exactly-at-cutoff"),
        pytest.param([61], 60, 1, id="just-above-cutoff"),
        pytest.param([59, 60, 61], 60, 2, id="around-cutoff"),
        pytest.param([60, 60, 60], 60, 3, id="all-at-cutoff"),
        pytest.param([0], 0, 1, id="zero-cutoff"),
        pytest.param([-1, 0, 1], 0, 2, id="around-zero-cutoff"),
        pytest.param([79, 80, 81], 80, 2, id="custom-cutoff-boundary"),
    ],
)
def test_count_pass_boundary(scores, cutoff, expected):
    assert count_pass(scores, cutoff=cutoff) == expected


# ── count_pass: 예외 ─────────────────────────────────────────

@pytest.mark.parametrize(
    "scores, cutoff",
    [
        pytest.param(None, 60, id="none-input"),
        pytest.param(70, 60, id="non-iterable-input"),
        pytest.param([70, "85"], 60, id="incomparable-string"),
        pytest.param([70, None], 60, id="incomparable-none"),
        pytest.param([70, 85], "60", id="string-cutoff"),
        pytest.param([70, 85], None, id="none-cutoff"),
    ],
)
def test_count_pass_invalid_input_raises_type_error(scores, cutoff):
    with pytest.raises(TypeError):
        count_pass(scores, cutoff=cutoff)