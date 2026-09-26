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
                    if counts.reviewLaterToday > 0 {
                        Text("오늘 중 복습 시기가 오는 카드 \(counts.reviewLaterToday)장이 더 있습니다.")
                    }
                }

                Section("레벨별 진도") {
                    ForEach(engine.levelStats(), id: \.level) { s in
                        LevelRow(stats: s, enabled: settings.enabledLevels.contains(s.level))
                    }
                }

                Section {
                    Text("매일 조금씩, 떠올린 다음에 답을 확인하세요. 기억이 흐려질 즈음 다시 묻도록 FSRS 가 복습 시점을 정합니다.")
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
