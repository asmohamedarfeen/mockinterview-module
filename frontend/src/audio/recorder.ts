/**
 * Audio recorder using Web Speech API
 * Phase 2: Full implementation with real-time transcription
 * Phase 1: Placeholder structure
 */

export interface RecorderCallbacks {
  onTranscript?: (transcript: string, isFinal: boolean) => void;
  onError?: (error: Error) => void;
  onStart?: () => void;
  onStop?: () => void;
}

export class AudioRecorder {
  private recognition: SpeechRecognition | null = null;
  private isRecording = false;
  private callbacks: RecorderCallbacks = {};
  private audioStream: MediaStream | null = null;
  private transcriptBuffer: string = "";

  constructor(callbacks: RecorderCallbacks = {}) {
    this.callbacks = callbacks;
    this.initializeRecognition();
  }

  /**
   * Initialize Web Speech API recognition
   */
  private initializeRecognition(): void {
    if (!("webkitSpeechRecognition" in window) && !("SpeechRecognition" in window)) {
      console.error("Web Speech API not supported in this browser");
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    this.recognition = new SpeechRecognition();
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.lang = "en-US";

    this.recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interimTranscript = "";
      let finalTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + " ";
        } else {
          interimTranscript += transcript;
        }
      }

      // Update transcript buffer with final results
      if (finalTranscript) {
        this.transcriptBuffer += finalTranscript;
      }

      // Call callback with interim results (for real-time feedback)
      if (interimTranscript && this.callbacks.onTranscript) {
        const fullInterim = this.transcriptBuffer + interimTranscript;
        this.callbacks.onTranscript(fullInterim.trim(), false);
      }

      // Call callback with final results
      if (finalTranscript && this.callbacks.onTranscript) {
        this.callbacks.onTranscript(this.transcriptBuffer.trim(), true);
      }
    };

    this.recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error("Speech recognition error:", event.error);
      
      // Handle specific error types
      if (event.error === "no-speech") {
        // No speech detected - not necessarily an error, just silence
        return;
      } else if (event.error === "audio-capture") {
        // Microphone not available
        if (this.callbacks.onError) {
          this.callbacks.onError(new Error("Microphone not available"));
        }
      } else if (event.error === "not-allowed") {
        // Permission denied
        if (this.callbacks.onError) {
          this.callbacks.onError(new Error("Microphone permission denied"));
        }
      } else {
        // Other errors
        if (this.callbacks.onError) {
          this.callbacks.onError(new Error(event.error));
        }
      }
    };

    this.recognition.onend = () => {
      this.isRecording = false;
      if (this.callbacks.onStop) {
        this.callbacks.onStop();
      }
    };
  }

  /**
   * Start recording audio
   */
  async start(): Promise<void> {
    if (!this.recognition) {
      throw new Error("Speech recognition not available");
    }

    if (this.isRecording) {
      console.warn("Already recording");
      return;
    }

    // Request microphone permission and get stream
    try {
      this.audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (error) {
      console.error("Failed to get microphone access:", error);
      if (this.callbacks.onError) {
        this.callbacks.onError(error as Error);
      }
      return;
    }

    // Reset transcript buffer
    this.transcriptBuffer = "";

    try {
      this.recognition.start();
      this.isRecording = true;
      if (this.callbacks.onStart) {
        this.callbacks.onStart();
      }
    } catch (error: any) {
      // Handle "already started" error gracefully
      if (error.message && error.message.includes("already started")) {
        this.isRecording = true;
        return;
      }
      console.error("Failed to start recording:", error);
      if (this.callbacks.onError) {
        this.callbacks.onError(error as Error);
      }
      // Clean up stream on error
      if (this.audioStream) {
        this.audioStream.getTracks().forEach((track) => track.stop());
        this.audioStream = null;
      }
    }
  }

  /**
   * Stop recording audio
   */
  stop(): void {
    if (!this.recognition || !this.isRecording) {
      return;
    }

    try {
      this.recognition.stop();
    } catch (error) {
      // Ignore errors when stopping
      console.debug("Error stopping recognition:", error);
    }
    
    this.isRecording = false;

    // Clean up audio stream
    if (this.audioStream) {
      this.audioStream.getTracks().forEach((track) => track.stop());
      this.audioStream = null;
    }
  }

  /**
   * Check if currently recording
   */
  getIsRecording(): boolean {
    return this.isRecording;
  }

  /**
   * Request microphone permission
   */
  async requestPermission(): Promise<boolean> {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Stop the stream immediately - we just needed permission
      stream.getTracks().forEach((track) => track.stop());
      return true;
    } catch (error) {
      console.error("Microphone permission denied:", error);
      return false;
    }
  }

  /**
   * Get the audio stream for sharing with other components (e.g., silence detector)
   */
  getAudioStream(): MediaStream | null {
    return this.audioStream;
  }

  /**
   * Get current transcript buffer
   */
  getTranscriptBuffer(): string {
    return this.transcriptBuffer.trim();
  }

  /**
   * Clear transcript buffer
   */
  clearTranscriptBuffer(): void {
    this.transcriptBuffer = "";
  }
}

// Type declarations for Web Speech API
interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
}

interface SpeechRecognitionEvent {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionErrorEvent {
  error: string;
  message: string;
}

declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}
