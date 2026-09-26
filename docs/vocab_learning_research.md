# JLPT 단어 9,200개를 효율적으로 외우는 방법 — 연구 근거와 앱 설계

한국어 화자가 네이버 JLPT 단어(N5→N1, 9,219개)를 외우는 상황을 전제로, 학술 문헌(메타분석·실험 논문)만 근거로 정리했다.

> **조사 범위와 한계**
> - 학술 도메인(PubMed, APA, Springer, SAGE, Cambridge, Wiley, ACL, ACM, J-STAGE, KCI 등)으로 제한한 검색 결과를 근거로 했다.
> - 원문 PDF 접근은 네트워크 정책으로 막혀 있었다. 그래서 수치는 초록·검색 요약 수준에서 확인했고, 확인 못 한 항목은 *(미확인)* 으로 표시했다.
> - 한국인 일본어 학습자를 대상으로 한자어 전이를 직접 실험한 통제 연구는 찾지 못했다.

## 핵심 원칙 7가지

| # | 원칙 | 근거 | 신뢰도 | 앱 반영 |
|---|---|---|---|---|
| 1 | **보지 말고 떠올려라** (인출 연습) | Roediger & Karpicke 2006; Karpicke & Roediger 2008 *Science*; Rowland 2014 메타분석; Adesope et al. 2017 메타분석; Dunlosky et al. 2013 | 높음 | 카드 앞면만 보고 떠올린 뒤 정답 공개. 객관식 없음 |
| 2 | **간격을 두고 복습하라** (분산 학습) | Cepeda et al. 2006 메타분석(839개 평가); Cepeda et al. 2008; Kornell 2009; Latimier et al. 2021 메타분석(g=0.74); Kim & Webb 2022 L2 메타분석 | 높음 | FSRS 가 단어별로 복습 시점을 정함 |
| 3 | **간격은 단어별로 적응형으로 정하라** | Lindsey et al. 2014(개인화 복습 +10.0%p vs 일률 간격); Settles & Meeder 2016; Tabibian et al. 2019 *PNAS*; Ye et al. 2022 *KDD*; Su et al. 2023 *TKDE* | 중간~높음 | FSRS-6 (Ye 2022 계열의 오픈소스 후속). 복습 기록을 모두 저장해 개인 파라미터 최적화 가능 |
| 4 | **확장 간격이냐 균등 간격이냐는 중요하지 않다** | Latimier et al. 2021(g=0.034, 차이 없음); Kang et al. 2014; Karpicke & Roediger 2007; Nakata 2015 | 높음 | 간격 모양은 알고리즘에 맡김 |
| 5 | **틀려도 정답을 꼭 보여줘라** | Pashler et al. 2005(정답 피드백 필수, 정오만 알리면 효과 없음); Kornell, Hays & Bjork 2009(실패한 인출도 학습 강화); Butterfield & Metcalfe 2001(확신하고 틀린 것이 가장 잘 교정됨) | 높음 | 공개 시 한자·가나·뜻·발음을 모두 표시. 연속 학습일 압박이나 오답 페널티 없음 |
| 6 | **비슷한 단어를 한꺼번에 배우지 마라** | Tinkham 1993; Waring 1997; Erten & Tekin 2008; Ishii 2015(형태 유사성이 핵심); Laufer 1988; Nakata & Suzuki 2019(간섭 오류 증가) | 중간 | 오십음 순서를 버리고 레벨 안에서 섞음. 20개 안에 읽기가 같거나 한자를 공유하는 단어가 오지 않게 재배치 |
| 7 | **알아보기 → 말하기 순서로** | Webb 2009; Steinel et al. 2007(학습 방향 = 시험 방향일 때 유리); Schneider et al. 2002; Terai et al. 2021(저숙달: L2→L1, 고숙달: L1→L2) | 중간 | 일본어→뜻 카드로 시작하고, 안정도 7일 이상이 되면 뜻→일본어 카드를 별도로 연다 |

## 보조 원칙

- **한국인의 강점: 한자어**
  - 한자권 학습자는 한자 형태를 거쳐 의미에 접근한다 (Chiu 2002, 教育心理学研究).
  - 동근어(cognate)는 배우기 쉽고 덜 잊힌다 (de Groot & Keijzer 2000).
  - 한자 형태소 지식은 새 한자어 의미 추론에 도움이 된다 (Mori 2003).
  - 한국인 학습자는 한국 한자음과 비슷한 음독을 고르는 전략을 쓴다 (J-STAGE 第二言語としての日本語の習得研究 14, 저자 미확인).
  - 앱 반영: 정답 면에 **한국 한자음 힌트**(経済 → 경제, 会う → 会(회))를 보여준다.
  - 신뢰도: 중간~낮음. 직접 통제 실험이 없다.
  - 주의: 일·한 동형이의어는 한자가 같아도 뜻이 다를 수 있다.
- **발음은 소리 내어**
  - 산출 효과: 소리 내어 읽은 단어가 더 잘 기억된다 (MacLeod et al. 2010; Fawcett 2013 메타분석 g=0.37).
  - L2 단어에서 이 효과가 더 컸다는 보고도 있다 (Brown & Roembke 2024).
  - 반대 결과도 있다. 알파벳 L1 학습자는 소리를 더해도 한자 의미 학습이 개선되지 않았다 (Hagiwara 2016).
  - 앱 반영: 정답 공개 시 일본어 음성을 자동 재생하고 따라 말하기를 권장한다.
  - 신뢰도: 낮음~중간.
- **세션 안에서 여러 번 떠올리기**
  - 세션 안에서 5~7회 인출하는 편이 1~3회보다 나았다 (Nakata 2017).
  - 다만 반복을 늘릴수록 수익은 줄어든다 (Pyc & Rawson 2009; Rawson & Dunlosky 2011).
  - 앱 반영: 새 단어는 1분 → 10분 학습 단계를 거친 뒤 날짜 간격 복습으로 넘어간다.
- **기억술(키워드법)은 보조로만**
  - 즉시 회상에는 유리하지만 더 빨리 잊힌다 (Wang, Thomas & Ouellette 1992).
  - 종합 평가에서 효용이 낮다 ("low utility", Dunlosky 2013).
  - 인출 연습과 결합하면 효과가 있다 (Miyatsu & McDaniel 2019).
  - 앱 반영: 선택형 **연상 메모**만 두고, 메모는 복습 카드에 함께 표시한다.
- **새 단어 도입 속도**
  - 도입 속도가 복습 처리량을 넘으면 적체가 끝없이 커진다 (Reddy et al. 2016 큐 모델, *미확인*).
  - 하루 몇 개가 최적인지 규명한 연구는 없다.
  - 앱 반영: 기본 하루 20개로 두고, 밀린 복습이 한도의 5배를 넘으면 절반, 10배를 넘으면 0으로 줄인다. 이 배수는 경험적 값이다.
  - 하루 20개면 9,219개를 모두 보는 데 약 460일이 걸린다.
- **목표 기억률 90%**
  - 기억률이 낮아진 뒤 연습하는 것은 시간 대비 비효율적이다 (Eglington & Pavlik 2020, 정확한 최적값은 *미확인*).
  - 90%는 FSRS 관행값이고 학술 근거는 간접적이다.
  - 앱 반영: 80~95% 범위에서 조절할 수 있다.
- **수면**
  - 학습과 재학습 사이에 수면을 넣으면 필요한 연습이 절반으로 줄었다 (Mazza et al. 2016).
  - 재학습 이득은 재현되지 않았다 (Cousins et al. 2021).
  - "저녁 학습 → 다음 날 복습"은 권장할 만하지만 강하게 주장하지는 않는다.

## 매일의 학습 루틴 (권장)

1. 하루 한 번 이상 앱을 열어 **복습을 먼저** 끝낸다. 앱이 복습 4장마다 새 단어 1장을 끼워 준다.
2. 새 단어는 하루 10~20개로 한다. 복습이 밀리면 앱이 자동으로 줄인다.
3. 카드마다 먼저 떠올린다(5~10초). 그다음 정답을 보고 **발음을 따라 말한다**.
4. 평가 기준은 다음과 같다.
   - **다시**: 못 떠올림
   - **어려움**: 겨우 떠올림
   - **알맞음**: 떠올림
   - **쉬움**: 즉시 떠올림
   - 정직하게 누를수록 스케줄이 정확해진다.
5. N5를 어느 정도 끝낸 뒤 N4를 켜는 식으로 **쉬운 레벨부터** 켠다. 여러 레벨을 켜도 쉬운 레벨의 새 단어가 먼저 나온다.
6. 몇 달 치 복습 기록이 쌓이면 설정 → 진도 내보내기로 기록을 받는다. py-fsrs Optimizer 로 개인 파라미터를 학습시킬 수 있다(다음 버전에서 앱에 넣을 수 있음).

## 참고문헌

- Adesope, O. O., Trevisan, D. A., & Sundararajan, N. (2017). Rethinking the use of tests: A meta-analysis of practice testing. *Review of Educational Research*. https://doi.org/10.3102/0034654316689306
- Atkinson, R. C., & Raugh, M. R. (1975). An application of the mnemonic keyword method to the acquisition of a Russian vocabulary. *JEP: Human Learning and Memory*. https://eric.ed.gov/?id=EJ113586
- Bjork, E. L., & Bjork, R. A. (2011). Making things hard on yourself, but in a good way. https://psycnet.apa.org/record/2011-19926-008
- Brown, R. M., & Roembke, T. C. (2024). Production benefits on encoding are modulated by language experience. https://pubmed.ncbi.nlm.nih.gov/38622490/
- Butterfield, B., & Metcalfe, J. (2001). Errors committed with high confidence are hypercorrected. *JEP: LMC*. https://pubmed.ncbi.nlm.nih.gov/11713883/
- Cepeda, N. J., Pashler, H., Vul, E., Wixted, J. T., & Rohrer, D. (2006). Distributed practice in verbal recall tasks: A review and quantitative synthesis. *Psychological Bulletin, 132*(3), 354–380. https://pubmed.ncbi.nlm.nih.gov/16719566/
- Cepeda, N. J., Vul, E., Rohrer, D., Wixted, J. T., & Pashler, H. (2008). Spacing effects in learning: A temporal ridgeline of optimal retention. *Psychological Science, 19*, 1095–1102. https://doi.org/10.1111/j.1467-9280.2008.02209.x
- Chiu, H. (2002). 漢字圏・非漢字圏日本語学習者における漢字熟語の処理過程. *教育心理学研究, 50*, 412–420. https://www.jstage.jst.go.jp/article/jjep1953/50/4/50_412/_article/-char/ja/ *(저자 표기 미확인)*
- Cousins, J. N., et al. (2021). Sleep after learning aids the consolidation of factual knowledge, but not relearning. *SLEEP, 44*(3). https://academic.oup.com/sleep/article/44/3/zsaa210/5920204
- de Groot, A. M. B., & Keijzer, R. (2000). What is hard to learn is easy to forget. *Language Learning*. https://onlinelibrary.wiley.com/doi/10.1111/0023-8333.00110
- Dunlosky, J., Rawson, K. A., Marsh, E. J., Nathan, M. J., & Willingham, D. T. (2013). Improving students' learning with effective learning techniques. *Psychological Science in the Public Interest, 14*(1). https://doi.org/10.1177/1529100612453266
- Eglington, L. G., & Pavlik, P. I. (2020). Optimizing practice scheduling requires quantitative tracking of individual item performance. *npj Science of Learning, 5*, 15. https://www.nature.com/articles/s41539-020-00074-4
- Erten, İ. H., & Tekin, M. (2008). Effects on vocabulary acquisition of presenting new words in semantic sets versus semantically unrelated sets. *System, 36*, 407–422. https://www.sciencedirect.com/science/article/abs/pii/S0346251X08000420
- Fawcett, J. M. (2013). The production effect benefits performance in between-subject designs: A meta-analysis. *Acta Psychologica, 142*(1). https://pubmed.ncbi.nlm.nih.gov/23142670
- Hagiwara, A. (2016). The role of phonology and phonetics in L2 kanji learning. *Modern Language Journal, 100*, 880–897. https://onlinelibrary.wiley.com/doi/abs/10.1111/modl.12350
- Ishii, T. (2015). Semantic connection or visual connection: Investigating the true source of confusion. *Language Teaching Research*. https://doi.org/10.1177/1362168814559799
- Kang, S. H. K., Lindsey, R. V., Mozer, M. C., & Pashler, H. (2014). Retrieval practice over the long term: Should spacing be expanding or equal-interval? *Psychonomic Bulletin & Review, 21*(6), 1544–1550. https://link.springer.com/article/10.3758/s13423-014-0636-z
- Karpicke, J. D., & Roediger, H. L. (2007). Expanding retrieval practice promotes short-term retention, but equally spaced retrieval enhances long-term retention. *JEP: LMC*.
- Karpicke, J. D., & Roediger, H. L. (2008). The critical importance of retrieval for learning. *Science, 319*, 966–968. https://www.science.org/doi/abs/10.1126/science.1152408
- Kim, S. K., & Webb, S. (2022). The effects of spaced practice on second language learning: A meta-analysis. *Language Learning*. https://onlinelibrary.wiley.com/doi/abs/10.1111/lang.12479
- Kornell, N. (2009). Optimising learning using flashcards: Spacing is more effective than cramming. *Applied Cognitive Psychology, 23*, 1297–1317. https://onlinelibrary.wiley.com/doi/abs/10.1002/acp.1537
- Kornell, N., Hays, M. J., & Bjork, R. A. (2009). Unsuccessful retrieval attempts enhance subsequent learning. *JEP: LMC*. https://psycnet.apa.org/record/2009-09620-017
- Latimier, A., Peyre, H., & Ramus, F. (2021). A meta-analytic review of the benefit of spacing out retrieval practice episodes on retention. *Educational Psychology Review, 33*, 959–987. https://link.springer.com/article/10.1007/s10648-020-09572-8
- Laufer, B. (1988). The concept of 'synforms' (similar lexical forms) in vocabulary acquisition. *Language and Education, 2*(2). https://www.tandfonline.com/doi/abs/10.1080/09500788809541228
- Lindsey, R. V., Shroyer, J. D., Pashler, H., & Mozer, M. C. (2014). Improving students' long-term knowledge retention through personalized review. *Psychological Science, 25*(3), 639–647. https://doi.org/10.1177/0956797613504302
- MacLeod, C. M., Gopie, N., Hourihan, K. L., Neary, K. R., & Ozubko, J. D. (2010). The production effect: Delineation of a phenomenon. *JEP: LMC, 36*, 671–685. https://pubmed.ncbi.nlm.nih.gov/20438265/
- Mazza, S., et al. (2016). Relearn faster and retain longer: Along with practice, sleep makes perfect. *Psychological Science*. https://doi.org/10.1177/0956797616659930
- Miyatsu, T., & McDaniel, M. A. (2019). Adding the keyword mnemonic to retrieval practice. *Memory & Cognition*. https://link.springer.com/article/10.3758/s13421-019-00936-2
- Mori, Y. (2003). The roles of context and word morphology in learning new kanji words. *Modern Language Journal, 87*, 404–420. https://onlinelibrary.wiley.com/doi/abs/10.1111/1540-4781.00198
- Nakata, T. (2015). Effects of expanding and equal spacing on second language vocabulary learning. *SSLA, 37*(4), 677–711.
- Nakata, T. (2017). Does repeated practice make perfect? *SSLA, 39*(4), 653–679. https://eric.ed.gov/?id=EJ1164199
- Nakata, T., & Suzuki, Y. (2019). Effects of massing and spacing on the learning of semantically related and unrelated words. *SSLA, 41*, 287–311.
- Pashler, H., Cepeda, N. J., Wixted, J. T., & Rohrer, D. (2005). When does feedback facilitate learning of words? *JEP: LMC, 31*, 3–8. https://pubmed.ncbi.nlm.nih.gov/15641900/
- Pyc, M. A., & Rawson, K. A. (2009). Testing the retrieval effort hypothesis. *Journal of Memory and Language, 60*, 437–447.
- Rawson, K. A., & Dunlosky, J. (2011). Optimizing schedules of retrieval practice for durable and efficient learning. *JEP: General, 140*, 283–302.
- Reddy, S., Labutov, I., Banerjee, S., & Joachims, T. (2016). Unbounded human learning: Optimal scheduling for spaced repetition. *KDD '16*. https://dl.acm.org/doi/10.1145/2939672.2939850
- Roediger, H. L., & Karpicke, J. D. (2006). Test-enhanced learning. *Psychological Science, 17*, 249–255. https://doi.org/10.1111/j.1467-9280.2006.01693.x
- Rowland, C. A. (2014). The effect of testing versus restudy on retention: A meta-analytic review. *Psychological Bulletin, 140*(6), 1432–1463. https://pubmed.ncbi.nlm.nih.gov/25150680/
- Schneider, V. I., Healy, A. F., & Bourne, L. E. (2002). What is learned under difficult conditions is hard to forget. *Journal of Memory and Language, 46*(2), 419–440.
- Settles, B., & Meeder, B. (2016). A trainable spaced repetition model for language learning. *ACL 2016*. https://aclanthology.org/P16-1174/
- Steinel, M. P., Hulstijn, J. H., & Steinel, W. (2007). Second language idiom learning in a paired-associate paradigm. *SSLA, 29*, 449–484.
- Su, J., Ye, J., Nie, L., Cao, Y., & Chen, Y. (2023). Optimizing spaced repetition schedule by capturing the dynamics of memory. *IEEE TKDE, 35*(10). https://dl.acm.org/doi/10.1109/TKDE.2023.3251721
- Tabibian, B., et al. (2019). Enhancing human learning via spaced repetition optimization. *PNAS, 116*(10), 3988–3993. https://www.pnas.org/doi/10.1073/pnas.1815156116
- Terai, M., Yamashita, J., & Pasich, K. E. (2021). Effects of learning direction in retrieval practice on EFL vocabulary learning. *SSLA*. https://eric.ed.gov/?id=EJ1319303
- Tinkham, T. (1993). The effect of semantic clustering on the learning of second language vocabulary. *System, 21*, 371–380.
- Wang, A. Y., Thomas, M. H., & Ouellette, J. A. (1992). Keyword mnemonic and retention of second-language vocabulary words. *Journal of Educational Psychology*. https://eric.ed.gov/?id=EJ456644
- Waring, R. (1997). The negative effects of learning words in semantic sets: A replication. *System, 25*(2), 261–274.
- Webb, S. (2009). The effects of receptive and productive learning of word pairs on vocabulary knowledge. *RELC Journal, 40*(3), 360–376. https://doi.org/10.1177/0033688209343854
- Ye, J., Su, J., & Cao, Y. (2022). A stochastic shortest path algorithm for optimizing spaced repetition scheduling. *KDD '22*. https://doi.org/10.1145/3534678.3539081
