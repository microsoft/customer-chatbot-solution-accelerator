/**
 * AudioWorklet processor for capturing microphone PCM audio.
 * Replaces the deprecated ScriptProcessorNode approach.
 */
class PCMProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const input = inputs[0];
    if (input && input[0] && input[0].length > 0) {
      // Copy the Float32 samples and send to main thread
      this.port.postMessage(new Float32Array(input[0]));
    }
    return true;
  }
}

registerProcessor('pcm-processor', PCMProcessor);
