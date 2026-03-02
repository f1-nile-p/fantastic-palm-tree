import { useEffect, useState, useCallback } from 'react'
import {
  getItems,
  getUOMs,
  uploadItemsCSV,
  uploadUOMsCSV,
  deleteItem,
  deleteUOM,
} from '../api'
import UploadZone from '../components/UploadZone'
import ConfirmModal from '../components/ConfirmModal'
import { TrashIcon } from '@heroicons/react/24/outline'

const ITEMS_TEMPLATE_HEADERS = 'code,description,unit_of_measure,unit_price,category'
const UOMS_TEMPLATE_HEADERS = 'code,description,aliases'

function downloadTemplate(headers, filename) {
  const blob = new Blob([headers + '\n'], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function MasterData() {
  const [tab, setTab] = useState('items')
  const [items, setItems] = useState([])
  const [uoms, setUoms] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploadingItems, setUploadingItems] = useState(false)
  const [uploadingUOMs, setUploadingUOMs] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [confirmState, setConfirmState] = useState(null) // { message, onConfirm }

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [itemsRes, uomsRes] = await Promise.all([getItems({ limit: 200 }), getUOMs({ limit: 200 })])
      setItems(itemsRes.data)
      setUoms(uomsRes.data)
    } catch {
      setError('Failed to load master data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const handleItemsUpload = async (file) => {
    setUploadingItems(true)
    setError(null)
    setSuccess(null)
    try {
      const res = await uploadItemsCSV(file)
      setSuccess(`Uploaded ${res.data.length} item(s) successfully`)
      await fetchData()
    } catch (e) {
      setError(e.response?.data?.detail || 'Items CSV upload failed')
    } finally {
      setUploadingItems(false)
    }
  }

  const handleUOMsUpload = async (file) => {
    setUploadingUOMs(true)
    setError(null)
    setSuccess(null)
    try {
      const res = await uploadUOMsCSV(file)
      setSuccess(`Uploaded ${res.data.length} UOM(s) successfully`)
      await fetchData()
    } catch (e) {
      setError(e.response?.data?.detail || 'UOMs CSV upload failed')
    } finally {
      setUploadingUOMs(false)
    }
  }

  const handleDeleteItem = async (id) => {
    setConfirmState({
      message: 'Delete this item?',
      onConfirm: async () => {
        setConfirmState(null)
        try {
          await deleteItem(id)
          setItems((prev) => prev.filter((i) => i.id !== id))
        } catch {
          setError('Failed to delete item')
        }
      },
    })
  }

  const handleDeleteUOM = async (id) => {
    setConfirmState({
      message: 'Delete this UOM?',
      onConfirm: async () => {
        setConfirmState(null)
        try {
          await deleteUOM(id)
          setUoms((prev) => prev.filter((u) => u.id !== id))
        } catch {
          setError('Failed to delete UOM')
        }
      },
    })
  }

  return (
    <div className="space-y-6">
      {confirmState && (
        <ConfirmModal
          message={confirmState.message}
          onConfirm={confirmState.onConfirm}
          onCancel={() => setConfirmState(null)}
        />
      )}
      <h1 className="text-2xl font-bold text-gray-900">Master Data</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">{error}</div>
      )}
      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 rounded-lg px-4 py-3 text-sm">{success}</div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        {[{ key: 'items', label: 'Items' }, { key: 'uoms', label: 'Units of Measure' }].map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === t.key
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'items' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">{items.length} item(s) loaded</p>
            <button
              onClick={() => downloadTemplate(ITEMS_TEMPLATE_HEADERS, 'items_template.csv')}
              className="text-sm text-indigo-600 hover:underline"
            >
              ↓ Download template CSV
            </button>
          </div>
          <UploadZone
            onFile={handleItemsUpload}
            accept=".csv"
            label="Upload Items CSV"
            loading={uploadingItems}
          />
          {loading ? (
            <div className="text-center py-8 text-gray-400">Loading…</div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    {['Code', 'Description', 'UOM', 'Unit Price', 'Category', ''].map((h) => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {items.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-gray-800">{item.code}</td>
                      <td className="px-4 py-3 text-gray-700">{item.description}</td>
                      <td className="px-4 py-3 text-gray-600">{item.unit_of_measure}</td>
                      <td className="px-4 py-3 text-gray-600">{item.unit_price != null ? `$${item.unit_price.toFixed(2)}` : '—'}</td>
                      <td className="px-4 py-3 text-gray-500">{item.category || '—'}</td>
                      <td className="px-4 py-3">
                        <button onClick={() => handleDeleteItem(item.id)} className="text-red-400 hover:text-red-600">
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {items.length === 0 && (
                    <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">No items yet. Upload a CSV to get started.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === 'uoms' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">{uoms.length} UOM(s) loaded</p>
            <button
              onClick={() => downloadTemplate(UOMS_TEMPLATE_HEADERS, 'uom_template.csv')}
              className="text-sm text-indigo-600 hover:underline"
            >
              ↓ Download template CSV
            </button>
          </div>
          <UploadZone
            onFile={handleUOMsUpload}
            accept=".csv"
            label="Upload UOMs CSV"
            loading={uploadingUOMs}
          />
          {loading ? (
            <div className="text-center py-8 text-gray-400">Loading…</div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    {['Code', 'Description', 'Aliases', ''].map((h) => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {uoms.map((uom) => (
                    <tr key={uom.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-gray-800">{uom.code}</td>
                      <td className="px-4 py-3 text-gray-700">{uom.description}</td>
                      <td className="px-4 py-3 text-gray-500">{(uom.aliases || []).join(', ') || '—'}</td>
                      <td className="px-4 py-3">
                        <button onClick={() => handleDeleteUOM(uom.id)} className="text-red-400 hover:text-red-600">
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {uoms.length === 0 && (
                    <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400">No UOMs yet. Upload a CSV to get started.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
