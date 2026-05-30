import { useEffect, useMemo, useRef, useState, type MouseEvent } from 'react'
import Prism from 'prismjs'
import 'prismjs/components/prism-yaml'
import 'prismjs/components/prism-python'
import 'prismjs/components/prism-bash'
import 'prismjs/components/prism-json'
import 'prismjs/components/prism-hcl'
import 'prismjs/components/prism-markdown'
import 'prismjs/components/prism-docker'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import type { FileEntry, Theme } from '../types'
import './CodeViewer.css'

const LANG_MAP: Record<string, string> = {
  yaml: 'yaml', python: 'python', bash: 'bash', sh: 'bash',
  json: 'json', hcl: 'hcl', terraform: 'hcl',
  markdown: 'markdown', dockerfile: 'docker',
}

function formatBytes(b: number): string {
  if (b < 1024) return `${b} B`
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`
  return `${(b / (1024 * 1024)).toFixed(1)} MB`
}

interface Props {
  file: FileEntry | null
  theme: Theme
  onOpenInternalLink: (currentFilePath: string, href: string) => boolean
}

// Configure marked once
marked.setOptions({ gfm: true, breaks: false })

export function CodeViewer({ file, theme: _theme, onOpenInternalLink }: Props) {
  const preRef  = useRef<HTMLPreElement>(null)
  const [copied,  setCopied]  = useState(false)
  const [viewKey, setViewKey] = useState(0)
  const [rawView, setRawView] = useState(false)

  const isMarkdown = file?.language === 'markdown'

  // Parsed & sanitized HTML — only computed for markdown files
  const renderedHtml = useMemo(() => {
    if (!file || !isMarkdown) return ''
    const html = marked.parse(file.content) as string
    return DOMPurify.sanitize(html, { USE_PROFILES: { html: true } })
  }, [file, isMarkdown])

  useEffect(() => {
    // Only highlight with Prism when showing raw/code view
    if (preRef.current && (!isMarkdown || rawView)) {
      Prism.highlightElement(preRef.current.querySelector('code')!)
    }
    setViewKey(k => k + 1)
    setCopied(false)
    // Reset to rendered view when switching to a new markdown file
    if (isMarkdown) setRawView(false)
  }, [file]) // eslint-disable-line react-hooks/exhaustive-deps

  const copyToClipboard = async () => {
    if (!file) return
    try {
      await navigator.clipboard.writeText(file.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // fallback for older browsers
      const ta = document.createElement('textarea')
      ta.value = file.content
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const onMarkdownClick = (event: MouseEvent<HTMLDivElement>) => {
    if (!file || !isMarkdown) return
    const target = event.target as HTMLElement | null
    const anchor = target?.closest('a') as HTMLAnchorElement | null
    if (!anchor) return

    const href = anchor.getAttribute('href')
    if (!href) return

    const handled = onOpenInternalLink(file.path, href)
    if (handled) event.preventDefault()
  }

  if (!file) {
    return (
      <main className="code-viewer-panel">
        <div className="cv-empty">
          <div className="cv-empty-icon">⚗️</div>
          <h3>Select a Template</h3>
          <p>
            Browse the sidebar to explore production-ready MLOps templates — CI/CD pipelines,
            training configs, serving stacks, monitoring hooks, and more.
          </p>
          <div className="terminal-demo">
            <div className="terminal-header">
              <div className="terminal-dot td1" />
              <div className="terminal-dot td2" />
              <div className="terminal-dot td3" />
            </div>
            <span className="terminal-line">$ mlops-playbook explore</span>
            <span className="terminal-line">  Scanning 156 templates across 14 categories…</span>
            <span className="terminal-line">  ✓ Index loaded successfully</span>
            <span className="terminal-line">$ # Click any template in the sidebar ←</span>
            <span className="terminal-line">  or press <kbd>Ctrl+K</kbd> to search</span>
            <span className="terminal-line">  🎲 Random template: try the header button!</span>
          </div>
        </div>
      </main>
    )
  }

  const prismLang = LANG_MAP[file.language] ?? 'markup'
  const segments  = file.path.split('/')
  const lineCount = file.content.split('\n').length

  return (
    <main className="code-viewer-panel">
      {/* Toolbar */}
      <div className="cv-toolbar">
        <div className="cv-breadcrumb" key={viewKey}>
          {segments.map((seg, i) => (
            <span key={i}>
              {i > 0 && <span className="cv-breadcrumb-sep"> / </span>}
              <span className={`cv-breadcrumb-seg ${i === segments.length - 1 ? 'last' : ''}`}>
                {seg}
              </span>
            </span>
          ))}
        </div>

        <div className="cv-meta">
          <span className="cv-lines-badge">{lineCount} lines</span>
          <span className="cv-size-badge">{formatBytes(file.size)}</span>
          <span className="cv-lang-chip">{file.language}</span>
        </div>

        {isMarkdown && (
          <button
            className={`cv-btn cv-toggle-btn ${rawView ? 'active' : ''}`}
            onClick={() => setRawView(v => !v)}
            title={rawView ? 'Show rendered preview' : 'Show raw source'}
          >
            {rawView ? '👁 Preview' : '⟨/⟩ Raw'}
          </button>
        )}

        <button
          className={`cv-btn ${copied ? 'copied' : ''}`}
          onClick={copyToClipboard}
          title="Copy to clipboard"
        >
          {copied ? '✓ Copied!' : '⎘ Copy'}
        </button>

        <a
          className="cv-btn"
          href={`https://github.com/vivek-doshi/mlops-playbook/blob/main/${file.path}`}
          target="_blank"
          rel="noopener noreferrer"
          title="View on GitHub"
        >
          ⎇ GitHub
        </a>
      </div>

      {/* Markdown preview */}
      {isMarkdown && !rawView ? (
        <div className="cv-scroll cv-md-scroll" key={viewKey}>
          <div
            className="cv-markdown"
            onClick={onMarkdownClick}
            dangerouslySetInnerHTML={{ __html: renderedHtml }}
          />
        </div>
      ) : (
        /* Code / raw view */
        <div className="cv-scroll" key={viewKey}>
          <pre ref={preRef} className="cv-pre cv-pre-with-lines">
            <code className={`language-${prismLang}`}>
              {file.content}
            </code>
          </pre>
        </div>
      )}
    </main>
  )
}
