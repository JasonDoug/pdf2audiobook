'use client'

import { Job, JobStatus as JobStatusEnum } from '../lib/types'
import { CheckCircle, AlertCircle, RefreshCw } from 'lucide-react'

interface JobStatusProps {
  job: Job
}

export default function JobStatus({ job }: JobStatusProps) {
  return (
    <div className="p-4 border rounded-lg">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-bold">{job.original_filename}</h3>
        <span
          className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
            job.status === JobStatusEnum.COMPLETED
              ? 'bg-green-100 text-green-800'
              : job.status === JobStatusEnum.FAILED
                ? 'bg-red-100 text-red-800'
                : 'bg-yellow-100 text-yellow-800'
          }`}
        >
          {job.status}
        </span>
      </div>
      <div className="mt-4">
        <div className="flex items-center">
          {job.status === JobStatusEnum.COMPLETED ? (
            <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
          ) : job.status === JobStatusEnum.FAILED ? (
            <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
          ) : (
            <RefreshCw className="h-5 w-5 text-yellow-500 mr-2 animate-spin" />
          )}
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-blue-600 h-2.5 rounded-full"
              style={{ width: `${job.progress_percentage}%` }}
            ></div>
          </div>
        </div>
        {job.status === JobStatusEnum.COMPLETED && job.audio_s3_url && (
          <div className="mt-4">
            <a
              href={job.audio_s3_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              Download Audiobook
            </a>
          </div>
        )}
        {job.status === JobStatusEnum.FAILED && job.error_message && (
          <div className="mt-4 text-red-600">
            <p>{job.error_message}</p>
          </div>
        )}
      </div>
    </div>
  )
}
