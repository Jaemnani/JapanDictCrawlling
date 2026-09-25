* JAPAN DICT CRAWLLING

네이버 일본어사전 JLPT 단어 목록(N1~N5) 크롤링 → 번역 → 단어장 생성.

## 파일

| 파일 | 역할 | 출력 |
| --- | --- | --- |
| `jlpt_crawlling.py` | 네이버 JLPT 목록 크롤링 (selenium) | `naver_jlpt_words_allclass.xlsx` (품사별 모드: `Class` 컬럼 추가) |
| `papago_translator.py` | 한국어 뜻 → 영어 → 12개 언어 번역 (Papago API, 일일 한도 넘으면 이어하기) | `allclass_translator.xlsx` |
| `check_crawl.py` | 크롤링 결과 완전성 검증 | 콘솔 리포트 (문제 있으면 exit 1) |
| `build_wordbook.py` | 크롤링 결과 → 단어장 | `wordbook/` |
| `discover_naver.py` | 사이트 구조 조사 (품사별 `part=` 값, 목록 API 주소·응답 샘플, 항목 HTML) | `naver_site_info.json` |

```bash
pip install -r requirement.txt
```

## 1. 크롤링 결과 검증

```bash
python check_crawl.py naver_jlpt_words_allclass.xlsx
python check_crawl.py naver_jlpt_words_allclass.xlsx --translations allclass_translator.xlsx
python check_crawl.py naver_jlpt_words_allclass.xlsx --probe   # 크롬 필요
```

- 레벨별 단어 수, 빈 칸, 줄 밀림 의심 행(단어 칸에 한글 / 뜻 칸에 한글 없음), 완전 중복 행
- `--translations`: 번역 파일에 없는 단어 수
- `--probe`: 목록 상단의 `N급, 전체, 3,246건` 총 개수와 크롤링 개수(중복 제외)를 비교한다. 또 레벨마다 1페이지로 페이지당 개수를 구하고, `ceil(크롤링 개수 / 페이지당 개수) + 1` 페이지를
  명시적으로 기다린 뒤 열어본다. 단어가 나오면 그 레벨은 크롤링이 덜 된 것.

`jlpt_crawlling.py` 는 아래 경우 **로그만 찍고 데이터를 조용히 잃을 수 있으므로** 검증을 권장한다.

1. `driver.get()` 직후 대기 없이 `#my_jlpt_list_template` 을 읽는다. 네이버 JLPT 목록은 해시 라우팅 SPA 라서
   목록이 비동기로 채워지기 전에 읽으면 `cnt : 0` → 해당 레벨의 나머지 페이지를 건너뛰고 다음 레벨로 넘어간다.
2. 페이지 텍스트를 3줄 단위로 (단어, ?, 뜻) 이라고 가정한다. 한 항목이라도 줄 수가 다르면
   `reshape` 에서 예외 → `ERROR ERROR !!!!` 출력 후 **그 페이지 전체가 버려지고** 다음 페이지로 진행한다.
   예외가 안 나는 경우(줄 수 합이 우연히 3의 배수)에는 이후 행이 밀린 채 저장된다.
3. 페이지마다 새 Chrome 을 띄우고 `quit()` 하지 않아서 긴 실행 중 메모리 부족으로 죽을 수 있다.
4. (품사별 모드) 뜻에 공백이 없으면 품사/뜻 분리 개수가 어긋나 2번과 같은 이유로 페이지가 버려진다.
5. (품사별 모드) 크롤러의 `category` 목록(noun, verb, adjective, adverb, measurement, phrases, conjunction,
   numeral, pronoun, interjection)이 사이트의 품사 필터(명사, 대명사, 동사, 조사, 형용사, 접사, 부사, 감동사,
   형용동사, 기타)와 다르다. 조사·접사·형용동사·기타에 해당하는 단어는 품사별 모드 결과에 빠져 있을 수 있다.
   이 모드 결과(`naver_jlpt_words.xlsx`)를 번역 입력으로 쓰고 있으므로 번역 파일도 같이 영향을 받는다.

크롤링 당시 로그에 `ERROR ERROR !!!!` 가 있었거나 레벨 중간에 `cnt : 0` 이 찍혔다면 누락이 있다.

## 2. 단어장 만들기

```bash
python build_wordbook.py naver_jlpt_words_allclass.xlsx
python build_wordbook.py naver_jlpt_words.xlsx --translations allclass_translator.xlsx --reverse
python build_wordbook.py naver_jlpt_words_allclass.xlsx --levels 4,5 --formats html --seed 42
```

| 출력 | 용도 |
| --- | --- |
| `wordbook/jlpt.apkg` | Anki 덱. `JLPT::N1` ~ `JLPT::N5` 하위 덱, 노트 필드 `Word/Reading/Meaning/English/Level`. 노트 GUID 가 (단어, 읽기, 레벨) 기준이라 다시 생성해서 import 해도 학습 기록이 유지된 채 내용만 갱신된다. `--reverse` 면 뜻 → 단어 카드 추가 |
| `wordbook/anki_jlpt.tsv` | Anki 텍스트 import (Basic 노트 타입, 덱/태그 컬럼 포함). genanki 없이 쓸 때 |
| `wordbook/quizlet_N{n}.tsv` | Quizlet 등 `단어<TAB>뜻` 2열 import 를 지원하는 앱 |
| `wordbook/html/N{n}.html` | 인쇄/화면 학습용. 읽기·뜻 가리기(셀 클릭 시 개별 공개), 섞기 |

- 한자가 들어있는 칸을 표제어(`Word`), 다른 칸을 읽기(`Reading`)로 쓴다. 가타카나어처럼 한자가 없으면 읽기는 비운다.
- 같은 레벨의 같은 단어가 품사별로 여러 행이면 한 카드로 합친다 (`[동사] …<br>[명사] …`).
- `--translations` 를 주면 `(일본어, 한국어 뜻)` 으로 매칭해서 영어 뜻을 붙인다.
- 줄 밀림 행도 그대로 들어가므로 `check_crawl.py` 로 먼저 정리할 것.
