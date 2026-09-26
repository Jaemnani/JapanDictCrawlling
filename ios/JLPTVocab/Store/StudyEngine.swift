import Foundation

struct StudyItem: Equatable {
    let key: CardKey
    let word: Word
    let card: FSRSCard
    let isNew: Bool
}

struct QueueCounts {
    var learning = 0   // 학습/재학습 단계 (분 단위)
    var review = 0     // 지금 복습할 카드
    var newRecognition = 0
    var newProduction = 0
    var reviewLaterToday = 0
    var newThrottled = false  // 밀린 복습 때문에 신규를 줄였는지

    var total: Int { learning + review + newRecognition + newProduction }
}

/// 세션 큐를 만들고 채점 결과를 FSRS 로 반영한다.
///
/// 다음 카드 고르는 순서
///  1. 학습 단계(1분·10분 뒤 재확인)에서 시간이 된 카드
///  2. 복습 카드 (due 가 지난 것, 오래된 순). 신규 카드가 남아 있으면 복습 4장마다 신규 1장을 끼운다
///  3. 신규 카드: 일본어 → 뜻 (레벨 안에서 섞인 순서, 쉬운 레벨부터) → 뜻 → 일본어
///  4. 더 없으면 20분 안에 돌아올 학습 단계 카드를 앞당겨 보여준다
@MainActor
final class StudyEngine: ObservableObject {
    static let learnAhead: TimeInterval = 20 * 60
    static let reviewsPerNew = 4
    /// 밀린 복습이 신규 한도의 이 배수를 넘으면 신규를 절반으로, 두 배를 넘으면 멈춘다.
    /// 도입 속도가 복습 처리량을 넘으면 적체가 끝없이 커진다 (Reddy et al. 2016). 배수 자체는 경험적 값.
    static let backlogFactor = 5

    let words: [Word]
    let wordsByID: [String: Word]
    private let newOrder: [Word]
    let settings: AppSettings

    @Published private(set) var progress: ProgressData
    @Published private(set) var current: StudyItem?
    @Published private(set) var waitingUntil: Date?
    @Published private(set) var sessionReviewed = 0

    private var reviewsSinceNew = 0
    private var shownAt: Date?

    init(settings: AppSettings, words: [Word] = WordBundle.loadFromBundle(), progress: ProgressData = ProgressStore.load()) {
        self.settings = settings
        self.words = words
        self.wordsByID = Dictionary(words.map { ($0.id, $0) }, uniquingKeysWith: { a, _ in a })
        // 쉬운 레벨(N5)부터, 레벨 안에서는 export 때 섞어 둔 순서대로
        self.newOrder = words.sorted { $0.level != $1.level ? $0.level > $1.level : $0.order < $1.order }
        self.progress = progress
    }

    var fsrs: FSRS {
        var f = FSRS()
        f.desiredRetention = settings.desiredRetention
        return f
    }

    // MARK: - Session

    func startSession() {
        sessionReviewed = 0
        reviewsSinceNew = 0
        advance()
    }

    func endSession() {
        current = nil
        waitingUntil = nil
    }

    func answer(_ rating: Rating, now: Date = Date()) {
        guard let item = current else { return }
        let updated = fsrs.review(item.card, rating: rating, at: now)
        progress.cards[item.key.string] = updated

        let day = StudyDay.key(for: now)
        if item.isNew {
            progress.introducedPerDay[introducedKey(day, item.key.direction), default: 0] += 1
            reviewsSinceNew = 0
        } else if item.card.phase == .review {
            reviewsSinceNew += 1
        }
        progress.reviewsPerDay[day, default: 0] += 1
        let duration = shownAt.map { Int(now.timeIntervalSince($0) * 1000) }
        progress.log.append(ReviewLogEntry(card: item.key.string, rating: rating.rawValue, reviewedAt: now, durationMs: duration))
        ProgressStore.save(progress)

        sessionReviewed += 1
        advance(now: now)
    }

    func previewIntervals() -> [Rating: TimeInterval] {
        guard let item = current else { return [:] }
        return fsrs.previewIntervals(item.card, at: Date())
    }

    func advance(now: Date = Date()) {
        let q = scan(now: now)
        waitingUntil = nil
        let next: StudyItem?
        if let l = q.learningDue.first {
            next = l
        } else if let r = q.reviewDue.first, q.newItem == nil || reviewsSinceNew < Self.reviewsPerNew {
            next = r
        } else if let n = q.newItem {
            next = n
        } else if let l = q.learningSoon.first {
            next = l
        } else {
            next = nil
            waitingUntil = q.learningLaterDue
        }
        current = next
        shownAt = next == nil ? nil : now
    }

    // MARK: - Counts

    func counts(now: Date = Date()) -> QueueCounts {
        let q = scan(now: now)
        var c = QueueCounts()
        c.learning = q.learningDue.count + q.learningSoon.count
        c.review = q.reviewDue.count
        c.reviewLaterToday = q.reviewLaterToday
        c.newRecognition = remainingNew(.recognition, now: now, backlog: q.reviewDue.count, next: { self.nextNewRecognition(skip: $0) })
        c.newProduction = settings.productionEnabled
            ? remainingNew(.production, now: now, backlog: q.reviewDue.count, next: { self.nextNewProduction(skip: $0) }) : 0
        c.newThrottled = effectiveLimit(settings.dailyNewLimit, backlog: q.reviewDue.count) < settings.dailyNewLimit
        return c
    }

    /// 아직 한 번도 안 본 단어를 지금 신규 한도로 다 여는 데 걸리는 날 수.
    func daysToFinish() -> Int? {
        let remaining = words.filter {
            settings.enabledLevels.contains($0.level)
                && progress.cards[CardKey(wordID: $0.id, direction: .recognition).string] == nil
        }.count
        guard settings.dailyNewLimit > 0 else { return nil }
        return Int((Double(remaining) / Double(settings.dailyNewLimit)).rounded(.up))
    }

    func note(for word: Word) -> String { progress.notes[word.id] ?? "" }

    func setNote(_ text: String, for word: Word) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        progress.notes[word.id] = trimmed.isEmpty ? nil : trimmed
        ProgressStore.save(progress)
    }

    struct LevelStats {
        let level: Int
        let total: Int
        let started: Int   // 일본어 → 뜻 카드를 한 번이라도 본 단어
        let mature: Int    // 안정도 21일 이상
    }

    func levelStats() -> [LevelStats] {
        var total: [Int: Int] = [:], started: [Int: Int] = [:], mature: [Int: Int] = [:]
        for w in words {
            total[w.level, default: 0] += 1
            if let c = progress.cards[CardKey(wordID: w.id, direction: .recognition).string] {
                started[w.level, default: 0] += 1
                if c.phase == .review, (c.stability ?? 0) >= 21 { mature[w.level, default: 0] += 1 }
            }
        }
        return total.keys.sorted(by: >).map { LevelStats(level: $0, total: total[$0]!, started: started[$0] ?? 0, mature: mature[$0] ?? 0) }
    }

    func card(for word: Word, _ direction: CardDirection) -> FSRSCard? {
        progress.cards[CardKey(wordID: word.id, direction: direction).string]
    }

    // MARK: - Maintenance

    func resetProgress() {
        progress = ProgressData()
        ProgressStore.save(progress)
        endSession()
    }

    func replaceProgress(_ data: ProgressData) {
        progress = data
        ProgressStore.save(progress)
        endSession()
    }

    // MARK: - Queue building

    private struct Scan {
        var learningDue: [StudyItem] = []
        var learningSoon: [StudyItem] = []
        var learningLaterDue: Date?
        var reviewDue: [StudyItem] = []
        var reviewLaterToday = 0
        var newItem: StudyItem?
    }

    private func scan(now: Date) -> Scan {
        var s = Scan()
        let rollover = StudyDay.nextRollover(after: now)
        for (k, card) in progress.cards {
            guard let key = CardKey(string: k), let word = wordsByID[key.wordID],
                  settings.enabledLevels.contains(word.level) else { continue }
            if key.direction == .production && !settings.productionEnabled { continue }
            let item = StudyItem(key: key, word: word, card: card, isNew: false)
            switch card.phase {
            case .learning, .relearning:
                if card.due <= now {
                    s.learningDue.append(item)
                } else if card.due <= now.addingTimeInterval(Self.learnAhead) {
                    s.learningSoon.append(item)
                } else {
                    s.learningLaterDue = min(s.learningLaterDue ?? card.due, card.due)
                }
            case .review:
                // 복습은 due 가 지난 뒤에만 보여준다. 일찍 보면 FSRS 가 같은 날 복습(단기 안정도)으로 계산한다.
                if card.due <= now {
                    s.reviewDue.append(item)
                } else if card.due < rollover {
                    s.reviewLaterToday += 1
                }
            }
        }
        s.learningDue.sort { $0.card.due < $1.card.due }
        s.learningSoon.sort { $0.card.due < $1.card.due }
        s.reviewDue.sort { $0.card.due < $1.card.due }
        s.newItem = nextNewItem(now: now, backlog: s.reviewDue.count)
        return s
    }

    private func introducedKey(_ day: String, _ direction: CardDirection) -> String {
        direction == .recognition ? day : "\(day)|production"
    }

    private func introducedToday(_ direction: CardDirection, now: Date) -> Int {
        progress.introducedPerDay[introducedKey(StudyDay.key(for: now), direction)] ?? 0
    }

    private func effectiveLimit(_ limit: Int, backlog: Int) -> Int {
        let threshold = max(limit, 1) * Self.backlogFactor
        if backlog > threshold * 2 { return 0 }
        if backlog > threshold { return limit / 2 }
        return limit
    }

    private func nextNewItem(now: Date, backlog: Int) -> StudyItem? {
        let recLimit = effectiveLimit(settings.dailyNewLimit, backlog: backlog)
        let prodLimit = effectiveLimit(settings.dailyNewProductionLimit, backlog: backlog)
        if introducedToday(.recognition, now: now) < recLimit, let w = nextNewRecognition(skip: 0) {
            return StudyItem(key: CardKey(wordID: w.id, direction: .recognition), word: w, card: FSRSCard(due: now), isNew: true)
        }
        if settings.productionEnabled,
           introducedToday(.production, now: now) < prodLimit,
           let w = nextNewProduction(skip: 0) {
            return StudyItem(key: CardKey(wordID: w.id, direction: .production), word: w, card: FSRSCard(due: now), isNew: true)
        }
        return nil
    }

    /// 오늘 남은 신규 카드 수 (한도와 후보 수 중 작은 값).
    private func remainingNew(_ direction: CardDirection, now: Date, backlog: Int, next: (Int) -> Word?) -> Int {
        let limit = effectiveLimit(direction == .recognition ? settings.dailyNewLimit : settings.dailyNewProductionLimit, backlog: backlog)
        let left = max(0, limit - introducedToday(direction, now: now))
        var n = 0
        while n < left, next(n) != nil { n += 1 }
        return n
    }

    private func nextNewRecognition(skip: Int) -> Word? {
        var skipped = 0
        for w in newOrder where settings.enabledLevels.contains(w.level) {
            if progress.cards[CardKey(wordID: w.id, direction: .recognition).string] != nil { continue }
            if skipped == skip { return w }
            skipped += 1
        }
        return nil
    }

    private func nextNewProduction(skip: Int) -> Word? {
        var skipped = 0
        for w in newOrder where settings.enabledLevels.contains(w.level) {
            guard let rec = progress.cards[CardKey(wordID: w.id, direction: .recognition).string],
                  rec.phase == .review, (rec.stability ?? 0) >= settings.productionUnlockDays,
                  progress.cards[CardKey(wordID: w.id, direction: .production).string] == nil else { continue }
            if skipped == skip { return w }
            skipped += 1
        }
        return nil
    }
}
