"""크롤링 결과 xlsx -> iOS 앱 번들용 words.json.

  python export_app_data.py naver_jlpt_words.xlsx
  -> ios/JLPTVocab/Resources/words.json

- 단어 단위 합치기·참조 뜻 처리는 build_wordbook.build_entries 와 같다.
- order: 레벨 안에서 고정 시드로 섞은 신규 학습 순서. 네이버 목록은 오십음 순이라
  발음이 비슷한 단어가 연달아 나오는데, 비슷한 단어를 같이 배우면 간섭이 생기므로 섞는다
  (Tinkham 1993, Waring 1997, Erten & Tekin 2008). 섞은 뒤에도 가까운 순서(SIMILAR_WINDOW)
  안에 읽기가 같거나 한자를 공유하는 단어가 오지 않게 다시 배치한다 (형태 유사어 혼동: Laufer 1988, Ishii 2015).
- hanjaKo: 한자 표기의 한국 한자음 (経済 -> 경제). hanja 패키지가 없으면 비운다.
"""
import argparse
import json
import os
import random
from datetime import datetime, timezone

from build_wordbook import build_entries
from wordbook_io import KANJI_RE, load_crawl

DEFAULT_OUT = os.path.join("ios", "JLPTVocab", "Resources", "words.json")
SIMILAR_WINDOW = 20  # 하루 신규 단어 수 기본값과 맞춤
SCAN_LIMIT = 300

try:
    import hanja
except ImportError:  # 선택 의존성
    hanja = None


def hanja_korean(word):
    """한자 표기 -> 한국 한자음. 한자가 없거나 변환이 안 되면 ""."""
    if hanja is None:
        return ""
    first = word.replace("∙", "·").split("·")[0]
    kanji = [ch for ch in first if KANJI_RE.match(ch) and ch != "々"]
    if not kanji:
        return ""
    readings = [hanja.translate(ch, "substitution") for ch in kanji]
    if any(r == ch for r, ch in zip(readings, kanji)):  # 변환 못 한 글자
        return ""
    if len(kanji) == len(first):  # 전부 한자인 한자어: 経済 -> 경제
        return "".join(readings)
    return " ".join(f"{ch}({r})" for ch, r in zip(kanji, readings))  # 会う -> 会(회)


def similarity_keys(e):
    """비슷한 단어 판정용 키: 읽기, 표기, 표기에 든 한자 각각."""
    keys = {("r", e.reading or e.word)}
    keys.update(("k", ch) for ch in e.word if KANJI_RE.match(ch) and ch != "々")
    return keys


def spread_similar(items, window=SIMILAR_WINDOW):
    """섞인 순서를 유지하되, 최근 window 개와 키가 겹치는 단어는 뒤로 미룬다."""
    remaining = list(items)
    out, recent_keys = [], []
    while remaining:
        taken = set().union(*recent_keys[-window:]) if recent_keys else set()
        pick = next((i for i, e in enumerate(remaining[:SCAN_LIMIT]) if not (similarity_keys(e) & taken)), 0)
        e = remaining.pop(pick)
        out.append(e)
        recent_keys.append(similarity_keys(e))
    return out


def conflicts(items, window=SIMILAR_WINDOW):
    keys = [similarity_keys(e) for e in items]
    return sum(1 for i, k in enumerate(keys) if k & set().union(*keys[max(0, i - window):i]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("crawl_xlsx")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--seed", type=int, default=20260926)
    args = ap.parse_args()

    entries = build_entries(load_crawl(args.crawl_xlsx))
    rng = random.Random(args.seed)
    words = []
    for level in sorted(entries["level"].unique(), key=str):
        sub = list(entries[entries["level"] == level].itertuples(index=False))
        rng.shuffle(sub)
        before = conflicts(sub)
        sub = spread_similar(sub)
        print(f"  N{level}: 가까운 순서의 유사 단어 {before} -> {conflicts(sub)}")
        for o, e in enumerate(sub):
            words.append({
                "id": f"{level}|{e.word}|{e.reading}",
                "level": int(level),
                "word": e.word,
                "reading": e.reading,
                "pos": list(e.pos),
                "meanings": list(e.meanings),
                "hanjaKo": hanja_korean(e.word),
                "order": o,
            })

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({
            "version": 1,
            "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "words": words,
        }, f, ensure_ascii=False, separators=(",", ":"))
    with_hanja = sum(1 for w in words if w["hanjaKo"])
    print(f"{len(words)} 단어 (한자음 {with_hanja}) -> {args.out} ({os.path.getsize(args.out) // 1024} KB)")


if __name__ == "__main__":
    main()
