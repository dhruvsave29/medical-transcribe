/**
 * WAV (16 kHz, mono, 16-bit PCM) encoding for VAD chunks and the
 * full-session recording (PRD Step 2).
 */

export function mergeFloat32(frames: Float32Array[]): Float32Array {
  const total = frames.reduce((n, f) => n + f.length, 0)
  const out = new Float32Array(total)
  let offset = 0
  for (const frame of frames) {
    out.set(frame, offset)
    offset += frame.length
  }
  return out
}

/** RFC 3162-style 44-byte header PCM WAV writer. */
export function encodeWavPcm16(samples: Float32Array, sampleRate = 16000): Blob {
  const bytesPerSample = 2
  const channels = 1
  const dataSize = samples.length * bytesPerSample
  const buffer = new ArrayBuffer(44 + dataSize)
  const view = new DataView(buffer)

  const writeAscii = (offset: number, s: string) => {
    for (let i = 0; i < s.length; i++) view.setUint8(offset + i, s.charCodeAt(i))
  }

  writeAscii(0, 'RIFF')
  view.setUint32(4, 36 + dataSize, true)
  writeAscii(8, 'WAVE')
  writeAscii(12, 'fmt ')
  view.setUint32(16, 16, true) // PCM chunk size
  view.setUint16(20, 1, true) // PCM format
  view.setUint16(22, channels, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * channels * bytesPerSample, true) // byte rate
  view.setUint16(32, channels * bytesPerSample, true) // block align
  view.setUint16(34, 16, true) // bits per sample
  writeAscii(36, 'data')
  view.setUint32(40, dataSize, true)

  let offset = 44
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]))
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true)
    offset += bytesPerSample
  }

  return new Blob([buffer], { type: 'audio/wav' })
}

export function wavDurationMs(byteLength: number, sampleRate = 16000): number {
  return ((byteLength - 44) / 2 / sampleRate) * 1000
}
