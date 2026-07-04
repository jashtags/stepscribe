import React, { useEffect } from 'react'
import ReactDOM from 'react-dom'

export default function SkillModal({ content, loading, onClose }) {
  // Trap escape key
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'SKILL.md'
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleCopy = async () => {
    if (!content) return
    try { await navigator.clipboard.writeText(content) } catch {}
  }

  return ReactDOM.createPortal(
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label="Skill file"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="glass-card modal-panel">
        <div className="modal-header">
          <div className="modal-title">
            <span>⚡</span>
            SKILL.md
            <span className="modal-title-badge">Claude Agent Ready</span>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close">✕</button>
        </div>

        <div className="modal-body">
          {loading ? (
            <div className="skill-generating">
              <div className="spinner" />
              Generating skill file with LLM…
            </div>
          ) : (
            <code className="skill-code">{content}</code>
          )}
        </div>

        {!loading && content && (
          <div className="modal-footer">
            <button className="btn-skill" onClick={handleDownload}>
              ↓ Download SKILL.md
            </button>
            <button className="btn-secondary" onClick={handleCopy}>
              Copy
            </button>
            <button className="btn-secondary" style={{ marginLeft: 'auto' }} onClick={onClose}>
              Close
            </button>
          </div>
        )}
      </div>
    </div>,
    document.body
  )
}
