import type { FileIndex, Theme } from '../types'
import './Header.css'

interface Props {
  theme: Theme
  onToggleTheme: () => void
  onPickRandom: () => void
  index: FileIndex | null
}

export function Header({ theme, onToggleTheme, onPickRandom, index }: Props) {
  const categories = index
    ? [...new Set(index.files.map(f => f.category))].length
    : 0

  const workflows = index
    ? index.files.filter(f => f.category === 'ci').length
    : 0

  return (
    <header className="header">
      <a className="header-logo" href="#" aria-label="MLOps Playbook home">
        <div className="logo-icon">⚗️</div>
        <div className="logo-text">
          <div className="logo-title">MLOps Playbook</div>
          <div className="logo-sub">Template Lab</div>
        </div>
      </a>

      <div className="header-stats">
        <div className="stat-pill">
          <span className="stat-icon">📄</span>
          <strong>{index?.totalFiles ?? '…'}</strong> Templates
        </div>
        <div className="stat-pill">
          <span className="stat-icon">🗂️</span>
          <strong>{categories || '…'}</strong> Categories
        </div>
        <div className="stat-pill">
          <span className="stat-icon">⚡</span>
          <strong>{workflows || '…'}</strong> Workflows
        </div>
        <div className="pipeline-status">
          <span className="pulse-dot" />
          Live Repo
        </div>
      </div>

      <div className="header-spacer" />

      <div className="header-actions">
        <button
          className="btn-random"
          onClick={onPickRandom}
          title="Open a random template (Shift+R)"
        >
          🎲 Random
        </button>

        <span className="theme-label">
          {theme === 'dusk' ? 'Synthetic Midnight' : 'Neural Daybreak'}
        </span>

        <button
          className="btn-theme"
          onClick={onToggleTheme}
          aria-label={`Switch to ${theme === 'dusk' ? 'light' : 'dark'} theme`}
          title={`Switch to ${theme === 'dusk' ? 'Neural Daybreak (light)' : 'Synthetic Midnight (dark)'}`}
        >
          <span className="theme-icons">
            <span>🌙</span>
            <span>☀️</span>
          </span>
        </button>

        <a
          className="btn-github"
          href="https://github.com/vivek-doshi/mlops-playbook"
          target="_blank"
          rel="noopener noreferrer"
          title="View source on GitHub"
        >
          ⎇
        </a>
      </div>
    </header>
  )
}
