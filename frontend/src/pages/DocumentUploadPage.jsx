import { useState } from 'react'
import client from '../api/client'

function DocumentUploadPage() {
  const [customerId, setCustomerId] = useState('')
  const [applicationId, setApplicationId] = useState('')
  const [files, setFiles] = useState([])
  const [status, setStatus] = useState('')
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [processingResult, setProcessingResult] = useState(null)

  const handleFileChange = (event) => {
    setFiles(Array.from(event.target.files || []))
    setError(null)
    setSuccess(null)
    setProcessingResult(null)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError(null)
    setSuccess(null)
    setProcessingResult(null)

    if (!customerId.trim() || !applicationId.trim()) {
      setError('Customer ID and Application ID are required.')
      return
    }

    if (files.length === 0) {
      setError('Select at least one PDF to upload.')
      return
    }

    try {
      setStatus('Uploading files...')
      const uploadResults = []

      for (const file of files) {
        const formData = new FormData()
        formData.append('file', file)

        const uploadResponse = await client.post('/api/documents/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })

        uploadResults.push(uploadResponse.data)
      }

      setSuccess('Files uploaded successfully.')
      setStatus('Processing documents...')

      const processResults = []
      for (const uploaded of uploadResults) {
        const processResponse = await client.post('/api/documents/process', null, {
          params: {
            file_id: uploaded.file_id,
            customer_id: customerId.trim(),
            application_id: applicationId.trim(),
          },
        })
        processResults.push(processResponse.data)
      }

      setProcessingResult(processResults)
      setStatus('Document processing complete.')
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload or processing failed.')
      setStatus('')
    }
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <h3 className="text-2xl font-semibold text-slate-900 mb-6">Document Upload</h3>
      {error && <div className="mb-4 rounded bg-red-100 px-4 py-3 text-sm text-red-700">{error}</div>}
      {success && <div className="mb-4 rounded bg-emerald-100 px-4 py-3 text-sm text-emerald-700">{success}</div>}
      <form onSubmit={handleSubmit} className="grid gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700">Customer ID</label>
          <input
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            className="mt-1 w-full max-w-xl rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-indigo-500"
            placeholder="Enter customer ID"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">Application ID</label>
          <input
            value={applicationId}
            onChange={(e) => setApplicationId(e.target.value)}
            className="mt-1 w-full max-w-xl rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-indigo-500"
            placeholder="Enter application ID"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">PDF Files</label>
          <input
            type="file"
            multiple
            accept="application/pdf"
            onChange={handleFileChange}
            className="mt-1 w-full max-w-xl text-sm text-slate-700"
          />
        </div>

        {files.length > 0 && (
          <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-700">
            <p className="font-semibold text-slate-900 mb-2">Selected files</p>
            <ul className="list-disc space-y-1 pl-5">
              {files.map((file) => (
                <li key={file.name + file.size}>{file.name}</li>
              ))}
            </ul>
          </div>
        )}

        <button
          type="submit"
          className="rounded-xl w-auto max-w-[10rem] bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
        >
          Upload and Process
        </button>
      </form>

      {status && <p className="mt-4 text-sm text-slate-600">{status}</p>}

      {processingResult && (
        <div className="mt-6 space-y-4 rounded-2xl bg-slate-50 p-6 shadow-sm">
          <h4 className="text-lg font-semibold text-slate-900">Processing Results</h4>
          {processingResult.map((result, index) => (
            <div key={index} className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">File: {result.file_name || 'Uploaded file'}</p>
              <p className="mt-2 text-sm text-slate-700">Decision: {result.decision || 'N/A'}</p>
              <p className="mt-1 text-sm text-slate-500">Risk score: {result.risk_score ?? 'N/A'}</p>
              <p className="mt-1 text-sm text-slate-500">Matched: {result.matched ? 'Yes' : 'No'}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default DocumentUploadPage
