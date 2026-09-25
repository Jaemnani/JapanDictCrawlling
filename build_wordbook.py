"""크롤링 결과 xlsx -> 단어장 (Anki / Quizlet / 인쇄용 HTML).

  python build_wordbook.py naver_jlpt_words_allclass.xlsx
  python build_wordbook.py naver_jlpt_words.xlsx --translations allclass_translator.xlsx --formats apkg,html --reverse

출력 (기본 ./wordbook):
  jlpt.apkg               Anki 덱 (JLPT::N1 ~ JLPT::N5 하위 덱, genanki 필요). 재생성 후 다시 import 하면 학습 기록 유지한 채 갱신됨
  anki_jlpt.tsv           Anki 텍스트 import 용 (Basic 노트, 덱/태그 컬럼 포함)
  quizlet_N{n}.tsv        Quizlet/기타 앱 import 용 (단어<TAB>뜻)
  html/N{n}.html          인쇄/화면 학습용 단어장 (읽기·뜻 가리기, 섞기)
"""
import argparse
import html
import os
import random
import re

import pandas as pd

from wordbook_io import load_crawl, load_translations, split_headword

FORMATS = ("apkg", "tsv", "quizlet", "html")

# genanki id 는 고정값이어야 재 import 시 같은 덱/노트타입으로 인식된다.
ANKI_MODEL_ID = 1607392319
ANKI_MODEL_REVERSE_ID = 1607392320
ANKI_DECK_BASE_ID = 2059400110


REF_NUM_RE = re.compile(r"\d+$")  # →おおばん2 처럼 동음이의어 번호


def dedupe_variants(hanmoon):
    """'後片付け·跡片付け·後片付け·跡片付け' -> '後片付け·跡片付け'"""
    parts = hanmoon.replace("∙", "·").split("·")
    return "·".join(dict.fromkeys(p for p in parts if p)) if len(parts) > 1 else hanmoon


def build_entries(df, translations=None):
    """크롤링 행 -> 단어 단위 엔트리.

    뜻은 줄바꿈으로 구분된 여러 개일 수 있고, 예전 품사별 크롤링 결과처럼 같은 단어/레벨이
    품사별로 여러 행이면 하나로 합친다.
    """
    en_map = {}
    if translations is not None and "en" in translations.columns:
        en_map = dict(zip(zip(translations.ja, translations.ko), translations.en))

    def split_meanings(text):
        return [m.strip() for m in text.split("\n") if m.strip()]

    # 네이버는 표준형이 따로 있는 단어의 뜻을 "→あとしまつ" 처럼 참조로만 준다.
    # 크롤러가 채운 ref_meaning 이 없으면(예전 파일) 참조 대상이 데이터에 있을 때 그 뜻을 가져온다.
    own_meanings = {}
    for r in df.itertuples(index=False):
        ms = split_meanings(r.meaning)
        if ms and not all(m.startswith(("→", "⇒")) for m in ms):
            own_meanings.setdefault(r.japanese, ms)

    def resolve(ms):
        if not ms or not all(m.startswith(("→", "⇒")) for m in ms):
            return ms
        out = []
        for m in ms:
            target = REF_NUM_RE.sub("", m.lstrip("→⇒").strip().rstrip("。")).strip()
            out += [f"(= {target}) {t}" for t in own_meanings.get(target, [])[:1]] + own_meanings.get(target, [])[1:]
            if target not in own_meanings:
                out.append(m)
        return out

    rows = []
    for r in df.itertuples(index=False):
        word, reading = split_headword(r.japanese, dedupe_variants(r.hanmoon))
        rows.append({
            "word": word,
            "reading": reading,
            "level": r.level,
            "pos": [p.strip() for p in r.pos.split(",") if p.strip()],
            "meanings": split_meanings(r.ref_meaning) or resolve(split_meanings(r.meaning)),
            "english": en_map.get((r.japanese, r.meaning), ""),
        })
    flat = pd.DataFrame(rows)

    def uniq(values):
        return list(dict.fromkeys(v for v in values if v))

    def uniq_flat(lists):
        return uniq(v for vs in lists for v in vs)

    grouped = (
        flat.groupby(["level", "word", "reading"], sort=False)
        .agg(pos=("pos", uniq_flat), meanings=("meanings", uniq_flat), english=("english", uniq))
        .reset_index()
    )
    return grouped.sort_values("level", kind="stable", key=lambda s: s.astype(str)).reset_index(drop=True)


def meanings_html(meanings):
    if len(meanings) == 1:
        return html.escape(meanings[0])
    return "<br>".join(f"{i}. {html.escape(m)}" for i, m in enumerate(meanings, 1))


def levels_of(entries):
    return sorted(entries["level"].unique(), key=str)


def write_tsv(entries, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("#separator:tab\n#html:true\n#notetype:Basic\n#deck column:3\n#tags column:4\n")
        for e in entries.itertuples(index=False):
            back = [html.escape(e.reading)] if e.reading else []
            if e.pos:
                back.append("<small>" + html.escape(", ".join(e.pos)) + "</small>")
            back.append(meanings_html(e.meanings))
            if e.english:
                back.append("<small>" + html.escape(", ".join(e.english)) + "</small>")
            cells = [html.escape(e.word), "<br>".join(back), f"JLPT::N{e.level}", f"JLPT N{e.level}"]
            f.write("\t".join(c.replace("\t", " ").replace("\n", " ") for c in cells) + "\n")


def write_quizlet(entries, out_dir):
    paths = []
    for level in levels_of(entries):
        path = os.path.join(out_dir, f"quizlet_N{level}.tsv")
        with open(path, "w", encoding="utf-8", newline="") as f:
            for e in entries[entries["level"] == level].itertuples(index=False):
                term = f"{e.word} ({e.reading})" if e.reading else e.word
                meaning = " / ".join(e.meanings)
                f.write(f"{term}\t{meaning}\n".replace("\r", ""))
        paths.append(path)
    return paths


def write_apkg(entries, path, reverse=False):
    import genanki

    css = (
        ".card{font-family:sans-serif;font-size:22px;text-align:center}"
        ".word{font-size:44px}.reading{color:#666}.pos{color:#999;font-size:14px}"
        ".meaning{text-align:left;display:inline-block}.en{color:#888;font-size:16px}"
    )
    back = (
        '<div class="reading">{{Reading}}</div><div class="pos">{{Part}}</div>'
        '<div class="meaning">{{Meaning}}</div>'
        '{{#English}}<div class="en">{{English}}</div>{{/English}}'
    )
    templates = [{
        "name": "단어 → 뜻",
        "qfmt": '<div class="word">{{Word}}</div>',
        "afmt": '{{FrontSide}}<hr id="answer">' + back,
    }]
    if reverse:
        templates.append({
            "name": "뜻 → 단어",
            "qfmt": '<div class="pos">{{Part}}</div><div class="meaning">{{Meaning}}</div>',
            "afmt": '{{FrontSide}}<hr id="answer"><div class="word">{{Word}}</div><div class="reading">{{Reading}}</div>',
        })
    model = genanki.Model(
        ANKI_MODEL_REVERSE_ID if reverse else ANKI_MODEL_ID,
        "JLPT Naver (양방향)" if reverse else "JLPT Naver",
        fields=[{"name": n} for n in ("Word", "Reading", "Meaning", "English", "Level", "Part")],
        templates=templates,
        css=css,
    )

    decks = []
    for i, level in enumerate(levels_of(entries)):
        deck = genanki.Deck(ANKI_DECK_BASE_ID + i, f"JLPT::N{level}")
        for e in entries[entries["level"] == level].itertuples(index=False):
            deck.add_note(genanki.Note(
                model=model,
                fields=[
                    html.escape(e.word),
                    html.escape(e.reading),
                    meanings_html(e.meanings),
                    html.escape(", ".join(e.english)),
                    f"N{level}",
                    html.escape(", ".join(e.pos)),
                ],
                tags=[f"JLPT_N{level}"],
                guid=genanki.guid_for(e.word, e.reading, level),
            ))
        decks.append(deck)
    genanki.Package(decks).write_to_file(path)


HTML_TEMPLATE = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>JLPT N{level} 단어장</title>
<style>
body{{font-family:sans-serif;margin:16px;color:#222}}
h1{{font-size:20px}} .bar{{margin-bottom:12px}} .bar button{{margin-right:6px}}
table{{border-collapse:collapse;width:100%}}
th,td{{border-bottom:1px solid #ddd;padding:6px 8px;text-align:left;vertical-align:top}}
td.no{{color:#999;width:3em}} td.word{{font-size:20px;width:22%}} td.reading{{width:18%}} td{{overflow-wrap:anywhere}}
td.en{{color:#777;font-size:13px}} .pos{{color:#999;font-size:12px;margin-right:4px}}
body.hide-reading td.reading span, body.hide-meaning td.meaning span{{visibility:hidden}}
td.reading.show span, td.meaning.show span{{visibility:visible!important}}
@media print{{.bar{{display:none}} tr{{break-inside:avoid}}}}
</style></head>
<body>
<h1>JLPT N{level} 단어장 ({count} 단어)</h1>
<div class="bar">
<button onclick="document.body.classList.toggle('hide-reading')">읽기 가리기</button>
<button onclick="document.body.classList.toggle('hide-meaning')">뜻 가리기</button>
<button onclick="shuffle()">섞기</button>
<button onclick="location.reload()">원래 순서</button>
</div>
<table><thead><tr><th>#</th><th>단어</th><th>읽기</th><th>뜻</th>{en_th}</tr></thead>
<tbody>
{rows}
</tbody></table>
<script>
document.querySelectorAll('td.reading, td.meaning').forEach(td =>
  td.addEventListener('click', () => td.classList.toggle('show')));
function shuffle() {{
  const tb = document.querySelector('tbody');
  const rows = [...tb.rows];
  for (let i = rows.length - 1; i > 0; i--) {{
    const j = Math.floor(Math.random() * (i + 1));
    [rows[i], rows[j]] = [rows[j], rows[i]];
  }}
  rows.forEach(r => tb.appendChild(r));
}}
</script>
</body></html>
"""


def write_html(entries, out_dir):
    html_dir = os.path.join(out_dir, "html")
    os.makedirs(html_dir, exist_ok=True)
    has_en = entries.english.map(bool).any()
    paths = []
    for level in levels_of(entries):
        sub = entries[entries["level"] == level]
        rows = []
        for n, e in enumerate(sub.itertuples(index=False), 1):
            cells = [
                f'<td class="no">{n}</td>',
                f'<td class="word">{html.escape(e.word)}</td>',
                f'<td class="reading"><span>{html.escape(e.reading)}</span></td>',
                '<td class="meaning"><span>'
                + (f'<span class="pos">{html.escape(", ".join(e.pos))}</span><br>' if e.pos else "")
                + meanings_html(e.meanings) + "</span></td>",
            ]
            if has_en:
                cells.append(f'<td class="en">{html.escape(", ".join(e.english))}</td>')
            rows.append("<tr>" + "".join(cells) + "</tr>")
        path = os.path.join(html_dir, f"N{level}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(HTML_TEMPLATE.format(
                level=level, count=len(sub), rows="\n".join(rows),
                en_th="<th>English</th>" if has_en else "",
            ))
        paths.append(path)
    return paths


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("crawl_xlsx")
    ap.add_argument("--translations", help="papago_translator.py 결과 xlsx (영어 뜻 추가)")
    ap.add_argument("--out", default="wordbook")
    ap.add_argument("--formats", default=",".join(FORMATS), help=f"쉼표 구분: {','.join(FORMATS)}")
    ap.add_argument("--levels", help="쉼표 구분 레벨만 출력 (예: 3,4,5)")
    ap.add_argument("--reverse", action="store_true", help="Anki 에 뜻 → 단어 카드도 생성")
    ap.add_argument("--seed", type=int, help="지정하면 레벨 내 단어 순서를 섞어서 출력")
    args = ap.parse_args()

    formats = {f.strip() for f in args.formats.split(",") if f.strip()}
    unknown = formats - set(FORMATS)
    if unknown:
        ap.error(f"알 수 없는 format: {', '.join(sorted(unknown))}")

    df = load_crawl(args.crawl_xlsx)
    if args.levels:
        df = df[df["level"].isin({l.strip() for l in args.levels.split(",")})]
    tr = load_translations(args.translations) if args.translations else None
    entries = build_entries(df, tr)
    if args.seed is not None:
        rng = random.Random(args.seed)
        entries = entries.sample(frac=1, random_state=rng.randrange(2**32))
        entries = entries.sort_values("level", kind="stable", key=lambda s: s.astype(str)).reset_index(drop=True)

    os.makedirs(args.out, exist_ok=True)
    print(f"{len(df)} 행 -> {len(entries)} 단어")
    for level, n in entries.groupby("level").size().items():
        print(f"  N{level}: {n}")

    outputs = []
    if "tsv" in formats:
        path = os.path.join(args.out, "anki_jlpt.tsv")
        write_tsv(entries, path)
        outputs.append(path)
    if "quizlet" in formats:
        outputs += write_quizlet(entries, args.out)
    if "html" in formats:
        outputs += write_html(entries, args.out)
    if "apkg" in formats:
        try:
            path = os.path.join(args.out, "jlpt.apkg")
            write_apkg(entries, path, reverse=args.reverse)
            outputs.append(path)
        except ImportError:
            print("genanki 가 없어 apkg 는 건너뜀 (pip install genanki)")
    for p in outputs:
        print("->", p)


if __name__ == "__main__":
    main()
