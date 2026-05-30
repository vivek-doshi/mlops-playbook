import { useState, useMemo } from 'react'
import type { FileEntry, FileIndex } from '../types'
import './Sidebar.css'

const CATEGORY_META: Record<string, { name: string; icon: string; color: string }> = {
  ci:            { name: 'CI Pipelines',       icon: '⚡', color: '#f59e0b' },
  cd:            { name: 'CD & Deploy',         icon: '🚀', color: '#06b6d4' },
  training:      { name: 'Model Training',      icon: '🧠', color: '#8b5cf6' },
  serving:       { name: 'Model Serving',       icon: '🔮', color: '#10b981' },
  monitoring:    { name: 'Monitoring',          icon: '📊', color: '#ef4444' },
  batch:         { name: 'Batch Inference',     icon: '⚙️', color: '#f97316' },
  pipelines:     { name: 'ML Pipelines',        icon: '🔄', color: '#0ea5e9' },
  fairness:      { name: 'Fairness & XAI',      icon: '⚖️', color: '#ec4899' },
  terraform:     { name: 'Infrastructure',      icon: '🏗️', color: '#7c3aed' },
  finops:        { name: 'FinOps',              icon: '💰', color: '#84cc16' },
  mlflow:        { name: 'MLflow',              icon: '🧪', color: '#0ea5e9' },
  dvc:           { name: 'Data Versioning',     icon: '📦', color: '#d946ef' },
  'feature-store': { name: 'Feature Store',    icon: '🗃️', color: '#14b8a6' },
  policy:        { name: 'Policy & Governance', icon: '🛡️', color: '#64748b' },
  docs:          { name: 'Documentation',       icon: '📚', color: '#78716c' },
}

const LANG_ICONS: Record<string, string> = {
  yaml: '📋', python: '🐍', hcl: '🏗️', terraform: '🏗️', json: '{}',
  bash: '⌨️', sh: '⌨️', markdown: '📝', dockerfile: '🐳',
}

function langBadgeClass(lang: string) {
  const map: Record<string, string> = {
    yaml: 'lang-yaml', python: 'lang-python', hcl: 'lang-hcl',
    terraform: 'lang-terraform', json: 'lang-json', bash: 'lang-bash',
    sh: 'lang-sh', markdown: 'lang-markdown', dockerfile: 'lang-dockerfile',
  }
  return `file-lang-badge ${map[lang] ?? ''}`
}

interface Props {
  index: FileIndex | null
  selectedFile: FileEntry | null
  onSelectFile: (f: FileEntry) => void
  searchQuery: string
  onSearchChange: (q: string) => void
}

export function Sidebar({ index, selectedFile, onSelectFile, searchQuery, onSearchChange }: Props) {
  const [openCategories, setOpenCategories] = useState<Set<string>>(new Set(['ci', 'training', 'serving']))

  const toggle = (cat: string) => {
    setOpenCategories(prev => {
      const next = new Set(prev)
      if (next.has(cat)) next.delete(cat)
      else next.add(cat)
      return next
    })
  }

  // Group files by category and sub-path
  const grouped = useMemo(() => {
    if (!index) return new Map<string, Map<string, FileEntry[]>>()
    const map = new Map<string, Map<string, FileEntry[]>>()
    for (const file of index.files) {
      const cat = file.category
      if (!map.has(cat)) map.set(cat, new Map())
      const sub = file.path.split('/').slice(1, -1).join('/') || '.'
      const catMap = map.get(cat)!
      if (!catMap.has(sub)) catMap.set(sub, [])
      catMap.get(sub)!.push(file)
    }
    return map
  }, [index])

  const isSearching = searchQuery.trim().length > 0

  const searchResults = useMemo(() => {
    if (!index || !isSearching) return []
    const q = searchQuery.toLowerCase()
    return index.files.filter(
      f =>
        f.name.toLowerCase().includes(q) ||
        f.path.toLowerCase().includes(q) ||
        (f.tags ?? []).some(t => t.toLowerCase().includes(q)) ||
        f.language.toLowerCase().includes(q)
    )
  }, [index, searchQuery, isSearching])

  // Category order
  const catOrder = ['ci', 'cd', 'training', 'serving', 'monitoring', 'batch', 'pipelines',
    'fairness', 'terraform', 'finops', 'mlflow', 'dvc', 'feature-store', 'policy', 'docs']
  const orderedCats = catOrder.filter(c => grouped.has(c))
  const remaining   = [...grouped.keys()].filter(c => !catOrder.includes(c))
  const allCats     = [...orderedCats, ...remaining]

  return (
    <aside className="sidebar">
      {/* Search */}
      <div className="sidebar-search-wrap">
        <div className="search-input-row">
          <span className="search-icon">🔍</span>
          <input
            id="sidebar-search"
            type="text"
            placeholder="Search templates…"
            value={searchQuery}
            onChange={e => onSearchChange(e.target.value)}
            autoComplete="off"
            spellCheck={false}
          />
          {searchQuery && (
            <button className="search-clear" onClick={() => onSearchChange('')} aria-label="Clear search">✕</button>
          )}
        </div>
        <div className="search-shortcut"><kbd>Ctrl</kbd> + <kbd>K</kbd></div>
      </div>

      {/* Tree */}
      <div className="sidebar-tree">
        {isSearching ? (
          <>
            <div className="search-results-label">
              <strong>{searchResults.length}</strong> results for "{searchQuery}"
            </div>
            {searchResults.length === 0 ? (
              <div className="no-results">
                <span className="no-results-icon">🔭</span>
                No templates matched.
              </div>
            ) : (
              searchResults.map((file, i) => (
                <div
                  key={file.id}
                  className={`file-item ${selectedFile?.id === file.id ? 'active' : ''}`}
                  onClick={() => { onSelectFile(file); onSearchChange('') }}
                  style={{ paddingLeft: 14, animationDelay: `${i * 0.03}s` }}
                >
                  <span className="file-icon">{LANG_ICONS[file.language] ?? '📄'}</span>
                  <span className="file-name" title={file.path}>{file.name}</span>
                  <span className={langBadgeClass(file.language)}>{file.language}</span>
                </div>
              ))
            )}
          </>
        ) : (
          allCats.map((cat, ci) => {
            const meta       = CATEGORY_META[cat] ?? { name: cat, icon: '📁', color: '#64748b' }
            const subMap     = grouped.get(cat)!
            const totalFiles = [...subMap.values()].reduce((s, a) => s + a.length, 0)
            const isOpen     = openCategories.has(cat)

            return (
              <div
                key={cat}
                className={`category-group ${isOpen ? 'open' : ''}`}
                style={{ animationDelay: `${ci * 0.04}s` }}
              >
                <div className="category-header" onClick={() => toggle(cat)}>
                  <span className="category-icon" style={{ color: meta.color }}>{meta.icon}</span>
                  <span className="category-name" style={{ color: meta.color }}>{meta.name}</span>
                  <span className="category-count">{totalFiles}</span>
                  <span className="category-chevron">▶</span>
                </div>

                {isOpen && (
                  <div className="file-list">
                    {[...subMap.entries()].map(([sub, files]) => (
                      <div key={sub}>
                        {sub !== '.' && (
                          <div className="subdir-label">{sub}</div>
                        )}
                        {files.map((file, fi) => (
                          <div
                            key={file.id}
                            className={`file-item ${selectedFile?.id === file.id ? 'active' : ''}`}
                            onClick={() => onSelectFile(file)}
                            style={{ animationDelay: `${fi * 0.04}s` }}
                          >
                            <span className="file-icon">{LANG_ICONS[file.language] ?? '📄'}</span>
                            <span className="file-name" title={file.path}>{file.name}</span>
                            <span className={langBadgeClass(file.language)}>{file.language}</span>
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>

      {index && (
        <div className="sidebar-footer">
          {new Date(index.generated).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
        </div>
      )}
    </aside>
  )
}
