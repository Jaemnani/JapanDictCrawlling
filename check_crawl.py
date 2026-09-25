"""크롤링 결과 xlsx 가 완전한지 검증.

  python check_crawl.py naver_jlpt_words_allclass.xlsx
  python check_crawl.py naver_jlpt_words_allclass.xlsx --translations allclass_translator.xlsx
  python check_crawl.py naver_jlpt_words_allclass.xlsx --probe      # 네이버에 실제로 남은 페이지가 있는지 확인 (selenium)

오프라인 검사:
  - 레벨별 단어 수
  - 빈 칸 / 줄 밀림(page_text 를 3줄 단위로 자르면서 어긋난 행) 의심 행
  - 중복 행
  - 번역 파일이 주어지면 번역 누락 단어 수
--probe:
  - 목록 상단의 "N급, 전체, 3,246건" 총 개수와 크롤링된 개수(중복 제외)를 비교
  - 레벨별로 (크롤링된 개수 / 페이지당 개수) 다음 페이지를 명시적 대기 후 열어봐서
    단어가 더 있으면 크롤링이 중간에 끊겼거나 페이지가 누락된 것.
"""
import argparse
import math
import re
import sys

from wordbook_io import HANGUL_RE, KANA_RE, KANJI_RE, load_crawl, load_translations

LIST_URL = "https://ja.dict.naver.com/#/jlpt/list?level={level}&part=allClass&page={page}"
LIST_SELECTOR = "#my_jlpt_list_template"
TOTAL_RE = re.compile(r"급,\s*전체,\s*([\d,]+)\s*건")


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

    # 크롤러는 텍스트를 3줄씩 끊어 (단어, ?, 뜻) 으로 가정한다. 한 항목이라도 줄 수가 다르면
    # 이후 행이 모두 밀려서 단어 칸에 한글이 들어가거나 뜻 칸에 한글이 없어진다.
    bad_word = ~df.japanese.str.contains(KANA_RE) & ~df.japanese.str.contains(KANJI_RE)
    bad_word |= df.japanese.str.contains(HANGUL_RE)
    bad_mean = ~df.meaning.str.contains(HANGUL_RE)
    shifted = df[(bad_word | bad_mean) & (df.japanese != "")]
    if len(shifted):
        problems += len(shifted)
        print(f"\n[줄 밀림 의심] {len(shifted)} 행 (단어 칸에 일본어가 없거나, 뜻 칸에 한글이 없음)")
        print(shifted.head(20).to_string(index=False))

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


def probe(df, timeout):
    from selenium import webdriver
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait

    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=opts)

    def count_entries(level, page):
        driver.get(LIST_URL.format(level=level, page=page))
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: d.find_element(By.CSS_SELECTOR, LIST_SELECTOR).text.strip() != ""
            )
        except TimeoutException:
            return 0
        text = driver.find_element(By.CSS_SELECTOR, LIST_SELECTOR).text
        return len(text.split("\n")) // 3

    def site_total():
        m = TOTAL_RE.search(driver.find_element(By.TAG_NAME, "body").text)
        return int(m.group(1).replace(",", "")) if m else None

    unique = df.drop_duplicates(["japanese", "hanmoon", "level", "pos", "meaning"])
    incomplete = 0
    try:
        print("\n[probe] 네이버 JLPT 목록과 비교")
        for level, n in unique.groupby("level").size().items():
            page_size = count_entries(level, 1)
            if page_size == 0:
                print(f"  N{level}: 1페이지를 읽지 못함 (선택자/사이트 구조 변경 확인 필요)")
                incomplete += 1
                continue
            total = site_total()
            if total is None:
                print(f"  N{level}: 사이트 총 개수를 찾지 못함")
            elif total != n:
                incomplete += 1
                print(f"  N{level}: 사이트 {total} 건 / 크롤링 {n} 건 -> {total - n:+d} 차이")
            else:
                print(f"  N{level}: 사이트 {total} 건 / 크롤링 {n} 건 일치")
            last = math.ceil(n / page_size)
            after = count_entries(level, last + 1)
            status = "OK" if after == 0 else f"미완료: {last + 1} 페이지에 {after} 개 더 있음"
            if after:
                incomplete += 1
            print(f"  N{level}: 크롤링 {n} 개, 페이지당 {page_size} 개 -> 마지막 {last} 페이지 / {status}")
    finally:
        driver.quit()
    return incomplete


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("crawl_xlsx")
    ap.add_argument("--translations", help="papago_translator.py 결과 xlsx")
    ap.add_argument("--probe", action="store_true", help="selenium 으로 네이버에 남은 페이지 확인")
    ap.add_argument("--timeout", type=float, default=10, help="--probe 페이지 로딩 대기 초")
    args = ap.parse_args()

    df = load_crawl(args.crawl_xlsx)
    problems = offline_checks(df)
    if args.translations:
        problems += translation_checks(df, load_translations(args.translations))
    if args.probe:
        problems += probe(df, args.timeout)

    print("\n결과:", "이상 없음" if problems == 0 else f"확인 필요 항목 {problems} 건")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
