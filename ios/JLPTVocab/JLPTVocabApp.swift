import SwiftUI

@main
struct JLPTVocabApp: App {
    @StateObject private var settings: AppSettings
    @StateObject private var engine: StudyEngine

    init() {
        let settings = AppSettings()
        _settings = StateObject(wrappedValue: settings)
        _engine = StateObject(wrappedValue: StudyEngine(settings: settings))
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(settings)
                .environmentObject(engine)
        }
    }
}

struct ContentView: View {
    @EnvironmentObject var engine: StudyEngine

    var body: some View {
        if engine.words.isEmpty {
            ContentUnavailableView(
                "단어 데이터가 없습니다",
                systemImage: "tray",
                description: Text("python export_app_data.py naver_jlpt_words.xlsx 로\nJLPTVocab/Resources/words.json 을 만든 뒤 다시 빌드하세요.")
            )
        } else {
            TabView {
                HomeView()
                    .tabItem { Label("학습", systemImage: "rectangle.stack") }
                WordListView()
                    .tabItem { Label("단어", systemImage: "list.bullet") }
                SettingsView()
                    .tabItem { Label("설정", systemImage: "gearshape") }
            }
        }
    }
}
