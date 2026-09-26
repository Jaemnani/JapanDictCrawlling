import SwiftUI

struct WordListView: View {
    @EnvironmentObject var engine: StudyEngine
    @State private var level = 5
    @State private var query = ""

    private var filtered: [Word] {
        let q = query.trimmingCharacters(in: .whitespaces)
        let base = engine.words.filter { q.isEmpty ? $0.level == level : true }
        let hits = q.isEmpty ? base : base.filter {
            $0.word.contains(q) || $0.reading.contains(q) || $0.meanings.contains { $0.contains(q) } || $0.hanjaKo.contains(q)
        }
        return hits.sorted { $0.level != $1.level ? $0.level > $1.level : $0.reading + $0.word < $1.reading + $1.word }
    }

    var body: some View {
        NavigationStack {
            List {
                if query.isEmpty {
                    Picker("레벨", selection: $level) {
                        ForEach([5, 4, 3, 2, 1], id: \.self) { Text("N\($0)").tag($0) }
                    }
                    .pickerStyle(.segmented)
                    .listRowBackground(Color.clear)
                }
                ForEach(filtered) { w in
                    NavigationLink(value: w) {
                        WordRow(word: w, status: status(w))
                    }
                }
            }
            .listStyle(.plain)
            .searchable(text: $query, prompt: "일본어·읽기·뜻·한자음 검색")
            .navigationTitle("단어")
            .navigationDestination(for: Word.self) { WordDetailView(word: $0) }
        }
    }

    private func status(_ w: Word) -> String {
        guard let c = engine.card(for: w, .recognition) else { return "" }
        switch c.phase {
        case .learning, .relearning: return "학습 중"
        case .review: return (c.stability ?? 0) >= 21 ? "장기" : "복습"
        }
    }
}

private struct WordRow: View {
    let word: Word
    let status: String

    var body: some View {
        HStack(alignment: .firstTextBaseline) {
            VStack(alignment: .leading, spacing: 2) {
                HStack(alignment: .firstTextBaseline, spacing: 6) {
                    Text(word.word).font(.headline)
                    Text(word.reading).font(.subheadline).foregroundStyle(.secondary)
                }
                Text(word.meanings.first ?? "")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }
            Spacer()
            if !status.isEmpty {
                Text(status)
                    .font(.caption2)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(.quaternary, in: Capsule())
            }
        }
    }
}

struct WordDetailView: View {
    @EnvironmentObject var engine: StudyEngine
    let word: Word
    @State private var note = ""

    var body: some View {
        List {
            Section {
                VStack(alignment: .leading, spacing: 6) {
                    Text(word.word).font(.largeTitle)
                    HStack {
                        if !word.reading.isEmpty { Text(word.reading).font(.title3) }
                        Button { Speaker.shared.speak(word.speechText) } label: { Image(systemName: "speaker.wave.2") }
                            .buttonStyle(.borderless)
                    }
                    .foregroundStyle(.secondary)
                    if !word.hanjaKo.isEmpty {
                        Text("한자음 \(word.hanjaKo)").font(.footnote).foregroundStyle(.secondary)
                    }
                }
            }
            Section(word.pos.isEmpty ? "뜻" : "뜻 · \(word.pos.joined(separator: ", "))") {
                ForEach(Array(word.meanings.enumerated()), id: \.offset) { i, m in
                    Text(word.meanings.count > 1 ? "\(i + 1). \(m)" : m)
                }
            }
            Section {
                TextField("예: 経済(けいざい) = 경제, 발음이 '케이자이'", text: $note, axis: .vertical)
                    .lineLimit(1...4)
                    .onSubmit { engine.setNote(note, for: word) }
            } header: {
                Text("연상 메모")
            } footer: {
                Text("스스로 만든 연상은 정답을 볼 때 함께 나옵니다. 연상만으로는 오래 가지 않으므로 복습과 같이 쓰세요.")
            }
            Section("학습 상태") {
                ForEach(CardDirection.allCases, id: \.self) { d in
                    LabeledContent(d.label, value: describe(engine.card(for: word, d)))
                }
            }
        }
        .navigationTitle(word.levelLabel)
        .navigationBarTitleDisplayMode(.inline)
        .onAppear { note = engine.note(for: word) }
        .onDisappear { engine.setNote(note, for: word) }
    }

    private func describe(_ c: FSRSCard?) -> String {
        guard let c else { return "아직 안 봄" }
        let due = c.due.formatted(date: .abbreviated, time: .shortened)
        let r = Int((engine.fsrs.retrievability(c, at: Date()) * 100).rounded())
        return c.phase == .review ? "다음 \(due) · 기억률 \(r)%" : "학습 단계 · 다음 \(due)"
    }
}
