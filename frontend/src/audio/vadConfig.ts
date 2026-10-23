/**
 * VAD tuning + audio constraints (PRD Step 2: "Tune VAD thresholds … and
 * expose them in a config file").
 *
 * Frame = 512 samples @ 16 kHz ≈ 32 ms with the v5 model.
 *
 * - positive/negative thresholds slightly higher than library defaults so that
 *   HVAC hum, fan noise and clicks do not open segments.
 - redemptionMs 700: a pause up to 0.7 s inside a sentence does not close a
 *   chunk (natural speech pauses).
 - preSpeechPadMs 500: keeps the attack of the first word inside the chunk.
 - minSpeechMs 400: discards coughs/intake breaths that would waste ASR
 *   calls in Step 3.
 */

export interface VadOptions {
  positiveSpeechThreshold: number
  negativeSpeechThreshold: number
  redemptionMs: number
  preSpeechPadMs: number
  minSpeechMs: number
  submitUserSpeechOnPause: boolean
}

export const VAD_OPTIONS: VadOptions = {
  positiveSpeechThreshold: 0.45,
  negativeSpeechThreshold: 0.32,
  redemptionMs: 700,
  preSpeechPadMs: 500,
  minSpeechMs: 400,
  submitUserSpeechOnPause: false,
}

/** The recogniser-relevant mono rate: chunks are encoded at 16 kHz (PRD 3.1). */
export const TARGET_SAMPLE_RATE = 16000

/** Base constraints for the consultation microphone (pragmatic defaults). */
export const MIC_CONSTRAINTS: MediaTrackConstraints = {
  channelCount: 1,
  echoCancellation: true,
  autoGainControl: true,
  noiseSuppression: true,
}
