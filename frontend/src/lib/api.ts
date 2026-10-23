/** Typed fetch wrappers for the MediScript API (PRD 3.2 contracts). */

export interface TranscribeResult {
  chunkIndex: number
  text: string
  durationMs: number
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    options?: { cause?: unknown },
  ) {
    super(message, options)
    this.name = 'ApiError'
  }
}

const parseError = async (res: Response): Promise<ApiError> => {
  const body = (await res.json().catch(() => null)) as
    | { error?: { code?: string; message?: string } }
    | null
  return new ApiError(
    res.status,
    body?.error?.code ?? `http_${res.status}`,
    body?.error?.message ?? `Request failed (HTTP ${res.status}).`,
  )
}

/** POST /api/transcribe — one 16 kHz mono speech-segment WAV in, text out. */
export async function transcribeChunk(
  wav: Blob,
  chunkIndex: number,
  language?: string,
): Promise<TranscribeResult> {
  const form = new FormData()
  form.append('audio', wav, `chunk-${chunkIndex}.wav`)
  form.append('chunk_index', String(chunkIndex))
  if (language) form.append('language', language)
  let res: Response
  try {
    res = await fetch('/api/transcribe', { method: 'POST', body: form })
  } catch (cause) {
    throw new ApiError(0, 'network_error', 'Backend not reachable.', { cause })
  }
  if (!res.ok) throw await parseError(res)
  const body = (await res.json()) as { chunk_index: number; text: string; duration_ms: number }
  return { chunkIndex: body.chunk_index, text: body.text, durationMs: body.duration_ms }
}
