/**
 * Audio utility functions for PCM16 conversion, resampling, and playback.
 */

/** Convert Float32 audio samples to 16-bit PCM. */
export const floatTo16BitPCM = (input: Float32Array): Int16Array => {
  const output = new Int16Array(input.length);
  for (let i = 0; i < input.length; i += 1) {
    const sample = Math.max(-1, Math.min(1, input[i]));
    output[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
  }
  return output;
};

/** Resample Float32 audio from inputSampleRate to 24kHz. */
export const resampleTo24k = (input: Float32Array, inputSampleRate: number): Float32Array => {
  if (inputSampleRate === 24000) {
    return input;
  }
  const ratio = inputSampleRate / 24000;
  const newLength = Math.round(input.length / ratio);
  const result = new Float32Array(newLength);
  for (let i = 0; i < newLength; i += 1) {
    const sourceIndex = i * ratio;
    const before = Math.floor(sourceIndex);
    const after = Math.min(before + 1, input.length - 1);
    const interp = sourceIndex - before;
    result[i] = input[before] * (1 - interp) + input[after] * interp;
  }
  return result;
};

/** Encode Int16Array PCM data as base64 string. */
export const pcm16ToBase64 = (pcm16: Int16Array): string => {
  const bytes = new Uint8Array(pcm16.buffer);
  const chunkSize = 0x8000; // process in chunks to avoid per-byte string concatenation
  const chunks: string[] = [];
  for (let i = 0; i < bytes.byteLength; i += chunkSize) {
    const subarray = bytes.subarray(i, Math.min(i + chunkSize, bytes.byteLength));
    chunks.push(String.fromCharCode(...(subarray as unknown as number[])));
  }
  const binary = chunks.join('');
  return btoa(binary);
};

/** Decode base64 string to Int16Array PCM data. */
export const base64ToPCM16 = (base64Data: string): Int16Array => {
  const binary = atob(base64Data);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return new Int16Array(bytes.buffer);
};

/** Convert Int16 PCM to Float32 (normalized -1 to 1). */
export const pcm16ToFloat32 = (pcm16: Int16Array): Float32Array => {
  const float32 = new Float32Array(pcm16.length);
  for (let i = 0; i < pcm16.length; i += 1) {
    float32[i] = pcm16[i] / 32768;
  }
  return float32;
};

/**
 * Play a base64-encoded PCM16 audio chunk through an AudioContext.
 * Returns the updated playback time.
 */
export const playPCM16Chunk = (
  base64Data: string,
  playbackContext: AudioContext,
  startTime: number,
  sampleRate = 24000,
): number => {
  const pcm16 = base64ToPCM16(base64Data);
  const float32 = pcm16ToFloat32(pcm16);

  const buffer = playbackContext.createBuffer(1, float32.length, sampleRate);
  buffer.copyToChannel(new Float32Array(float32), 0);

  const source = playbackContext.createBufferSource();
  source.buffer = buffer;
  source.connect(playbackContext.destination);

  const scheduleTime = Math.max(startTime, playbackContext.currentTime);
  source.start(scheduleTime);
  return scheduleTime + buffer.duration;
};