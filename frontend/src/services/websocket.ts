/**
 * WebSocket client service for Qrow IQ
 * Type-safe message handling with reconnection logic
 */

// Message types matching backend
export enum MessageType {
  TRANSCRIBE = "TRANSCRIBE",
  SILENCE_DETECTED = "SILENCE_DETECTED",
  START_INTERVIEW = "START_INTERVIEW",
  END_INTERVIEW = "END_INTERVIEW",
  PING = "PING",
}

export enum ServerMessageType {
  QUESTION_READY = "QUESTION_READY",
  TTS_AUDIO = "TTS_AUDIO",
  EVALUATION_UPDATE = "EVALUATION_UPDATE",
  INTERVIEW_COMPLETE = "INTERVIEW_COMPLETE",
  ERROR = "ERROR",
  PONG = "PONG",
  STATE_UPDATE = "STATE_UPDATE",
}

// Client message interfaces
export interface StartInterviewMessage {
  type: MessageType.START_INTERVIEW;
  session_id: string;
  job_role: string;
  job_description: string;
  question_count: number;
  timestamp?: string;
}

export interface TranscribeMessage {
  type: MessageType.TRANSCRIBE;
  session_id: string;
  transcript: string;
  is_final: boolean;
  timestamp?: string;
}

export interface SilenceDetectedMessage {
  type: MessageType.SILENCE_DETECTED;
  session_id: string;
  duration_seconds: number;
  timestamp?: string;
}

// Server message interfaces
export interface QuestionReadyMessage {
  type: ServerMessageType.QUESTION_READY;
  session_id: string;
  question: string;
  question_number: number;
  total_questions: number;
  timestamp?: string;
}

export interface TTSAudioMessage {
  type: ServerMessageType.TTS_AUDIO;
  session_id: string;
  audio_base64: string;
  audio_format: string;
  question_id?: string;
  timestamp?: string;
}

export interface EvaluationUpdateMessage {
  type: ServerMessageType.EVALUATION_UPDATE;
  session_id: string;
  scores: Record<string, number>;
  current_question_number: number;
  timestamp?: string;
}

export interface InterviewCompleteMessage {
  type: ServerMessageType.INTERVIEW_COMPLETE;
  session_id: string;
  final_scores: Record<string, number>;
  verdict: string;
  report_url?: string;
  timestamp?: string;
}

export interface ErrorMessage {
  type: ServerMessageType.ERROR;
  session_id: string;
  error_code: string;
  error_message: string;
  timestamp?: string;
}

export interface StateUpdateMessage {
  type: ServerMessageType.STATE_UPDATE;
  session_id: string;
  state: string;
  timestamp?: string;
}

export type ClientMessage = StartInterviewMessage | TranscribeMessage | SilenceDetectedMessage;
export type ServerMessage =
  | QuestionReadyMessage
  | TTSAudioMessage
  | EvaluationUpdateMessage
  | InterviewCompleteMessage
  | ErrorMessage
  | StateUpdateMessage;

// WebSocket event handlers
export type OnMessageHandler = (message: ServerMessage) => void;
export type OnErrorHandler = (error: Event) => void;
export type OnCloseHandler = () => void;
export type OnOpenHandler = () => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private reconnectTimer: NodeJS.Timeout | null = null;
  private pingInterval: NodeJS.Timeout | null = null;

  // Event handlers
  private onMessageHandler: OnMessageHandler | null = null;
  private onErrorHandler: OnErrorHandler | null = null;
  private onCloseHandler: OnCloseHandler | null = null;
  private onOpenHandler: OnOpenHandler | null = null;

  constructor(sessionId: string, backendUrl: string = "ws://localhost:8000") {
    this.sessionId = sessionId;
    this.url = `${backendUrl}/ws/interview/${sessionId}`;
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log(`WebSocket connected: ${this.sessionId}`);
          this.reconnectAttempts = 0;
          this.reconnectDelay = 1000;
          this.startPingInterval();
          if (this.onOpenHandler) {
            this.onOpenHandler();
          }
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: ServerMessage = JSON.parse(event.data);
            if (this.onMessageHandler) {
              this.onMessageHandler(message);
            }
          } catch (error) {
            console.error("Failed to parse WebSocket message:", error);
          }
        };

        this.ws.onerror = (error) => {
          console.error("WebSocket error:", error);
          if (this.onErrorHandler) {
            this.onErrorHandler(error);
          }
          reject(error);
        };

        this.ws.onclose = () => {
          console.log(`WebSocket closed: ${this.sessionId}`);
          this.stopPingInterval();
          if (this.onCloseHandler) {
            this.onCloseHandler();
          }
          this.attemptReconnect();
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      return;
    }

    this.reconnectAttempts++;
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000); // Max 30 seconds

    console.log(
      `Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${this.reconnectDelay}ms`
    );

    this.reconnectTimer = setTimeout(() => {
      this.connect().catch((error) => {
        console.error("Reconnection failed:", error);
      });
    }, this.reconnectDelay);
  }

  /**
   * Send ping messages to keep connection alive
   */
  private startPingInterval(): void {
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({
          type: MessageType.PING,
          session_id: this.sessionId,
        });
      }
    }, 20000); // Ping every 20 seconds
  }

  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  /**
   * Send message to server
   */
  send(message: ClientMessage): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error("WebSocket is not connected");
      return;
    }

    try {
      this.ws.send(JSON.stringify(message));
    } catch (error) {
      console.error("Failed to send WebSocket message:", error);
    }
  }

  /**
   * Disconnect from server
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.stopPingInterval();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  // Event handler setters
  onMessage(handler: OnMessageHandler): void {
    this.onMessageHandler = handler;
  }

  onError(handler: OnErrorHandler): void {
    this.onErrorHandler = handler;
  }

  onClose(handler: OnCloseHandler): void {
    this.onCloseHandler = handler;
  }

  onOpen(handler: OnOpenHandler): void {
    this.onOpenHandler = handler;
  }
}
