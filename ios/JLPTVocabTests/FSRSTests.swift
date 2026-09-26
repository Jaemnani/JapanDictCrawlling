import XCTest
@testable import JLPTVocab

/// 기대값은 py-fsrs 6.3.2 (enable_fuzzing=False) 로 같은 시각·같은 평가 순서를 재생해서 뽑은 것.
final class FSRSTests: XCTestCase {
    typealias Step = (at: TimeInterval, rating: Int, phase: Int, step: Int?, stability: Double, difficulty: Double, due: TimeInterval)

    private let t0 = Date(timeIntervalSince1970: 1_767_225_600) // 2026-01-01T00:00:00Z

    private func replay(_ steps: [Step], file: StaticString = #filePath, line: UInt = #line) {
        var fsrs = FSRS()
        fsrs.enableFuzzing = false
        var card = FSRSCard(due: t0)
        for (i, s) in steps.enumerated() {
            card = fsrs.review(card, rating: Rating(rawValue: s.rating)!, at: t0.addingTimeInterval(s.at))
            XCTAssertEqual(card.phase.rawValue, s.phase, "step \(i) phase", file: file, line: line)
            XCTAssertEqual(card.step, s.step, "step \(i) step", file: file, line: line)
            XCTAssertEqual(card.stability!, s.stability, accuracy: 1e-9, "step \(i) stability", file: file, line: line)
            XCTAssertEqual(card.difficulty!, s.difficulty, accuracy: 1e-9, "step \(i) difficulty", file: file, line: line)
            XCTAssertEqual(card.due.timeIntervalSince(t0), s.due, accuracy: 0.001, "step \(i) due", file: file, line: line)
        }
    }

    func testGoodPath() {
        replay([
            (0, 3, 1, 1, 2.3065, 2.118103970459016, 600),
            (60, 3, 2, nil, 2.3065, 2.111214235785395, 172860),
            (660, 3, 2, nil, 2.3065, 2.1043313908464483, 173460),
            (173460, 3, 2, nil, 10.977757474408312, 2.0974554287524403, 1123860),
            (1123860, 3, 2, nil, 46.35346335760037, 2.0905863426205262, 5098260),
            (5098260, 1, 3, 0, 2.9351108100987533, 7.385457884129076, 5098860),
            (5098860, 3, 2, nil, 2.9351108100987533, 7.373300795541786, 5358060),
            (5358060, 4, 2, nil, 12.053402270779435, 6.480808694891617, 6394860),
        ])
    }

    func testAgainHardEasy() {
        replay([
            (0, 1, 1, 0, 0.212, 6.4133, 60),
            (60, 2, 1, 0, 0.212, 7.604209769076838, 390),
            (400, 3, 1, 1, 0.24668918777567272, 7.5918339286046, 1000),
            (1100, 4, 2, nil, 0.48892083828453853, 6.772365417380022, 87500),
            (87500, 2, 2, nil, 1.6934165145475426, 7.842574125582147, 260300),
            (260300, 1, 3, 0, 0.4677298914348687, 9.276097154871636, 260900),
            (1124300, 3, 2, nil, 2.5629241855988645, 9.2620494270136, 1383500),
        ])
    }

    func testFuzzStaysInRange() {
        var fsrs = FSRS()
        var card = FSRSCard(due: t0)
        card = fsrs.review(card, rating: .easy, at: t0)
        fsrs.enableFuzzing = false
        let plain = fsrs.review(card, rating: .good, at: t0.addingTimeInterval(30 * 86400)).due
        fsrs.enableFuzzing = true
        for r in [0.0, 0.5, 0.999] {
            let fuzzed = fsrs.review(card, rating: .good, at: t0.addingTimeInterval(30 * 86400), random: { r }).due
            XCTAssertLessThan(abs(fuzzed.timeIntervalSince(plain)) / 86400, max(3, plain.timeIntervalSince(t0) / 86400 * 0.1))
        }
    }
}
