export const money = (value, digits = 2) => {
  const amount = Number(value || 0)
  return `₹${amount.toLocaleString('en-IN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}`
}

export const number = (value) => Number(value || 0).toLocaleString('en-IN')

export const percent = (part, whole) => {
  if (!whole) return 0
  return (Number(part || 0) / Number(whole)) * 100
}

export const percentLabel = (part, whole) =>
  `${percent(part, whole).toFixed(1)}%`

export const formatDate = (iso) => {
  if (!iso) return '—'
  const date = new Date(`${iso}T00:00:00`)
  if (Number.isNaN(date.getTime())) return iso
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

export const initials = (name) =>
  (name || '?')
    .split(' ')
    .filter(Boolean)
    .slice(0, 1)
    .map((part) => part.charAt(0).toUpperCase())
    .join('') || '?'
