/**
 * Text-to-Speech utility using Web Speech API
 * Provides a professional female voice for the AI interviewer
 */

export const speak = (text: string, onEnd?: () => void, onStart?: () => void) => {
    if (!window.speechSynthesis) {
        console.error('Web Speech API not supported');
        if (onEnd) onEnd();
        return;
    }

    const synth = window.speechSynthesis;

    // Cancel any pending speech
    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);

    // Try to find a good female voice
    const voices = synth.getVoices();
    const femaleVoice = voices.find(v =>
        v.lang.includes('en') &&
        (v.name.includes('Female') || v.name.includes('Google') || v.name.includes('Samantha') || v.name.includes('Victoria'))
    );

    if (femaleVoice) {
        utterance.voice = femaleVoice;
    }

    // Configure speech parameters for a professional tone
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    // Event handlers
    utterance.onstart = () => {
        if (onStart) onStart();
    };

    utterance.onend = () => {
        if (onEnd) onEnd();
    };

    utterance.onerror = (event) => {
        console.error('TTS Error:', event);
        if (onEnd) onEnd();
    };

    synth.speak(utterance);
};

export const stopSpeaking = () => {
    if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
    }
};
