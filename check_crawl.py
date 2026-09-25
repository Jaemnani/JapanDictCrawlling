"""크롤링 결과 xlsx 가 완전한지 검증.

  python check_crawl.py naver_jlpt_words_allclass.xlsx
  python check_crawl.py naver_jlpt_words_allclass.xlsx --translations allclass_translator.xlsx
  python check_crawl.py naver_jlpt_words_allclass.xlsx --probe      # 네이버 사이트 총 건수와 비교

오프라인 검사:
  - 레벨별 단어 수
  - 빈 칸 / 줄 밀림(page_text 를 3줄 단위로 자르면서 어긋난 행) 의심 행
  - 중복 행
  - 번역 파일이 주어지면 번역 누락 단어 수
--probe:
  - 레벨별 사이트 총 건수(목록 상단 "1급, 전체, 3,246건", API 의 m_total)와 크롤링 개수(중복 제외)를 비교
"""
import argparse
import sys

from wordbook_io import HANGUL_RE, KANA_RE, KANJI_RE, load_crawl, load_translations

def offline_checks(df):
    problems = 0
    print(f"총 {len(df)} 행")
    print("\n[레벨별 개수]")
    for level, n in df.groupby("level").size().items():
        print(f"  N{level}: {n}")

    empty = df[(df.japanese == "") | (df.meaning == "")]
    if len(empty):
        problems += len(empty)
        print(f"\n[빈 칸] {len(empty)} 행")
        print(empty.head(20).to_string(index=False))

    # 예전 셀레니움 크롤러는 텍스트를 3줄씩 끊어 (단어, ?, 뜻) 으로 가정했다. 뜻이 여러 줄인 항목이 있으면
    # 이후 행이 모두 밀려서 단어 칸에 한글이 들어가거나 뜻 칸에 한글이 없어진다.
    bad_word = ~df.japanese.str.contains(KANA_RE) & ~df.japanese.str.contains(KANJI_RE)
    bad_word |= df.japanese.str.contains(HANGUL_RE)
    ref_only = df.meaning.map(lambda m: bool(m) and all(x.strip().startswith(("→", "⇒")) for x in m.split("\n")))
    bad_mean = ~df.meaning.str.contains(HANGUL_RE) & ~ref_only
    shifted = df[(bad_word | bad_mean) & (df.japanese != "")]
    if len(shifted):
        problems += len(shifted)
        print(f"\n[줄 밀림 의심] {len(shifted)} 행 (단어 칸에 일본어가 없거나, 뜻 칸에 한글이 없음)")
        print(shifted.head(20).to_string(index=False))

    if ref_only.any():
        unresolved = df[ref_only & (df.ref_meaning == "")]
        print(f"\n[참고] 뜻이 '→다른단어' 참조뿐인 단어 {int(ref_only.sum())} 개, 그중 참조 뜻(RefMean)이 없는 단어 {len(unresolved)} 개")
        if len(unresolved):
            print(unresolved[["japanese", "hanmoon", "level", "meaning"]].head(10).to_string(index=False))

    key = ["japanese", "hanmoon", "level", "pos", "meaning"]
    dup = df[df.duplicated(key, keep=False)]
    if len(dup):
        problems += len(dup)
        print(f"\n[완전 중복] {len(dup)} 행 (같은 페이지를 두 번 저장했을 가능성)")
        print(dup.head(20).to_string(index=False))

    multi = df.groupby(["japanese", "hanmoon"])["level"].nunique()
    multi = multi[multi > 1]
    if len(multi):
        print(f"\n[참고] 여러 레벨에 동시에 등장하는 단어 {len(multi)} 개 (네이버 원본 특성일 수 있음)")
    return problems


def translation_checks(df, tr):
    if "ko" not in tr.columns or "ja" not in tr.columns:
        print("\n[번역] ja/ko 컬럼을 찾지 못해 건너뜀")
        return 0
    done = set(zip(tr.ja, tr.ko))
    missing = df[[(j, m) not in done for j, m in zip(df.japanese, df.meaning)]]
    empty_en = int((tr["en"] == "").sum()) if "en" in tr.columns else 0
    print(f"\n[번역] 번역 파일 {len(tr)} 행 / 번역 누락 단어 {len(missing)} 개 / 영어 빈 칸 {empty_en} 행")
    if len(missing):
        print(missing.head(10).to_string(index=False))
    return len(missing)


def probe(df):
    from jlpt_crawlling import fetch

    unique = df.drop_duplicates(["japanese", "hanmoon", "level", "pos", "meaning"])
    incomplete = 0
    print("\n[probe] 네이버 JLPT 목록 총 건수와 비교")
    for level, n in unique.groupby("level").size().items():
        total = fetch(level, "allClass", 1)["m_total"]
        if total != n:
            incomplete += 1
            print(f"  N{level}: 사이트 {total} 건 / 크롤링 {n} 건 -> {total - n:+d} 차이")
        else:
            print(f"  N{level}: 사이트 {total} 건 / 크롤링 {n} 건 일치")
    return incomplete


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("crawl_xlsx")
    ap.add_argument("--translations", help="papago_translator.py 결과 xlsx")
    ap.add_argument("--probe", action="store_true", help="네이버 사이트 총 건수와 비교")
    args = ap.parse_args()

    df = load_crawl(args.crawl_xlsx)
    problems = offline_checks(df)
    if args.translations:
        problems += translation_checks(df, load_translations(args.translations))
    if args.probe:
        problems += probe(df)

    print("\n결과:", "이상 없음" if problems == 0 else f"확인 필요 항목 {problems} 건")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
