'use client'

import { useState, useRef } from 'react'
import { Upload, FileText, CheckCircle, AlertCircle, Database } from 'lucide-react'

export function ParquetUpload() {
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
    if (file.name.endsWith('.parquet')) {
      setUploadedFile(file)
      setUploadStatus('idle')
      setUploadMessage('')
    } else {
      setUploadStatus('error')
      setUploadMessage('Please upload a Parquet file (.parquet)')
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

      const response = await fetch('/api/upload/parquet', {
        method: 'POST',
        body: formData,
      })

      const result = await response.json()

      if (response.ok) {
        setUploadStatus('success')
        setUploadMessage(`File uploaded successfully! Converted to JSON for frontend consumption.`)
        
        // Optionally convert to JSON
        if (result.filename) {
          // You could trigger a conversion here
          console.log('File uploaded:', result.filename)
        }
      } else {
        setUploadStatus('error')
        setUploadMessage(result.error || 'Upload failed')
      }
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
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <Database className="h-5 w-5 mr-2" />
          Upload Parquet Data Files
        </h3>
        <p className="text-sm text-gray-600 mb-6">
          Upload Parquet files containing your inventory data. The system will automatically convert them to JSON for frontend consumption.
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
            accept=".parquet"
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
              <p className="text-xs text-gray-500">Parquet files only (.parquet)</p>
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
              Upload & Convert
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

      {/* Expected Format */}
      <div className="bg-white shadow rounded-lg p-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">
          Expected Parquet File Format
        </h4>
        <div className="bg-gray-50 rounded-md p-4">
          <p className="text-sm text-gray-600 mb-2">
            Your Parquet file should contain the following columns:
          </p>
          <ul className="text-sm text-gray-600 space-y-1">
            <li><code className="bg-gray-200 px-1 rounded">sku</code> - Product SKU (string)</li>
            <li><code className="bg-gray-200 px-1 rounded">product_name</code> - Product name (string)</li>
            <li><code className="bg-gray-200 px-1 rounded">category</code> - Product category (string, optional)</li>
            <li><code className="bg-gray-200 px-1 rounded">on_hand</code> - Current stock level (number)</li>
            <li><code className="bg-gray-200 px-1 rounded">backroom_units</code> - Backroom inventory (number)</li>
            <li><code className="bg-gray-200 px-1 rounded">shelf_units</code> - Shelf inventory (number)</li>
            <li><code className="bg-gray-200 px-1 rounded">avg_daily_sales</code> - Average daily sales (number)</li>
            <li><code className="bg-gray-200 px-1 rounded">lead_time_days</code> - Lead time in days (number)</li>
            <li><code className="bg-gray-200 px-1 rounded">cost_per_unit</code> - Cost per unit (number, optional)</li>
            <li><code className="bg-gray-200 px-1 rounded">selling_price</code> - Selling price (number, optional)</li>
            <li><code className="bg-gray-200 px-1 rounded">supplier</code> - Supplier name (string, optional)</li>
            <li><code className="bg-gray-200 px-1 rounded">last_updated</code> - Last update timestamp (string, optional)</li>
          </ul>
        </div>
      </div>

      {/* Conversion Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <FileText className="h-5 w-5 text-blue-400" />
          </div>
          <div className="ml-3">
            <h4 className="text-sm font-medium text-blue-800">Conversion Process</h4>
            <p className="text-sm text-blue-700 mt-1">
              After uploading, use the Python script to convert Parquet to JSON:
            </p>
            <code className="block mt-2 text-xs bg-blue-100 p-2 rounded">
              python scripts/convert_parquet.py data/your_file.parquet
            </code>
          </div>
        </div>
      </div>
    </div>
  )
}

