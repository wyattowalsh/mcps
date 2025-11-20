'use client'

import { createClient } from '@/lib/supabase/client'
import { useState } from 'react'

interface FileUploadProps {
  bucket?: string
  onUploadComplete?: (url: string, path: string) => void
  accept?: string
  maxSizeMB?: number
}

/**
 * File upload component using Supabase Storage
 * Supports drag and drop, progress tracking, and file validation
 */
export default function FileUpload({
  bucket = 'mcps-files',
  onUploadComplete,
  accept,
  maxSizeMB = 10,
}: FileUploadProps) {
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [uploadedUrl, setUploadedUrl] = useState<string | null>(null)
  const supabase = createClient()

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    try {
      setUploading(true)
      setError(null)
      setProgress(0)

      if (!event.target.files || event.target.files.length === 0) {
        return
      }

      const file = event.target.files[0]

      // Validate file size
      const maxSizeBytes = maxSizeMB * 1024 * 1024
      if (file.size > maxSizeBytes) {
        throw new Error(`File size must be less than ${maxSizeMB}MB`)
      }

      // Generate unique file path
      const fileExt = file.name.split('.').pop()
      const fileName = `${Math.random().toString(36).substring(2)}_${Date.now()}.${fileExt}`
      const filePath = `uploads/${fileName}`

      // Upload file to Supabase Storage
      const { error: uploadError, data } = await supabase.storage
        .from(bucket)
        .upload(filePath, file, {
          cacheControl: '3600',
          upsert: false,
        })

      if (uploadError) {
        throw uploadError
      }

      setProgress(100)

      // Get public URL
      const {
        data: { publicUrl },
      } = supabase.storage.from(bucket).getPublicUrl(filePath)

      setUploadedUrl(publicUrl)

      if (onUploadComplete) {
        onUploadComplete(publicUrl, filePath)
      }
    } catch (error: any) {
      console.error('Error uploading file:', error)
      setError(error.message || 'Failed to upload file')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (filePath: string) => {
    try {
      setError(null)

      const { error: deleteError } = await supabase.storage
        .from(bucket)
        .remove([filePath])

      if (deleteError) {
        throw deleteError
      }

      setUploadedUrl(null)
    } catch (error: any) {
      console.error('Error deleting file:', error)
      setError(error.message || 'Failed to delete file')
    }
  }

  return (
    <div className="w-full max-w-md space-y-4">
      <div className="relative">
        <label
          htmlFor="file-upload"
          className={`
            flex cursor-pointer flex-col items-center justify-center
            rounded-lg border-2 border-dashed border-gray-300 bg-gray-50
            px-6 py-10 transition-colors hover:border-gray-400 hover:bg-gray-100
            dark:border-gray-600 dark:bg-gray-800 dark:hover:border-gray-500 dark:hover:bg-gray-700
            ${uploading ? 'cursor-not-allowed opacity-50' : ''}
          `}
        >
          <div className="space-y-2 text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
              aria-hidden="true"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              <span className="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400">
                {uploading ? 'Uploading...' : 'Upload a file'}
              </span>
              {!uploading && <span> or drag and drop</span>}
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {accept ? `${accept.replace(/,/g, ', ')}` : 'Any file type'} up to {maxSizeMB}MB
            </p>
          </div>
          <input
            id="file-upload"
            name="file-upload"
            type="file"
            className="sr-only"
            onChange={handleUpload}
            disabled={uploading}
            accept={accept}
          />
        </label>

        {uploading && (
          <div className="mt-2">
            <div className="relative h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
              <div
                className="h-full bg-blue-600 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="mt-1 text-center text-xs text-gray-600 dark:text-gray-400">
              {progress}% uploaded
            </p>
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4 dark:bg-red-900/20">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-red-800 dark:text-red-200">
                {error}
              </p>
            </div>
          </div>
        </div>
      )}

      {uploadedUrl && (
        <div className="rounded-md bg-green-50 p-4 dark:bg-green-900/20">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-green-800 dark:text-green-200">
                File uploaded successfully!
              </p>
              <a
                href={uploadedUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-1 block truncate text-xs text-green-700 hover:text-green-800 dark:text-green-300 dark:hover:text-green-200"
              >
                {uploadedUrl}
              </a>
            </div>
            <button
              onClick={() => {
                navigator.clipboard.writeText(uploadedUrl)
                alert('URL copied to clipboard!')
              }}
              className="ml-2 text-green-700 hover:text-green-800 dark:text-green-300 dark:hover:text-green-200"
              title="Copy URL"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
