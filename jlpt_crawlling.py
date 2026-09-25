"""네이버 일본어사전 JLPT 등급별 단어 크롤링 (JSON API).

  python jlpt_crawlling.py                  # N1~N5 전체 + 품사
  python jlpt_crawlling.py --levels 4,5 --no-parts

화면(https://ja.dict.naver.com/#/jlpt/list?level=1)이 쓰는 API 를 그대로 호출한다.
  GET https://ja.dict.naver.com/api/jako/getJLPTList?level=1&part=allClass&page=1
  -> {"m_total": 3246, "m_pageSize": 10, "m_totalPage": 325, "m_items": [{entry, pron, means[], parts[], ...}]}

- 레벨별로 part=allClass 를 끝 페이지까지 받고, 개수가 m_total 과 다르면 실패로 처리한다.
- 품사는 allClass 응답에 없으므로(parts=null) 품사별(part=명사, 동사, ...) 목록을 한 번 더 받아서
  entry_id 기준으로 붙인다. 한 단어가 여러 품사에 속할 수 있다.

출력:
  naver_jlpt_words.xlsx   japanese, Hanmoon, Level, Class, Mean, entry_id, origin_entry_id
                          (Mean 은 뜻이 여러 개면 줄바꿈으로 구분)
  naver_jlpt_raw.json     API 원본 항목 (발음 파일 URL 제외)
"""
import argparse
import json
import sys
import time
from urllib.error import URLError
from urllib.parse import unquote, urlencode
from urllib.request import Request, urlopen

import pandas as pd

API = "https://ja.dict.naver.com/api/jako/getJLPTList"
LEVELS = ["1", "2", "3", "4", "5"]
PARTS = ["명사", "대명사", "동사", "조사", "형용사", "접사", "부사", "감동사", "형용동사", "기타"]
HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://ja.dict.naver.com/"}


def fetch(level, part, page, retries=5):
    url = f"{API}?{urlencode({'level': level, 'part': part, 'page': page})}"
    for attempt in range(retries):
        try:
            with urlopen(Request(url, headers=HEADERS), timeout=20) as res:
                return json.load(res)
        except (URLError, TimeoutError, json.JSONDecodeError) as e:
            if attempt == retries - 1:
                raise
            wait = 2 ** attempt
            print(f"  재시도 {attempt + 1}/{retries - 1} ({e.__class__.__name__}), {wait}s 대기", file=sys.stderr)
            time.sleep(wait)


def crawl_list(level, part, delay):
    first = fetch(level, part, 1)
    total, pages = first["m_total"], first["m_totalPage"]
    items = list(first["m_items"])
    for page in range(2, pages + 1):
        time.sleep(delay)
        items += fetch(level, part, page)["m_items"]
        print(f"\r  N{level} {part}: {page}/{pages} 페이지", end="", flush=True)
    print(f"\r  N{level} {part}: {len(items)}/{total} 건" + " " * 20)
    return total, items


def crawl(levels, with_parts, delay):
    rows, raw, problems = [], [], []
    for level in levels:
        total, items = crawl_list(level, "allClass", delay)
        ids = [it["entry_id"] for it in items]
        if len(items) != total or len(set(ids)) != total:
            problems.append(f"N{level}: 사이트 {total} 건 / 수집 {len(items)} 건 (고유 {len(set(ids))} 건)")

        parts_by_id = {}
        if with_parts:
            for part in PARTS:
                part_total, part_items = crawl_list(level, part, delay)
                if len(part_items) != part_total:
                    problems.append(f"N{level} {part}: 사이트 {part_total} 건 / 수집 {len(part_items)} 건")
                for it in part_items:
                    parts_by_id.setdefault(it["entry_id"], set()).update(it.get("parts") or [part])
            no_part = sum(1 for i in ids if i not in parts_by_id)
            if no_part:
                print(f"  N{level}: 품사 정보 없는 단어 {no_part} 개")

        seen = set()
        for it in items:
            if it["entry_id"] in seen:
                continue
            seen.add(it["entry_id"])
            parts = sorted(parts_by_id.get(it["entry_id"], ()), key=lambda p: PARTS.index(p) if p in PARTS else 99)
            rows.append({
                # entry 가 퍼센트 인코딩돼서 오는 경우가 있다 (show_entry 는 あ-う 처럼 어간 구분 '-' 가 섞여 있음)
                "japanese": unquote(it["entry"]),
                "Hanmoon": it.get("pron") or "",
                "Level": level,
                "Class": ", ".join(parts),
                "Mean": "\n".join(m.strip() for m in it.get("means") or [] if m and m.strip()),
                "entry_id": it["entry_id"],
                "origin_entry_id": it.get("origin_entry_id") or "",
            })
            raw.append({k: v for k, v in it.items() if k != "pron_file"} | {"entry": unquote(it["entry"]), "parts": parts})
    return rows, raw, problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--levels", default=",".join(LEVELS), help="쉼표 구분 (기본 1,2,3,4,5)")
    ap.add_argument("--no-parts", action="store_true", help="품사 수집 생략 (요청 수 약 절반)")
    ap.add_argument("--delay", type=float, default=0.2, help="요청 간격(초)")
    ap.add_argument("--out", default="naver_jlpt_words.xlsx")
    ap.add_argument("--raw", default="naver_jlpt_raw.json")
    args = ap.parse_args()

    levels = [l.strip() for l in args.levels.split(",") if l.strip()]
    rows, raw, problems = crawl(levels, not args.no_parts, args.delay)

    pd.DataFrame(rows).to_excel(args.out, index=False)
    with open(args.raw, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=1)

    print(f"\n{len(rows)} 단어 -> {args.out}, {args.raw}")
    if problems:
        print("개수 불일치:\n  " + "\n  ".join(problems))
        sys.exit(1)
    print("모든 레벨이 사이트 총 건수와 일치")


if __name__ == "__main__":
    main()
