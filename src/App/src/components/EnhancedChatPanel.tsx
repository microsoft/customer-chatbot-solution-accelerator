import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { getApiBaseUrl, getVoiceLiveConfig } from '@/lib/api';
import { ChatMessage, Product } from '@/lib/types';
import { cn } from '@/lib/utils';
import { PaperPlaneRight } from '@phosphor-icons/react';
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

  isTypingRef.current = isTyping;
  isLoadingRef.current = isLoading;
  onSendMessageRef.current = onSendMessage;
  const speakingMessageIdRef = useRef<string | null>(null);

  const getVoiceMessageKey = (message: ChatMessage, index: number): string => {
    const rawTimestamp = message.timestamp instanceof Date ? message.timestamp.getTime() : new Date(message.timestamp).getTime();
    const safeTimestamp = Number.isNaN(rawTimestamp) ? 0 : rawTimestamp;
    return `${message.id || 'no-id'}-${message.sender}-${safeTimestamp}-${index}`;
  };

  const speakAssistantMessage = (message: ChatMessage, voiceMessageKey: string) => {
    const assistantText = message.content?.trim();
    if (!assistantText) {
      return;
    }

    if (speakingMessageIdRef.current === voiceMessageKey) {
      window.speechSynthesis.cancel();
      speakingMessageIdRef.current = null;
      setSpeakingMessageId(null);
      return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(assistantText);
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.onstart = () => {
      speakingMessageIdRef.current = voiceMessageKey;
      setSpeakingMessageId(voiceMessageKey);
    };
    utterance.onend = () => {
      speakingMessageIdRef.current = null;
      setSpeakingMessageId((current) => (current === voiceMessageKey ? null : current));
    };
    utterance.onerror = () => {
      speakingMessageIdRef.current = null;
      setSpeakingMessageId((current) => (current === voiceMessageKey ? null : current));
    };

    window.speechSynthesis.speak(utterance);
    setSpokenAssistantIds((current) => (
      current.includes(voiceMessageKey) ? current : [...current, voiceMessageKey]
    ));
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

  const floatTo16BitPCM = (input: Float32Array): Int16Array => {
    const output = new Int16Array(input.length);
    for (let index = 0; index < input.length; index += 1) {
      const sample = Math.max(-1, Math.min(1, input[index]));
      output[index] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
    }
    return output;
  };

  const resampleTo24k = (input: Float32Array, inputSampleRate: number): Float32Array => {
    if (inputSampleRate === 24000) {
      return input;
    }

    const ratio = inputSampleRate / 24000;
    const newLength = Math.round(input.length / ratio);
    const result = new Float32Array(newLength);

    for (let index = 0; index < newLength; index += 1) {
      const sourceIndex = index * ratio;
      const indexBefore = Math.floor(sourceIndex);
      const indexAfter = Math.min(indexBefore + 1, input.length - 1);
      const interpolation = sourceIndex - indexBefore;
      result[index] = (input[indexBefore] * (1 - interpolation)) + (input[indexAfter] * interpolation);
    }

    return result;
  };

  const pcm16ToBase64 = (pcm16: Int16Array): string => {
    const bytes = new Uint8Array(pcm16.buffer);
    let binary = '';
    for (let index = 0; index < bytes.byteLength; index += 1) {
      binary += String.fromCharCode(bytes[index]);
    }
    return btoa(binary);
  };

  const base64ToPCM16 = (base64Data: string): Int16Array => {
    const binary = atob(base64Data);
    const byteLength = binary.length;
    const bytes = new Uint8Array(byteLength);
    for (let index = 0; index < byteLength; index += 1) {
      bytes[index] = binary.charCodeAt(index);
    }
    return new Int16Array(bytes.buffer);
  };

  const playAssistantAudioChunk = (base64Data: string, sampleRate: number = 24000) => {
    const pcm16 = base64ToPCM16(base64Data);
    if (!playbackContextRef.current) {
      playbackContextRef.current = new AudioContext();
      playbackTimeRef.current = playbackContextRef.current.currentTime;
    }

    const playbackContext = playbackContextRef.current;
    const float32 = new Float32Array(pcm16.length);
    for (let index = 0; index < pcm16.length; index += 1) {
      float32[index] = pcm16[index] / 32768;
    }

    const buffer = playbackContext.createBuffer(1, float32.length, sampleRate);
    buffer.copyToChannel(float32, 0);

    const source = playbackContext.createBufferSource();
    source.buffer = buffer;
    source.connect(playbackContext.destination);

    if (playbackTimeRef.current < playbackContext.currentTime) {
      playbackTimeRef.current = playbackContext.currentTime;
    }

    source.start(playbackTimeRef.current);
    playbackTimeRef.current += buffer.duration;
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

    await stopMicrophoneCapture();
    setIsVoiceActive(false);
    setVoiceSessionState('idle');
    setIsVoiceTransitioning(false);
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

    sessionReadyRef.current = false;
    audioBufferQueueRef.current = [];
    setIsVoiceTransitioning(true);
    setVoiceSessionState('connecting');
    setVoiceError(null);

    // Start mic immediately for instant feedback
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

          setInputValue(transcript);

          if (transcript !== lastSentTranscriptRef.current) {
            lastSentTranscriptRef.current = transcript;
            onSendMessageRef.current(transcript);
            setInputValue('');
          }
        }

        if (message.type === 'audio_data' && message.data) {
          setVoiceSessionState('speaking');
          if (isAgentVoiceEnabled) {
            playAssistantAudioChunk(message.data, message.sampleRate || 24000);
          }
        }

        if (message.type === 'transcript' && message.role === 'assistant' && message.text) {
          setVoiceSessionState('speaking');
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
          if (state === 'listening' || state === 'thinking' || state === 'speaking') {
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
      await stopVoiceSession();
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
    if ((isTyping || isLoading) && isVoiceActive) {
      stopVoiceSession();
    }
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
          <div className="p-6 space-y-6">
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
      <div className="flex-shrink-0 border-t bg-background p-4 space-y-3">
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
                (isVoiceActive || voiceSessionState === 'connecting') && !isTyping && !isLoading && 'text-primary bg-primary/10',
              )}
              title={
                !isVoiceEnabled
                  ? 'Voice unavailable'
                  : isTyping || isLoading
                    ? 'Wait for agent to finish'
                    : isVoiceActive
                      ? 'Stop voice input'
                      : 'Start voice input'
              }
              onClick={handleVoiceToggle}
              disabled={
                isTyping
                || isLoading
                || !isVoiceEnabled
                || isVoiceTransitioning
                || voiceSessionState === 'thinking'
                || voiceSessionState === 'speaking'
              }
            >
              {(isVoiceActive || voiceSessionState === 'connecting') && !isTyping && !isLoading && (
                <span className="absolute inline-flex h-6 w-6 rounded-full bg-primary/20 animate-ping" />
              )}
              <VoiceWaveIcon />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              title="Send message"
              onClick={handleSend}
              disabled={!inputValue.trim() || isTyping || isLoading}
            >
              <PaperPlaneRight className="h-4 w-4" />
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
        {isVoiceActive && !voiceError && !isTyping && !isLoading && (
          <p className="text-xs text-primary text-center" role="status" aria-live="polite">
            {voiceSessionState === 'connecting'
              ? 'Starting voice...'
              : voiceSessionState === 'thinking'
              ? 'Heard you. Thinking...'
              : voiceSessionState === 'speaking'
                ? 'Assistant is speaking...'
                : 'Listening... Speak now'}
          </p>
        )}
      </div>
    </div>
  );
};
