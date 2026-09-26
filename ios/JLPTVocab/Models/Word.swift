import Foundation

/// export_app_data.py 가 만든 words.json 의 단어 하나.
struct Word: Codable, Identifiable, Hashable {
    let id: String          // "5|会う|あう"
    let level: Int          // 1(N1) ~ 5(N5)
    let word: String        // 한자 표기가 있으면 한자, 없으면 가나
    let reading: String     // 가나 읽기 (한자 표기가 없으면 "")
    let pos: [String]
    let meanings: [String]
    let hanjaKo: String     // 한국 한자음 힌트 (経済 -> 경제, 会う -> 会(회))
    let order: Int          // 레벨 안 신규 학습 순서 (섞인 순서)

    /// TTS 로 읽을 텍스트. 접사 표시 '-' 는 뺀다.
    var speechText: String {
        (reading.isEmpty ? word : reading).replacingOccurrences(of: "-", with: "")
    }

    var levelLabel: String { "N\(level)" }
}

struct WordBundle: Codable {
    let version: Int
    let generatedAt: String
    let words: [Word]

    static func loadFromBundle() -> [Word] {
        guard let url = Bundle.main.url(forResource: "words", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let bundle = try? JSONDecoder().decode(WordBundle.self, from: data)
        else { return [] }
        return bundle.words
    }
}

/// 카드 방향. 수용(일본어 → 뜻)을 먼저 익히고, 익숙해진 단어만 산출(뜻 → 일본어)을 추가한다.
enum CardDirection: String, Codable, CaseIterable {
    case recognition, production

    var label: String {
        switch self {
        case .recognition: return "일본어 → 뜻"
        case .production: return "뜻 → 일본어"
        }
    }
}

struct CardKey: Hashable, Codable {
    let wordID: String
    let direction: CardDirection

    var string: String { "\(direction.rawValue):\(wordID)" }

    init(wordID: String, direction: CardDirection) {
        self.wordID = wordID
        self.direction = direction
    }

    init?(string: String) {
        guard let colon = string.firstIndex(of: ":"),
              let dir = CardDirection(rawValue: String(string[..<colon])) else { return nil }
        self.direction = dir
        self.wordID = String(string[string.index(after: colon)...])
    }
}

struct ReviewLogEntry: Codable {
    let card: String        // CardKey.string
    let rating: Int
    let reviewedAt: Date
    let durationMs: Int?
}
