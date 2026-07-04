import React from 'react'

function formatTimestamp(seconds) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function getTimestampUrl(step, video) {
  if (!video) return null
  if (video.platform === 'youtube') {
    return `https://www.youtube.com/watch?v=${video.video_id}&t=${Math.floor(step.start)}s`
  }
  if (video.platform === 'instagram') {
    return `https://www.instagram.com/p/${video.video_id}/`
  }
  return null
}

export default function StepCard({ step, video, isLast }) {
  const tsUrl = getTimestampUrl(step, video)
  const tsLabel = formatTimestamp(step.start)

  return (
    <div className="step-card">
      <div className="step-number-col">
        <span className="step-number" aria-hidden="true">
          {step.n}
        </span>
        {!isLast && <div className="step-connector" aria-hidden="true" />}
      </div>
      <div className="step-content">
        <p className="step-text">{step.text}</p>
        {tsUrl ? (
          <a
            href={tsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="timestamp-chip"
            title={`Jump to ${tsLabel} in video`}
          >
            ▶ {tsLabel}
          </a>
        ) : (
          <span className="timestamp-chip timestamp-chip--static">{tsLabel}</span>
        )}
      </div>
    </div>
  )
}
