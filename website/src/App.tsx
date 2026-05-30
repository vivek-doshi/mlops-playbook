import { useState, useEffect, useCallback } from 'react'
import { NeuralCanvas } from './components/NeuralCanvas'
import { Header } from './components/Header'
import { Sidebar } from './components/Sidebar'
import { CodeViewer } from './components/CodeViewer'
import { MLOpsIcon } from './components/MLOpsIcon'
import type { FileEntry, FileIndex, Theme } from './types'

const FILE_QUERY_PARAM = 'file'
const MOBILE_MEDIA_QUERY = '(max-width: 900px)'

function normalizePath(path: string): string {
  return path.replace(/\\/g, '/').replace(/^\.\//, '').replace(/^\//, '')
}

function hasExtension(path: string): boolean {
  const seg = path.split('/').pop() ?? ''
  return seg.includes('.')
}

function getQueryFilePath(): string | null {
  const url = new URL(window.location.href)
  const value = url.searchParams.get(FILE_QUERY_PARAM)
  if (!value) return null
  return normalizePath(value)
}

function getIsMobileLayout(): boolean {
  return window.matchMedia(MOBILE_MEDIA_QUERY).matches
}

function resolveInternalLinkTarget(currentFilePath: string, href: string): string | null {
  const raw = href.trim()
  if (!raw || raw.startsWith('#')) return null
  if (raw.startsWith('mailto:') || raw.startsWith('tel:') || raw.startsWith('javascript:')) return null

  try {
    const absolute = new URL(raw)
    if (absolute.protocol === 'http:' || absolute.protocol === 'https:') {
      const blobPrefix = '/vivek-doshi/mlops-playbook/blob/main/'
      if (absolute.hostname === 'github.com' && absolute.pathname.includes(blobPrefix)) {
        const idx = absolute.pathname.indexOf(blobPrefix)
        const fromRepoRoot = absolute.pathname.slice(idx + blobPrefix.length)
        return normalizePath(decodeURIComponent(fromRepoRoot))
      }
      return null
    }
    return null
  } catch {
    // Continue as relative URL.
  }

  const withoutFragment = raw.split('#')[0].split('?')[0]
  if (!withoutFragment) return null

  if (withoutFragment.startsWith('/')) {
    return normalizePath(decodeURIComponent(withoutFragment))
  }

  const baseParts = currentFilePath.split('/')
  baseParts.pop()
  const relParts = withoutFragment.split('/')
  for (const part of relParts) {
    if (!part || part === '.') continue
    if (part === '..') {
      if (baseParts.length > 0) baseParts.pop()
      continue
    }
    baseParts.push(part)
  }
  return normalizePath(decodeURIComponent(baseParts.join('/')))
}

function pickExistingFilePath(candidate: string, filesByPath: Map<string, FileEntry>): string | null {
  const normalized = normalizePath(candidate)
  const variants = [normalized]

  if (normalized.endsWith('/')) {
    variants.push(`${normalized}README.md`)
  } else {
    variants.push(`${normalized}/README.md`)
    if (!hasExtension(normalized)) variants.push(`${normalized}.md`)
  }

  for (const variant of variants) {
    if (filesByPath.has(variant)) return variant
  }
  return null
}

function resolveIndexedFilePath(currentFilePath: string, href: string, filesByPath: Map<string, FileEntry>): string | null {
  const raw = href.trim()
  if (!raw || raw.startsWith('#')) return null

  const directMatch = pickExistingFilePath(raw, filesByPath)
  if (directMatch) return directMatch

  const relativeCandidate = resolveInternalLinkTarget(currentFilePath, href)
  if (!relativeCandidate) return null

  return pickExistingFilePath(relativeCandidate, filesByPath)
}

export default function App() {
  const [index, setIndex] = useState<FileIndex | null>(null)
  const [selectedFile, setSelectedFile] = useState<FileEntry | null>(null)
  const [theme, setTheme] = useState<Theme>('dusk')
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [isMobileLayout, setIsMobileLayout] = useState(() => getIsMobileLayout())
  const [isSidebarOpen, setIsSidebarOpen] = useState(() => !getIsMobileLayout())

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
        if (getIsMobileLayout()) setIsSidebarOpen(true)
        document.getElementById('sidebar-search')?.focus()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  useEffect(() => {
    const mediaQuery = window.matchMedia(MOBILE_MEDIA_QUERY)
    const syncLayout = (matches: boolean) => {
      setIsMobileLayout(matches)
      setIsSidebarOpen(prev => (matches ? prev : true))
    }

    syncLayout(mediaQuery.matches)

    const onChange = (event: MediaQueryListEvent) => syncLayout(event.matches)
    mediaQuery.addEventListener('change', onChange)
    return () => mediaQuery.removeEventListener('change', onChange)
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

  const filesByPath = useCallback(() => {
    const map = new Map<string, FileEntry>()
    if (!index) return map
    for (const file of index.files) map.set(normalizePath(file.path), file)
    return map
  }, [index])

  const updateUrlForFile = useCallback((file: FileEntry | null, replace = false) => {
    const url = new URL(window.location.href)
    if (file) {
      url.searchParams.set(FILE_QUERY_PARAM, normalizePath(file.path))
    } else {
      url.searchParams.delete(FILE_QUERY_PARAM)
    }
    const historyState = { filePath: file ? normalizePath(file.path) : null }
    const nextUrl = `${url.pathname}${url.search}${url.hash}`
    if (replace) {
      window.history.replaceState(historyState, '', nextUrl)
    } else {
      window.history.pushState(historyState, '', nextUrl)
    }
  }, [])

  const selectFile = useCallback((file: FileEntry | null, pushHistory = true, replaceHistory = false) => {
    setSelectedFile(file)
    if (file && isMobileLayout) setIsSidebarOpen(false)
    if (!pushHistory) return
    const currentPath = selectedFile ? normalizePath(selectedFile.path) : null
    const nextPath = file ? normalizePath(file.path) : null
    if (currentPath === nextPath) return
    updateUrlForFile(file, replaceHistory)
  }, [isMobileLayout, selectedFile, updateUrlForFile])

  useEffect(() => {
    if (!index) return
    const map = filesByPath()
    const fromUrl = getQueryFilePath()
    if (fromUrl && map.has(fromUrl)) {
      setSelectedFile(map.get(fromUrl) ?? null)
      if (isMobileLayout) setIsSidebarOpen(false)
      return
    }

    // Keep URL and app state in sync when query points to an unknown file.
    updateUrlForFile(selectedFile, true)
  }, [index, filesByPath, isMobileLayout, selectedFile, updateUrlForFile])

  useEffect(() => {
    const onPopState = () => {
      if (!index) return
      const map = filesByPath()
      const fromUrl = getQueryFilePath()
      if (!fromUrl) {
        setSelectedFile(null)
        return
      }
      setSelectedFile(map.get(fromUrl) ?? null)
    }

    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [index, filesByPath])

  const openLinkTarget = useCallback((currentFilePath: string, href: string): boolean => {
    if (!index) return false
    const map = filesByPath()
    const matchedPath = resolveIndexedFilePath(currentFilePath, href, map)
    if (!matchedPath) return false
    const next = map.get(matchedPath)
    if (!next) return false
    selectFile(next, true, false)
    return true
  }, [index, filesByPath, selectFile])

  const toggleTheme = useCallback(() => {
    setTheme(t => (t === 'dawn' ? 'dusk' : 'dawn'))
  }, [])

  const openSidebar = useCallback(() => {
    setIsSidebarOpen(true)
  }, [])

  const toggleSidebar = useCallback(() => {
    setIsSidebarOpen(prev => !prev)
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
    selectFile(pick)
    setSearchQuery('')
  }, [index, searchQuery, selectFile])

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
          isMobileLayout={isMobileLayout}
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={toggleSidebar}
        />
        <div className={`app-body${isMobileLayout ? ' mobile-layout' : ''}`}>
          <Sidebar
            index={index}
            selectedFile={selectedFile}
            onSelectFile={selectFile}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            isMobileLayout={isMobileLayout}
            isOpen={isSidebarOpen}
            onClose={setIsSidebarOpen.bind(null, false)}
          />
          <CodeViewer
            file={selectedFile}
            theme={theme}
            onOpenInternalLink={openLinkTarget}
            isMobileLayout={isMobileLayout}
            onOpenSidebar={openSidebar}
          />
        </div>
      </div>
    </div>
  )
}
