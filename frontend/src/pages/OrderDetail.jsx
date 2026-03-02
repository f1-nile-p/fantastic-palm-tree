import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  getOrder,
  approveOrder,
  rejectOrder,
  updatePOLine,
  exportXML,
} from '../api'
import StatusBadge from '../components/StatusBadge'
import ConfidenceScore from '../components/ConfidenceScore'

function EditableCell({ value, onSave, type = 'text' }) {
  const [editing, setEditing] = useState(false)
  const [val, setVal] = useState(value ?? '')

  const commit = () => {
    setEditing(false)
    if (val !== (value ?? '')) onSave(type === 'number' ? parseFloat(val) || null : val || null)
  }

  if (editing) {
    return (
      <input
        autoFocus
        type={type}
        value={val}
        onChange={(e) => setVal(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => e.key === 'Enter' && commit()}
        className="w-full border border-indigo-400 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
      />
    )
  }
  return (
    <span
      onClick={() => setEditing(true)}
      title="Click to edit"
      className="cursor-pointer hover:bg-indigo-50 rounded px-1 py-0.5 text-sm text-gray-800"
    >
      {value ?? <span className="text-gray-300">—</span>}
    </span>
  )
}

export default function OrderDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [po, setPo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchPO = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getOrder(id)
      setPo(res.data)
    } catch {
      setError('Failed to load purchase order')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { fetchPO() }, [fetchPO])

  const handleApprove = async () => {
    setActionLoading(true)
    try {
      await approveOrder(id)
      await fetchPO()
    } catch (e) {
      setError(e.response?.data?.detail || 'Approval failed')
    } finally {
      setActionLoading(false)
    }
  }

  const handleReject = async () => {
    setActionLoading(true)
    try {
      await rejectOrder(id)
      await fetchPO()
    } catch (e) {
      setError(e.response?.data?.detail || 'Rejection failed')
    } finally {
      setActionLoading(false)
    }
  }

  const handleLineUpdate = async (lineId, field, value) => {
    try {
      await updatePOLine(id, lineId, { [field]: value })
      await fetchPO()
    } catch (e) {
      setError('Failed to update line')
    }
  }

  const handleDownloadXML = async () => {
    try {
      const blob = await exportXML(id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `po_${id}.xml`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      setError('Failed to download XML')
    }
  }

  if (loading) return <div className="text-center py-16 text-gray-400">Loading…</div>
  if (error && !po) return <div className="text-center py-16 text-red-500">{error}</div>
  if (!po) return null

  const extracted = po.extracted_data || {}
  const isApproved = po.status === 'approved'

  return (
    <div className="space-y-6">
      {/* Back + Title */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/')}
          className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
        >
          ← Back to Queue
        </button>
        <h1 className="text-2xl font-bold text-gray-900 truncate">{po.filename}</h1>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {/* Header card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <p className="text-xs text-gray-500 uppercase font-semibold">Status</p>
          <StatusBadge status={po.status} />
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase font-semibold">Confidence</p>
          <ConfidenceScore score={po.confidence_score} />
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase font-semibold">Vendor</p>
          <p className="text-sm text-gray-800">{extracted.vendor_name || '—'}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase font-semibold">PO Number</p>
          <p className="text-sm text-gray-800">{extracted.po_number || '—'}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase font-semibold">Date</p>
          <p className="text-sm text-gray-800">{extracted.date || '—'}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase font-semibold">Created</p>
          <p className="text-sm text-gray-800">{new Date(po.created_at).toLocaleString()}</p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        {po.status !== 'approved' && po.status !== 'rejected' && (
          <>
            <button
              onClick={handleApprove}
              disabled={actionLoading}
              className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              ✓ Approve
            </button>
            <button
              onClick={handleReject}
              disabled={actionLoading}
              className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
            >
              ✗ Reject
            </button>
          </>
        )}
        {isApproved && (
          <button
            onClick={handleDownloadXML}
            className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
          >
            ↓ Download XML
          </button>
        )}
      </div>

      {/* Lines table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              {['#', 'Description', 'Matched Item', 'Qty', 'UOM', 'Unit Price', 'Total', 'Conf.', 'Notes'].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {(po.lines || []).sort((a, b) => a.line_number - b.line_number).map((line) => (
              <tr key={line.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-gray-500">{line.line_number}</td>
                <td className="px-4 py-3 text-gray-800 max-w-xs">{line.raw_description || '—'}</td>
                <td className="px-4 py-3">
                  <EditableCell
                    value={line.matched_item_code}
                    onSave={(v) => handleLineUpdate(line.id, 'matched_item_code', v)}
                  />
                </td>
                <td className="px-4 py-3">
                  <EditableCell
                    value={line.quantity}
                    type="number"
                    onSave={(v) => handleLineUpdate(line.id, 'quantity', v)}
                  />
                </td>
                <td className="px-4 py-3">
                  <EditableCell
                    value={line.matched_uom_code || line.uom_raw}
                    onSave={(v) => handleLineUpdate(line.id, 'matched_uom_code', v)}
                  />
                </td>
                <td className="px-4 py-3">
                  <EditableCell
                    value={line.unit_price}
                    type="number"
                    onSave={(v) => handleLineUpdate(line.id, 'unit_price', v)}
                  />
                </td>
                <td className="px-4 py-3 text-gray-600">
                  {line.total_price != null ? line.total_price.toFixed(2) : '—'}
                </td>
                <td className="px-4 py-3">
                  <ConfidenceScore score={line.confidence_score} />
                </td>
                <td className="px-4 py-3">
                  <EditableCell
                    value={line.notes}
                    onSave={(v) => handleLineUpdate(line.id, 'notes', v)}
                  />
                </td>
              </tr>
            ))}
            {(!po.lines || po.lines.length === 0) && (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-gray-400">
                  No line items extracted.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
