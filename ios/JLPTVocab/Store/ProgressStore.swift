import Foundation

/// 학습 진도 (카드 상태 + 복습 기록). Application Support/progress.json 에 저장한다.
/// 복습 기록은 나중에 py-fsrs Optimizer 로 개인 파라미터를 학습시킬 때 쓸 수 있도록 남긴다.
struct ProgressData: Codable {
    var cards: [String: FSRSCard] = [:]     // CardKey.string -> 상태
    var introducedPerDay: [String: Int] = [:] // "2026-09-26" -> 그날 처음 본 카드 수
    var reviewsPerDay: [String: Int] = [:]
    var log: [ReviewLogEntry] = []
}

enum ProgressStore {
    static var fileURL: URL {
        let dir = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir.appendingPathComponent("progress.json")
    }

    static func load() -> ProgressData {
        guard let data = try? Data(contentsOf: fileURL) else { return ProgressData() }
        return (try? decoder.decode(ProgressData.self, from: data)) ?? ProgressData()
    }

    static func save(_ progress: ProgressData) {
        guard let data = try? encoder.encode(progress) else { return }
        try? data.write(to: fileURL, options: .atomic)
    }

    /// 공유 시트로 내보낼 백업 파일.
    static func exportURL(_ progress: ProgressData) -> URL? {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("jlpt-progress.json")
        guard let data = try? encoder.encode(progress), (try? data.write(to: url, options: .atomic)) != nil else { return nil }
        return url
    }

    static func importData(from url: URL) -> ProgressData? {
        let scoped = url.startAccessingSecurityScopedResource()
        defer { if scoped { url.stopAccessingSecurityScopedResource() } }
        guard let data = try? Data(contentsOf: url) else { return nil }
        return try? decoder.decode(ProgressData.self, from: data)
    }

    private static let encoder: JSONEncoder = {
        let e = JSONEncoder()
        e.dateEncodingStrategy = .iso8601
        return e
    }()

    private static let decoder: JSONDecoder = {
        let d = JSONDecoder()
        d.dateDecodingStrategy = .iso8601
        return d
    }()
}

/// 하루의 경계. Anki 처럼 새벽 4시에 날짜가 바뀐다.
enum StudyDay {
    static let rolloverHour = 4

    static func key(for date: Date = Date()) -> String {
        let shifted = date.addingTimeInterval(-Double(rolloverHour) * 3600)
        let f = DateFormatter()
        f.calendar = Calendar(identifier: .gregorian)
        f.locale = Locale(identifier: "en_US_POSIX")
        f.dateFormat = "yyyy-MM-dd"
        return f.string(from: shifted)
    }

    /// 다음 날짜 경계 시각. 복습 카드는 due 가 이 시각 이전이면 오늘 할 일로 본다.
    static func nextRollover(after date: Date = Date()) -> Date {
        let cal = Calendar.current
        var comps = cal.dateComponents([.year, .month, .day], from: date)
        comps.hour = rolloverHour
        let todayRollover = cal.date(from: comps) ?? date
        return todayRollover > date ? todayRollover : cal.date(byAdding: .day, value: 1, to: todayRollover) ?? date
    }
}
