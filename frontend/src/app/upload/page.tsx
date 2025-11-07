'use client'

import { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X, CheckCircle, AlertCircle } from 'lucide-react'
import { createJob } from '../../lib/api'
import { Job } from '../../lib/types'
import toast, { Toaster } from 'react-hot-toast'
import { useAuth } from '@clerk/nextjs'

export default function UploadPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [jobResponse, setJobResponse] = useState<Job | null>(null)
  const { getToken } = useAuth()

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024, // 50MB
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setSelectedFile(acceptedFiles[0])
        setJobResponse(null)
      }
    },
  })

  const handleUpload = async () => {
    if (!selectedFile) return

    setIsUploading(true)
    setUploadProgress(0)

    try {
      const token = await getToken()
      if (!token) {
        throw new Error('You must be signed in to upload a file.')
      }

      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('voice_provider', 'openai')
      formData.append('voice_type', 'alloy')
      formData.append('reading_speed', '1.0')
      formData.append('include_summary', 'true')

      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 10, 90))
      }, 200)

      const response = await createJob(formData, token)

      clearInterval(progressInterval)
      setUploadProgress(100)
      setJobResponse(response)

      toast.success('PDF uploaded successfully! Processing will begin shortly.')

      // Reset after success
      setTimeout(() => {
        setSelectedFile(null)
        setUploadProgress(0)
        setJobResponse(null)
      }, 3000)
    } catch (error) {
      console.error('Upload failed:', error)
      toast.error(
        error instanceof Error
          ? error.message
          : 'Upload failed. Please try again.'
      )
      setUploadProgress(0)
    } finally {
      setIsUploading(false)
    }
  }

  const removeFile = () => {
    setSelectedFile(null)
    setJobResponse(null)
    setUploadProgress(0)
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <Toaster position="top-right" />

      <div className="text-center mb-12">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
          Upload Your PDF
        </h1>
        <p className="text-xl text-gray-600">
          Convert your PDF documents to high-quality audiobooks
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-8">
        {/* Upload Area */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-blue-400 bg-blue-50'
              : selectedFile
                ? 'border-green-400 bg-green-50'
                : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />

          {selectedFile ? (
            <div className="space-y-4">
              <div className="flex items-center justify-center space-x-3">
                <FileText className="h-12 w-12 text-green-600" />
                <div className="text-left">
                  <p className="text-lg font-medium text-gray-900">
                    {selectedFile.name}
                  </p>
                  <p className="text-sm text-gray-500">
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    removeFile()
                  }}
                  className="p-1 hover:bg-gray-200 rounded"
                >
                  <X className="h-5 w-5 text-gray-500" />
                </button>
              </div>

              {isUploading && (
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              )}

              {jobResponse && (
                <div className="flex items-center justify-center space-x-2 text-green-600">
                  <CheckCircle className="h-5 w-5" />
                  <span>Job created successfully! ID: {jobResponse.id}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              <Upload className="h-16 w-16 text-gray-400 mx-auto" />
              <div>
                <p className="text-xl font-medium text-gray-900">
                  {isDragActive
                    ? 'Drop your PDF here'
                    : 'Drag & drop your PDF here'}
                </p>
                <p className="text-gray-500 mt-2">or click to browse files</p>
              </div>
              <div className="text-sm text-gray-500">
                <p>Maximum file size: 50MB</p>
                <p>Supported format: PDF only</p>
              </div>
            </div>
          )}
        </div>

        {/* Upload Button */}
        {selectedFile && !isUploading && !jobResponse && (
          <div className="mt-8 text-center">
            <button
              onClick={handleUpload}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold text-lg flex items-center space-x-2 mx-auto"
            >
              <Upload className="h-5 w-5" />
              <span>Start Conversion</span>
            </button>
          </div>
        )}

        {/* Processing Status */}
        {isUploading && (
          <div className="mt-8 text-center">
            <div className="inline-flex items-center space-x-2 text-blue-600">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
              <span>Processing your PDF...</span>
            </div>
          </div>
        )}

        {/* Job Response */}
        {jobResponse && (
          <div className="mt-8 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div>
                <p className="font-medium text-green-800">Upload Successful!</p>
                <p className="text-sm text-green-700">
                  Job ID: {jobResponse.id} - Status: {jobResponse.status}
                </p>
                <p className="text-sm text-green-700 mt-1">
                  Check your jobs page to monitor progress.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Error Handling */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <div className="flex items-center justify-center space-x-1">
            <AlertCircle className="h-4 w-4" />
            <span>
              Having trouble? Make sure you're signed in and your file is under
              50MB.
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
