# test_ai_A.py
# 테스트 대상 코드를 scores.py로 저장한 뒤 실행: pytest -q test_ai_A.py

import pytest

from scores import load_scores


@pytest.fixture
def make_csv(tmp_path):
    def _make_csv(content, encoding="utf-8"):
        path = tmp_path / "scores.csv"
        path.write_bytes(content.encode(encoding))
        return path

    return _make_csv


def test_load_scores_normal_rows(make_csv):
    path = make_csv(
        "name,score\n"
        "김지현,85\n"
        "홍길동,100\n"
        "이영희,72\n"
    )

    assert load_scores(path) == (
        [("김지현", 85), ("홍길동", 100), ("이영희", 72)],
        [],
    )


@pytest.mark.parametrize("score", [0, 1, 99, 100])
def test_load_scores_accepts_boundary_scores(make_csv, score):
    path = make_csv(f"name,score\n김지현,{score}\n")

    assert load_scores(path) == ([("김지현", score)], [])


@pytest.mark.parametrize("score", [-1, 101, -1000, 1000])
def test_load_scores_skips_out_of_range_scores(make_csv, score):
    path = make_csv(f"name,score\n김지현,{score}\n")

    assert load_scores(path) == (
        [],
        [(2, f"김지현,{score}", "점수가 0~100 밖")],
    )


@pytest.mark.parametrize(
    ("row", "reason"),
    [
        ("김지현", "열 개수가 2가 아님"),
        ("김지현,80,추가", "열 개수가 2가 아님"),
        (",", "이름이 비어 있음"),
        (",80", "이름이 비어 있음"),
        ("   ,80", "이름이 비어 있음"),
        ("김지현,", "점수가 비어 있음"),
        ("김지현,   ", "점수가 비어 있음"),
        ("김지현,abc", "점수가 정수가 아님"),
        ("김지현,80.0", "점수가 정수가 아님"),
        ("김지현,1e2", "점수가 정수가 아님"),
    ],
)
def test_load_scores_records_invalid_rows(make_csv, row, reason):
    path = make_csv(f"name,score\n{row}\n")

    assert load_scores(path) == ([], [(2, row, reason)])


def test_load_scores_strips_surrounding_whitespace(make_csv):
    path = make_csv("name,score\n  김지현  , \t85 \t\n")

    assert load_scores(path) == ([("김지현", 85)], [])


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("+85", 85),
        ("085", 85),
        ("-0", 0),
    ],
)
def test_load_scores_accepts_integer_formats(make_csv, raw, expected):
    path = make_csv(f"name,score\n김지현,{raw}\n")

    assert load_scores(path) == ([("김지현", expected)], [])


def test_load_scores_preserves_original_whitespace_in_skipped_record(make_csv):
    path = make_csv("name,score\n  김지현  ,  abc  \n")

    assert load_scores(path) == (
        [],
        [(2, "  김지현  ,  abc  ", "점수가 정수가 아님")],
    )


def test_load_scores_empty_file(make_csv):
    path = make_csv("")

    assert load_scores(path) == ([], [])


def test_load_scores_header_only(make_csv):
    path = make_csv("name,score\n")

    assert load_scores(path) == ([], [])


def test_load_scores_always_skips_first_record(make_csv):
    path = make_csv("김지현,85\n홍길동,90\n")

    assert load_scores(path) == ([("홍길동", 90)], [])


def test_load_scores_ignores_empty_lines_but_counts_them(make_csv):
    path = make_csv(
        "name,score\n"   # 1
        "\n"             # 2: 빈 줄
        "김지현,85\n"    # 3
        "\n"             # 4: 빈 줄
        "홍길동,abc\n"   # 5
        "\n"             # 6: 빈 줄
    )

    assert load_scores(path) == (
        [("김지현", 85)],
        [(5, "홍길동,abc", "점수가 정수가 아님")],
    )


def test_load_scores_whitespace_only_line_is_not_empty_row(make_csv):
    path = make_csv("name,score\n   \n")

    assert load_scores(path) == (
        [],
        [(2, "   ", "열 개수가 2가 아님")],
    )


def test_load_scores_mixed_valid_and_invalid_rows(make_csv):
    path = make_csv(
        "name,score\n"
        "김지현,0\n"
        ",50\n"
        "홍길동,100\n"
        "이영희,101\n"
        "박민수,abc\n"
        "최유진,75\n"
    )

    assert load_scores(path) == (
        [("김지현", 0), ("홍길동", 100), ("최유진", 75)],
        [
            (3, ",50", "이름이 비어 있음"),
            (5, "이영희,101", "점수가 0~100 밖"),
            (6, "박민수,abc", "점수가 정수가 아님"),
        ],
    )


def test_load_scores_preserves_duplicate_names_and_order(make_csv):
    path = make_csv("name,score\n김지현,80\n김지현,90\n")

    assert load_scores(path) == (
        [("김지현", 80), ("김지현", 90)],
        [],
    )


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig"])
def test_load_scores_supports_utf8_with_and_without_bom(make_csv, encoding):
    path = make_csv("이름,점수\n김지현,85\n", encoding=encoding)

    assert load_scores(path) == ([("김지현", 85)], [])


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_load_scores_supports_line_endings(make_csv, newline):
    path = make_csv(
        newline.join(["name,score", "김지현,85", "홍길동,90", ""])
    )

    assert load_scores(path) == (
        [("김지현", 85), ("홍길동", 90)],
        [],
    )


def test_load_scores_accepts_missing_final_newline(make_csv):
    path = make_csv("name,score\n김지현,85")

    assert load_scores(path) == ([("김지현", 85)], [])


def test_load_scores_accepts_quoted_fields(make_csv):
    path = make_csv('name,score\n"김,지현","85"\n')

    assert load_scores(path) == ([("김,지현", 85)], [])


def test_load_scores_skipped_original_is_joined_parsed_fields(make_csv):
    path = make_csv('name,score\n"김,지현","abc"\n')

    # 원본 CSV 문자열이 아니라 파싱한 필드를 ","로 연결한 값이 기록된다.
    assert load_scores(path) == (
        [],
        [(2, "김,지현,abc", "점수가 정수가 아님")],
    )


def test_load_scores_multiline_field_counts_csv_records(make_csv):
    path = make_csv(
        "name,score\n"
        '"김\n지현",85\n'
        "홍길동,abc\n"
    )

    # line_no는 물리적 행 번호가 아니라 csv.reader가 반환한 레코드 순번이다.
    assert load_scores(path) == (
        [("김\n지현", 85)],
        [(3, "홍길동,abc", "점수가 정수가 아님")],
    )


def test_load_scores_accepts_string_path(make_csv):
    path = make_csv("name,score\n김지현,85\n")

    assert load_scores(str(path)) == ([("김지현", 85)], [])


def test_load_scores_missing_file_raises_file_not_found(tmp_path):
    path = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        load_scores(path)


def test_load_scores_permission_error_is_propagated(tmp_path, monkeypatch):
    def deny_open(*args, **kwargs):
        raise PermissionError("접근 권한이 없습니다.")

    monkeypatch.setattr("builtins.open", deny_open)

    with pytest.raises(PermissionError, match="접근 권한"):
        load_scores(tmp_path / "scores.csv")


def test_load_scores_invalid_utf8_raises_unicode_decode_error(tmp_path):
    path = tmp_path / "invalid_encoding.csv"
    path.write_bytes(b"name,score\n\xff,85\n")

    with pytest.raises(UnicodeDecodeError):
        load_scores(path)