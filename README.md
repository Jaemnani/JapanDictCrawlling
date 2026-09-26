* JAPAN DICT CRAWLLING

네이버 일본어사전 JLPT 단어 목록(N1~N5) 크롤링 → 단어장 생성.

## 파일

| 파일 | 역할 | 출력 |
| --- | --- | --- |
| `jlpt_crawlling.py` | 네이버 JLPT 목록 크롤링 (JSON API, 품사 포함) | `naver_jlpt_words.xlsx`, `naver_jlpt_raw.json` |
| `check_crawl.py` | 크롤링 결과 검증 (사이트 총 건수 비교 포함) | 콘솔 리포트 (문제 있으면 exit 1) |
| `build_wordbook.py` | 크롤링 결과 → 단어장 | `wordbook/` |
| `export_app_data.py` | 크롤링 결과 → iOS 앱 번들 데이터 | `ios/JLPTVocab/Resources/words.json` |
| `ios/` | iOS 단어 학습 앱 (SwiftUI + FSRS) | |
| `papago_translator.py` | 한국어 뜻 → 영어 → 12개 언어 번역 (Papago API). 예전 셀레니움 크롤러 출력 형식 기준 | `allclass_translator.xlsx` |

```bash
pip install -r requirement.txt
python jlpt_crawlling.py                         # 약 2,200 요청, 30분 안팎
python check_crawl.py naver_jlpt_words.xlsx --probe
python build_wordbook.py naver_jlpt_words.xlsx
```

## 1. 크롤링

화면(`https://ja.dict.naver.com/#/jlpt/list?level=1`)이 내부적으로 호출하는 API 를 그대로 쓴다.

```
GET https://ja.dict.naver.com/api/jako/getJLPTList?level=1&part=allClass&page=1
-> {"m_total": 3246, "m_pageSize": 10, "m_totalPage": 325,
    "m_items": [{"entry_id", "entry", "show_entry", "pron", "means": [...], "parts": [...], ...}]}
```

- `level`: 1~5, `page`: 1부터, 페이지당 10개 고정
- `part`: `allClass` 또는 한글 품사명 `명사, 대명사, 동사, 조사, 형용사, 접사, 부사, 감동사, 형용동사, 기타`
  (영어 코드 `noun`, `verb` 등은 0건)
- `entry` 는 가나 표제어인데 **퍼센트 인코딩돼서 오는 경우가 있어** 디코딩한다. `show_entry` 는 `あ-う` 처럼 어간 구분 `-` 가 섞여 있다.
- `pron` 은 한자 표기(`宛·充て`), `means` 는 뜻 목록
- `allClass` 응답은 `parts` 가 비어 있으므로 품사별 목록을 한 번 더 받아서 `entry_id` 로 붙인다. 한 단어가 여러 품사에 속할 수 있다.

- 정렬 기준이 같은 단어들은 요청마다 순서가 바뀌어서, 페이지 경계에서 한 단어가 두 번 나오고 다른 단어가
  빠지는 일이 있다 (첫 수집에서 N2 4건, N3 2건). 중복이 나온 페이지 주변을 다시 받아서 빠진 단어를 채운다.
- 뜻이 `→あとしまつ`, `⇒デジタル・カメラ。` 같은 참조뿐인 단어(약 70개)는 참조 대상의 뜻을 `RefMean` 컬럼에 채운다.
  대상이 JLPT 목록에 있으면 그 뜻을, 없으면 사전 검색 API(`/api3/jako/search?query=`)의 첫 정확 일치 항목을 쓴다.

레벨별 수집 개수가 `m_total` 과 다르면 실패(exit 1)로 끝난다. `--levels 4,5`, `--no-parts`, `--delay` 옵션이 있다.

### 예전 셀레니움 크롤러의 문제 (참고)

예전 결과 파일을 가지고 있다면 `check_crawl.py` 로 확인할 것.

1. `driver.get()` 직후 대기 없이 목록을 읽어서, 비동기 로딩 전이면 `cnt : 0` → 그 레벨 나머지를 건너뜀
2. 텍스트를 3줄 단위(단어, ?, 뜻)로 가정했는데 **뜻이 여러 개인 단어가 흔하다** (N5 744개 중 331개).
   줄 수가 어긋나면 `ERROR ERROR !!!!` 후 페이지 전체를 버리거나, 이후 행이 밀린 채 저장된다.
3. 페이지마다 Chrome 을 새로 띄우고 닫지 않음
4. 품사별 모드의 품사 코드(`noun`, `verb` …)가 현재 API 에서 모두 0건

## 2. 검증

```bash
python check_crawl.py naver_jlpt_words.xlsx --probe
python check_crawl.py 예전파일.xlsx --translations allclass_translator.xlsx
```

- 레벨별 단어 수, 빈 칸, 줄 밀림 의심 행(단어 칸에 한글 / 뜻 칸에 한글 없음), 완전 중복 행
- `--probe`: 레벨별 사이트 총 건수(`m_total`)와 크롤링 개수(중복 제외) 비교
- `--translations`: 번역 파일에 없는 단어 수

## 3. 단어장 만들기

```bash
python build_wordbook.py naver_jlpt_words.xlsx
python build_wordbook.py naver_jlpt_words.xlsx --reverse
python build_wordbook.py naver_jlpt_words.xlsx --levels 4,5 --formats html --seed 42
```

| 출력 | 용도 |
| --- | --- |
| `wordbook/jlpt.apkg` | Anki 덱. `JLPT::N1` ~ `JLPT::N5` 하위 덱, 노트 필드 `Word/Reading/Meaning/English/Level/Part`. 노트 GUID 가 (단어, 읽기, 레벨) 기준이라 다시 생성해서 import 해도 학습 기록이 유지된 채 내용만 갱신된다. `--reverse` 면 뜻 → 단어 카드 추가 |
| `wordbook/anki_jlpt.tsv` | Anki 텍스트 import (Basic 노트 타입, 덱/태그 컬럼 포함). genanki 없이 쓸 때 |
| `wordbook/quizlet_N{n}.tsv` | Quizlet 등 `단어<TAB>뜻` 2열 import 를 지원하는 앱 |
| `wordbook/html/N{n}.html` | 인쇄/화면 학습용. 읽기·뜻 가리기(셀 클릭 시 개별 공개), 섞기 |

- 한자 표기가 있으면 한자를 표제어(`Word`), 가나를 읽기(`Reading`)로 쓴다. 한자가 없으면(가타카나어 등) 읽기는 비운다.
- 뜻이 여러 개면 번호를 붙여 줄바꿈으로 보여준다. 참조뿐인 뜻은 `RefMean` 으로 대체한다 (`(= あとしまつ) 뒤처리.`).
- 한자 표기가 `後片付け·跡片付け·後片付け·跡片付け` 처럼 반복되면 중복을 제거한다.
- 같은 레벨의 같은 단어가 여러 행이면(예전 품사별 결과) 한 카드로 합친다.
- `--translations` 를 주면 `(일본어, 한국어 뜻)` 으로 매칭해서 영어 뜻을 붙인다.

## 4. iOS 앱

학습 방법의 연구 근거는 [docs/vocab_learning_research.md](docs/vocab_learning_research.md) 참고.

```bash
pip install hanja                                   # 한국 한자음 힌트용 (선택)
python export_app_data.py naver_jlpt_words.xlsx     # -> ios/JLPTVocab/Resources/words.json
open ios/JLPTVocab.xcodeproj                        # Xcode 16 이상, iOS 17 이상
```

Xcode 에서 Signing & Capabilities 의 Team 을 본인 계정으로 바꾸고 기기나 시뮬레이터에서 실행한다.
`words.json` 은 네이버 사전 데이터라 레포에 넣지 않는다 (개인 학습용. 앱스토어 배포 시 라이선스 문제가 있음).

| 기능 | 내용 |
| --- | --- |
| 스케줄링 | FSRS-6 (py-fsrs 6.3 포팅, `JLPTVocabTests/FSRSTests.swift` 에 py-fsrs 기대값 테스트) |
| 카드 | 일본어 → 뜻(먼저), 안정도 7일 이상이면 뜻 → 일본어 추가 |
| 신규 순서 | 쉬운 레벨부터. 레벨 안에서 섞고, 20개 안에 같은 읽기·같은 한자가 겹치지 않게 배치 |
| 세션 | 학습 단계(1분·10분) → 복습 → 신규. 복습 4장마다 신규 1장. 밀린 복습이 많으면 신규 자동 감소 |
| 정답 면 | 한자·가나·품사·뜻 전체, 일본어 음성 자동 재생, 한국 한자음 힌트, 연상 메모 |
| 데이터 | 진도는 기기에 저장, JSON 내보내기/가져오기 (복습 기록 포함 → py-fsrs Optimizer 로 개인 파라미터 학습 가능) |
