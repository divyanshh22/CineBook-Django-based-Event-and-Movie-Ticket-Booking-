import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'

export default function Layout() {
  return (
    <>
      <Navbar />
      <main className="page">
        <Outlet />
      </main>
      <footer
        style={{
          borderTop: '1px solid var(--border)',
          padding: '2rem 0',
          textAlign: 'center',
          color: 'var(--text-faint)',
          fontSize: '0.85rem',
        }}
      >
        CineBook © {new Date().getFullYear()} — Your movies, events &amp; cinemas, one place. Built by Divyansh.
      </footer>
    </>
  )
}
