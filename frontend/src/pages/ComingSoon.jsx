export default function ComingSoon({ title, description }) {
  return (
    <div className="container">
      <h2>{title}</h2>
      <div className="empty-state">
        <span className="icon">🚧</span>
        <h3>Coming in a later phase</h3>
        <p>{description || 'This section is being built. Check back soon!'}</p>
      </div>
    </div>
  )
}
