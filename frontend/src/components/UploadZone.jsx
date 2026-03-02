import { useCallback, useState } from 'react'
import { CloudArrowUpIcon } from '@heroicons/react/24/outline'

export default function UploadZone({ onFile, accept = '*', label = 'Upload file', loading = false }) {
  const [dragging, setDragging] = useState(false)

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault()
      setDragging(false)
      const file = e.dataTransfer.files?.[0]
      if (file) onFile(file)
    },
    [onFile],
  )

  const handleChange = (e) => {
    const file = e.target.files?.[0]
    if (file) onFile(file)
    e.target.value = ''
  }

  return (
    <label
      className={`flex flex-col items-center justify-center w-full border-2 border-dashed rounded-xl p-6 cursor-pointer transition-colors ${
        dragging
          ? 'border-indigo-500 bg-indigo-50'
          : 'border-gray-300 bg-gray-50 hover:border-indigo-400 hover:bg-indigo-50'
      }`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
    >
      <CloudArrowUpIcon className="w-8 h-8 text-indigo-400 mb-2" />
      {loading ? (
        <span className="text-sm text-indigo-600 font-medium animate-pulse">Uploading…</span>
      ) : (
        <>
          <span className="text-sm text-gray-700 font-medium">{label}</span>
          <span className="text-xs text-gray-400 mt-1">Drag & drop or click to browse</span>
        </>
      )}
      <input type="file" className="hidden" accept={accept} onChange={handleChange} disabled={loading} />
    </label>
  )
}
