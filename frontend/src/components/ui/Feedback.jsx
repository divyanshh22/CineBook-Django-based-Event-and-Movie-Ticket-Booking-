export function Spinner({ size = '' }) {
  return <span className={`spinner ${size}`} aria-label="Loading" />
}

export function LoadingScreen({ label = 'Loading...' }) {
  return (
    <div className="loading-screen">
      <Spinner size="spinner-lg" />
      <span>{label}</span>
    </div>
  )
}

export function EmptyState({ icon = '🎬', title = 'Nothing here yet', description }) {
  return (
    <div className="empty-state">
      <span className="icon">{icon}</span>
      <h3>{title}</h3>
      {description && <p>{description}</p>}
    </div>
  )
}

export function ErrorBanner({ message }) {
  if (!message) return null
  return (
    <div role="alert" className="form-error">
      {message}
    </div>
  )
}

export function SuccessBanner({ message }) {
  if (!message) return null
  return (
    <div role="status" className="form-success">
      {message}
    </div>
  )
}

export function Badge({ children, variant = '' }) {
  return <span className={`badge ${variant ? `badge-${variant}` : ''}`}>{children}</span>
}
