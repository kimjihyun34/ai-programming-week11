import pytest
from load_scores import load_scores
from helpers import 쓰기


def test_정상_파일을_읽는다():
    kept, skipped = load_scores("scores.csv")
    assert len(kept) == 5


def test_없는_파일이면_오류가_난다():
    with pytest.raises(FileNotFoundError):
        load_scores("없는파일.csv")


def test_헤더만_있으면_빈_결과():
    kept, skipped = load_scores("empty.csv")
    assert kept == []
    assert skipped == []
    from helpers import 쓰기


@pytest.mark.parametrize("점수, 유효한가", [
    (-1, False),
    (0, True),
    (1, True),
    (99, True),
    (100, True),
    (101, False),
])
def test_점수_경계값(점수, 유효한가):
    쓰기("임시.csv", 점수)
    kept, skipped = load_scores("임시.csv")

    if 유효한가:
        assert len(kept) == 1
        assert skipped == []
    else:
        assert kept == []
        assert len(skipped) == 1
    
def test_빈_줄은_건너뛴다(tmp_path):
    with open("empty.csv", encoding="utf-8-sig") as f:
        header = f.readline().rstrip("\r\n")

    path = tmp_path / "blank_lines.csv"
    path.write_text(
        header + "\n김하나,88\n\n윤보람,64\n\n",
        encoding="utf-8",
    )

    kept, skipped = load_scores(str(path))

    assert kept == [("김하나", 88), ("윤보람", 64)]
    assert skipped == []


def test_이름에_쉼표가_있어도_읽는다(tmp_path):
    with open("empty.csv", encoding="utf-8-sig") as f:
        header = f.readline().rstrip("\r\n")

    path = tmp_path / "comma_name.csv"
    path.write_text(
        header + '\n"김, 하나",88\n',
        encoding="utf-8",
    )

    kept, skipped = load_scores(str(path))

    assert kept == [("김, 하나", 88)]
    assert skipped == []
def test_이름이_비어_있으면_건너뛴다(tmp_path):
    path = tmp_path / "empty_name.csv"
    path.write_text("이름,점수\n,88\n", encoding="utf-8")

    kept, skipped = load_scores(str(path))

    assert kept == []
    assert skipped == [(2, ",88", "이름이 비어 있음")]


def test_직접_실행하면_결과를_출력한다(tmp_path, monkeypatch, capsys):
    import runpy
    from pathlib import Path

    script = Path(__file__).resolve().with_name("load_scores.py")
    path = tmp_path / "output_scores.csv"
    path.write_text(
        "이름,점수\n김하나,88\n,77\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("sys.argv", [str(script), str(path)])
    runpy.run_path(str(script), run_name="__main__")

    output = capsys.readouterr().out

    assert "읽은 줄 : 1개" in output
    assert "김하나 88" in output
    assert "건너뛴 줄 : 1개" in output
    assert "이름이 비어 있음" in output