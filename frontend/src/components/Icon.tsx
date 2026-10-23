/**
 * Inline SVG icon set (stroke style, lucide-like). No icon library dependency
 * and no network fonts/icons, keeping every asset local.
 */

import type { JSX } from 'react'

export type IconName =
  | 'mic'
  | 'stop'
  | 'trash'
  | 'download'
  | 'wand'
  | 'zap'
  | 'hourglass'
  | 'x'
  | 'chat'
  | 'pulse'
  | 'clipboard'
  | 'complaint'
  | 'thermometer'
  | 'bulb'
  | 'pill'
  | 'flask'
  | 'alert'
  | 'folder'
  | 'calendar'
  | 'history'
  | 'info'
  | 'copy'
  | 'check'

const PATHS: Record<IconName, string[]> = {
  mic: ['M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z', 'M19 10v2a7 7 0 0 1-14 0v-2', 'M12 19v3'],
  stop: ['M6 6h12v12H6z'],
  trash: [
    'M3 6h18',
    'M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6',
    'M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2',
    'M10 11v6',
    'M14 11v6',
  ],
  download: ['M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4', 'M7 10l5 5 5-5', 'M12 15V3'],
  wand: [
    'M15 4V2',
    'M15 16v-2',
    'M8 9h2',
    'M20 9h2',
    'M17.8 11.8 19 13',
    'M17.8 6.2 19 5',
    'M13.4 10.6 4 20l1.4 1.4 9.4-9.4',
  ],
  zap: ['M13 2 3 14h9l-1 8 10-12h-9l1-8z'],
  hourglass: [
    'M5 22h14',
    'M5 2h14',
    'M17 22v-4.17a2 2 0 0 0-.59-1.42L12 12l-4.41 4.41A2 2 0 0 0 7 17.83V22',
    'M7 2v4.17a2 2 0 0 0 .59 1.42L12 12l4.41-4.41A2 2 0 0 0 17 6.17V2',
  ],
  x: ['M18 6 6 18', 'M6 6l12 12'],
  chat: ['M21 11.5a8.5 8.5 0 0 1-8.5 8.5c-1.53 0-2.97-.4-4.22-1.1L3 21l2.1-5.28A8.44 8.44 0 0 1 4 11.5 8.5 8.5 0 0 1 21 11.5Z'],
  pulse: ['M22 12h-4l-3 9L9 3l-3 9H2'],
  clipboard: [
    'M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2',
    'M9 2h6a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1Z',
    'M9 12h6',
    'M9 16h4',
  ],
  complaint: ['M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z', 'M8 9h8', 'M8 12.5h5'],
  thermometer: ['M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z'],
  bulb: [
    'M9 18h6',
    'M10 22h4',
    'M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5.76.76 1.23 1.52 1.41 2.5',
  ],
  pill: ['M10.5 20.5 3.5 13.5a5 5 0 0 1 7-7l7 7a5 5 0 0 1-7 7Z', 'm9 11 4 4'],
  flask: ['M10 2v7.31L4.31 19.43A2 2 0 0 0 6 22h12a2 2 0 0 0 1.69-2.57L14 9.31V2', 'M8 2h8', 'M7 16h10'],
  alert: [
    'm21.73 18-8-14a2 2 0 0 0-3.46 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z',
    'M12 9v4',
    'M12 17h.01',
  ],
  folder: [
    'M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z',
  ],
  calendar: [
    'M8 2v4',
    'M16 2v4',
    'M3 10h18',
    'M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z',
  ],
  history: ['M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8', 'M3 3v5h5', 'M12 7v5l4 2'],
  info: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z', 'M12 16v-4', 'M12 8h.01'],
  copy: [
    'M8 8h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V10a2 2 0 0 1 2-2Z',
    'M4 16a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2',
  ],
  check: ['M20 6 9 17l-5-5'],
}

const FILLED = new Set<IconName>(['stop'])

export function Icon({
  name,
  size = 18,
  className,
}: {
  name: IconName
  size?: number
  className?: string
}): JSX.Element {
  const filled = FILLED.has(name)
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={filled ? 'currentColor' : 'none'}
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {PATHS[name].map((d, i) => (
        <path key={i} d={d} />
      ))}
    </svg>
  )
}
