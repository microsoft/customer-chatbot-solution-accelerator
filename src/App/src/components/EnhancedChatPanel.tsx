import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { getApiBaseUrl, getVoiceLiveConfig } from '@/lib/api';
import { floatTo16BitPCM, pcm16ToBase64, playPCM16Chunk, resampleTo24k } from '@/lib/audioUtils';
import { cleanTextForSpeech } from '@/lib/textCleaners';
import { ChatMessage, Product } from '@/lib/types';
import { cn } from '@/lib/utils';
import { Send20Regular, Stop20Filled } from '@fluentui/react-icons';
import React, { useEffect, useRef, useState } from 'react';
import { EnhancedChatMessageBubble } from './EnhancedChatMessageBubble';

interface EnhancedChatPanelProps {
  messages: ChatMessage[];
  onSendMessage: (content: string) => void;
  isTyping: boolean;
  isOpen: boolean;
  onClose: () => void;
  onAddToCart?: (product: Product) => void;
  className?: string;
  isLoading?: boolean;
}

export const EnhancedChatPanel = ({
  messages,
  onSendMessage,
  isTyping,
  isOpen,
  onClose,
  onAddToCart,
  className,
  isLoading = false,
}: EnhancedChatPanelProps) => {
  const [inputValue, setInputValue] = useState('');
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const [isAgentVoiceEnabled, setIsAgentVoiceEnabled] = useState(false);
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(true);
  const [speakingMessageId, setSpeakingMessageId] = useState<string | null>(null);
  const [spokenAssistantIds, setSpokenAssistantIds] = useState<string[]>([]);
  const [voiceSessionState, setVoiceSessionState] = useState<'idle' | 'connecting' | 'listening' | 'thinking' | 'speaking'>('idle');
  const [isVoiceTransitioning, setIsVoiceTransitioning] = useState(false);
  const [streamingVoiceText, setStreamingVoiceText] = useState('');
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const processorNodeRef = useRef<ScriptProcessorNode | null>(null);
  const gainNodeRef = useRef<GainNode | null>(null);
  const playbackContextRef = useRef<AudioContext | null>(null);
  const playbackTimeRef = useRef<number>(0);
  const clientIdRef = useRef<string>(crypto.randomUUID());
  const lastSentTranscriptRef = useRef<string>('');
  const isTypingRef = useRef(isTyping);
  const isLoadingRef = useRef(isLoading);
  const onSendMessageRef = useRef(onSendMessage);
  const voiceConfigCacheRef = useRef<any>(null);
  const audioBufferQueueRef = useRef<string[]>([]);
  const sessionReadyRef = useRef(false);
  const isSpeakingRef = useRef(false);

  isTypingRef.current = isTyping;
  isLoadingRef.current = isLoading;
  onSendMessageRef.current = onSendMessage;
  const speakingMessageIdRef = useRef<string | null>(null);

  const getVoiceMessageKey = (message: ChatMessage, index: number): string => {
    const rawTimestamp = message.timestamp instanceof Date ? message.timestamp.getTime() : new Date(message.timestamp).getTime();
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
      // Stop any playing audio
      if (playbackContextRef.current) {
        await playbackContextRef.current.close();
        playbackContextRef.current = null;
        playbackTimeRef.current = 0;
      }
      window.speechSynthesis.cancel();
      speakingMessageIdRef.current = null;
      setSpeakingMessageId(null);
      return;
    }

    // Stop any other playing message
    if (playbackContextRef.current) {
      await playbackContextRef.current.close();
      playbackContextRef.current = null;
      playbackTimeRef.current = 0;
    }
    window.speechSynthesis.cancel();
    speakingMessageIdRef.current = voiceMessageKey;
    setSpeakingMessageId(voiceMessageKey);

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
      });

      if (!resp.ok) {
        throw new Error(`TTS failed: ${resp.status}`);
      }

      const pcmData = await resp.arrayBuffer();
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
        setSpeakingMessageId(null);
      };
      source.start();
    } catch (err) {
      console.error('TTS error, falling back to browser speech:', err);
      // Fallback to browser speechSynthesis
      speakingMessageIdRef.current = null;
      setSpeakingMessageId(null);

      const cleanText = cleanTextForSpeech(rawText);

      if (cleanText) {
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = 1.05;
        utterance.onstart = () => {
          speakingMessageIdRef.current = voiceMessageKey;
          setSpeakingMessageId(voiceMessageKey);
        };
        utterance.onend = () => {
          speakingMessageIdRef.current = null;
          setSpeakingMessageId(null);
        };
        utterance.onerror = () => {
          speakingMessageIdRef.current = null;
          setSpeakingMessageId(null);
        };
        setTimeout(() => window.speechSynthesis.speak(utterance), 50);
      }
    }
  };

  const handleSend = () => {
    if (inputValue.trim()) {
      onSendMessage(inputValue.trim());
      setInputValue('');
      // Focus the input after sending
      setTimeout(() => {
        inputRef.current?.focus();
      }, 0);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

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

  // Maintain focus on input when not typing
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

  const SpeakerIcon = () => (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="h-4 w-4"
      aria-hidden="true"
    >
      <path d="M3 8H6L10 5V15L6 12H3V8Z" fill="currentColor" />
      <path d="M13 8.2C13.6 8.7 14 9.5 14 10.4C14 11.3 13.6 12.1 13 12.6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M14.8 6.7C15.8 7.6 16.4 8.9 16.4 10.4C16.4 11.9 15.8 13.2 14.8 14.1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
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
      processorNodeRef.current.disconnect();
      processorNodeRef.current.onaudioprocess = null;
      processorNodeRef.current = null;
    }

    if (sourceNodeRef.current) {
      sourceNodeRef.current.disconnect();
      sourceNodeRef.current = null;
    }

    if (gainNodeRef.current) {
      gainNodeRef.current.disconnect();
      gainNodeRef.current = null;
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
    audioBufferQueueRef.current = [];

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

  /** Stop listening only — mic stops but let the agent finish responding */
  const stopListeningOnly = async () => {
    await stopMicrophoneCapture();
    setIsVoiceActive(false);
    setVoiceSessionState('idle');
    // Keep WebSocket open so agent response can still come through
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

    const processorNode = audioContext.createScriptProcessor(2048, 1, 1);
    processorNodeRef.current = processorNode;

    const gainNode = audioContext.createGain();
    gainNode.gain.value = 0;
    gainNodeRef.current = gainNode;

    processorNode.onaudioprocess = (event) => {
      // Don't send audio while agent is speaking (prevents feedback loop)
      if (isSpeakingRef.current) {
        return;
      }

      const input = event.inputBuffer.getChannelData(0);
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

    sourceNode.connect(processorNode);
    processorNode.connect(gainNode);
    gainNode.connect(audioContext.destination);
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
      setVoiceSessionState('listening');
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

          // Display user transcript in chat
          onSendMessageRef.current(`__voice_user__${transcript}`);

          // Auto-stop mic after question captured — prevents feedback
          stopMicrophoneCapture().then(() => setIsVoiceActive(false));
        }

        if (message.type === 'audio_data' && message.data) {
          setVoiceSessionState('speaking');
          isSpeakingRef.current = true;
          playAssistantAudioChunk(message.data, message.sampleRate || 24000);
        }

        // Show intermediate transcript text as it streams in (alongside audio)
        if (message.type === 'transcript' && message.role === 'assistant' && !message.isFinal && message.text) {
          setStreamingVoiceText(message.text);
        }

        if (message.type === 'transcript' && message.role === 'assistant' && message.isFinal && message.text) {
          // Clear streaming text and add the final message to chat history
          setStreamingVoiceText('');
          const displayText = message.text;
          onSendMessageRef.current(`__voice_assistant__${displayText}`);
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
      window.speechSynthesis.cancel();
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
      window.speechSynthesis.cancel();
      speakingMessageIdRef.current = null;
      setSpeakingMessageId(null);
      return;
    }

    if (isVoiceActive) {
      window.speechSynthesis.cancel();
      speakingMessageIdRef.current = null;
      setSpeakingMessageId(null);
      return;
    }

    const latestAssistantMessage = [...messages].reverse().find((message) => message.sender === 'assistant');
    if (!latestAssistantMessage) {
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
      {/* Scrollable Chat Content Area - Takes remaining space */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <ScrollArea className="flex-1 h-full" ref={scrollAreaRef}>
          <div className="p-3 sm:p-6 space-y-4 sm:space-y-6">
            {/* Loading State - Show skeleton when loading chat history */}
            {isLoading && messages.length === 0 ? (
              <div className="space-y-4">
                {/* Loading skeleton for messages */}
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
                {/* Welcome Message - Only show when no messages and not loading */}
                {messages.length === 0 && !isTyping && !isLoading && (
              <div className="flex flex-col items-center justify-center text-center space-y-6 h-full min-h-[400px]">
                {/* AI Assistant Icon */}
                <img 
                  src="/contoso-ai-icon.png" 
                  alt="AI Assistant" 
                  className="w-16 h-16"
                />
                
                {/* Welcome Text */}
                <div className="space-y-2">
                  <h2 className="text-xl font-semibold text-foreground">
                    Hey! I'm here to help.
                  </h2>
                  <p className="text-muted-foreground max-w-sm">
                    Ask me about returns & exchanges, warranties, or general product advice.
                  </p>
                </div>
                
                {/* Quick Start Hint */}
                <div className="text-xs text-muted-foreground">
                  Click the new chat button above to start a new chat anytime
                </div>
              </div>
            )}

            {/* Chat Messages */}
            {messages.map((message, index) => {
              const voiceMessageKey = getVoiceMessageKey(message, index);
              return (
              <EnhancedChatMessageBubble
                key={voiceMessageKey}
                message={message}
                onAddToCart={onAddToCart}
                voiceMessageKey={voiceMessageKey}
                onPlayAssistantMessage={message.sender === 'assistant' ? speakAssistantMessage : undefined}
                isAssistantMessagePlaying={speakingMessageId === voiceMessageKey}
                hasBeenSpoken={spokenAssistantIds.includes(voiceMessageKey)}
              />
            );
            })}
            
            {/* Streaming voice assistant transcript — shown while audio plays */}
            {streamingVoiceText && (
              <EnhancedChatMessageBubble
                message={{
                  id: 'voice-streaming',
                  content: streamingVoiceText,
                  sender: 'assistant',
                  timestamp: new Date()
                }}
              />
            )}

            {/* Typing Indicator - Only show when AI is actively responding */}
            {isTyping && !isLoading && (
              <EnhancedChatMessageBubble
                message={{
                  id: 'typing',
                  content: '',
                  sender: 'assistant',
                  timestamp: new Date()
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

      {/* Fixed Input Footer */}
      <div className="flex-shrink-0 border-t bg-background p-2 sm:p-4 space-y-2 sm:space-y-3">
        {/* Input Field */}
        <div className="flex-1 relative">
          <Input
            ref={inputRef}
            placeholder="Ask a question"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            className="pr-16 resize-none min-h-[40px]"
            disabled={isTyping || isLoading}
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
              disabled={!inputValue.trim() || isTyping || isLoading}
            >
              <Send20Regular className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Disclaimer */}
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
