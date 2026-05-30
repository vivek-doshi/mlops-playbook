import { useState, useEffect, useCallback } from 'react'
import { NeuralCanvas } from './components/NeuralCanvas'
import { Header } from './components/Header'
import { Sidebar } from './components/Sidebar'
import { CodeViewer } from './components/CodeViewer'
import { MLOpsIcon } from './components/MLOpsIcon'
import type { FileEntry, FileIndex, Theme } from './types'

export default function App() {
  const [index, setIndex] = useState<FileIndex | null>(null)
  const [selectedFile, setSelectedFile] = useState<FileEntry | null>(null)
  const [theme, setTheme] = useState<Theme>('dusk')
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)

  // Restore theme from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('mlops-theme') as Theme | null
    if (saved === 'dawn' || saved === 'dusk') setTheme(saved)
  }, [])

  // Apply theme to <html> attribute and save
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    document.body.setAttribute('data-theme', theme)
    localStorage.setItem('mlops-theme', theme)
  }, [theme])

  // Keyboard shortcut: Ctrl+K focuses sidebar search
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        document.getElementById('sidebar-search')?.focus()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  // Load index.json
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}index.json`)
      .then(r => r.json())
      .then((data: FileIndex) => {
        setIndex(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const toggleTheme = useCallback(() => {
    setTheme(t => (t === 'dawn' ? 'dusk' : 'dawn'))
  }, [])

  const pickRandom = useCallback(() => {
    if (!index) return
    const pool = searchQuery
      ? index.files.filter(f =>
          f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          f.path.toLowerCase().includes(searchQuery.toLowerCase())
        )
      : index.files
    if (pool.length === 0) return
    const pick = pool[Math.floor(Math.random() * pool.length)]
    setSelectedFile(pick)
    setSearchQuery('')
  }, [index, searchQuery])

  if (loading) {
    return (
      <div data-theme={theme} style={{ height: '100vh', background: 'var(--bg-base)', position: 'relative' }}>
        <NeuralCanvas theme={theme} />
        <div className="loading-screen" style={{ background: 'transparent' }}>
          <div className="loading-content">
            <div className="loading-logo">
              <MLOpsIcon size={44} className="loading-icon-svg" />
              <h1>MLOps Playbook</h1>
            </div>
            <div className="loading-bar">
              <div className="loading-fill" />
            </div>
            <p className="loading-text">Indexing templates…</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div data-theme={theme} className="app">
      <NeuralCanvas theme={theme} />
      <div className="app-layout">
        <Header
          theme={theme}
          onToggleTheme={toggleTheme}
          onPickRandom={pickRandom}
          index={index}
        />
        <div className="app-body">
          <Sidebar
            index={index}
            selectedFile={selectedFile}
            onSelectFile={setSelectedFile}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
          />
          <CodeViewer file={selectedFile} theme={theme} />
        </div>
      </div>
    </div>
  )
}
