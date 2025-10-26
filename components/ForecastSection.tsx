'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, Download, RefreshCw, AlertTriangle, BarChart3, Search } from 'lucide-react'

interface ForecastData {
  sku: string
  product_name: string
  current_stock: number
  daily_demand: number
  days_remaining: number
  reorder_point: number
  suggested_order: number
  priority: 'High' | 'Medium' | 'Low'
}

interface InventoryHistory {
  date: string
  stock_level: number
  demand: number
  reorder_point: number
}

export function ForecastSection() {
  const [forecastData, setForecastData] = useState<ForecastData[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all')
  const [selectedItem, setSelectedItem] = useState<string>('')
  const [inventoryHistory, setInventoryHistory] = useState<InventoryHistory[]>([])
  const [showChart, setShowChart] = useState(false)
  
  // Query-based graph generation states
  const [query, setQuery] = useState('')
  const [queryChart, setQueryChart] = useState<any>(null)
  const [showQueryChart, setShowQueryChart] = useState(false)
  const [isQueryLoading, setIsQueryLoading] = useState(false)

  useEffect(() => {
    fetchForecastData()
  }, [])

  const fetchForecastData = async () => {
    try {
      setLoading(true)
      // This would call your Streamlit backend API
      // For now, we'll use mock data
      const mockData: ForecastData[] = [
        {
          sku: 'SKU-001',
          product_name: 'Premium Shampoo',
          current_stock: 150,
          daily_demand: 12.5,
          days_remaining: 12,
          reorder_point: 100,
          suggested_order: 200,
          priority: 'High'
        },
        {
          sku: 'SKU-002',
          product_name: 'Conditioner',
          current_stock: 75,
          daily_demand: 8.2,
          days_remaining: 9,
          reorder_point: 50,
          suggested_order: 150,
          priority: 'High'
        },
        {
          sku: 'SKU-003',
          product_name: 'Body Lotion',
          current_stock: 200,
          daily_demand: 15.3,
          days_remaining: 13,
          reorder_point: 100,
          suggested_order: 100,
          priority: 'Medium'
        }
      ]
      
      setForecastData(mockData)
    } catch (error) {
      console.error('Error fetching forecast data:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredData = forecastData.filter(item => {
    if (filter === 'all') return true
    return item.priority.toLowerCase() === filter
  })

  const generateInventoryHistory = async (item: ForecastData): Promise<InventoryHistory[]> => {
    try {
      // Try to fetch real historical data
      const response = await fetch(`/api/inventory/history/${item.sku}`)
      if (response.ok) {
        const realData = await response.json()
        return realData.map((record: any) => ({
          date: record.date,
          stock_level: record.stock_level,
          demand: record.demand,
          reorder_point: record.reorder_point
        }))
      }
    } catch (error) {
      console.error('Error fetching real history data:', error)
    }

    // Fallback to generated data
    const history: InventoryHistory[] = []
    const today = new Date()
    
    // Generate 30 days of historical data
    for (let i = 29; i >= 0; i--) {
      const date = new Date(today)
      date.setDate(date.getDate() - i)
      
      // Simulate realistic inventory changes
      const baseStock = item.current_stock + (Math.random() - 0.5) * 20
      const dailyVariation = (Math.random() - 0.5) * 10
      const stockLevel = Math.max(0, Math.round(baseStock + dailyVariation))
      
      history.push({
        date: date.toISOString().split('T')[0],
        stock_level: stockLevel,
        demand: item.daily_demand + (Math.random() - 0.5) * 2,
        reorder_point: item.reorder_point
      })
    }
    
    return history
  }

  const handleItemSelect = async (sku: string) => {
    const item = forecastData.find(item => item.sku === sku)
    if (item) {
      setSelectedItem(sku)
      const history = await generateInventoryHistory(item)
      setInventoryHistory(history)
      setShowChart(true)
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'High':
        return 'bg-red-100 text-red-800'
      case 'Medium':
        return 'bg-yellow-100 text-yellow-800'
      case 'Low':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const handleDownload = () => {
    // This would generate and download the CSV
    console.log('Downloading forecast data...')
  }

  // Query-based graph generation
  const handleQuery = async () => {
    if (!query.trim()) return

    setIsQueryLoading(true)
    setShowQueryChart(false)
    
    try {
      // Simple query processing - you can replace this with your existing query system
      const lowerQuery = query.toLowerCase()
      
      // Determine chart type based on query
      let chartType = 'line'
      if (lowerQuery.includes('compare') || lowerQuery.includes('vs')) {
        chartType = 'bar'
      } else if (lowerQuery.includes('forecast') || lowerQuery.includes('predict')) {
        chartType = 'line'
      } else if (lowerQuery.includes('summary') || lowerQuery.includes('total')) {
        chartType = 'pie'
      }

      // Generate data based on query
      let data: InventoryHistory[] | { x: string; y: number; label: string }[] = []
      if (lowerQuery.includes('sku-001') || lowerQuery.includes('shampoo')) {
        // Get specific item data
        const item = forecastData.find(item => item.sku === 'SKU-001')
        if (item) {
          data = await generateInventoryHistory(item)
        }
      } else if (lowerQuery.includes('compare') || lowerQuery.includes('all')) {
        // Use forecast data for comparison
        data = forecastData.map(item => ({
          x: item.sku,
          y: item.current_stock,
          label: item.product_name
        }))
      } else {
        // Default to first item's history
        const item = forecastData[0]
        if (item) {
          data = await generateInventoryHistory(item)
        }
      }

      // Create chart configuration
      const chartConfig = {
        type: chartType,
        title: `Query Result: ${query}`,
        data: data,
        xAxis: chartType === 'bar' ? 'SKU' : 'Date',
        yAxis: 'Stock Level'
      }

      setQueryChart(chartConfig)
      setShowQueryChart(true)
      
    } catch (error) {
      console.error('Error processing query:', error)
    } finally {
      setIsQueryLoading(false)
    }
  }

  // Simple chart renderer for query results
  const QueryChartComponent = () => {
    if (!showQueryChart || !queryChart) return null

    const { type, title, data, xAxis, yAxis } = queryChart

    return (
      <div className="mt-6 bg-white p-6 rounded-lg shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900 flex items-center">
            <BarChart3 className="h-5 w-5 mr-2" />
            {title}
          </h3>
          <button
            onClick={() => setShowQueryChart(false)}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>
        
        <div className="relative">
          <svg width={800} height={300} className="border rounded">
            {type === 'line' && (
              <>
                {/* Simple line chart */}
                <polyline
                  points={data.map((point: any, index: number) => 
                    `${40 + (index / (data.length - 1)) * 720},${260 - (point.y / Math.max(...data.map((d: any) => d.y))) * 200}`
                  ).join(' ')}
                  fill="none"
                  stroke="#3b82f6"
                  strokeWidth={3}
                />
                {data.map((point: any, index: number) => (
                  <circle
                    key={index}
                    cx={40 + (index / (data.length - 1)) * 720}
                    cy={260 - (point.y / Math.max(...data.map((d: any) => d.y))) * 200}
                    r={4}
                    fill="#3b82f6"
                  />
                ))}
              </>
            )}
            
            {type === 'bar' && (
              <>
                {/* Simple bar chart */}
                {data.map((point: any, index: number) => {
                  const barHeight = (point.y / Math.max(...data.map((d: any) => d.y))) * 200
                  const barWidth = 720 / data.length * 0.8
                  const x = 40 + (index / data.length) * 720 + (720 / data.length - barWidth) / 2
                  const y = 260 - barHeight
                  
                  return (
                    <g key={index}>
                      <rect
                        x={x}
                        y={y}
                        width={barWidth}
                        height={barHeight}
                        fill="#3b82f6"
                      />
                      <text
                        x={x + barWidth / 2}
                        y={y - 5}
                        textAnchor="middle"
                        className="text-xs fill-gray-600"
                      >
                        {point.y}
                      </text>
                    </g>
                  )
                })}
              </>
            )}
            
            {type === 'pie' && (
              <>
                {/* Simple pie chart */}
                <circle
                  cx={400}
                  cy={150}
                  r={80}
                  fill="#3b82f6"
                  opacity={0.3}
                />
                <text
                  x={400}
                  y={150}
                  textAnchor="middle"
                  className="text-sm fill-gray-600"
                >
                  {data.length} Items
                </text>
              </>
            )}
          </svg>
        </div>
        
        <div className="mt-4 text-sm text-gray-600">
          <div className="flex justify-between">
            <span><strong>Chart Type:</strong> {type.toUpperCase()}</span>
            <span><strong>Data Points:</strong> {data.length}</span>
          </div>
        </div>
      </div>
    )
  }

  const ChartComponent = () => {
    if (!showChart || inventoryHistory.length === 0) return null

    const selectedItemData = forecastData.find(item => item.sku === selectedItem)
    if (!selectedItemData) return null

    const maxStock = Math.max(...inventoryHistory.map(h => h.stock_level))
    const chartHeight = 300
    const chartWidth = 800
    const padding = 40
    const innerWidth = chartWidth - 2 * padding
    const innerHeight = chartHeight - 2 * padding

    const points = inventoryHistory.map((point, index) => {
      const x = padding + (index / (inventoryHistory.length - 1)) * innerWidth
      const y = padding + (1 - point.stock_level / maxStock) * innerHeight
      return { x, y, ...point }
    })

    return (
      <div className="mt-6 bg-white p-6 rounded-lg shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900 flex items-center">
            <BarChart3 className="h-5 w-5 mr-2" />
            Inventory Trend: {selectedItemData.product_name} ({selectedItemData.sku})
          </h3>
          <button
            onClick={() => setShowChart(false)}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>
        
        <div className="relative">
          <svg width={chartWidth} height={chartHeight} className="border rounded">
            {/* Grid lines */}
            {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => (
              <g key={i}>
                <line
                  x1={padding}
                  y1={padding + ratio * innerHeight}
                  x2={chartWidth - padding}
                  y2={padding + ratio * innerHeight}
                  stroke="#e5e7eb"
                  strokeWidth={1}
                />
                <text
                  x={padding - 10}
                  y={padding + ratio * innerHeight + 5}
                  textAnchor="end"
                  className="text-xs fill-gray-500"
                >
                  {Math.round(maxStock * (1 - ratio))}
                </text>
              </g>
            ))}
            
            {/* Date labels */}
            {inventoryHistory.filter((_, i) => i % 5 === 0).map((point, i) => {
              const x = padding + ((i * 5) / (inventoryHistory.length - 1)) * innerWidth
              return (
                <text
                  key={i}
                  x={x}
                  y={chartHeight - 10}
                  textAnchor="middle"
                  className="text-xs fill-gray-500"
                >
                  {new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </text>
              )
            })}
            
            {/* Reorder point line */}
            <line
              x1={padding}
              y1={padding + (1 - selectedItemData.reorder_point / maxStock) * innerHeight}
              x2={chartWidth - padding}
              y2={padding + (1 - selectedItemData.reorder_point / maxStock) * innerHeight}
              stroke="#ef4444"
              strokeWidth={2}
              strokeDasharray="5,5"
            />
            <text
              x={chartWidth - padding + 5}
              y={padding + (1 - selectedItemData.reorder_point / maxStock) * innerHeight - 5}
              className="text-xs fill-red-600 font-medium"
            >
              Reorder Point ({selectedItemData.reorder_point})
            </text>
            
            {/* Stock level line */}
            <polyline
              points={points.map(p => `${p.x},${p.y}`).join(' ')}
              fill="none"
              stroke="#3b82f6"
              strokeWidth={3}
            />
            
            {/* Data points */}
            {points.map((point, index) => (
              <circle
                key={index}
                cx={point.x}
                cy={point.y}
                r={4}
                fill="#3b82f6"
                className="hover:r-6 transition-all cursor-pointer"
              />
            ))}
          </svg>
        </div>
        
        <div className="mt-4 flex justify-between text-sm text-gray-600">
          <div>
            <span className="font-medium">Current Stock:</span> {selectedItemData.current_stock}
          </div>
          <div>
            <span className="font-medium">Daily Demand:</span> {selectedItemData.daily_demand}
          </div>
          <div>
            <span className="font-medium">Days Remaining:</span> {selectedItemData.days_remaining}
          </div>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with Actions */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-medium text-gray-900">
            Reorder Planning & Forecast
          </h3>
          <p className="text-sm text-gray-600">
            AI-powered inventory forecasting and reorder recommendations
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={fetchForecastData}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
          <button
            onClick={handleDownload}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <Download className="h-4 w-4 mr-2" />
            Download CSV
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'all', label: 'All Items', count: forecastData.length },
            { id: 'high', label: 'High Priority', count: forecastData.filter(item => item.priority === 'High').length },
            { id: 'medium', label: 'Medium Priority', count: forecastData.filter(item => item.priority === 'Medium').length },
            { id: 'low', label: 'Low Priority', count: forecastData.filter(item => item.priority === 'Low').length },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilter(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                filter === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </nav>
      </div>

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <BarChart3 className="h-5 w-5 text-blue-400" />
          </div>
          <div className="ml-3">
            <p className="text-sm text-blue-700">
              <strong>Tip:</strong> Click on any row in the table below to view the inventory trend chart for that item.
            </p>
          </div>
        </div>
      </div>

      {/* Chart Component */}
      <ChartComponent />

      {/* Forecast Table */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  SKU
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Product
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current Stock
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Daily Demand
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Days Remaining
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reorder Point
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Suggested Order
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Priority
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredData.map((item) => (
                <tr 
                  key={item.sku} 
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => handleItemSelect(item.sku)}
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {item.sku}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {item.product_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {item.current_stock}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {item.daily_demand}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="flex items-center">
                      {item.days_remaining < 10 && (
                        <AlertTriangle className="h-4 w-4 text-yellow-400 mr-1" />
                      )}
                      {item.days_remaining} days
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {item.reorder_point}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {item.suggested_order}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPriorityColor(item.priority)}`}>
                      {item.priority}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrendingUp className="h-6 w-6 text-blue-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Items Needing Reorder
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {forecastData.filter(item => item.current_stock <= item.reorder_point).length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <AlertTriangle className="h-6 w-6 text-yellow-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    High Priority Items
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {forecastData.filter(item => item.priority === 'High').length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrendingUp className="h-6 w-6 text-green-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Suggested Orders
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {forecastData.reduce((sum, item) => sum + item.suggested_order, 0)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Query Input Section - Moved to Bottom */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h4 className="text-lg font-medium text-gray-900 mb-4">
          Ask Questions About Your Data
        </h4>
        
        <div className="flex space-x-2">
          <div className="flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleQuery()}
              placeholder="e.g., Show me trends for SKU-001, Compare all products, Forecast next week"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={handleQuery}
            disabled={isQueryLoading || !query.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <Search className="h-4 w-4" />
            <span>{isQueryLoading ? 'Analyzing...' : 'Ask'}</span>
          </button>
        </div>

        {/* Example Queries */}
        <div className="mt-4">
          <p className="text-sm text-gray-600 mb-2">Try these examples:</p>
          <div className="flex flex-wrap gap-2">
            {[
              'Show me trends for SKU-001',
              'Compare all products',
              'Forecast next week',
              'Summary of high priority items'
            ].map((example, index) => (
              <button
                key={index}
                onClick={() => setQuery(example)}
                className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Query Chart Component */}
      <QueryChartComponent />
    </div>
  )
}
