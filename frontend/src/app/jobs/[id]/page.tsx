'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth, SignedIn, SignedOut } from '@clerk/nextjs'
import { getJob, getJobStatus } from '../../../lib/api'
import { Job, JobStatus } from '../../../lib/types'
import {
  ArrowLeft,
  Download,
  Loader2,
  PlayCircle,
  FileText,
  AlertCircle,
} from 'lucide-react'

const POLL_INTERVAL_MS = 5000

export default function JobDetailPage() {
  const params = useParams()
  const router = useRouter()
  const { getToken } = useAuth()

  const [job, setJob] = useState<Job | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const jobIdParam = params?.id
  const jobId =
    typeof jobIdParam === 'string'
      ? Number(jobIdParam)
      : Array.isArray(jobIdParam)
        ? Number(jobIdParam[0])
        : NaN

  useEffect(() => {
    if (!jobId || Number.isNaN(jobId)) {
      setError('Invalid job ID.')
      setIsLoading(false)
      return
    }

    let intervalId: NodeJS.Timeout | null = null
    let cancelled = false

    const loadJob = async () => {
      try {
        const token = await getToken()

        if (!token) {
          setError('You must be signed in to view this job.')
          setIsLoading(false)
          return
        }

        const initialJob = await getJob(jobId, token)
        if (cancelled) return

        setJob(initialJob)
        setError(null)
        setIsLoading(false)

        const shouldPoll =
          initialJob.status === JobStatus.PENDING ||
          initialJob.status === JobStatus.PROCESSING

        if (shouldPoll) {
          intervalId = setInterval(async () => {
            try {
              const status = await getJobStatus(jobId, token)
              if (cancelled) return

              setJob((prev) =>
                prev
                  ? {
                      ...prev,
                      ...status,
                    }
                  : {
                      ...initialJob,
                      ...status,
                    }
              )

              const finalStatus =
                status.status || status.job_status || initialJob.status

              if (
                finalStatus === JobStatus.COMPLETED ||
                finalStatus === JobStatus.FAILED
              ) {
                if (intervalId) {
                  clearInterval(intervalId)
                  intervalId = null
                }
              }
            } catch (pollError) {
              // Keep polling on transient errors, but log for debugging.
              console.error('Failed to poll job status', pollError)
            }
          }, POLL_INTERVAL_MS)
        }
      } catch (loadError) {
        console.error('Failed to fetch job', loadError)
        setError('Failed to load job. Please refresh and try again.')
        setIsLoading(false)
      }
    }

    loadJob()

    return () => {
      cancelled = true
      if (intervalId) clearInterval(intervalId)
    }
  }, [jobId, getToken])

  const handleDownload = () => {
    if (job?.audio_s3_url) {
      window.open(job.audio_s3_url, '_blank', 'noopener,noreferrer')
    }
  }

  const renderStatusBadge = (status: JobStatus) => {
    const base =
      'inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium'
    switch (status) {
      case JobStatus.COMPLETED:
        return (
          <span className={`${base} bg-emerald-50 text-emerald-700`}>
            Completed
          </span>
        )
      case JobStatus.FAILED:
        return (
          <span className={`${base} bg-rose-50 text-rose-700`}>Failed</span>
        )
      case JobStatus.PROCESSING:
        return (
          <span className={`${base} bg-blue-50 text-blue-700`}>
            In progress
          </span>
        )
      case JobStatus.PENDING:
      default:
        return (
          <span className={`${base} bg-amber-50 text-amber-700`}>Queued</span>
        )
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <button
        onClick={() => router.push('/jobs')}
        className="mb-6 inline-flex items-center text-xs sm:text-sm text-slate-500 hover:text-blue-600 transition-colors"
      >
        <ArrowLeft className="h-4 w-4 mr-1" />
        Back to jobs
      </button>

      <SignedOut>
        <div className="bg-white border border-slate-200 rounded-xl p-6 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-amber-500 mt-0.5" />
          <div>
            <h2 className="text-sm font-semibold text-slate-900">
              Sign in required
            </h2>
            <p className="mt-1 text-xs sm:text-sm text-slate-600">
              You need to be signed in to view job details. Use the header
              controls to sign in, then return to this page.
            </p>
          </div>
        </div>
        <div className="mt-6" />
      </SignedOut>

      <SignedIn>
        {isLoading && (
          <div className="bg-white/80 backdrop-blur border border-slate-100 rounded-2xl px-6 py-10 flex flex-col items-center justify-center shadow-sm">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
            <p className="text-sm sm:text-base text-slate-600">
              Fetching job details…
            </p>
          </div>
        )}

        {!isLoading && error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 px-4 py-3 rounded-xl text-xs sm:text-sm flex items-start gap-2">
            <AlertCircle className="h-4 w-4 mt-0.5" />
            <div>{error}</div>
          </div>
        )}

        {!isLoading && !error && job && (
          <div className="space-y-6">
            {/* Title + meta */}
            <div className="bg-white/80 backdrop-blur border border-slate-100 rounded-2xl p-6 shadow-sm space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className="mt-1">
                    <FileText className="h-8 w-8 text-blue-500" />
                  </div>
                  <div>
                    <h1 className="text-lg sm:text-xl font-semibold text-slate-900 break-words">
                      {job.original_filename}
                    </h1>
                    <p className="mt-1 text-xs sm:text-sm text-slate-500">
                      Created{' '}
                      {new Date(job.created_at).toLocaleString(undefined, {
                        dateStyle: 'medium',
                        timeStyle: 'short',
                      })}
                    </p>
                  </div>
                </div>
                <div className="flex flex-col items-start sm:items-end gap-2">
                  {renderStatusBadge(job.status)}
                  <p className="text-[10px] sm:text-xs text-slate-500">
                    Voice: {job.voice_provider} · {job.voice_type} ·
                    &nbsp;Speed: {job.reading_speed}x
                  </p>
                  <p className="text-[10px] sm:text-xs text-slate-500">
                    Mode:{' '}
                    {job.conversion_mode === 'summary_explanation'
                      ? 'AI summary & explanation'
                      : 'Full text narration'}
                  </p>
                </div>
              </div>

              {/* Progress / status */}
              {(job.status === JobStatus.PENDING ||
                job.status === JobStatus.PROCESSING) && (
                <div className="mt-2 space-y-2">
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-500"
                      style={{
                        width: `${Math.min(
                          Math.max(job.progress_percentage || 10, 10),
                          95
                        )}%`,
                      }}
                    />
                  </div>
                  <p className="text-[10px] sm:text-xs text-slate-500">
                    Your PDF is being processed using our OCR and TTS pipeline.
                    For long or scanned papers, this can take a few minutes.
                  </p>
                </div>
              )}

              {job.status === JobStatus.FAILED && job.error_message && (
                <div className="mt-2 bg-rose-50 border border-rose-200 rounded-xl px-3 py-2 text-[10px] sm:text-xs text-rose-800 flex gap-2">
                  <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
                  <div>
                    <div className="font-medium mb-0.5">Conversion failed</div>
                    <div>{job.error_message}</div>
                  </div>
                </div>
              )}
            </div>

            {/* Output / audio section */}
            <div className="bg-white/80 backdrop-blur border border-slate-100 rounded-2xl p-6 shadow-sm space-y-4">
              <h2 className="text-sm sm:text-base font-semibold text-slate-900">
                Output
              </h2>

              {job.status === JobStatus.COMPLETED && job.audio_s3_url && (
                <div className="space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <PlayCircle className="h-6 w-6 text-blue-500" />
                      <div className="text-xs sm:text-sm text-slate-700">
                        Stream the generated audio directly, or download it for
                        offline listening.
                      </div>
                    </div>
                    <button
                      onClick={handleDownload}
                      className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg bg-blue-600 text-white text-[10px] sm:text-xs font-medium hover:bg-blue-700 transition-colors"
                    >
                      <Download className="h-3 w-3 mr-1.5" />
                      Download audio
                    </button>
                  </div>
                  <audio
                    controls
                    src={job.audio_s3_url}
                    className="w-full rounded-lg border border-slate-200"
                  >
                    Your browser does not support the audio element.
                  </audio>
                </div>
              )}

              {job.status === JobStatus.COMPLETED && !job.audio_s3_url && (
                <div className="flex items-start gap-2 text-[10px] sm:text-xs text-slate-600">
                  <AlertCircle className="h-4 w-4 mt-0.5 text-amber-500" />
                  <div>
                    This job is marked as completed, but no audio URL is
                    available. If this is unexpected, verify the backend
                    configuration or S3 permissions.
                  </div>
                </div>
              )}

              {(job.status === JobStatus.PENDING ||
                job.status === JobStatus.PROCESSING) && (
                <div className="flex items-start gap-2 text-[10px] sm:text-xs text-slate-600">
                  <Loader2 className="h-4 w-4 mt-0.5 animate-spin text-blue-500" />
                  <div>
                    We are extracting text, generating the narration or summary,
                    and preparing your audio. You can safely leave this page and
                    return later from the “My Jobs” view.
                  </div>
                </div>
              )}

              {job.status === JobStatus.FAILED && (
                <div className="flex items-start gap-2 text-[10px] sm:text-xs text-slate-600">
                  <AlertCircle className="h-4 w-4 mt-0.5 text-rose-500" />
                  <div>
                    If this is a scanned or very large PDF, try again with a
                    clearer copy or contact support with this job ID:{' '}
                    <span className="font-mono text-rose-700">{job.id}</span>.
                  </div>
                </div>
              )}
            </div>

            {/* Contextual hints for academic/novel use cases */}
            <div className="text-[9px] sm:text-[10px] text-slate-500 leading-relaxed">
              <p>
                Tip for researchers: use the summary mode for dense scientific
                PDFs to get an AI-generated overview you can listen to while
                commuting. For deep reading of novels or long-form reports, use
                full-text narration for a faithful audiobook experience.
              </p>
            </div>
          </div>
        )}
      </SignedIn>
    </div>
  )
}
