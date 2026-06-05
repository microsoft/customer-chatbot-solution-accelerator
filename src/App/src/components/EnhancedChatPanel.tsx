import { Button } from '@/components/primitives/button';
import { Input } from '@/components/primitives/input';
import { ScrollArea } from '@/components/primitives/scroll-area';
import { Skeleton } from '@/components/primitives/skeleton';
import { useAutoScroll } from '@/hooks/useAutoScroll';
import { getApiBaseUrl, getVoiceLiveConfig } from '@/lib/api';
import { floatTo16BitPCM, pcm16ToBase64, playPCM16Chunk, resampleTo24k } from '@/lib/audioUtils';
import { ChatMessage, Product } from '@/lib/types';
import { cn } from '@/lib/utils';
import { Send20Regular, Stop20Filled } from '@fluentui/react-icons';
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { EnhancedChatMessageBubble } from './EnhancedChatMessageBubble';

interface EnhancedChatPanelProps {
  messages: ChatMessage[];
  onSendMessage: (content: string) => void;
  onVoiceMessage?: (text: string, role: 'user' | 'assistant') => void;
  isTyping: boolean;
  onAddToCart?: (product: Product) => void;
  className?: string;
  isLoading?: boolean;
  onVoiceProcessingChange?: (isProcessing: boolean) => void;
}

export const EnhancedChatPanel = ({
  messages,
  onSendMessage,
  onVoiceMessage,
  isTyping,
  onAddToCart,
  className,
  isLoading = false,
  onVoiceProcessingChange,
}: EnhancedChatPanelProps) => {
  const [inputValue, setInputValue] = useState('');
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const [isAgentVoiceEnabled] = useState(false);
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(true);
  const [, setSpeakingMessageId] = useState<string | null>(null);
  const [spokenAssistantIds, setSpokenAssistantIds] = useState<string[]>([]);
  const [voiceSessionState, setVoiceSessionState] = useState<'idle' | 'connecting' | 'listening' | 'thinking' | 'speaking'>('idle');
  const [isVoiceTransitioning, setIsVoiceTransitioning] = useState(false);
  const [streamingVoiceText, setStreamingVoiceText] = useState('');
  const [isVoiceProcessing, setIsVoiceProcessing] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const processorNodeRef = useRef<AudioWorkletNode | null>(null);
  const playbackContextRef = useRef<AudioContext | null>(null);
  const ttsAbortControllerRef = useRef<AbortController | null>(null);
  const playbackTimeRef = useRef<number>(0);
  const clientIdRef = useRef<string>(crypto.randomUUID());
  const lastSentTranscriptRef = useRef<string>('');
  const isTypingRef = useRef(isTyping);
  const isLoadingRef = useRef(isLoading);
  const onSendMessageRef = useRef(onSendMessage);
  const onVoiceMessageRef = useRef(onVoiceMessage);
  const onVoiceProcessingChangeRef = useRef(onVoiceProcessingChange);
  const voiceConfigCacheRef = useRef<any>(null);
  const audioBufferQueueRef = useRef<string[]>([]);
  const sessionReadyRef = useRef(false);
  const isSpeakingRef = useRef(false);
  const awaitingResponseRef = useRef(false);
  const responseTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Tracks whether the current voice turn has already posted the structured tool
  // result to chat history (via the early `tool_result` event). When true, the
  // final RESPONSE_DONE transcript skips re-posting to avoid duplicates.
  const voiceStructuredPostedRef = useRef(false);
  // Buffer for tool_result text that arrives before the user transcript (transcription
  // is async in Azure Voice Live and can lag behind the function-call response).
  const pendingToolResultRef = useRef<string | null>(null);
  // Whether the user transcript for the current turn has been posted to chat history.
  const userTranscriptPostedRef = useRef(false);
  // Fallback flush timer for buffered tool_result when user transcript never finalizes (#42108).
  const pendingToolResultFlushTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  isTypingRef.current = isTyping;
  isLoadingRef.current = isLoading;
  onSendMessageRef.current = onSendMessage;
  onVoiceMessageRef.current = onVoiceMessage;
  onVoiceProcessingChangeRef.current = onVoiceProcessingChange;
  const speakingMessageIdRef = useRef<string | null>(null);

  const getVoiceMessageKey = (message: ChatMessage, index: number): string => {
    const rawTimestamp = new Date(message.timestamp).getTime();
    const safeTimestamp = Number.isNaN(rawTimestamp) ? 0 : rawTimestamp;
    return `${message.id || 'no-id'}-${message.sender}-${safeTimestamp}-${index}`;
  };

  const speakAssistantMessage = async (message: ChatMessage, voiceMessageKey: string) => {
    const rawText = message.content?.trim();
    if (!rawText) {
      return;
    }

    // If currently playing this message, stop it
    if (speakingMessageIdRef.current === voiceMessageKey) {
      // Abort any in-flight TTS fetch
      if (ttsAbortControllerRef.current) {
        ttsAbortControllerRef.current.abort();
        ttsAbortControllerRef.current = null;
      }
      // Stop any playing audio
      if (playbackContextRef.current) {
        await playbackContextRef.current.close();
        playbackContextRef.current = null;
        playbackTimeRef.current = 0;
      }
      speakingMessageIdRef.current = null;
      setSpeakingMessageId(null);
      return;
    }

    // Abort any in-flight TTS fetch for a different message
    if (ttsAbortControllerRef.current) {
      ttsAbortControllerRef.current.abort();
      ttsAbortControllerRef.current = null;
    }
    // Stop any other playing message
    if (playbackContextRef.current) {
      await playbackContextRef.current.close();
      playbackContextRef.current = null;
      playbackTimeRef.current = 0;
    }
    speakingMessageIdRef.current = voiceMessageKey;
    setSpeakingMessageId(voiceMessageKey);

    const abortController = new AbortController();
    ttsAbortControllerRef.current = abortController;

    setSpokenAssistantIds((current) => (
      current.includes(voiceMessageKey) ? current : [...current, voiceMessageKey]
    ));

    // Use gpt-realtime-mini TTS via backend
    try {
      const apiBase = getApiBaseUrl();
      const resp = await fetch(`${apiBase}/api/voice/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: rawText }),
        signal: abortController.signal,
      });

      if (!resp.ok) {
        throw new Error(`TTS failed: ${resp.status}`);
      }

      const pcmData = await resp.arrayBuffer();

      // Bail out if the user stopped/switched while the response was being read
      if (abortController.signal.aborted || speakingMessageIdRef.current !== voiceMessageKey) {
        return;
      }

      const sampleRate = parseInt(resp.headers.get('X-Sample-Rate') || '24000', 10);

      // Play PCM16 audio
      const ctx = new AudioContext({ sampleRate });
      playbackContextRef.current = ctx;
      const int16 = new Int16Array(pcmData);
      const float32 = new Float32Array(int16.length);
      for (let i = 0; i < int16.length; i += 1) {
        float32[i] = int16[i] / 32768;
      }

      const buffer = ctx.createBuffer(1, float32.length, sampleRate);
      buffer.copyToChannel(float32, 0);

      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(ctx.destination);
      source.onended = () => {
        speakingMessageIdRef.current = null;
        ctx.close();
        if (playbackContextRef.current === ctx) {
          playbackContextRef.current = null;
        }
        setSpeakingMessageId(null);
      };
      source.start();
    } catch (err) {
      // Ignore aborts — the user stopped/switched intentionally
      if ((err as Error)?.name === 'AbortError') {
        return;
      }
      console.error('TTS error:', err);
      if (speakingMessageIdRef.current === voiceMessageKey) {
        speakingMessageIdRef.current = null;
        setSpeakingMessageId(null);
      }
    } finally {
      if (ttsAbortControllerRef.current === abortController) {
        ttsAbortControllerRef.current = null;
      }
    }
  };

  const isInputDisabled = useMemo(
    () => isTyping || isLoading || isVoiceProcessing,
    [isTyping, isLoading, isVoiceProcessing],
  );

  const handleSend = useCallback(() => {
    if (inputValue.trim()) {
      onSendMessage(inputValue.trim());
      setInputValue('');
      setTimeout(() => {
        inputRef.current?.focus();
      }, 0);
    }
  }, [inputValue, onSendMessage]);

  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  useAutoScroll(messagesEndRef, [messages, isTyping]);

  // Derive voice processing state from voiceSessionState
  useEffect(() => {
    const processing = voiceSessionState === 'thinking' || voiceSessionState === 'speaking';
    setIsVoiceProcessing(processing);
    onVoiceProcessingChangeRef.current?.(processing);
  }, [voiceSessionState]);

  useEffect(() => {
    let isMounted = true;

    getVoiceLiveConfig()
      .then((config) => {
        if (isMounted) {
          setIsVoiceEnabled(Boolean(config.enabled));
          voiceConfigCacheRef.current = config;
        }
      })
      .catch(() => {
        if (isMounted) {
          setIsVoiceEnabled(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (!isTyping && !isLoading && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isTyping, isLoading]);

  const VoiceWaveIcon = () => (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn('h-4 w-4', isVoiceActive && 'animate-pulse')}
      aria-hidden="true"
    >
      <rect x="2" y="8" width="2" height="4" rx="1" fill="currentColor" />
      <rect x="6" y="6" width="2" height="8" rx="1" fill="currentColor" />
      <rect x="10" y="4" width="2" height="12" rx="1" fill="currentColor" />
      <rect x="14" y="6" width="2" height="8" rx="1" fill="currentColor" />
      <rect x="18" y="8" width="2" height="4" rx="1" fill="currentColor" />
    </svg>
  );

  // Audio conversion functions imported from @/lib/audioUtils

  const playAssistantAudioChunk = (base64Data: string, sampleRate = 24000) => {
    if (!playbackContextRef.current) {
      playbackContextRef.current = new AudioContext();
      playbackTimeRef.current = playbackContextRef.current.currentTime;
    }
    playbackTimeRef.current = playPCM16Chunk(
      base64Data,
      playbackContextRef.current,
      playbackTimeRef.current,
      sampleRate,
    );
  };

  const stopMicrophoneCapture = async () => {
    if (processorNodeRef.current) {
      processorNodeRef.current.port.close();
      processorNodeRef.current.disconnect();
      processorNodeRef.current = null;
    }

    if (sourceNodeRef.current) {
      sourceNodeRef.current.disconnect();
      sourceNodeRef.current = null;
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }

    if (audioContextRef.current) {
      await audioContextRef.current.close();
      audioContextRef.current = null;
    }
  };

  const stopVoiceSession = async () => {
    setIsVoiceTransitioning(true);
    sessionReadyRef.current = false;
    awaitingResponseRef.current = false;
    voiceStructuredPostedRef.current = false;
    pendingToolResultRef.current = null;
    userTranscriptPostedRef.current = false;
    audioBufferQueueRef.current = [];
    if (responseTimeoutRef.current) {
      clearTimeout(responseTimeoutRef.current);
      responseTimeoutRef.current = null;
    }
    if (pendingToolResultFlushTimeoutRef.current) {
      clearTimeout(pendingToolResultFlushTimeoutRef.current);
      pendingToolResultFlushTimeoutRef.current = null;
    }

    const ws = wsRef.current;
    wsRef.current = null;

    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'stop_session' }));
      ws.close();
    }

    // Stop any playing voice audio
    if (playbackContextRef.current) {
      try { await playbackContextRef.current.close(); } catch { /* already closed */ }
      playbackContextRef.current = null;
      playbackTimeRef.current = 0;
    }

    await stopMicrophoneCapture();
    setIsVoiceActive(false);
    setVoiceSessionState('idle');
    isSpeakingRef.current = false;
    setIsVoiceTransitioning(false);
    setStreamingVoiceText('');
  };

  const startMicrophoneCapture = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    mediaStreamRef.current = stream;
    const audioContext = new AudioContext();
    audioContextRef.current = audioContext;

    const sourceNode = audioContext.createMediaStreamSource(stream);
    sourceNodeRef.current = sourceNode;

    // Use AudioWorkletNode instead of deprecated ScriptProcessorNode
    await audioContext.audioWorklet.addModule('/pcm-processor.js');
    const workletNode = new AudioWorkletNode(audioContext, 'pcm-processor');
    processorNodeRef.current = workletNode;

    workletNode.port.onmessage = (event: MessageEvent<Float32Array>) => {
      // Don't send audio while agent is speaking (prevents feedback loop)
      if (isSpeakingRef.current) {
        return;
      }

      const input = event.data;
      const resampled = resampleTo24k(input, audioContext.sampleRate);
      const pcm16 = floatTo16BitPCM(resampled);
      const payload = pcm16ToBase64(pcm16);

      const ws = wsRef.current;
      if (ws && ws.readyState === WebSocket.OPEN && sessionReadyRef.current) {
        // Flush any buffered chunks first
        while (audioBufferQueueRef.current.length > 0) {
          const buffered = audioBufferQueueRef.current.shift()!;
          ws.send(JSON.stringify({ type: 'audio_chunk', data: buffered }));
        }
        ws.send(JSON.stringify({ type: 'audio_chunk', data: payload }));
      } else {
        // Buffer audio until session is ready (keep last ~2s at 24kHz)
        audioBufferQueueRef.current.push(payload);
        if (audioBufferQueueRef.current.length > 50) {
          audioBufferQueueRef.current.shift();
        }
      }
    };

    sourceNode.connect(workletNode);
    // Connect to destination to keep the audio graph alive
    workletNode.connect(audioContext.destination);
  };

  const startVoiceSession = async () => {
    if (isVoiceTransitioning || isVoiceActive) {
      return;
    }

    // Stop any audio still playing from a previous voice session
    if (playbackContextRef.current) {
      try { await playbackContextRef.current.close(); } catch { /* already closed */ }
      playbackContextRef.current = null;
      playbackTimeRef.current = 0;
    }
    // Also close any existing WebSocket that might still be open
    const existingWs = wsRef.current;
    if (existingWs && existingWs.readyState === WebSocket.OPEN) {
      existingWs.send(JSON.stringify({ type: 'stop_session' }));
      existingWs.close();
      wsRef.current = null;
    }
    isSpeakingRef.current = false;

    sessionReadyRef.current = false;
    audioBufferQueueRef.current = [];
    setIsVoiceTransitioning(true);
    setVoiceSessionState('connecting');
    setVoiceError(null);

    // Start mic capture for backend WebSocket
    try {
      await startMicrophoneCapture();
      setIsVoiceActive(true);
      // Stay in 'connecting' — the 'listening' state is set when the
      // WebSocket session_started event arrives, which means the backend
      // is actually ready to accept audio input.
    } catch (micError) {
      console.error('Unable to start microphone capture', micError);
      setVoiceError('Microphone access failed. Check browser permissions and try again.');
      setIsVoiceTransitioning(false);
      setVoiceSessionState('idle');
      return;
    }

    if (!isVoiceEnabled) {
      setVoiceError('Voice is unavailable. Configure Azure Voice Live endpoint and key.');
      await stopMicrophoneCapture();
      setIsVoiceActive(false);
      setIsVoiceTransitioning(false);
      setVoiceSessionState('idle');
      return;
    }

    const config = voiceConfigCacheRef.current || await getVoiceLiveConfig();
    if (!config.enabled) {
      setIsVoiceEnabled(false);
      setVoiceError('Voice is unavailable. Configure Azure Voice Live endpoint and key.');
      await stopMicrophoneCapture();
      setIsVoiceActive(false);
      setIsVoiceTransitioning(false);
      setVoiceSessionState('idle');
      return;
    }

    const apiBase = getApiBaseUrl();
    const apiUrl = new URL(apiBase);
    const wsProtocol = apiUrl.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${apiUrl.host}/api/voice/ws/${clientIdRef.current}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          type: 'start_session',
          mode: config.mode,
          model: config.model,
          voice: config.voice,
          transcribe_model: config.transcribe_model,
          instructions: config.instructions,
        }),
      );
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        if (message.type === 'transcript' && message.role === 'user' && message.isFinal && message.text) {
          const transcript = String(message.text).trim();
          if (!transcript) {
            return;
          }

          setVoiceSessionState('thinking');
          setInputValue('');
          lastSentTranscriptRef.current = transcript;
          awaitingResponseRef.current = true;

          // Display user transcript in chat
          onVoiceMessageRef.current?.(transcript, 'user');
          userTranscriptPostedRef.current = true;

          // If the tool_result arrived before the transcription completed
          // (Azure Voice Live transcription is async), flush the buffered
          // assistant message now so it appears AFTER the user message.
          if (pendingToolResultRef.current) {
            onVoiceMessageRef.current?.(pendingToolResultRef.current, 'assistant');
            pendingToolResultRef.current = null;
          }
          // User transcript arrived — cancel fallback flush.
          if (pendingToolResultFlushTimeoutRef.current) {
            clearTimeout(pendingToolResultFlushTimeoutRef.current);
            pendingToolResultFlushTimeoutRef.current = null;
          }

          // Timeout: if no assistant response within 30s, show error
          if (responseTimeoutRef.current) clearTimeout(responseTimeoutRef.current);
          responseTimeoutRef.current = setTimeout(() => {
            if (awaitingResponseRef.current) {
              awaitingResponseRef.current = false;
              voiceStructuredPostedRef.current = false;
              setVoiceError('No response received. Please try again.');
              setStreamingVoiceText('');
              setVoiceSessionState('idle');
              const ws = wsRef.current;
              wsRef.current = null;
              if (ws) {
                if (ws.readyState === WebSocket.OPEN) {
                  ws.send(JSON.stringify({ type: 'stop_session' }));
                }
                if (ws.readyState !== WebSocket.CLOSED) {
                  ws.close();
                }
              }
            }
          }, 30_000);

          // Auto-stop mic after question captured — prevents feedback
          stopMicrophoneCapture().then(() => setIsVoiceActive(false));
        }

        if (message.type === 'audio_data' && message.data) {
          // Assistant is responding — clear the no-response timeout
          awaitingResponseRef.current = false;
          if (responseTimeoutRef.current) {
            clearTimeout(responseTimeoutRef.current);
            responseTimeoutRef.current = null;
          }
          setVoiceSessionState('speaking');
          isSpeakingRef.current = true;
          playAssistantAudioChunk(message.data, message.sampleRate || 24000);
        }

        // Tool result from the Foundry agent. If the user transcript has already
        // been posted we can render the assistant message immediately; otherwise
        // buffer it so that the user message always appears first in chat.
        if (message.type === 'tool_result' && typeof message.structuredText === 'string' && message.structuredText.trim()) {
          // Assistant is responding — clear the no-response timeout
          awaitingResponseRef.current = false;
          if (responseTimeoutRef.current) {
            clearTimeout(responseTimeoutRef.current);
            responseTimeoutRef.current = null;
          }
          setStreamingVoiceText('');
          if (userTranscriptPostedRef.current) {
            // User message already in chat — safe to post assistant immediately
            onVoiceMessageRef.current?.(message.structuredText, 'assistant');
          } else {
            // Transcription still pending — buffer until user message is posted
            pendingToolResultRef.current = message.structuredText;
            // Fallback: flush buffered answer after 5s if user transcript never arrives (#42108).
            if (pendingToolResultFlushTimeoutRef.current) {
              clearTimeout(pendingToolResultFlushTimeoutRef.current);
            }
            pendingToolResultFlushTimeoutRef.current = setTimeout(() => {
              pendingToolResultFlushTimeoutRef.current = null;
              const buffered = pendingToolResultRef.current;
              if (buffered && !userTranscriptPostedRef.current) {
                // Skip synthesizing user message — lastSentTranscriptRef may hold a stale prior turn.
                onVoiceMessageRef.current?.(buffered, 'assistant');
                pendingToolResultRef.current = null;
              }
            }, 5_000);
          }
          voiceStructuredPostedRef.current = true;
        }

        // Show intermediate transcript text as it streams in (alongside audio)
        if (message.type === 'transcript' && message.role === 'assistant' && !message.isFinal && message.text) {
          // Assistant is responding — clear the no-response timeout
          if (awaitingResponseRef.current) {
            awaitingResponseRef.current = false;
            if (responseTimeoutRef.current) {
              clearTimeout(responseTimeoutRef.current);
              responseTimeoutRef.current = null;
            }
          }
          if (!voiceStructuredPostedRef.current) {
            setStreamingVoiceText(message.text);
          }
        }

        if (message.type === 'transcript' && message.role === 'assistant' && message.isFinal && message.text) {
          // Response received — clear timeout and flag
          awaitingResponseRef.current = false;
          if (responseTimeoutRef.current) {
            clearTimeout(responseTimeoutRef.current);
            responseTimeoutRef.current = null;
          }

          // Clear streaming text and add the final message to chat history
          setStreamingVoiceText('');
          // If the structured tool result was already posted via the earlier
          // `tool_result` event, skip re-posting on RESPONSE_DONE. Otherwise prefer
          // structuredText (Foundry markdown for product cards) over the spoken
          // paraphrase so cards render the same way as the text-chat path.
          if (!voiceStructuredPostedRef.current) {
            const displayText =
              (typeof message.structuredText === 'string' && message.structuredText.trim())
                ? message.structuredText
                : message.text;
            onVoiceMessageRef.current?.(displayText, 'assistant');
          } else if (pendingToolResultRef.current && !userTranscriptPostedRef.current) {
            // Flush buffered answer instead of silent drop (#42108).
            onVoiceMessageRef.current?.(pendingToolResultRef.current, 'assistant');
          }
          if (pendingToolResultFlushTimeoutRef.current) {
            clearTimeout(pendingToolResultFlushTimeoutRef.current);
            pendingToolResultFlushTimeoutRef.current = null;
          }
          voiceStructuredPostedRef.current = false;
          pendingToolResultRef.current = null;
          userTranscriptPostedRef.current = false;
          setVoiceSessionState('idle');
          isSpeakingRef.current = false;

          // Close the WS session — user clicks wave again for next question
          const ws = wsRef.current;
          wsRef.current = null;
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'stop_session' }));
            ws.close();
          }
        }

        if (message.type === 'stop_playback') {
          if (playbackContextRef.current) {
            playbackTimeRef.current = playbackContextRef.current.currentTime;
          }
        }

        if (message.type === 'session_stopped') {
          setIsVoiceActive(false);
          setVoiceSessionState('idle');
          setIsVoiceTransitioning(false);
        }

        if (message.type === 'status' && typeof message.state === 'string') {
          const state = message.state as 'listening' | 'thinking' | 'speaking';
          if (state === 'listening') {
            isSpeakingRef.current = false;
            setVoiceSessionState(state);
          } else if (state === 'thinking' || state === 'speaking') {
            setVoiceSessionState(state);
          }
        }

        if (message.type === 'session_started') {
          sessionReadyRef.current = true;
          setVoiceSessionState('listening');
          setVoiceError(null);
          setIsVoiceTransitioning(false);
        }

        if (message.type === 'error' && message.message) {
          setVoiceError(String(message.message));
          setIsVoiceTransitioning(false);
          setVoiceSessionState('idle');
        }
      } catch (parseError) {
        console.error('Failed to parse voice message', parseError);
      }
    };

    ws.onerror = () => {
      setVoiceError('Unable to connect to Voice Live. Check backend and Voice Live settings.');
      setIsVoiceTransitioning(false);
      setVoiceSessionState('idle');
    };

    ws.onclose = async () => {
      // If we were still waiting for an assistant response, the connection
      // dropped before the answer arrived — notify the user.
      if (awaitingResponseRef.current) {
        awaitingResponseRef.current = false;
        if (responseTimeoutRef.current) {
          clearTimeout(responseTimeoutRef.current);
          responseTimeoutRef.current = null;
        }
        setVoiceError('Voice connection closed before a response was received. Please try again.');
      }
      // Flush buffered answer before nulling refs to avoid silent drop on early close (#42108).
      if (pendingToolResultRef.current && !userTranscriptPostedRef.current) {
        onVoiceMessageRef.current?.(pendingToolResultRef.current, 'assistant');
      }
      voiceStructuredPostedRef.current = false;
      pendingToolResultRef.current = null;
      userTranscriptPostedRef.current = false;
      if (pendingToolResultFlushTimeoutRef.current) {
        clearTimeout(pendingToolResultFlushTimeoutRef.current);
        pendingToolResultFlushTimeoutRef.current = null;
      }
      setStreamingVoiceText('');
      await stopMicrophoneCapture();
      setIsVoiceActive(false);
      setVoiceSessionState('idle');
      setIsVoiceTransitioning(false);
    };
  };

  const handleVoiceToggle = async () => {
    if (isVoiceTransitioning) {
      return;
    }

    if (isVoiceActive) {
      if (voiceSessionState === 'speaking') {
        // Interrupt agent mid-speech — send interrupt and go back to listening
        const ws = wsRef.current;
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'interrupt' }));
        }
        // Stop playback
        if (playbackContextRef.current) {
          await playbackContextRef.current.close();
          playbackContextRef.current = null;
          playbackTimeRef.current = 0;
        }
        isSpeakingRef.current = false;
        setVoiceSessionState('listening');
      } else if (voiceSessionState === 'listening') {
        // Stop listening — close voice session
        await stopVoiceSession();
      }
      // If thinking — button is disabled, can't reach here
      setVoiceError(null);
      return;
    }

    try {
      await startVoiceSession();
    } catch (error) {
      console.error('Unable to start voice session', error);
      await stopVoiceSession();
    }
  };

  useEffect(() => {
    // Don't auto-stop voice when agent is responding — keep session alive
    // Voice session stays active so user can speak again after agent responds
  }, [isTyping, isLoading]);

  useEffect(() => {
    return () => {
      stopVoiceSession();
      speakingMessageIdRef.current = null;
      setSpeakingMessageId(null);
      if (playbackContextRef.current) {
        playbackContextRef.current.close();
        playbackContextRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!isAgentVoiceEnabled) {
      speakingMessageIdRef.current = null;
      setSpeakingMessageId(null);
      return;
    }

    if (isVoiceActive) {
      speakingMessageIdRef.current = null;
      setSpeakingMessageId(null);
      return;
    }

    const latestAssistantMessage = [...messages].reverse().find((message) => message.sender === 'assistant');
    if (!latestAssistantMessage) {
      return;
    }

    // Skip messages that originated from a voice session — they were already
    // played back as streamed audio, so auto-speaking them would produce a
    // duplicate "second voice".
    if (latestAssistantMessage.id?.startsWith('voice-assistant-')) {
      return;
    }

    const latestAssistantIndex = messages.findIndex((message) => message.id === latestAssistantMessage.id && message.timestamp === latestAssistantMessage.timestamp);
    const safeIndex = latestAssistantIndex >= 0 ? latestAssistantIndex : Math.max(messages.length - 1, 0);
    const voiceMessageKey = getVoiceMessageKey(latestAssistantMessage, safeIndex);

    if (spokenAssistantIds.includes(voiceMessageKey)) {
      return;
    }

    speakAssistantMessage(latestAssistantMessage, voiceMessageKey);
  }, [messages, isAgentVoiceEnabled, isVoiceActive, spokenAssistantIds]);

  return (
    <div className={cn("flex flex-col h-full bg-background", className)}>
      <div className="flex-1 flex flex-col overflow-hidden">
        <ScrollArea className="flex-1 h-full" ref={scrollAreaRef}>
          <div className="p-3 sm:p-6 space-y-4 sm:space-y-6">
            {isLoading && messages.length === 0 ? (
              <div className="space-y-4">
                <div className="flex gap-3 justify-start">
                  <Skeleton className="w-8 h-8 rounded-full flex-shrink-0" />
                  <div className="space-y-2 flex-1 max-w-[80%]">
                    <Skeleton className="h-16 w-full rounded-2xl" />
                  </div>
                </div>
                <div className="flex gap-3 justify-end">
                  <div className="space-y-2 flex-1 max-w-[80%] flex flex-col items-end">
                    <Skeleton className="h-12 w-3/4 rounded-2xl" />
                  </div>
                  <Skeleton className="w-8 h-8 rounded-full flex-shrink-0" />
                </div>
                <div className="flex gap-3 justify-start">
                  <Skeleton className="w-8 h-8 rounded-full flex-shrink-0" />
                  <div className="space-y-2 flex-1 max-w-[80%]">
                    <Skeleton className="h-20 w-full rounded-2xl" />
                  </div>
                </div>
              </div>
            ) : (
              <>
                {/* Welcome Message - Only show when no messages, not loading, and no active voice session */}
                {messages.length === 0 && !isTyping && !isLoading && voiceSessionState === 'idle' && !streamingVoiceText && (
              <div className="flex flex-col items-center justify-center text-center space-y-6 h-full min-h-[400px]">
                <img 
                  src="/contoso-ai-icon.png" 
                  alt="AI Assistant" 
                  className="w-16 h-16"
                />
                
                <div className="space-y-2">
                  <h2 className="text-xl font-semibold text-foreground">
                    Hey! I'm here to help.
                  </h2>
                  <p className="text-muted-foreground max-w-sm">
                    Ask me about returns & exchanges, warranties, or general product advice.
                  </p>
                </div>
                
                <div className="text-xs text-muted-foreground">
                  Click the new chat button above to start a new chat anytime
                </div>
              </div>
            )}

            {messages.map((message, index) => {
              const voiceMessageKey = getVoiceMessageKey(message, index);
              return (
              <EnhancedChatMessageBubble
                key={voiceMessageKey}
                message={message}
                onAddToCart={onAddToCart}
              />
            );
            })}
            
            {/* Streaming voice assistant — show typing indicator instead of paraphrased
                plain text. The final message arrives with structuredText (markdown) and
                renders as product cards, so showing the partial text here causes a visible
                flicker (plain text → cards). The TTS audio provides the spoken feedback. */}
            {streamingVoiceText && (
              <EnhancedChatMessageBubble
                message={{
                  id: 'voice-streaming',
                  content: '',
                  sender: 'assistant',
                  timestamp: new Date().toISOString()
                }}
                isTyping={true}
              />
            )}

            {isTyping && !isLoading && (
              <EnhancedChatMessageBubble
                message={{
                  id: 'typing',
                  content: '',
                  sender: 'assistant',
                  timestamp: new Date().toISOString()
                }}
                isTyping={true}
              />
            )}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>
      </div>

      <div className="flex-shrink-0 border-t bg-background p-2 sm:p-4 space-y-2 sm:space-y-3">
        <div className="flex-1 relative">
          <Input
            ref={inputRef}
            placeholder="Ask a question"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            className="pr-21 resize-none min-h-[40px]"
            disabled={isInputDisabled}
          />
          <div className="absolute right-1 top-1/2 transform -translate-y-1/2 flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                'h-9 w-9 p-0 relative rounded-full transition-all',
                isVoiceActive && voiceSessionState === 'listening' && 'text-red-500 bg-red-50 hover:bg-red-100',
                isVoiceActive && voiceSessionState === 'thinking' && 'text-amber-500 bg-amber-50 cursor-wait',
                isVoiceActive && voiceSessionState === 'speaking' && 'text-primary bg-primary/10',
                !isVoiceActive && (voiceSessionState === 'connecting') && 'text-primary bg-primary/10',
              )}
              title={
                !isVoiceEnabled
                  ? 'Voice unavailable'
                  : voiceSessionState === 'thinking'
                    ? 'Processing...'
                    : voiceSessionState === 'speaking'
                      ? 'Tap to interrupt'
                      : isVoiceActive
                        ? 'Tap to stop listening'
                        : 'Tap to speak'
              }
              onClick={handleVoiceToggle}
              disabled={
                !isVoiceEnabled
                || isVoiceTransitioning
                || voiceSessionState === 'thinking'
                || isVoiceProcessing
                || isTyping
                || isLoading
                || inputValue.trim().length > 0
              }
            >
              {isVoiceActive && voiceSessionState === 'listening' && (
                <span className="absolute inline-flex h-6 w-6 rounded-full bg-red-400/30 animate-ping" />
              )}
              {voiceSessionState === 'thinking' ? (
                <span className="h-4 w-4 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
              ) : isVoiceActive ? (
                <Stop20Filled className="h-4 w-4" />
              ) : (
                <VoiceWaveIcon />
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              title="Send message"
              onClick={handleSend}
              disabled={!inputValue.trim() || isInputDisabled}
            >
              <Send20Regular className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <p className="text-xs text-muted-foreground text-center">
          AI-generated content may be incorrect
        </p>
        {voiceError && (
          <p className="text-xs text-red-600 text-center" role="status" aria-live="polite">
            {voiceError}
          </p>
        )}
        {isVoiceActive && !voiceError && (
          <p className="text-xs text-center" role="status" aria-live="polite">
            {voiceSessionState === 'connecting'
              ? <span className="text-primary">Starting voice...</span>
              : voiceSessionState === 'thinking'
              ? <span className="text-amber-600">Processing your question...</span>
              : voiceSessionState === 'speaking'
                ? <span className="text-primary">🔊 Agent is responding...</span>
                : <span className="text-red-500">● Listening — speak now</span>}
          </p>
        )}
      </div>
    </div>
  );
};
