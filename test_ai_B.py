# test_ai_B.py
"""
명세에 함수명과 반환 자료형이 없어 다음 인터페이스를 가정합니다.
실제 구현이 다르면 import와 call_loader()만 수정하세요.

가정한 인터페이스:
    grades.load_grades(path)
        -> (정상 성적 목록, 제외 기록 목록)

정상 성적 목록:
    [("김지현", 90.0), ...]

제외 기록 목록:
    [{"line": 3, "reason": "점수 누락"}, ...]

추가 가정:
- 첫 행이 정확히 name,score가 아니면 ValueError가 발생합니다.
- 빈 파일도 헤더가 없으므로 ValueError가 발생합니다.
- 파일 접근 실패는 OSError 또는 그 하위 예외로 전달합니다.
- 제외 이유는 사람이 이해할 수 있는 비어 있지 않은 문자열입니다.
- 점수 누락과 중복 제외 기록에는 각각 '누락', '중복'이 포함됩니다.
- 줄 번호는 헤더를 1번으로 세는 원본 파일의 물리적 줄 번호입니다.
"""

import builtins
import io
from pathlib import Path

import pytest

from grades import load_grades


def call_loader(path):
    """실제 함수의 반환 형식이 다르면 여기서 위의 형식으로 변환합니다."""
    return load_grades(path)


@pytest.fixture
def csv_file(tmp_path):
    def create(content):
        path = tmp_path / "grades.csv"
        with path.open("w", encoding="utf-8", newline="") as file:
            file.write(content)
        return path

    return create


def assert_errors(errors, expected_lines):
    assert isinstance(errors, list)
    assert len(errors) == len(expected_lines)

    for error in errors:
        assert isinstance(error, dict)
        assert isinstance(error["line"], int)
        assert isinstance(error["reason"], str)
        assert error["reason"].strip(), "제외 이유가 비어 있으면 안 됩니다."

    assert sorted(error["line"] for error in errors) == sorted(expected_lines)


def error_at(errors, line):
    matches = [error for error in errors if error["line"] == line]
    assert len(matches) == 1
    return matches[0]


# ── 정상 처리 ──────────────────────────────────────────


def test_normal_rows_are_returned_without_header(csv_file):
    path = csv_file(
        "name,score\n"
        "김지현,90\n"
        "이민수,82.5\n"
    )

    grades, errors = call_loader(path)

    assert grades == [("김지현", 90.0), ("이민수", 82.5)]
    assert errors == []


def test_header_only_is_a_valid_empty_grade_list(csv_file):
    path = csv_file("name,score\n")

    grades, errors = call_loader(path)

    assert grades == []
    assert errors == []


def test_last_row_without_final_newline_is_processed(csv_file):
    path = csv_file("name,score\n김지현,90")

    grades, errors = call_loader(path)

    assert grades == [("김지현", 90.0)]
    assert errors == []


def test_csv_quoted_comma_in_name(csv_file):
    path = csv_file(
        "name,score\n"
        '"Kim, Jihyun",91\n'
    )

    grades, errors = call_loader(path)

    assert grades == [("Kim, Jihyun", 91.0)]
    assert errors == []


def test_csv_escaped_quote_in_name(csv_file):
    path = csv_file(
        "name,score\n"
        '"Kim ""Jihyun""",91\n'
    )

    grades, errors = call_loader(path)

    assert grades == [('Kim "Jihyun"', 91.0)]
    assert errors == []


def test_windows_line_endings(csv_file):
    path = csv_file(
        "name,score\r\n"
        "김지현,90\r\n"
        "이민수,80\r\n"
    )

    grades, errors = call_loader(path)

    assert grades == [("김지현", 90.0), ("이민수", 80.0)]
    assert errors == []


# ── 파일 접근 예외 ──────────────────────────────────────


def test_missing_file_raises_instead_of_returning_empty(tmp_path):
    path = tmp_path / "missing.csv"

    with pytest.raises(OSError) as exc_info:
        call_loader(path)

    assert str(exc_info.value).strip()


def test_directory_is_not_accepted_as_regular_file(tmp_path):
    with pytest.raises(OSError) as exc_info:
        call_loader(tmp_path)

    assert str(exc_info.value).strip()


def test_unreadable_file_raises_permission_error(csv_file, monkeypatch):
    path = csv_file("name,score\n김지현,90\n")
    target = path.resolve()

    original_builtin_open = builtins.open
    original_io_open = io.open

    def is_target(file):
        try:
            return Path(file).resolve() == target
        except (TypeError, ValueError, OSError):
            return False

    def guarded_builtin_open(file, *args, **kwargs):
        if is_target(file):
            raise PermissionError("읽기 권한이 없습니다.")
        return original_builtin_open(file, *args, **kwargs)

    def guarded_io_open(file, *args, **kwargs):
        if is_target(file):
            raise PermissionError("읽기 권한이 없습니다.")
        return original_io_open(file, *args, **kwargs)

    # Windows에서도 chmod에 의존하지 않고 읽기 실패를 재현합니다.
    # pathlib.Path.open()도 io.open()을 사용합니다.
    monkeypatch.setattr(builtins, "open", guarded_builtin_open)
    monkeypatch.setattr(io, "open", guarded_io_open)

    with pytest.raises(OSError) as exc_info:
        call_loader(path)

    assert str(exc_info.value).strip()


# ── 헤더 검증 ───────────────────────────────────────────


@pytest.mark.parametrize(
    "content",
    [
        "",
        "김지현,90\n",
        "score,name\n90,김지현\n",
        "student,score\n김지현,90\n",
        "name,score,extra\n김지현,90,x\n",
        "name\n김지현,90\n",
    ],
    ids=[
        "empty-file",
        "missing-header",
        "reversed-header",
        "wrong-column-name",
        "extra-header-column",
        "missing-header-column",
    ],
)
def test_invalid_header_raises_value_error(csv_file, content):
    path = csv_file(content)

    with pytest.raises(ValueError):
        call_loader(path)


# ── 열 개수 검증 ────────────────────────────────────────


@pytest.mark.parametrize(
    "invalid_row",
    [
        "열부족",
        "열초과,70,extra",
        "열다수,70,extra,more",
    ],
)
def test_wrong_column_count_is_skipped_and_processing_continues(
    csv_file, invalid_row
):
    path = csv_file(
        "name,score\n"
        "앞정상,80\n"
        f"{invalid_row}\n"
        "뒤정상,90\n"
    )

    grades, errors = call_loader(path)

    assert grades == [("앞정상", 80.0), ("뒤정상", 90.0)]
    assert_errors(errors, [3])


# ── 점수 정상값 및 경계값 ────────────────────────────────


@pytest.mark.parametrize(
    ("score_text", "expected"),
    [
        ("0", 0.0),
        ("0.0", 0.0),
        ("0.001", 0.001),
        ("50.5", 50.5),
        ("99.999", 99.999),
        ("100", 100.0),
        ("100.0", 100.0),
    ],
)
def test_scores_inside_inclusive_range_are_accepted(
    csv_file, score_text, expected
):
    path = csv_file(f"name,score\n김지현,{score_text}\n")

    grades, errors = call_loader(path)

    assert len(grades) == 1
    assert grades[0][0] == "김지현"
    assert grades[0][1] == pytest.approx(expected)
    assert errors == []


@pytest.mark.parametrize(
    "invalid_score",
    [
        "-0.001",
        "-1",
        "100.001",
        "105",
        "1000",
        "abc",
        "구십",
        "NaN",
        "inf",
        "-inf",
    ],
)
def test_invalid_scores_are_skipped_without_clamping(
    csv_file, invalid_score
):
    path = csv_file(
        "name,score\n"
        "앞정상,20\n"
        f"제외대상,{invalid_score}\n"
        "뒤정상,80\n"
    )

    grades, errors = call_loader(path)

    assert grades == [("앞정상", 20.0), ("뒤정상", 80.0)]
    assert_errors(errors, [3])


# ── 점수 누락 ───────────────────────────────────────────


@pytest.mark.parametrize("missing_score", ["", " ", "   ", "\t", " \t "])
def test_missing_score_is_not_converted_to_zero(csv_file, missing_score):
    path = csv_file(
        "name,score\n"
        f"점수누락,{missing_score}\n"
        "실제영점,0\n"
        "뒤정상,75\n"
    )

    grades, errors = call_loader(path)

    assert grades == [("실제영점", 0.0), ("뒤정상", 75.0)]
    assert_errors(errors, [2])
    assert "누락" in error_at(errors, 2)["reason"]


def test_all_invalid_rows_return_empty_grades_with_error_records(csv_file):
    path = csv_file(
        "name,score\n"
        "누락,\n"
        "문자,abc\n"
        "범위초과,105\n"
    )

    grades, errors = call_loader(path)

    assert grades == []
    assert_errors(errors, [2, 3, 4])


# ── 중복 이름 ───────────────────────────────────────────


def test_duplicate_name_keeps_first_valid_score(csv_file):
    path = csv_file(
        "name,score\n"
        "김지현,70\n"
        "김지현,95\n"
        "김지현,80\n"
        "이민수,88\n"
    )

    grades, errors = call_loader(path)

    assert grades == [("김지현", 70.0), ("이민수", 88.0)]
    assert_errors(errors, [3, 4])
    assert all("중복" in error["reason"] for error in errors)


@pytest.mark.parametrize("invalid_score", ["", "abc", "-1", "105"])
def test_invalid_first_occurrence_does_not_reserve_name(
    csv_file, invalid_score
):
    path = csv_file(
        "name,score\n"
        f"김지현,{invalid_score}\n"
        "김지현,85\n"
        "김지현,99\n"
    )

    grades, errors = call_loader(path)

    assert grades == [("김지현", 85.0)]
    assert_errors(errors, [2, 4])
    assert "중복" in error_at(errors, 4)["reason"]


def test_zero_score_counts_as_first_valid_duplicate_entry(csv_file):
    path = csv_file(
        "name,score\n"
        "김지현,0\n"
        "김지현,100\n"
    )

    grades, errors = call_loader(path)

    assert grades == [("김지현", 0.0)]
    assert_errors(errors, [3])
    assert "중복" in error_at(errors, 3)["reason"]


# ── 제외 기록 및 복합 상황 ───────────────────────────────


def test_mixed_errors_have_correct_original_line_numbers(csv_file):
    path = csv_file(
        "name,score\n"         # 1
        "김지현,90\n"          # 2: 정상
        "열부족\n"             # 3: 열 개수 오류
        "점수누락,   \n"       # 4: 점수 누락
        "문자점수,abc\n"       # 5: 숫자 아님
        "범위초과,105\n"       # 6: 범위 초과
        "김지현,95\n"          # 7: 중복
        '"Lee, Minsu",100\n'   # 8: 정상
        "실제영점,0\n"         # 9: 정상
    )

    grades, errors = call_loader(path)

    assert grades == [
        ("김지현", 90.0),
        ("Lee, Minsu", 100.0),
        ("실제영점", 0.0),
    ]
    assert_errors(errors, [3, 4, 5, 6, 7])
    assert "누락" in error_at(errors, 4)["reason"]
    assert "중복" in error_at(errors, 7)["reason"]


def test_error_line_after_multiline_csv_name_uses_physical_line_number(
    csv_file,
):
    path = csv_file(
        "name,score\n"         # 1
        '"Kim\n'              # 2: 이름 시작
        'Jihyun",90\n'        # 3: 이름 끝
        "점수오류,105\n"      # 4: 제외
        "정상,80\n"           # 5: 정상
    )

    grades, errors = call_loader(path)

    assert grades == [("Kim\nJihyun", 90.0), ("정상", 80.0)]
    assert_errors(errors, [4])