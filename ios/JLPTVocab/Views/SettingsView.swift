import SwiftUI
import UniformTypeIdentifiers

struct SettingsView: View {
    @EnvironmentObject var engine: StudyEngine
    @EnvironmentObject var settings: AppSettings
    @State private var confirmReset = false
    @State private var importing = false
    @State private var exportURL: URL?
    @State private var message: String?

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    ForEach([5, 4, 3, 2, 1], id: \.self) { level in
                        Toggle("N\(level)", isOn: Binding(
                            get: { settings.enabledLevels.contains(level) },
                            set: { on in
                                if on { settings.enabledLevels.insert(level) } else { settings.enabledLevels.remove(level) }
                            }
                        ))
                    }
                } header: {
                    Text("학습할 레벨")
                } footer: {
                    Text("여러 레벨을 켜면 쉬운 레벨(N5)의 새 단어부터 나옵니다.")
                }

                Section {
                    Stepper("새 단어 하루 \(settings.dailyNewLimit)개", value: $settings.dailyNewLimit, in: 0...100, step: 5)
                    VStack(alignment: .leading) {
                        Text("목표 기억률 \(Int((settings.desiredRetention * 100).rounded()))%")
                        Slider(value: $settings.desiredRetention, in: 0.8...0.95, step: 0.01)
                    }
                } header: {
                    Text("하루 학습량")
                } footer: {
                    Text("새 단어 1개는 이후 복습 부담이 계속 쌓입니다. 목표 기억률을 높이면 복습이 더 자주 돌아옵니다 (FSRS 기본값 90%).")
                }

                Section {
                    Toggle("뜻 → 일본어 카드", isOn: $settings.productionEnabled)
                    if settings.productionEnabled {
                        Stepper("하루 \(settings.dailyNewProductionLimit)개 추가", value: $settings.dailyNewProductionLimit, in: 0...100, step: 5)
                        Stepper("일본어 → 뜻 안정도 \(Int(settings.productionUnlockDays))일부터", value: $settings.productionUnlockDays, in: 1...60, step: 1)
                    }
                } header: {
                    Text("말하기·쓰기용 카드")
                } footer: {
                    Text("뜻을 보고 일본어를 떠올리는 카드는 알아보는 카드가 어느 정도 익숙해진 단어만 엽니다.")
                }

                Section("표시") {
                    Toggle("정답 볼 때 발음 자동 재생", isOn: $settings.autoSpeak)
                    Toggle("한국 한자음 힌트 (経済 → 경제)", isOn: $settings.showHanjaHint)
                }

                Section {
                    Button("진도 내보내기") {
                        exportURL = ProgressStore.exportURL(engine.progress)
                    }
                    if let url = exportURL {
                        ShareLink(item: url) { Label("jlpt-progress.json 공유", systemImage: "square.and.arrow.up") }
                    }
                    Button("진도 가져오기") { importing = true }
                    Button("진도 초기화", role: .destructive) { confirmReset = true }
                } header: {
                    Text("데이터")
                } footer: {
                    Text("복습 기록 \(engine.progress.log.count)건. 내보낸 파일의 기록으로 py-fsrs Optimizer 를 돌리면 개인 맞춤 파라미터를 얻을 수 있습니다.")
                }
            }
            .navigationTitle("설정")
            .confirmationDialog("모든 학습 기록을 지울까요?", isPresented: $confirmReset, titleVisibility: .visible) {
                Button("초기화", role: .destructive) { engine.resetProgress() }
            }
            .fileImporter(isPresented: $importing, allowedContentTypes: [.json]) { result in
                if case .success(let url) = result, let data = ProgressStore.importData(from: url) {
                    engine.replaceProgress(data)
                    message = "카드 \(data.cards.count)장, 기록 \(data.log.count)건을 가져왔습니다."
                } else {
                    message = "가져오지 못했습니다."
                }
            }
            .alert(message ?? "", isPresented: Binding(get: { message != nil }, set: { if !$0 { message = nil } })) {
                Button("확인", role: .cancel) {}
            }
        }
    }
}
