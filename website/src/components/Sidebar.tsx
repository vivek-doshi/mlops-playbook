import { useState, useMemo, useCallback } from 'react'
import type { FileEntry, FileIndex } from '../types'
import './Sidebar.css'

const CATEGORY_META: Record<string, { name: string; icon: string; color: string }> = {
  ci:                  { name: 'CI Pipelines',        icon: '⚡', color: '#f59e0b' },
  cd:                  { name: 'CD & Deploy',          icon: '🚀', color: '#06b6d4' },
  training:            { name: 'Model Training',       icon: '🧠', color: '#8b5cf6' },
  serving:             { name: 'Model Serving',        icon: '🔮', color: '#10b981' },
  monitoring:          { name: 'Monitoring',           icon: '📊', color: '#ef4444' },
  batch:               { name: 'Batch Inference',      icon: '⚙️', color: '#f97316' },
  pipelines:           { name: 'ML Pipelines',         icon: '🔄', color: '#0ea5e9' },
  fairness:            { name: 'Fairness & XAI',       icon: '⚖️', color: '#ec4899' },
  terraform:           { name: 'Infrastructure',       icon: '🏗️', color: '#7c3aed' },
  finops:              { name: 'FinOps',               icon: '💰', color: '#84cc16' },
  mlflow:              { name: 'MLflow',               icon: '🧪', color: '#0ea5e9' },
  dvc:                 { name: 'Data Versioning',      icon: '📦', color: '#d946ef' },
  'feature-store':     { name: 'Feature Store',        icon: '🗃️', color: '#14b8a6' },
  policy:              { name: 'Policy & Governance',  icon: '🛡️', color: '#64748b' },
  docs:                { name: 'Documentation',        icon: '📚', color: '#78716c' },
  llmops:              { name: 'LLMOps',               icon: '🤖', color: '#a855f7' },
  model_optimization:  { name: 'Model Optimization',   icon: '🔧', color: '#f97316' },
  multi_cloud_serving: { name: 'Multi-Cloud Serving',  icon: '☁️', color: '#0ea5e9' },
  online_learning:     { name: 'Online Learning',      icon: '🔁', color: '#06b6d4' },
  portal:              { name: 'Self-Service Portal',  icon: '🖥️', color: '#f59e0b' },
  federated_learning:  { name: 'Federated Learning',   icon: '🌐', color: '#8b5cf6' },
  scripts:             { name: 'Scripts',              icon: '📜', color: '#94a3b8' },
  '.devcontainer':     { name: 'Dev Container',        icon: '🐳', color: '#2496ed' },
  root:                { name: 'Root Files',           icon: '📁', color: '#64748b' },
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

// ── Tree data structure ───────────────────────────────────────────────────

type FolderNode = {
  name:     string
  fullPath: string
  children: Map<string, FolderNode>
  files:    FileEntry[]
}

function buildTree(files: FileEntry[], category: string): FolderNode {
  const root: FolderNode = { name: category, fullPath: category, children: new Map(), files: [] }
  for (const file of files) {
    // 'root' category files have no path prefix (e.g. 'README.md')
    const parts = category === 'root' ? [file.name] : file.path.split('/').slice(1)
    let node = root
    for (let i = 0; i < parts.length - 1; i++) {
      const seg = parts[i]
      if (!node.children.has(seg)) {
        const fp = category === 'root' ? seg : [category, ...parts.slice(0, i + 1)].join('/')
        node.children.set(seg, { name: seg, fullPath: fp, children: new Map(), files: [] })
      }
      node = node.children.get(seg)!
    }
    node.files.push(file)
  }
  return root
}

function countFiles(node: FolderNode): number {
  let n = node.files.length
  for (const child of node.children.values()) n += countFiles(child)
  return n
}

function collectFolderPaths(node: FolderNode, out: string[] = []): string[] {
  for (const child of node.children.values()) {
    out.push(child.fullPath)
    collectFolderPaths(child, out)
  }
  return out
}

// ── Props & component ─────────────────────────────────────────────────────

interface Props {
  index: FileIndex | null
  selectedFile: FileEntry | null
  onSelectFile: (f: FileEntry) => void
  searchQuery: string
  onSearchChange: (q: string) => void
  isMobileLayout: boolean
  isOpen: boolean
  onClose: () => void
}

export function Sidebar({ index, selectedFile, onSelectFile, searchQuery, onSearchChange, isMobileLayout, isOpen, onClose }: Props) {
  const [openCategories, setOpenCategories] = useState<Set<string>>(new Set())
  const [openFolders,    setOpenFolders]    = useState<Set<string>>(new Set())

  const toggleCat = useCallback((cat: string) => {
    setOpenCategories(prev => {
      const next = new Set(prev)
      next.has(cat) ? next.delete(cat) : next.add(cat)
      return next
    })
  }, [])

  const toggleFolder = useCallback((fp: string) => {
    setOpenFolders(prev => {
      const next = new Set(prev)
      next.has(fp) ? next.delete(fp) : next.add(fp)
      return next
    })
  }, [])

  // Build per-category folder tree
  const grouped = useMemo(() => {
    if (!index) return new Map<string, FolderNode>()
    const byCategory = new Map<string, FileEntry[]>()
    for (const file of index.files) {
      if (!byCategory.has(file.category)) byCategory.set(file.category, [])
      byCategory.get(file.category)!.push(file)
    }
    const map = new Map<string, FolderNode>()
    for (const [cat, files] of byCategory) map.set(cat, buildTree(files, cat))
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

  // Category order — dot-dirs first, then A→Z, root files last
  const catOrder = [
    '.devcontainer',
    'batch', 'cd', 'ci', 'docs', 'dvc', 'fairness', 'feature-store',
    'federated_learning', 'finops', 'llmops', 'mlflow', 'model_optimization',
    'monitoring', 'multi_cloud_serving', 'online_learning', 'pipelines',
    'policy', 'portal', 'scripts', 'serving', 'terraform', 'training',
    'root',
  ]
  const orderedCats = catOrder.filter(c => grouped.has(c))
  const remaining   = [...grouped.keys()].filter(c => !catOrder.includes(c)).sort()
  const allCats     = [...orderedCats, ...remaining]

  const collapseAll = useCallback(() => {
    setOpenCategories(new Set())
    setOpenFolders(new Set())
  }, [])

  const expandAll = useCallback(() => {
    setOpenCategories(new Set(allCats))
    const allFolderPaths: string[] = []
    for (const cat of allCats) {
      const tree = grouped.get(cat)
      if (tree) collectFolderPaths(tree, allFolderPaths)
    }
    setOpenFolders(new Set(allFolderPaths))
  }, [allCats, grouped])

  // ── Recursive tree renderer ─────────────────────────────────────────────
  const renderNode = useCallback((node: FolderNode, depth: number): React.ReactNode => {
    const baseIndent = 12
    const step       = 14
    const folderLeft = baseIndent + depth * step
    const fileLeft   = baseIndent + (depth + 1) * step + 6

    const sortedFolders = [...node.children.entries()].sort(([a], [b]) => a.localeCompare(b))
    const sortedFiles   = [...node.files].sort((a, b) => a.name.localeCompare(b.name))

    return (
      <>
        {sortedFolders.map(([, child]) => {
          const isOpen = openFolders.has(child.fullPath)
          const fCount = countFiles(child)
          return (
            <div key={child.fullPath} className={`folder-group${isOpen ? ' open' : ''}`}>
              <div
                className="folder-row"
                style={{ paddingLeft: folderLeft }}
                onClick={() => toggleFolder(child.fullPath)}
              >
                <span className="folder-chevron">▶</span>
                <span className="folder-icon">{isOpen ? '📂' : '📁'}</span>
                <span className="folder-name">{child.name}</span>
                <span className="folder-count">{fCount}</span>
              </div>
              {isOpen && renderNode(child, depth + 1)}
            </div>
          )
        })}
        {sortedFiles.map((file, fi) => (
          <div
            key={file.id}
            className={`file-item${selectedFile?.id === file.id ? ' active' : ''}`}
            onClick={() => onSelectFile(file)}
            style={{ paddingLeft: fileLeft, animationDelay: `${fi * 0.03}s` }}
          >
            <span className="file-icon">{LANG_ICONS[file.language] ?? '📄'}</span>
            <span className="file-name" title={file.path}>{file.name}</span>
            <span className={langBadgeClass(file.language)}>{file.language}</span>
          </div>
        ))}
      </>
    )
  }, [openFolders, toggleFolder, selectedFile, onSelectFile])

  // ── Render ──────────────────────────────────────────────────────────────
  return (
    <aside className={`sidebar${isMobileLayout ? ' mobile-sidebar' : ''}${isOpen ? ' mobile-open' : ''}`}>
      {/* Search */}
      <div className="sidebar-search-wrap">
        {isMobileLayout && (
          <div className="sidebar-mobile-bar">
            <span className="sidebar-mobile-title">Browse templates</span>
            <button className="sidebar-mobile-close" onClick={onClose} aria-label="Close template browser">✕</button>
          </div>
        )}
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

      {/* Controls */}
      <div className="sidebar-controls">
        <button className="sidebar-ctrl-btn" onClick={collapseAll} title="Collapse all">⊟ Collapse</button>
        <button className="sidebar-ctrl-btn" onClick={expandAll}   title="Expand all">⊞ Expand</button>
        <a
          className="sidebar-devops-link"
          href="https://vivek-doshi.github.io/devops-playbook/"
          target="_blank"
          rel="noopener noreferrer"
        >
          🔗 DevOps ↗
        </a>
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
                  className={`file-item${selectedFile?.id === file.id ? ' active' : ''}`}
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
            const meta   = CATEGORY_META[cat] ?? { name: cat, icon: '📁', color: '#64748b' }
            const tree   = grouped.get(cat)!
            const isOpen = openCategories.has(cat)
            return (
              <div
                key={cat}
                className={`category-group${isOpen ? ' open' : ''}`}
                style={{ animationDelay: `${ci * 0.04}s` }}
              >
                <div className="category-header" onClick={() => toggleCat(cat)}>
                  <span className="category-icon" style={{ color: meta.color }}>{meta.icon}</span>
                  <span className="category-name"  style={{ color: meta.color }}>{meta.name}</span>
                  <span className="category-count">{countFiles(tree)}</span>
                  <span className="category-chevron">▶</span>
                </div>
                {isOpen && (
                  <div className="file-list">
                    {renderNode(tree, 0)}
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
