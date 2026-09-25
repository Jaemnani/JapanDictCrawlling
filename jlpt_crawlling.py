"""네이버 일본어사전 JLPT 등급별 단어 크롤링 (JSON API).

  python jlpt_crawlling.py                  # N1~N5 전체 + 품사
  python jlpt_crawlling.py --levels 4,5 --no-parts

화면(https://ja.dict.naver.com/#/jlpt/list?level=1)이 쓰는 API 를 그대로 호출한다.
  GET https://ja.dict.naver.com/api/jako/getJLPTList?level=1&part=allClass&page=1
  -> {"m_total": 3246, "m_pageSize": 10, "m_totalPage": 325, "m_items": [{entry, pron, means[], parts[], ...}]}

- 레벨별로 part=allClass 를 끝 페이지까지 받고, 개수가 m_total 과 다르면 실패로 처리한다.
  페이지 경계에서 순서가 흔들려 생기는 중복/누락은 해당 페이지를 다시 받아 메운다.
- 품사는 allClass 응답에 없으므로(parts=null) 품사별(part=명사, 동사, ...) 목록을 한 번 더 받아서
  entry_id 기준으로 붙인다. 한 단어가 여러 품사에 속할 수 있다.

출력:
  naver_jlpt_words.xlsx   japanese, Hanmoon, Level, Class, Mean, entry_id, origin_entry_id, RefMean
                          (Mean 은 뜻이 여러 개면 줄바꿈으로 구분. 뜻이 '→あとしまつ' 같은 참조뿐이면
                           RefMean 에 참조 대상의 뜻을 채운다)
  naver_jlpt_raw.json     API 원본 항목 (발음 파일 URL 제외)
"""
import argparse
import html
import json
import re
import sys
import time
from urllib.error import URLError
from urllib.parse import unquote, urlencode
from urllib.request import Request, urlopen

import pandas as pd

API = "https://ja.dict.naver.com/api/jako/getJLPTList"
SEARCH_API = "https://ja.dict.naver.com/api3/jako/search"
LEVELS = ["1", "2", "3", "4", "5"]
PARTS = ["명사", "대명사", "동사", "조사", "형용사", "접사", "부사", "감동사", "형용동사", "기타"]
HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://ja.dict.naver.com/"}


def fetch(level, part, page, retries=5):
    return get_json(f"{API}?{urlencode({'level': level, 'part': part, 'page': page})}", retries)


def get_json(url, retries=5):
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


def crawl_list(level, part, delay, repair_rounds=10):
    """한 목록(level, part)을 끝까지 받아 entry_id 기준 고유 항목을 사이트 순서대로 반환."""
    first = fetch(level, part, 1)
    total, pages = first["m_total"], first["m_totalPage"]
    found = {}  # entry_id -> ((page, idx), item)
    by_page = {}

    def add(page, items):
        by_page[page] = items
        for i, it in enumerate(items):
            found.setdefault(it["entry_id"], ((page, i), it))

    add(1, first["m_items"])
    for page in range(2, pages + 1):
        time.sleep(delay)
        add(page, fetch(level, part, page)["m_items"])
        print(f"\r  N{level} {part}: {page}/{pages} 페이지", end="", flush=True)

    # 정렬 기준이 같은 단어들은 요청마다 순서가 바뀌어서, 페이지 경계에서 한 단어가 두 번 나오고
    # 다른 단어 하나가 빠질 수 있다. 중복이 나온 페이지 주변을 다시 받아서 빠진 단어를 채운다.
    suspects = set()
    rounds = 0
    while len(found) < total and rounds < repair_rounds:
        rounds += 1
        pages_of = {}
        for p, items in by_page.items():
            for it in items:
                pages_of.setdefault(it["entry_id"], set()).add(p)
        suspects |= {q for ps in pages_of.values() if len(ps) > 1 for p in ps for q in (p - 1, p, p + 1) if 1 <= q <= pages}
        if not suspects:
            break
        for p in sorted(suspects):
            time.sleep(delay)
            add(p, fetch(level, part, p)["m_items"])
    items = [it for _, it in sorted(found.values(), key=lambda v: v[0])]
    repaired = f" (경계 페이지 재요청 {rounds}회)" if rounds else ""
    print(f"\r  N{level} {part}: {len(items)}/{total} 건{repaired}" + " " * 20)
    return total, items


TAG_RE = re.compile(r"<[^>]+>")
REF_NUM_RE = re.compile(r"\d+$")  # →おおばん2 처럼 동음이의어 번호


def search_meanings(word, limit=3):
    """사전 검색 API 에서 표제어가 정확히 일치하는 첫 항목의 뜻."""
    data = get_json(f"{SEARCH_API}?{urlencode({'query': word})}")
    items = data["searchResultMap"]["searchResultListMap"]["WORD"]["items"]
    for it in items:
        if it.get("handleEntry") != word or not str(it.get("matchType", "")).startswith("exact"):
            continue
        means = [
            html.unescape(TAG_RE.sub("", m.get("value") or "")).strip()
            for mc in it.get("meansCollector") or []
            for m in mc.get("means") or []
        ]
        means = [m for m in means if m]
        if means:
            return means[:limit]
    return []


def resolve_refs(rows, delay):
    """뜻이 '→あとしまつ' 같은 참조뿐인 단어에 참조 대상의 뜻을 RefMean 으로 채운다.

    대상이 JLPT 목록 안에 있으면 그 뜻을, 없으면 사전 검색 결과를 쓴다. Mean 원문은 그대로 둔다.
    """
    own = {}
    for r in rows:
        ms = r["Mean"].split("\n")
        if r["Mean"] and not all(m.startswith(("→", "⇒")) for m in ms):
            own.setdefault(r["japanese"], ms)
    unresolved = 0
    for r in rows:
        ms = r["Mean"].split("\n")
        if not r["Mean"] or not all(m.startswith(("→", "⇒")) for m in ms):
            continue
        resolved = []
        for m in ms:
            target = REF_NUM_RE.sub("", m.lstrip("→⇒").strip().rstrip("。"))
            means = own.get(target)
            if means is None:
                time.sleep(delay)
                means = search_meanings(target)
            if means:
                resolved.append(f"(= {target}) {means[0]}")
                resolved += means[1:]
        r["RefMean"] = "\n".join(resolved)
        unresolved += not resolved
    return unresolved


def crawl(levels, with_parts, delay):
    rows, raw, problems = [], [], []
    for level in levels:
        total, items = crawl_list(level, "allClass", delay)
        ids = [it["entry_id"] for it in items]
        if len(items) != total:
            problems.append(f"N{level}: 사이트 {total} 건 / 수집 {len(items)} 건")

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

        for it in items:
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
                "RefMean": "",
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
    unresolved = resolve_refs(rows, args.delay)
    n_refs = sum(1 for r in rows if r["RefMean"]) + unresolved
    print(f"참조 뜻(→) 단어 {n_refs} 개 중 {n_refs - unresolved} 개 채움")

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
