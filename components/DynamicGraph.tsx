'use client'

import { useEffect, useRef } from 'react'
import { GraphConfig } from '@/lib/queryParser'

interface DynamicGraphProps {
  config: GraphConfig
  width?: number
  height?: number
}

export function DynamicGraph({ config, width = 800, height = 400 }: DynamicGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    if (!canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Clear canvas
    ctx.clearRect(0, 0, width, height)

    // Draw graph based on type
    switch (config.type) {
      case 'line':
        drawLineChart(ctx, config, width, height)
        break
      case 'bar':
        drawBarChart(ctx, config, width, height)
        break
      case 'scatter':
        drawScatterChart(ctx, config, width, height)
        break
      case 'area':
        drawAreaChart(ctx, config, width, height)
        break
      case 'pie':
        drawPieChart(ctx, config, width, height)
        break
    }
  }, [config, width, height])

  const drawLineChart = (ctx: CanvasRenderingContext2D, config: GraphConfig, width: number, height: number) => {
    const padding = 60
    const chartWidth = width - 2 * padding
    const chartHeight = height - 2 * padding

    // Find min/max values
    const values = config.data.map(d => d.y)
    const minY = Math.min(...values)
    const maxY = Math.max(...values)
    const rangeY = maxY - minY || 1

    // Draw axes
    ctx.strokeStyle = '#374151'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(padding, padding)
    ctx.lineTo(padding, height - padding)
    ctx.lineTo(width - padding, height - padding)
    ctx.stroke()

    // Draw grid lines
    ctx.strokeStyle = '#e5e7eb'
    ctx.lineWidth = 1
    for (let i = 0; i <= 5; i++) {
      const y = padding + (i / 5) * chartHeight
      ctx.beginPath()
      ctx.moveTo(padding, y)
      ctx.lineTo(width - padding, y)
      ctx.stroke()
    }

    // Draw line
    ctx.strokeStyle = '#3b82f6'
    ctx.lineWidth = 3
    ctx.beginPath()
    
    config.data.forEach((point, index) => {
      const x = padding + (index / (config.data.length - 1)) * chartWidth
      const y = height - padding - ((point.y - minY) / rangeY) * chartHeight
      
      if (index === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    })
    ctx.stroke()

    // Draw data points
    ctx.fillStyle = '#3b82f6'
    config.data.forEach((point, index) => {
      const x = padding + (index / (config.data.length - 1)) * chartWidth
      const y = height - padding - ((point.y - minY) / rangeY) * chartHeight
      
      ctx.beginPath()
      ctx.arc(x, y, 4, 0, 2 * Math.PI)
      ctx.fill()
    })

    // Draw labels
    ctx.fillStyle = '#374151'
    ctx.font = '12px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(config.title, width / 2, 20)
    
    // Y-axis labels
    ctx.textAlign = 'right'
    for (let i = 0; i <= 5; i++) {
      const value = minY + (i / 5) * rangeY
      const y = padding + (i / 5) * chartHeight
      ctx.fillText(value.toFixed(0), padding - 10, y + 4)
    }
  }

  const drawBarChart = (ctx: CanvasRenderingContext2D, config: GraphConfig, width: number, height: number) => {
    const padding = 60
    const chartWidth = width - 2 * padding
    const chartHeight = height - 2 * padding

    const values = config.data.map(d => d.y)
    const maxY = Math.max(...values)
    const barWidth = chartWidth / config.data.length * 0.8

    // Draw axes
    ctx.strokeStyle = '#374151'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(padding, padding)
    ctx.lineTo(padding, height - padding)
    ctx.lineTo(width - padding, height - padding)
    ctx.stroke()

    // Draw bars
    config.data.forEach((point, index) => {
      const barHeight = (point.y / maxY) * chartHeight
      const x = padding + (index / config.data.length) * chartWidth + (chartWidth / config.data.length - barWidth) / 2
      const y = height - padding - barHeight

      ctx.fillStyle = '#3b82f6'
      ctx.fillRect(x, y, barWidth, barHeight)

      // Draw value label
      ctx.fillStyle = '#374151'
      ctx.font = '10px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(point.y.toFixed(0), x + barWidth / 2, y - 5)
    })

    // Draw title
    ctx.fillStyle = '#374151'
    ctx.font = '12px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(config.title, width / 2, 20)
  }

  const drawScatterChart = (ctx: CanvasRenderingContext2D, config: GraphConfig, width: number, height: number) => {
    const padding = 60
    const chartWidth = width - 2 * padding
    const chartHeight = height - 2 * padding

    const xValues = config.data.map(d => d.x)
    const yValues = config.data.map(d => d.y)
    const minX = Math.min(...xValues)
    const maxX = Math.max(...xValues)
    const minY = Math.min(...yValues)
    const maxY = Math.max(...yValues)
    const rangeX = maxX - minX || 1
    const rangeY = maxY - minY || 1

    // Draw axes
    ctx.strokeStyle = '#374151'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(padding, padding)
    ctx.lineTo(padding, height - padding)
    ctx.lineTo(width - padding, height - padding)
    ctx.stroke()

    // Draw points
    ctx.fillStyle = '#3b82f6'
    config.data.forEach(point => {
      const x = padding + ((point.x - minX) / rangeX) * chartWidth
      const y = height - padding - ((point.y - minY) / rangeY) * chartHeight
      
      ctx.beginPath()
      ctx.arc(x, y, 6, 0, 2 * Math.PI)
      ctx.fill()
    })

    // Draw title
    ctx.fillStyle = '#374151'
    ctx.font = '12px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(config.title, width / 2, 20)
  }

  const drawAreaChart = (ctx: CanvasRenderingContext2D, config: GraphConfig, width: number, height: number) => {
    const padding = 60
    const chartWidth = width - 2 * padding
    const chartHeight = height - 2 * padding

    const values = config.data.map(d => d.y)
    const minY = Math.min(...values)
    const maxY = Math.max(...values)
    const rangeY = maxY - minY || 1

    // Draw area
    ctx.fillStyle = 'rgba(59, 130, 246, 0.3)'
    ctx.beginPath()
    
    config.data.forEach((point, index) => {
      const x = padding + (index / (config.data.length - 1)) * chartWidth
      const y = height - padding - ((point.y - minY) / rangeY) * chartHeight
      
      if (index === 0) {
        ctx.moveTo(x, height - padding)
        ctx.lineTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    })
    
    ctx.lineTo(width - padding, height - padding)
    ctx.closePath()
    ctx.fill()

    // Draw line
    ctx.strokeStyle = '#3b82f6'
    ctx.lineWidth = 3
    ctx.beginPath()
    
    config.data.forEach((point, index) => {
      const x = padding + (index / (config.data.length - 1)) * chartWidth
      const y = height - padding - ((point.y - minY) / rangeY) * chartHeight
      
      if (index === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    })
    ctx.stroke()

    // Draw title
    ctx.fillStyle = '#374151'
    ctx.font = '12px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(config.title, width / 2, 20)
  }

  const drawPieChart = (ctx: CanvasRenderingContext2D, config: GraphConfig, width: number, height: number) => {
    const centerX = width / 2
    const centerY = height / 2
    const radius = Math.min(width, height) / 2 - 40

    const total = config.data.reduce((sum, item) => sum + item.value, 0)
    let currentAngle = 0

    const colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4']

    config.data.forEach((item, index) => {
      const sliceAngle = (item.value / total) * 2 * Math.PI
      
      // Draw slice
      ctx.fillStyle = colors[index % colors.length]
      ctx.beginPath()
      ctx.moveTo(centerX, centerY)
      ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle)
      ctx.closePath()
      ctx.fill()

      // Draw label
      const labelAngle = currentAngle + sliceAngle / 2
      const labelX = centerX + Math.cos(labelAngle) * (radius + 20)
      const labelY = centerY + Math.sin(labelAngle) * (radius + 20)
      
      ctx.fillStyle = '#374151'
      ctx.font = '10px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(item.label, labelX, labelY)
      ctx.fillText(item.value.toFixed(0), labelX, labelY + 12)

      currentAngle += sliceAngle
    })

    // Draw title
    ctx.fillStyle = '#374151'
    ctx.font = '12px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(config.title, width / 2, 20)
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="border rounded"
      />
    </div>
  )
}

