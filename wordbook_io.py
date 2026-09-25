"""jlpt_crawlling.py / papago_translator.py 가 저장한 xlsx 를 읽어 표준 DataFrame 으로 정규화.

예전 셀레니움 크롤러는 np.array 첫 행에 라벨(["japanese", "Hanmoon", ...])을 넣고
pd.DataFrame(...).to_excel(index=False) 로 저장해서 엑셀 첫 줄이 0,1,2,... 이고 둘째 줄이 라벨이다.
지금 크롤러는 첫 줄이 바로 라벨이다. 둘 다 읽을 수 있도록 라벨 행을 찾아서 헤더로 사용한다.
"""
import re

import pandas as pd

KANJI_RE = re.compile(r"[㐀-䶿一-鿿豈-﫿々]")
KANA_RE = re.compile(r"[぀-ヿｦ-ﾟ]")
HANGUL_RE = re.compile(r"[가-힣ㄱ-ㆎ]")

# 크롤러 라벨 -> 표준 컬럼명
CRAWL_COLUMNS = {
    "japanese": "japanese",
    "hanmoon": "hanmoon",
    "level": "level",
    "class": "pos",
    "mean": "meaning",
    "refmean": "ref_meaning",
}


def _read_labeled_sheet(path, first_label):
    raw = pd.read_excel(path, header=None, dtype=str).fillna("")
    for i in range(min(5, len(raw))):
        if str(raw.iloc[i, 0]).strip().lower() == first_label:
            labels = [str(v).strip() for v in raw.iloc[i]]
            df = raw.iloc[i + 1:].reset_index(drop=True)
            df.columns = labels
            # 엑셀 기준 행 번호(1-based) - 검증 리포트에서 원본 위치를 찾기 위함
            df["xlsx_row"] = range(i + 2, i + 2 + len(df))
            return df
    raise ValueError(f"{path}: '{first_label}' 라벨 행을 찾지 못했습니다.")


def load_crawl(path):
    """크롤링 결과 xlsx -> columns: japanese, hanmoon, level, pos, meaning (+ 원본 row 번호).

    meaning 은 뜻이 여러 개면 줄바꿈으로 구분되어 있다 (API 크롤러). pos 는 "명사, 동사" 처럼 쉼표 구분.
    ref_meaning 은 뜻이 '→あとしまつ' 같은 참조뿐인 단어에 크롤러가 채운 참조 대상의 뜻.
    """
    df = _read_labeled_sheet(path, "japanese")
    df = df.rename(columns={c: CRAWL_COLUMNS[c.lower()] for c in df.columns if c.lower() in CRAWL_COLUMNS})
    for c in ("pos", "ref_meaning"):
        if c not in df.columns:
            df[c] = ""
    cols = ["japanese", "hanmoon", "level", "pos", "meaning", "ref_meaning"]
    df = df[cols + ["xlsx_row"]].copy()
    for c in cols:
        df[c] = df[c].astype(str).str.strip()
    return df


def load_translations(path):
    """papago_translator.py 결과 xlsx -> columns: ja, ko, en, zh-CN, ..."""
    df = _read_labeled_sheet(path, "ja")
    for c in df.columns:
        if c != "xlsx_row":
            df[c] = df[c].astype(str).str.strip()
    return df


def split_headword(japanese, hanmoon):
    """(표제어, 읽기) 반환. 한자가 들어있는 쪽을 표제어로 쓴다. 한자가 없으면(가타카나어 등) 읽기는 비운다."""
    if hanmoon and KANJI_RE.search(hanmoon) and not KANJI_RE.search(japanese):
        return hanmoon, japanese
    if KANJI_RE.search(japanese) and hanmoon and not KANJI_RE.search(hanmoon):
        return japanese, hanmoon
    if hanmoon:
        return hanmoon, japanese
    return japanese, ""
