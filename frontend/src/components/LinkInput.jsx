import React, { useState } from 'react'

const URL_PATTERN = /(?:youtube\.com|youtu\.be|instagram\.com)/i

export default function LinkInput({ onSubmit, disabled }) {
  const [value, setValue] = useState('')
  const [urlError, setUrlError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    const trimmed = value.trim()
    if (!trimmed) {
      setUrlError('Please enter a URL.')
      return
    }
    if (!URL_PATTERN.test(trimmed)) {
      setUrlError('Only YouTube and Instagram URLs are supported.')
      return
    }
    setUrlError('')
    onSubmit(trimmed)
  }

  return (
    <div className="link-input-wrapper">
      <form className="link-form" onSubmit={handleSubmit} noValidate>
        <div className="input-row">
          <input
            type="url"
            className={`link-input${urlError ? ' input-error' : ''}`}
            placeholder="https://youtube.com/watch?v=... or instagram.com/reel/..."
            value={value}
            onChange={(e) => {
              setValue(e.target.value)
              setUrlError('')
            }}
            disabled={disabled}
            aria-label="Video URL"
            aria-describedby={urlError ? 'url-error' : undefined}
          />
          <button type="submit" className="btn-primary" disabled={disabled}>
            {disabled ? 'Working…' : 'Get Steps'}
          </button>
        </div>
        {urlError && (
          <p id="url-error" className="input-error-msg" role="alert">
            {urlError}
          </p>
        )}
      </form>
      <p className="input-hint">
        Paste a YouTube or Instagram link — get the tutorial as clear numbered steps.
      </p>
    </div>
  )
}
