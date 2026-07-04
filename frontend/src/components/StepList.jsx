import React from 'react'
import StepCard from './StepCard'

function formatTimestamp(seconds) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function stepsToMarkdown(steps, video) {
  const header = video?.title ? `# ${video.title}\n\n` : '# Tutorial Steps\n\n'
  const lines = steps.map((step) => `${step.n}. [${formatTimestamp(step.start)}] ${step.text}`)
  return header + lines.join('\n')
}

export default function StepList({ steps, video }) {
  if (!steps || steps.length === 0) return null

  const handleCopy = async () => {
    const md = stepsToMarkdown(steps, video)
    try {
      await navigator.clipboard.writeText(md)
    } catch {
      // clipboard API unavailable in some contexts
    }
  }

  const handleDownload = () => {
    const md = stepsToMarkdown(steps, video)
    const blob = new Blob([md], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'steps.md'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="step-list-wrapper">
      {video?.title && <p className="video-title-label">{video.title}</p>}
      <div className="step-list-actions">
        <button className="btn-secondary" onClick={handleCopy}>
          Copy as Markdown
        </button>
        <button className="btn-secondary" onClick={handleDownload}>
          Download .md
        </button>
      </div>
      <div className="step-rail" role="list">
        {steps.map((step, i) => (
          <StepCard
            key={step.n}
            step={step}
            video={video}
            isLast={i === steps.length - 1}
          />
        ))}
      </div>
    </div>
  )
}
