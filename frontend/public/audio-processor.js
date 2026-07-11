class AudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.targetSampleRate = 16000;
    this.inputBuffer = [];
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (!input || !input[0]) return true;

    // Accumulate floating point samples from channel 0
    const channelData = input[0];
    for (let i = 0; i < channelData.length; i++) {
      this.inputBuffer.push(channelData[i]);
    }

    // Step size for downsampling (decimation factor)
    const step = sampleRate / this.targetSampleRate;
    
    // Chunk size: 30ms of 16kHz mono audio is exactly 480 samples
    const targetChunkSize = 480; 
    const requiredInputSamples = Math.ceil(targetChunkSize * step);

    // Consume input samples in chunks of requiredInputSamples
    while (this.inputBuffer.length >= requiredInputSamples) {
      const pcm16 = new Int16Array(targetChunkSize);
      let inputIndex = 0;

      for (let i = 0; i < targetChunkSize; i++) {
        const idx = Math.floor(inputIndex);
        // Clamp floating sample to [-1.0, 1.0]
        const s = Math.max(-1, Math.min(1, this.inputBuffer[idx] || 0));
        // Convert to 16-bit PCM integer
        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        inputIndex += step;
      }

      // Send the Int16PCM ArrayBuffer back to the main thread
      this.port.postMessage(pcm16.buffer, [pcm16.buffer]);

      // Remove consumed samples from the buffer
      const consumed = Math.floor(targetChunkSize * step);
      this.inputBuffer = this.inputBuffer.slice(consumed);
    }

    return true;
  }
}

registerProcessor('audio-processor', AudioProcessor);
