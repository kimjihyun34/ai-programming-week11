import pandas as pd


def 정제(df):
    # 원본을 수정하지 않도록 복사본을 만든다.
    결과 = df.copy()

    # 1단계: 점수가 비어 있는 행을 삭제한다.
    결과 = 결과.dropna(subset=["점수"])
    print(f"1단계: {len(결과)}행 남음")

    # 2단계: 모든 열의 값이 같은 행은 첫 번째 행만 남긴다.
    결과 = 결과.drop_duplicates()
    print(f"2단계: {len(결과)}행 남음")

    # 3단계: 반과 과목 값의 앞뒤 공백을 제거한다.
    결과["반"] = 결과["반"].astype("string").str.strip()
    결과["과목"] = 결과["과목"].astype("string").str.strip()
    print(f"3단계: {len(결과)}행 남음")

    # 4단계: 점수가 0~100 범위의 정수인 행만 남긴다.
    점수 = pd.to_numeric(결과["점수"], errors="coerce")
    유효한_점수 = 점수.between(0, 100) & (점수 % 1 == 0)
    결과 = 결과.loc[유효한_점수].copy()
    결과["점수"] = 점수.loc[유효한_점수].astype(int)
    print(f"4단계: {len(결과)}행 남음")

    return 결과
def 반별평균(df):
    return df.groupby("반")["점수"].mean()


if __name__ == "__main__":
    원본 = pd.read_csv("scores_2026.csv")
    print(f"시작: {len(원본)}행")
    정제본 = 정제(원본)

    # B. 수학 필터링
    수학 = 정제본[정제본["과목"] == "수학"]
    print(f"수학: {len(수학)}행")

    # C. 반별 평균과 과목 × 반 평균
    print("\n[반별 평균]")
    print(반별평균(정제본))

    print("\n[과목 × 반 평균]")
    과목반평균 = 정제본.groupby(["과목", "반"])["점수"].mean()
    print(과목반평균.unstack("반"))
        # D. 반별 통계
    통계표 = (
        정제본.groupby("반")["점수"]
        .agg(개수="count", 평균="mean", 중앙값="median", 최댓값="max")
        .round(2)
    )
    print("\n[반별 통계]")
    print(통계표.to_string(formatters={
        "평균": "{:.2f}".format,
        "중앙값": "{:.2f}".format,
        "최댓값": "{:.2f}".format,
    }))
        # 검산: 반별로 묶기 전후의 점수 합계와 개수 비교
    반별점수 = 정제본.groupby("반")["점수"]
    print("\n[검산]")
    print("반별 점수 합계의 합:", 반별점수.sum().sum())
    print("전체 점수 합계:", 정제본["점수"].sum())
    print("반별 점수 개수의 합:", 반별점수.count().sum())
    print("정제본 전체 행 수:", len(정제본))

    # 스팟 체크: 1반 수학 점수 목록 출력
    일반_수학_점수 = 정제본.loc[
        (정제본["반"] == "1반") & (정제본["과목"] == "수학"), "점수"
    ]
    print("1반 수학 점수 목록:", 일반_수학_점수.tolist())