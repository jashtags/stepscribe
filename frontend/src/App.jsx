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
          // transient — keep polling
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
    <div className="app-container">
      <header className="app-header">
        <h1 className="app-title">StepScribe</h1>
        <p className="app-tagline">Paste a tutorial link. Get clear numbered steps.</p>
      </header>

      <main className="app-main">
        {(phase === 'idle' || phase === 'submitting' || phase === 'error') && (
          <LinkInput onSubmit={handleSubmit} disabled={phase === 'submitting'} />
        )}

        {phase === 'error' && (
          <div className="error-box" role="alert">
            <strong>Something went wrong</strong>
            <p>{errorMsg}</p>
            <button className="btn-secondary" onClick={handleReset}>
              Try another link
            </button>
          </div>
        )}

        {(phase === 'polling' || phase === 'submitting') && (
          <ProgressLog
            stage={job?.stage || 'Starting…'}
            progress={job?.progress || 0}
            status={job?.status || 'processing'}
          />
        )}

        {phase === 'done' && job && (
          <>
            <div className="done-header">
              {job.summary && <p className="video-summary">{job.summary}</p>}
              <button className="btn-secondary" onClick={handleReset}>
                Process another video
              </button>
            </div>
            <StepList steps={job.steps} video={job.video} />
          </>
        )}
      </main>
    </div>
  )
}
