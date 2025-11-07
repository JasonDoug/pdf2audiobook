'use client'

import { useEffect, useState } from 'react'
import { getJob } from '../../../lib/api'
import { Job } from '../../../lib/types'
import JobStatus from '../../../components/JobStatus'
import { useParams } from 'next/navigation'
import { useAuth } from '@clerk/nextjs'

export default function JobDetailsPage() {
  const [job, setJob] = useState<Job | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const params = useParams() as { jobId: string }
  const { jobId } = params
  const { getToken } = useAuth()

  useEffect(() => {
    const fetchJob = async () => {
      if (jobId) {
        try {
          const token = await getToken()
          if (!token) {
            return
          }
          const fetchedJob = await getJob(Number(jobId), token)
          setJob(fetchedJob)
        } catch (error) {
          console.error('Failed to fetch job:', error)
        } finally {
          setIsLoading(false)
        }
      }
    }

    fetchJob()
  }, [jobId, getToken])

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="text-center mb-12">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
          Job Details
        </h1>
      </div>

      {isLoading ? (
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4">Loading job details...</p>
        </div>
      ) : job ? (
        <JobStatus job={job} />
      ) : (
        <p>Job not found.</p>
      )}
    </div>
  )
}
