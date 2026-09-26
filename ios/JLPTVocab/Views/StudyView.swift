import SwiftUI

struct StudyView: View {
    @EnvironmentObject var engine: StudyEngine
    @EnvironmentObject var settings: AppSettings
    @State private var revealed = false

    var body: some View {
        VStack(spacing: 0) {
            if let item = engine.current {
                ScrollView {
                    CardFace(item: item, revealed: revealed, showHanja: settings.showHanjaHint)
                        .padding(.horizontal, 20)
                        .padding(.top, 24)
                        .frame(maxWidth: .infinity)
                }
                .contentShape(Rectangle())
                .onTapGesture { if !revealed { reveal(item) } }

                controls(item)
                    .padding(.horizontal, 16)
                    .padding(.bottom, 12)
            } else {
                FinishedView(reviewed: engine.sessionReviewed, waitingUntil: engine.waitingUntil) {
                    engine.advance()
                }
            }
        }
        .navigationTitle("\(engine.sessionReviewed)장 완료")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            revealed = false
            engine.startSession()
        }
        .onDisappear { engine.endSession() }
    }

    @ViewBuilder
    private func controls(_ item: StudyItem) -> some View {
        if revealed {
            let intervals = engine.previewIntervals()
            HStack(spacing: 8) {
                RateButton(title: "다시", interval: intervals[.again], color: .red) { rate(.again) }
                RateButton(title: "어려움", interval: intervals[.hard], color: .orange) { rate(.hard) }
                RateButton(title: "알맞음", interval: intervals[.good], color: .green) { rate(.good) }
                RateButton(title: "쉬움", interval: intervals[.easy], color: .blue) { rate(.easy) }
            }
        } else {
            Button {
                reveal(item)
            } label: {
                Text("정답 보기")
                    .font(.headline)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
            }
            .buttonStyle(.borderedProminent)
        }
    }

    private func reveal(_ item: StudyItem) {
        revealed = true
        if settings.autoSpeak { Speaker.shared.speak(item.word.speechText) }
    }

    private func rate(_ rating: Rating) {
        revealed = false
        engine.answer(rating)
    }
}

/// 카드 앞/뒷면.
struct CardFace: View {
    let item: StudyItem
    let revealed: Bool
    let showHanja: Bool

    var body: some View {
        VStack(spacing: 18) {
            HStack {
                Text(item.word.levelLabel)
                Text(item.key.direction.label)
                if item.isNew { Text("NEW").foregroundStyle(.blue) }
                Spacer()
            }
            .font(.caption.bold())
            .foregroundStyle(.secondary)

            switch item.key.direction {
            case .recognition:
                japanese(showReading: revealed)
                if revealed {
                    Divider()
                    meanings
                }
            case .production:
                meanings
                if revealed {
                    Divider()
                    japanese(showReading: true)
                }
            }
        }
    }

    private func japanese(showReading: Bool) -> some View {
        VStack(spacing: 8) {
            Text(item.word.word)
                .font(.system(size: 44, weight: .medium))
                .multilineTextAlignment(.center)
                .minimumScaleFactor(0.5)
            if showReading {
                HStack(spacing: 8) {
                    if !item.word.reading.isEmpty {
                        Text(item.word.reading).font(.title3)
                    }
                    Button {
                        Speaker.shared.speak(item.word.speechText)
                    } label: {
                        Image(systemName: "speaker.wave.2")
                    }
                    .buttonStyle(.borderless)
                }
                .foregroundStyle(.secondary)
                if showHanja && !item.word.hanjaKo.isEmpty {
                    Text("한자음 \(item.word.hanjaKo)")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .frame(maxWidth: .infinity)
    }

    private var meanings: some View {
        VStack(alignment: .leading, spacing: 6) {
            if !item.word.pos.isEmpty {
                Text(item.word.pos.joined(separator: ", "))
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            ForEach(Array(item.word.meanings.enumerated()), id: \.offset) { i, m in
                Text(item.word.meanings.count > 1 ? "\(i + 1). \(m)" : m)
                    .font(.title3)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

private struct RateButton: View {
    let title: String
    let interval: TimeInterval?
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 2) {
                Text(title).font(.subheadline.bold())
                Text(interval.map(formatInterval) ?? "")
                    .font(.caption2.monospacedDigit())
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 8)
        }
        .buttonStyle(.bordered)
        .tint(color)
    }
}

private struct FinishedView: View {
    let reviewed: Int
    let waitingUntil: Date?
    let refresh: () -> Void

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "checkmark.circle")
                .font(.system(size: 56))
                .foregroundStyle(.green)
            Text(reviewed > 0 ? "\(reviewed)장 완료" : "지금 할 카드가 없습니다")
                .font(.title2.bold())
            if let t = waitingUntil {
                Text("학습 단계 카드가 \(t.formatted(date: .omitted, time: .shortened))에 다시 나옵니다.")
                    .foregroundStyle(.secondary)
                Button("다시 확인", action: refresh)
                    .buttonStyle(.bordered)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

func formatInterval(_ t: TimeInterval) -> String {
    let minutes = t / 60
    if minutes < 60 { return "\(max(1, Int(minutes.rounded())))분" }
    let hours = minutes / 60
    if hours < 24 { return "\(Int(hours.rounded()))시간" }
    let days = hours / 24
    if days < 30 { return "\(Int(days.rounded()))일" }
    if days < 365 { return String(format: "%.1f개월", days / 30) }
    return String(format: "%.1f년", days / 365)
}
