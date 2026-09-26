import Foundation

/// FSRS-6 스케줄러. py-fsrs 6.3 (https://github.com/open-spaced-repetition/py-fsrs) 의 Scheduler 를 그대로 옮긴 것.
/// 수식·기본 파라미터·상태 전이를 바꾸면 FSRSTests 의 기대값(py-fsrs 로 생성)과 어긋나므로 같이 확인할 것.
enum Rating: Int, Codable, CaseIterable {
    case again = 1, hard, good, easy
}

enum CardPhase: Int, Codable {
    case learning = 1, review, relearning
}

struct FSRSCard: Codable, Equatable {
    var phase: CardPhase = .learning
    var step: Int? = 0
    var stability: Double?
    var difficulty: Double?
    var due: Date
    var lastReview: Date?

    init(due: Date) {
        self.due = due
    }
}

struct FSRS {
    static let defaultParameters: [Double] = [
        0.212, 1.2931, 2.3065, 8.2956, 6.4133, 0.8334, 3.0194, 0.001, 1.8722, 0.1666, 0.796,
        1.4835, 0.0614, 0.2629, 1.6483, 0.6014, 1.8729, 0.5425, 0.0912, 0.0658, 0.1542,
    ]
    static let stabilityMin = 0.001
    static let minDifficulty = 1.0
    static let maxDifficulty = 10.0

    var parameters: [Double] = FSRS.defaultParameters
    var desiredRetention: Double = 0.9
    var learningSteps: [TimeInterval] = [60, 600]
    var relearningSteps: [TimeInterval] = [600]
    var maximumInterval: Int = 36500
    var enableFuzzing: Bool = true

    private var w: [Double] { parameters }
    private var decay: Double { -parameters[20] }
    private var factor: Double { pow(0.9, 1 / decay) - 1 }

    // MARK: - Public

    /// 지금(또는 date) 시점에 기억하고 있을 확률.
    func retrievability(_ card: FSRSCard, at date: Date) -> Double {
        guard let last = card.lastReview, let s = card.stability else { return 0 }
        let elapsed = max(0, Self.wholeDays(from: last, to: date))
        return pow(1 + factor * Double(elapsed) / s, decay)
    }

    /// rating 으로 복습했을 때의 다음 카드 상태. random 은 fuzz 용 (0..<1), 테스트에서 고정값을 넣는다.
    func review(_ input: FSRSCard, rating: Rating, at now: Date, random: () -> Double = { Double.random(in: 0..<1) }) -> FSRSCard {
        var card = input
        let daysSinceLast: Int? = card.lastReview.map { Self.wholeDays(from: $0, to: now) }
        var nextInterval: TimeInterval

        switch card.phase {
        case .learning:
            let step = card.step ?? 0
            if card.stability == nil || card.difficulty == nil {
                card.stability = initialStability(rating)
                card.difficulty = initialDifficulty(rating, clamp: true)
            } else if let d = daysSinceLast, d < 1 {
                card.stability = shortTermStability(card.stability!, rating)
                card.difficulty = nextDifficulty(card.difficulty!, rating)
            } else {
                card.stability = nextStability(card.difficulty!, card.stability!, retrievability(card, at: now), rating)
                card.difficulty = nextDifficulty(card.difficulty!, rating)
            }
            if learningSteps.isEmpty || (step >= learningSteps.count && rating != .again) {
                nextInterval = graduate(&card)
            } else {
                switch rating {
                case .again:
                    card.step = 0
                    nextInterval = learningSteps[0]
                case .hard:
                    if step == 0 && learningSteps.count == 1 {
                        nextInterval = learningSteps[0] * 1.5
                    } else if step == 0 && learningSteps.count >= 2 {
                        nextInterval = (learningSteps[0] + learningSteps[1]) / 2
                    } else {
                        nextInterval = learningSteps[step]
                    }
                case .good:
                    if step + 1 == learningSteps.count {
                        nextInterval = graduate(&card)
                    } else {
                        card.step = step + 1
                        nextInterval = learningSteps[step + 1]
                    }
                case .easy:
                    nextInterval = graduate(&card)
                }
            }

        case .review:
            if let d = daysSinceLast, d < 1 {
                card.stability = shortTermStability(card.stability!, rating)
            } else {
                card.stability = nextStability(card.difficulty!, card.stability!, retrievability(card, at: now), rating)
            }
            card.difficulty = nextDifficulty(card.difficulty!, rating)
            if rating == .again && !relearningSteps.isEmpty {
                card.phase = .relearning
                card.step = 0
                nextInterval = relearningSteps[0]
            } else {
                nextInterval = days(nextIntervalDays(card.stability!))
            }

        case .relearning:
            let step = card.step ?? 0
            if let d = daysSinceLast, d < 1 {
                card.stability = shortTermStability(card.stability!, rating)
            } else {
                card.stability = nextStability(card.difficulty!, card.stability!, retrievability(card, at: now), rating)
            }
            card.difficulty = nextDifficulty(card.difficulty!, rating)
            if relearningSteps.isEmpty || (step >= relearningSteps.count && rating != .again) {
                nextInterval = graduate(&card)
            } else {
                switch rating {
                case .again:
                    card.step = 0
                    nextInterval = relearningSteps[0]
                case .hard:
                    if step == 0 && relearningSteps.count == 1 {
                        nextInterval = relearningSteps[0] * 1.5
                    } else if step == 0 && relearningSteps.count >= 2 {
                        nextInterval = (relearningSteps[0] + relearningSteps[1]) / 2
                    } else {
                        nextInterval = relearningSteps[step]
                    }
                case .good:
                    if step + 1 == relearningSteps.count {
                        nextInterval = graduate(&card)
                    } else {
                        card.step = step + 1
                        nextInterval = relearningSteps[step + 1]
                    }
                case .easy:
                    nextInterval = graduate(&card)
                }
            }
        }

        if enableFuzzing && card.phase == .review {
            nextInterval = fuzzed(nextInterval, random: random)
        }
        card.due = now.addingTimeInterval(nextInterval)
        card.lastReview = now
        return card
    }

    /// 버튼 아래에 보여줄 예상 간격.
    func previewIntervals(_ card: FSRSCard, at now: Date) -> [Rating: TimeInterval] {
        var fsrs = self
        fsrs.enableFuzzing = false
        var out: [Rating: TimeInterval] = [:]
        for r in Rating.allCases {
            out[r] = fsrs.review(card, rating: r, at: now).due.timeIntervalSince(now)
        }
        return out
    }

    // MARK: - Model

    private func graduate(_ card: inout FSRSCard) -> TimeInterval {
        card.phase = .review
        card.step = nil
        return days(nextIntervalDays(card.stability!))
    }

    private func clampDifficulty(_ d: Double) -> Double { min(max(d, Self.minDifficulty), Self.maxDifficulty) }
    private func clampStability(_ s: Double) -> Double { max(s, Self.stabilityMin) }

    private func initialStability(_ r: Rating) -> Double { clampStability(w[r.rawValue - 1]) }

    private func initialDifficulty(_ r: Rating, clamp: Bool) -> Double {
        let d = w[4] - exp(w[5] * Double(r.rawValue - 1)) + 1
        return clamp ? clampDifficulty(d) : d
    }

    func nextIntervalDays(_ stability: Double) -> Int {
        let raw = (stability / factor) * (pow(desiredRetention, 1 / decay) - 1)
        return min(max(Int(raw.rounded(.toNearestOrEven)), 1), maximumInterval)
    }

    private func shortTermStability(_ s: Double, _ r: Rating) -> Double {
        var increase = exp(w[17] * (Double(r.rawValue) - 3 + w[18])) * pow(s, -w[19])
        if r != .again { increase = max(increase, 1) }
        return clampStability(s * increase)
    }

    private func nextDifficulty(_ d: Double, _ r: Rating) -> Double {
        let delta = -(w[6] * Double(r.rawValue - 3))
        let damped = d + (10 - d) * delta / 9
        let reverted = w[7] * initialDifficulty(.easy, clamp: false) + (1 - w[7]) * damped
        return clampDifficulty(reverted)
    }

    private func nextStability(_ d: Double, _ s: Double, _ r: Double, _ rating: Rating) -> Double {
        let next: Double
        if rating == .again {
            let longTerm = w[11] * pow(d, -w[12]) * (pow(s + 1, w[13]) - 1) * exp((1 - r) * w[14])
            let shortTerm = s / exp(w[17] * w[18])
            next = min(longTerm, shortTerm)
        } else {
            let hardPenalty = rating == .hard ? w[15] : 1
            let easyBonus = rating == .easy ? w[16] : 1
            next = s * (1 + exp(w[8]) * (11 - d) * pow(s, -w[9]) * (exp((1 - r) * w[10]) - 1) * hardPenalty * easyBonus)
        }
        return clampStability(next)
    }

    private func fuzzed(_ interval: TimeInterval, random: () -> Double) -> TimeInterval {
        let intervalDays = Int(interval / 86400)
        if Double(intervalDays) < 2.5 { return interval }
        let ranges: [(start: Double, end: Double, factor: Double)] = [(2.5, 7, 0.15), (7, 20, 0.1), (20, .infinity, 0.05)]
        var delta = 1.0
        for range in ranges {
            delta += range.factor * max(min(Double(intervalDays), range.end) - range.start, 0)
        }
        var minIvl = Int((Double(intervalDays) - delta).rounded(.toNearestOrEven))
        var maxIvl = Int((Double(intervalDays) + delta).rounded(.toNearestOrEven))
        minIvl = max(2, minIvl)
        maxIvl = min(maxIvl, maximumInterval)
        minIvl = min(minIvl, maxIvl)
        let fuzzedDays = min(Int((random() * Double(maxIvl - minIvl + 1) + Double(minIvl)).rounded(.toNearestOrEven)), maximumInterval)
        return days(fuzzedDays)
    }

    private func days(_ n: Int) -> TimeInterval { TimeInterval(n) * 86400 }

    /// Python timedelta.days 와 같은 내림 일수.
    static func wholeDays(from a: Date, to b: Date) -> Int {
        Int((b.timeIntervalSince(a) / 86400).rounded(.down))
    }
}
