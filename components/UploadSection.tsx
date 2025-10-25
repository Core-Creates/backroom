'use client'

import { useState, useRef } from 'react'
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react'

export function UploadSection() {
  const [dragActive, setDragActive] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle')
  const [uploadMessage, setUploadMessage] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleFile = (file: File) => {
    if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
      setUploadedFile(file)
      setUploadStatus('idle')
      setUploadMessage('')
    } else {
      setUploadStatus('error')
      setUploadMessage('Please upload a CSV file')
    }
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!uploadedFile) return

    setUploadStatus('uploading')
    setUploadMessage('')

    try {
      const formData = new FormData()
      formData.append('file', uploadedFile)

      // This would call your Streamlit backend API
      // For now, we'll simulate the upload
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      setUploadStatus('success')
      setUploadMessage('File uploaded and processed successfully!')
    } catch (error) {
      setUploadStatus('error')
      setUploadMessage('Upload failed. Please try again.')
    }
  }

  const resetUpload = () => {
    setUploadedFile(null)
    setUploadStatus('idle')
    setUploadMessage('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Upload Inventory CSV
        </h3>
        <p className="text-sm text-gray-600 mb-6">
          Upload a CSV file with columns: sku, product_name, on_hand, backroom_units, shelf_units, avg_daily_sales, lead_time_days
        </p>

        {/* Upload Area */}
        <div
          className={`relative border-2 border-dashed rounded-lg p-6 text-center ${
            dragActive
              ? 'border-blue-400 bg-blue-50'
              : uploadedFile
              ? 'border-green-400 bg-green-50'
              : 'border-gray-300'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileInput}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          
          {uploadedFile ? (
            <div className="space-y-2">
              <CheckCircle className="mx-auto h-12 w-12 text-green-400" />
              <p className="text-sm font-medium text-green-600">
                {uploadedFile.name}
              </p>
              <p className="text-xs text-green-500">
                {(uploadedFile.size / 1024).toFixed(1)} KB
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              <Upload className="mx-auto h-12 w-12 text-gray-400" />
              <p className="text-sm text-gray-600">
                <span className="font-medium text-blue-600 hover:text-blue-500">
                  Click to upload
                </span>{' '}
                or drag and drop
              </p>
              <p className="text-xs text-gray-500">CSV files only</p>
            </div>
          )}
        </div>

        {/* Upload Status */}
        {uploadMessage && (
          <div className={`mt-4 p-4 rounded-md ${
            uploadStatus === 'success' 
              ? 'bg-green-50 border border-green-200' 
              : 'bg-red-50 border border-red-200'
          }`}>
            <div className="flex">
              <div className="flex-shrink-0">
                {uploadStatus === 'success' ? (
                  <CheckCircle className="h-5 w-5 text-green-400" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-red-400" />
                )}
              </div>
              <div className="ml-3">
                <p className={`text-sm font-medium ${
                  uploadStatus === 'success' ? 'text-green-800' : 'text-red-800'
                }`}>
                  {uploadMessage}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-6 flex justify-end space-x-3">
          {uploadedFile && uploadStatus !== 'success' && (
            <button
              onClick={resetUpload}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Cancel
            </button>
          )}
          
          {uploadedFile && uploadStatus === 'idle' && (
            <button
              onClick={handleUpload}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Upload & Process
            </button>
          )}
          
          {uploadStatus === 'success' && (
            <button
              onClick={resetUpload}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
            >
              Upload Another File
            </button>
          )}
        </div>
      </div>

      {/* Sample Data Format */}
      <div className="bg-white shadow rounded-lg p-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">
          Sample CSV Format
        </h4>
        <div className="bg-gray-50 rounded-md p-4 overflow-x-auto">
          <pre className="text-sm text-gray-600">
{`sku,product_name,on_hand,backroom_units,shelf_units,avg_daily_sales,lead_time_days
SKU-001,Premium Shampoo,150,100,50,12.5,7
SKU-002,Conditioner,75,50,25,8.2,5
SKU-003,Body Lotion,200,150,50,15.3,10`}
          </pre>
        </div>
      </div>
    </div>
  )
}
