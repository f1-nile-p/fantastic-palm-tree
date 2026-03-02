import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// Orders
export const getOrders = (params = {}) => api.get('/orders', { params })
export const getOrder = (id) => api.get(`/orders/${id}`)
export const uploadPO = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/orders/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const updateOrder = (id, data) => api.patch(`/orders/${id}`, data)
export const updatePOLine = (poId, lineId, data) =>
  api.patch(`/orders/${poId}/lines/${lineId}`, data)
export const approveOrder = (id) => api.post(`/orders/${id}/approve`)
export const rejectOrder = (id) => api.post(`/orders/${id}/reject`)

// Master data
export const getItems = (params = {}) => api.get('/master-data/items', { params })
export const createItem = (data) => api.post('/master-data/items', data)
export const deleteItem = (id) => api.delete(`/master-data/items/${id}`)
export const uploadItemsCSV = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/master-data/items/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const getUOMs = (params = {}) => api.get('/master-data/uoms', { params })
export const createUOM = (data) => api.post('/master-data/uoms', data)
export const deleteUOM = (id) => api.delete(`/master-data/uoms/${id}`)
export const uploadUOMsCSV = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/master-data/uoms/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// Export
export const exportXML = async (poId) => {
  const res = await api.get(`/export/orders/${poId}/xml`, { responseType: 'blob' })
  return res.data
}

export default api
