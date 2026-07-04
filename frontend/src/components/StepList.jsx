import React, { useState } from 'react'
import StepCard from './StepCard'
import SkillModal from './SkillModal'
import { generateSkillFile } from '../api'

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

export default function StepList({ steps, video, jobId }) {
  const [skillOpen, setSkillOpen] = useState(false)
  const [skillContent, setSkillContent] = useState(null)
  const [skillLoading, setSkillLoading] = useState(false)

  if (!steps || steps.length === 0) return null

  const handleCopy = async () => {
    const md = stepsToMarkdown(steps, video)
    try { await navigator.clipboard.writeText(md) } catch {}
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

  const handleGenerateSkill = async () => {
    setSkillOpen(true)
    setSkillLoading(true)
    setSkillContent(null)
    try {
      const md = await generateSkillFile(jobId)
      setSkillContent(md)
    } catch (e) {
      setSkillContent(`# Error\n\nFailed to generate skill file: ${e.message}`)
    } finally {
      setSkillLoading(false)
    }
  }

  return (
    <div className="step-list-wrapper">
      {video?.title && <p className="video-title-label">{video.title}</p>}

      <div className="step-list-actions">
        <button className="btn-secondary" onClick={handleCopy} title="Copy steps as Markdown">
          Copy MD
        </button>
        <button className="btn-secondary" onClick={handleDownload} title="Download steps as Markdown">
          Download .md
        </button>
        {jobId && (
          <button
            className="btn-skill"
            onClick={handleGenerateSkill}
            disabled={skillLoading}
            title="Generate a reusable SKILL.md for AI agents"
          >
            ⚡ Generate Skill File
          </button>
        )}
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

      {skillOpen && (
        <SkillModal
          content={skillContent}
          loading={skillLoading}
          onClose={() => { setSkillOpen(false); setSkillContent(null) }}
        />
      )}
    </div>
  )
}
