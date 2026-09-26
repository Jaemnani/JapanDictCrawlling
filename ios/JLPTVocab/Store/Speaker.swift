import AVFoundation

/// 일본어 TTS. 기기에 설치된 ja-JP 음성을 쓴다 (설정 > 손쉬운 사용 > 읽기 및 말하기 > 음성 에서 고음질 음성 추가 가능).
final class Speaker {
    static let shared = Speaker()
    private let synth = AVSpeechSynthesizer()
    private let voice = AVSpeechSynthesisVoice(language: "ja-JP")

    func speak(_ text: String) {
        guard !text.isEmpty else { return }
        try? AVAudioSession.sharedInstance().setCategory(.playback, mode: .spokenAudio, options: [.duckOthers])
        if synth.isSpeaking { synth.stopSpeaking(at: .immediate) }
        let u = AVSpeechUtterance(string: text)
        u.voice = voice
        u.rate = AVSpeechUtteranceDefaultSpeechRate * 0.9
        synth.speak(u)
    }
}
