import SwiftUI

struct HomeView: View {
    @EnvironmentObject var engine: StudyEngine
    @EnvironmentObject var settings: AppSettings
    @State private var studying = false

    var body: some View {
        let counts = engine.counts()
        NavigationStack {
            List {
                Section {
                    HStack(spacing: 0) {
                        CountTile(title: "신규", value: counts.newRecognition + counts.newProduction, color: .blue)
                        CountTile(title: "학습 중", value: counts.learning, color: .orange)
                        CountTile(title: "복습", value: counts.review, color: .green)
                    }
                    .listRowInsets(EdgeInsets(top: 12, leading: 0, bottom: 12, trailing: 0))

                    Button {
                        studying = true
                    } label: {
                        Text(counts.total > 0 ? "학습 시작" : "오늘 할 카드를 다 했습니다")
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 6)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(counts.total == 0)
                    .listRowInsets(EdgeInsets())
                    .listRowBackground(Color.clear)
                } footer: {
                    VStack(alignment: .leading, spacing: 4) {
                        if counts.newThrottled {
                            Text("밀린 복습이 많아 오늘은 새 단어를 줄였습니다. 복습을 먼저 정리하면 다시 늘어납니다.")
                        }
                        if counts.reviewLaterToday > 0 {
                            Text("오늘 중 복습 시기가 오는 카드 \(counts.reviewLaterToday)장이 더 있습니다.")
                        }
                        if let days = engine.daysToFinish(), days > 0 {
                            Text("지금 속도(하루 \(settings.dailyNewLimit)개)로 켜 둔 레벨의 새 단어를 모두 보는 데 약 \(days)일.")
                        }
                    }
                }

                Section("레벨별 진도") {
                    ForEach(engine.levelStats(), id: \.level) { s in
                        LevelRow(stats: s, enabled: settings.enabledLevels.contains(s.level))
                    }
                }

                Section {
                    Text("답을 보기 전에 먼저 떠올려 보세요. 틀려도 괜찮습니다. 떠올리려는 시도 자체가 기억을 강화합니다. 정답이 나오면 발음을 소리 내어 따라 해 보세요. 복습 시점은 기억이 흐려질 즈음으로 FSRS 가 정합니다.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("JLPT 단어")
            .navigationDestination(isPresented: $studying) {
                StudyView()
            }
        }
    }
}

private struct CountTile: View {
    let title: String
    let value: Int
    let color: Color

    var body: some View {
        VStack(spacing: 4) {
            Text("\(value)")
                .font(.title.bold().monospacedDigit())
                .foregroundStyle(color)
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
    }
}

private struct LevelRow: View {
    let stats: StudyEngine.LevelStats
    let enabled: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("N\(stats.level)").font(.headline)
                if !enabled {
                    Text("꺼짐").font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
                Text("\(stats.started) / \(stats.total)")
                    .font(.subheadline.monospacedDigit())
                    .foregroundStyle(.secondary)
            }
            ProgressView(value: Double(stats.started), total: Double(max(stats.total, 1)))
            Text("장기 기억(안정도 21일+) \(stats.mature)")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .opacity(enabled ? 1 : 0.5)
    }
}
