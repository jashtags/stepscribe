import React from 'react'

const STAGES = [
  { key: 'download', label: 'Downloading' },
  { key: 'transcribe', label: 'Transcribing' },
  { key: 'frames', label: 'Keyframes' },
  { key: 'synthesize', label: 'Writing Steps' },
]

function getActiveStage(stage) {
  if (!stage) return 0
  const s = stage.toLowerCase()
  if (s.includes('download')) return 0
  if (s.includes('transcrib')) return 1
  if (s.includes('keyframe') || s.includes('screen') || s.includes('ocr')) return 2
  if (s.includes('writ') || s.includes('synth') || s.includes('done')) return 3
  return 0
}

export default function ProgressLog({ stage, progress }) {
  const activeIdx = getActiveStage(stage)

  return (
    <div className="progress-wrapper" role="status" aria-live="polite">
      <div className="stage-pills">
        {STAGES.map((s, i) => (
          <div
            key={s.key}
            className={[
              'stage-pill',
              i < activeIdx ? 'pill-done' : '',
              i === activeIdx ? 'pill-active' : '',
            ]
              .filter(Boolean)
              .join(' ')}
          >
            {i < activeIdx && <span className="pill-check">✓ </span>}
            {s.label}
          </div>
        ))}
      </div>
      <div className="progress-track" aria-label={`Progress: ${progress}%`}>
        <div
          className="progress-bar-fill"
          style={{ width: `${progress}%` }}
          role="progressbar"
          aria-valuenow={progress}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
      <p className="stage-label">{stage}</p>
    </div>
  )
}
