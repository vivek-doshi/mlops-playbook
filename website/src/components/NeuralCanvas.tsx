import { useEffect, useRef } from 'react'
import type { Theme } from '../types'

interface Node {
  x: number; y: number
  vx: number; vy: number
  radius: number
  pulsePhase: number
}

interface Props { theme: Theme }

export function NeuralCanvas({ theme }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animRef  = useRef<number>(0)
  const nodesRef = useRef<Node[]>([])
  const themeRef = useRef(theme)

  useEffect(() => { themeRef.current = theme }, [theme])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const resize = () => {
      canvas.width  = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()

    const N = 55
    nodesRef.current = Array.from({ length: N }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.35,
      vy: (Math.random() - 0.5) * 0.35,
      radius: Math.random() * 1.8 + 0.8,
      pulsePhase: Math.random() * Math.PI * 2,
    }))

    let tick = 0

    const animate = () => {
      tick++
      const w = canvas.width
      const h = canvas.height
      ctx.clearRect(0, 0, w, h)

      const isDark = themeRef.current === 'dusk'
      const primary   = isDark ? '0,212,255'   : '79,70,229'
      const secondary = isDark ? '168,85,247'  : '124,58,237'
      const maxDist   = 160
      const maxAlpha  = isDark ? 0.22 : 0.10
      const dotAlpha  = isDark ? 0.75 : 0.45

      const nodes = nodesRef.current

      for (const n of nodes) {
        n.x += n.vx; n.y += n.vy
        n.pulsePhase += 0.018
        if (n.x < 0 || n.x > w) n.vx *= -1
        if (n.y < 0 || n.y > h) n.vy *= -1
      }

      // Connections
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx   = nodes[j].x - nodes[i].x
          const dy   = nodes[j].y - nodes[i].y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist > maxDist) continue

          const alpha = (1 - dist / maxDist) * maxAlpha
          ctx.beginPath()
          ctx.moveTo(nodes[i].x, nodes[i].y)
          ctx.lineTo(nodes[j].x, nodes[j].y)
          ctx.strokeStyle = `rgba(${primary},${alpha})`
          ctx.lineWidth = 0.6
          ctx.stroke()

          // Flowing data particle along connection
          if (tick % 3 === 0 && Math.random() < 0.06) {
            const t = (tick * 0.008 + i * 0.07) % 1
            ctx.beginPath()
            ctx.arc(nodes[i].x + dx * t, nodes[i].y + dy * t, 1.5, 0, Math.PI * 2)
            ctx.fillStyle = `rgba(${secondary},${alpha * 5})`
            ctx.fill()
          }
        }
      }

      // Nodes
      for (const n of nodes) {
        const pulse = Math.sin(n.pulsePhase) * 0.5 + 0.5
        const r     = n.radius * (1 + pulse * 0.5)
        const a     = dotAlpha * (0.5 + pulse * 0.5)

        const grd = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, r * 5)
        grd.addColorStop(0, `rgba(${primary},${a * 0.8})`)
        grd.addColorStop(1, `rgba(${primary},0)`)
        ctx.beginPath()
        ctx.arc(n.x, n.y, r * 5, 0, Math.PI * 2)
        ctx.fillStyle = grd
        ctx.fill()

        ctx.beginPath()
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(${primary},${a})`
        ctx.fill()
      }

      animRef.current = requestAnimationFrame(animate)
    }
    animate()
    window.addEventListener('resize', resize)

    return () => {
      cancelAnimationFrame(animRef.current)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed', top: 0, left: 0,
        width: '100%', height: '100%',
        pointerEvents: 'none', zIndex: 0,
      }}
    />
  )
}
