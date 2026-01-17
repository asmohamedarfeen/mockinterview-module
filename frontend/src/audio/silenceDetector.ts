/**
 * Silence detection using Web Audio API
 * Detects silence using RMS energy calculation
 * Phase 2: Full implementation with 2-second threshold
 * Phase 1: Placeholder structure
 */

export interface SilenceDetectorCallbacks {
  onSilenceDetected?: (durationSeconds: number) => void;
  onAudioLevel?: (level: number) => void; // 0-1 audio level for visualization
  onError?: (error: Error) => void;
}

export class SilenceDetector {
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private microphone: MediaStreamAudioSourceNode | null = null;
  private stream: MediaStream | null = null;
  private dataArray: Uint8Array | null = null;
  private timeDataArray: Uint8Array | null = null; // Time domain data for RMS
  private silenceThreshold = 0.01; // RMS threshold (0-1)
  private silenceDuration = 0; // Current silence duration in seconds
  private silenceThresholdSeconds = 2.0; // 2 seconds of silence triggers detection
  private checkInterval: NodeJS.Timeout | null = null;
  private lastSoundTime = Date.now();
  private callbacks: SilenceDetectorCallbacks = {};
  private hasTriggeredSilence = false; // Prevent multiple triggers

  constructor(callbacks: SilenceDetectorCallbacks = {}) {
    this.callbacks = callbacks;
  }

  /**
   * Initialize audio context and analyser
   */
  async initialize(stream: MediaStream): Promise<void> {
    try {
      this.stream = stream;
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 2048;
      this.analyser.smoothingTimeConstant = 0.3; // Lower for more responsive detection

      this.microphone = this.audioContext.createMediaStreamSource(stream);
      this.microphone.connect(this.analyser);

      const bufferLength = this.analyser.frequencyBinCount;
      this.dataArray = new Uint8Array(bufferLength);
      this.timeDataArray = new Uint8Array(this.analyser.fftSize);

      // Start checking for silence
      this.startSilenceDetection();
    } catch (error) {
      console.error("Failed to initialize silence detector:", error);
      if (this.callbacks.onError) {
        this.callbacks.onError(error as Error);
      }
    }
  }

  /**
   * Start silence detection loop
   */
  private startSilenceDetection(): void {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
    }

    this.checkInterval = setInterval(() => {
      this.checkSilence();
    }, 100); // Check every 100ms
  }

  /**
   * Check current audio level and detect silence
   */
  private checkSilence(): void {
    if (!this.analyser || !this.timeDataArray) {
      return;
    }

    // Get time domain data (waveform data) for accurate RMS calculation
    this.analyser.getByteTimeDomainData(this.timeDataArray);

    // Calculate RMS (Root Mean Square) energy from time domain data
    let sum = 0;
    for (let i = 0; i < this.timeDataArray.length; i++) {
      // Convert byte (0-255) to normalized sample (-1 to 1)
      const normalizedSample = (this.timeDataArray[i] - 128) / 128;
      sum += normalizedSample * normalizedSample;
    }
    const rms = Math.sqrt(sum / this.timeDataArray.length);

    // Notify audio level for visualization (0-1 range)
    if (this.callbacks.onAudioLevel) {
      this.callbacks.onAudioLevel(Math.min(1, rms * 10)); // Scale for better visualization
    }

    // Check if audio level is below threshold
    if (rms < this.silenceThreshold) {
      this.silenceDuration += 0.1; // Add 100ms (check interval)

      // Check if silence threshold exceeded (only trigger once)
      if (this.silenceDuration >= this.silenceThresholdSeconds && !this.hasTriggeredSilence) {
        this.hasTriggeredSilence = true;
        if (this.callbacks.onSilenceDetected) {
          this.callbacks.onSilenceDetected(this.silenceDuration);
        }
      }
    } else {
      // Sound detected, reset silence duration and trigger flag
      this.silenceDuration = 0;
      this.hasTriggeredSilence = false;
      this.lastSoundTime = Date.now();
    }
  }

  /**
   * Stop silence detection and cleanup
   */
  stop(): void {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }

    if (this.microphone) {
      this.microphone.disconnect();
      this.microphone = null;
    }

    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }

    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }

    this.analyser = null;
    this.dataArray = null;
    this.timeDataArray = null;
    this.silenceDuration = 0;
    this.hasTriggeredSilence = false;
  }

  /**
   * Reset silence detection (useful when starting new recording)
   */
  reset(): void {
    this.silenceDuration = 0;
    this.hasTriggeredSilence = false;
    this.lastSoundTime = Date.now();
  }

  /**
   * Get current audio level (0-1)
   */
  getCurrentAudioLevel(): number {
    if (!this.analyser || !this.timeDataArray) {
      return 0;
    }

    this.analyser.getByteTimeDomainData(this.timeDataArray);
    let sum = 0;
    for (let i = 0; i < this.timeDataArray.length; i++) {
      const normalizedSample = (this.timeDataArray[i] - 128) / 128;
      sum += normalizedSample * normalizedSample;
    }
    const rms = Math.sqrt(sum / this.timeDataArray.length);
    return Math.min(1, rms * 10);
  }

  /**
   * Set silence threshold in seconds
   */
  setSilenceThreshold(seconds: number): void {
    this.silenceThresholdSeconds = seconds;
  }

  /**
   * Set RMS energy threshold (0-1)
   */
  setRMSThreshold(threshold: number): void {
    this.silenceThreshold = Math.max(0, Math.min(1, threshold));
  }
}
