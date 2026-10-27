import { useEffect, useRef, useState } from 'react'

interface CanvasCodeBlockProps {
  content: string
  className?: string
  fontFamily?: string
  fontSize?: number
  lineHeight?: number
}

export function CanvasCodeBlock({
  content,
  className = '',
  fontFamily = '14px "Courier New", monospace',
  fontSize = 14,
  lineHeight = 1.65,
}: CanvasCodeBlockProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const wrapperRef = useRef<HTMLDivElement>(null)
  const [copied, setCopied] = useState(false)
  const workerRef = useRef<Worker | null>(null)

  useEffect(() => {
    // Initialize worker
    workerRef.current = new Worker(new URL('./yaml-renderer.worker.ts', import.meta.url), { type: 'module' });

    return () => {
      if (workerRef.current) {
        workerRef.current.terminate();
        workerRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current
    const wrapper = wrapperRef.current
    if (!canvas || !wrapper || !workerRef.current) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Parse font
    const fontMatch = fontFamily.match(/(\d+)px/)
    const baseFontSize = fontMatch ? parseInt(fontMatch[1], 10) : fontSize
    const fontFamilyName = fontFamily.replace(/(\d+)px/, '').trim()

    const dpr = window.devicePixelRatio || 1
    const padding = 24

    // Create initial canvas with reasonable size - worker will resize as needed
    const initialWidth = 800 + padding * 2
    const initialHeight = 400 + padding * 2

    // Set canvas size for HiDPI
    canvas.width = Math.ceil(initialWidth * dpr)
    canvas.height = Math.ceil(initialHeight * dpr)
    canvas.style.width = `${initialWidth}px`
    canvas.style.height = `${initialHeight}px`

    // Transfer canvas to worker
    const offscreen = canvas.transferControlToOffscreen()
    
    workerRef.current.postMessage({
      canvas: offscreen,
      text: content,
      pixelRatio: dpr,
      fontFamily: fontFamilyName,
      fontSize: baseFontSize,
      lineHeight,
      maxWidth: 800
    }, [offscreen])

    // Let worker handle sizing - use auto height for wrapper
    wrapper.style.height = 'auto'
  }, [content, fontFamily, fontSize, lineHeight])

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // fallback
      const ta = document.createElement('textarea')
      ta.value = content
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault()
  }

  return (
    <div
      ref={wrapperRef}
      className={`canvas-code-block ${className}`}
      onContextMenu={handleContextMenu}
      style={{
        position: 'relative',
        padding: '24px 28px',
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: '13px',
        lineHeight: '1.65',
        background: 'transparent',
        minWidth: 'max-content',
        overflow: 'hidden',
      }}
    >
      <canvas
        ref={canvasRef}
        aria-hidden="true"
        style={{
          display: 'block',
          width: '100%',
          height: '100%',
        }}
      />
      <button
        onClick={handleCopy}
        title="Copy to clipboard"
        style={{
          position: 'absolute',
          top: '8px',
          right: '8px',
          padding: '5px 11px',
          borderRadius: '7px',
          fontSize: '12px',
          fontWeight: 500,
          cursor: 'pointer',
          border: '1px solid var(--border)',
          background: 'var(--bg-elevated)',
          color: 'var(--text-secondary)',
          zIndex: 1,
        }}
      >
        {copied ? '✓ Copied!' : '⎘ Copy'}
      </button>
    </div>
  )
}
