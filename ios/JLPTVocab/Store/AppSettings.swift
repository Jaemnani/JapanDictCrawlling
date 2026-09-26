import Foundation

final class AppSettings: ObservableObject {
    private let defaults = UserDefaults.standard

    /// 하루에 새로 배우는 단어 수 (일본어 → 뜻 카드 기준).
    @Published var dailyNewLimit: Int { didSet { defaults.set(dailyNewLimit, forKey: "dailyNewLimit") } }
    /// 뜻 → 일본어 카드를 하루에 새로 여는 수.
    @Published var dailyNewProductionLimit: Int { didSet { defaults.set(dailyNewProductionLimit, forKey: "dailyNewProductionLimit") } }
    /// FSRS 목표 기억률. 높을수록 복습이 잦아진다.
    @Published var desiredRetention: Double { didSet { defaults.set(desiredRetention, forKey: "desiredRetention") } }
    @Published var enabledLevels: Set<Int> { didSet { defaults.set(Array(enabledLevels), forKey: "enabledLevels") } }
    @Published var productionEnabled: Bool { didSet { defaults.set(productionEnabled, forKey: "productionEnabled") } }
    /// 일본어 → 뜻 카드가 이 안정도(일) 이상이 되면 뜻 → 일본어 카드를 연다.
    @Published var productionUnlockDays: Double { didSet { defaults.set(productionUnlockDays, forKey: "productionUnlockDays") } }
    @Published var autoSpeak: Bool { didSet { defaults.set(autoSpeak, forKey: "autoSpeak") } }
    @Published var showHanjaHint: Bool { didSet { defaults.set(showHanjaHint, forKey: "showHanjaHint") } }

    init() {
        // 모든 저장 프로퍼티가 초기화되기 전에는 self.defaults 를 쓸 수 없으므로 지역 상수로 읽는다.
        let defaults = UserDefaults.standard
        defaults.register(defaults: [
            "dailyNewLimit": 20,
            "dailyNewProductionLimit": 10,
            "desiredRetention": 0.9,
            "enabledLevels": [5],
            "productionEnabled": true,
            "productionUnlockDays": 7.0,
            "autoSpeak": true,
            "showHanjaHint": true,
        ])
        dailyNewLimit = defaults.integer(forKey: "dailyNewLimit")
        dailyNewProductionLimit = defaults.integer(forKey: "dailyNewProductionLimit")
        desiredRetention = defaults.double(forKey: "desiredRetention")
        enabledLevels = Set((defaults.array(forKey: "enabledLevels") as? [Int]) ?? [5])
        productionEnabled = defaults.bool(forKey: "productionEnabled")
        productionUnlockDays = defaults.double(forKey: "productionUnlockDays")
        autoSpeak = defaults.bool(forKey: "autoSpeak")
        showHanjaHint = defaults.bool(forKey: "showHanjaHint")
    }
}
