import React, { useState, useEffect, useRef } from 'react'
import { submitUrl, pollJob } from './api'
import LinkInput from './components/LinkInput'
import ProgressLog from './components/ProgressLog'
import StepList from './components/StepList'

export default function App() {
  const [phase, setPhase] = useState('idle')
  const [jobId, setJobId] = useState(null)
  const [job, setJob] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')
  const intervalRef = useRef(null)

  const stopPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }

  useEffect(() => () => stopPolling(), [])

  const handleSubmit = async (url) => {
    setPhase('submitting')
    setErrorMsg('')
    setJob(null)
    try {
      const { job_id } = await submitUrl(url)
      setJobId(job_id)
      setPhase('polling')
      intervalRef.current = setInterval(async () => {
        try {
          const jobData = await pollJob(job_id)
          setJob(jobData)
          if (jobData.status === 'done') {
            stopPolling()
            setPhase('done')
          } else if (jobData.status === 'error') {
            stopPolling()
            setErrorMsg(jobData.error || 'Something went wrong.')
            setPhase('error')
          }
        } catch {
          // transient network error — keep polling
        }
      }, 2000)
    } catch (e) {
      setErrorMsg(e.message)
      setPhase('error')
    }
  }

  const handleReset = () => {
    stopPolling()
    setPhase('idle')
    setJob(null)
    setJobId(null)
    setErrorMsg('')
  }

  return (
    <>
      {/* Liquid glass background orbs */}
      <div className="bg-orbs" aria-hidden="true">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />
      </div>

      <div className="app-container">
        <header className="app-header">
          <div className="app-logo-row">
            <div className="logo-icon" aria-hidden="true">⏱</div>
            <h1 className="app-title">StepScribe</h1>
          </div>
          <p className="app-tagline">
            Paste any tutorial link — get precise, numbered steps with timestamps.
          </p>
        </header>

        <main>
          {(phase === 'idle' || phase === 'submitting' || phase === 'error') && (
            <div className="glass-card" style={{ padding: '1.75rem', marginBottom: '2rem' }}>
              <LinkInput onSubmit={handleSubmit} disabled={phase === 'submitting'} />
            </div>
          )}

          {phase === 'error' && (
            <div className="error-box" role="alert">
              <strong>Processing failed</strong>
              <p>{errorMsg}</p>
              <button className="btn-secondary" onClick={handleReset}>
                Try another link
              </button>
            </div>
          )}

          {(phase === 'polling' || phase === 'submitting') && (
            <div className="glass-card" style={{ marginBottom: '2rem' }}>
              <ProgressLog
                stage={job?.stage || 'Starting…'}
                progress={job?.progress || 0}
                status={job?.status || 'processing'}
              />
            </div>
          )}

          {phase === 'done' && job && (
            <div className="glass-card" style={{ padding: '2rem' }}>
              <div className="done-header">
                {job.summary && <p className="video-summary">{job.summary}</p>}
                <button className="btn-secondary" onClick={handleReset}>
                  Process another video
                </button>
              </div>
              <StepList steps={job.steps} video={job.video} jobId={jobId} />
            </div>
          )}
        </main>
      </div>
    </>
  )
}
