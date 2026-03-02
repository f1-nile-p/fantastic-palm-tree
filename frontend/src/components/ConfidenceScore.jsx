export default function ConfidenceScore({ score }) {
  if (score == null) return <span className="text-gray-400 text-sm">—</span>

  const pct = Math.round(score * 100)
  let colorClass = 'text-green-700 bg-green-50 ring-green-200'
  if (pct < 60) colorClass = 'text-red-700 bg-red-50 ring-red-200'
  else if (pct < 80) colorClass = 'text-yellow-700 bg-yellow-50 ring-yellow-200'

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${colorClass}`}
    >
      {pct}%
    </span>
  )
}
