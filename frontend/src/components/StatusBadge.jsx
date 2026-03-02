const STATUS_CONFIG = {
  pending: { label: 'Pending', classes: 'bg-gray-100 text-gray-700 ring-gray-300' },
  under_review: { label: 'Under Review', classes: 'bg-yellow-100 text-yellow-800 ring-yellow-300' },
  approved: { label: 'Approved', classes: 'bg-green-100 text-green-800 ring-green-300' },
  rejected: { label: 'Rejected', classes: 'bg-red-100 text-red-800 ring-red-300' },
}

export default function StatusBadge({ status }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${config.classes}`}
    >
      {config.label}
    </span>
  )
}
