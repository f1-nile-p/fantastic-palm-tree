import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { getOrders, uploadPO } from '../api'
import StatusBadge from '../components/StatusBadge'
import ConfidenceScore from '../components/ConfidenceScore'
import UploadZone from '../components/UploadZone'

const TABS = [
  { key: 'all', label: 'All' },
  { key: 'pending', label: 'Pending' },
  { key: 'under_review', label: 'Under Review' },
  { key: 'approved', label: 'Approved' },
  { key: 'rejected', label: 'Rejected' },
]

export default function OrderQueue() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [activeTab, setActiveTab] = useState('all')
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const fetchOrders = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getOrders({ limit: 100 })
      setOrders(res.data)
    } catch (e) {
      setError('Failed to load orders')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchOrders() }, [fetchOrders])

  const handleUpload = async (file) => {
    setUploading(true)
    setError(null)
    try {
      await uploadPO(file)
      await fetchOrders()
    } catch (e) {
      setError(e.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const filtered = activeTab === 'all'
    ? orders
    : orders.filter((o) => o.status === activeTab)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Purchase Orders</h1>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <p className="text-sm font-medium text-gray-700 mb-3">Upload new PO document</p>
        <UploadZone
          onFile={handleUpload}
          accept=".pdf,.docx,.txt"
          label="Upload PO (PDF, DOCX, TXT)"
          loading={uploading}
        />
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </div>

      {/* Status filter tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              activeTab === tab.key
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-400">Loading orders…</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          No orders found.{activeTab !== 'all' && ' Try a different filter.'}
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {['Filename', 'Status', 'Confidence', 'Created', 'Actions'].map((h) => (
                  <th
                    key={h}
                    className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((order) => (
                <tr key={order.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900 max-w-xs truncate">
                    {order.filename}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={order.status} />
                  </td>
                  <td className="px-6 py-4">
                    <ConfidenceScore score={order.confidence_score} />
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(order.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => navigate(`/orders/${order.id}`)}
                      className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
                    >
                      Review →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
