'use client'

import { useState, useEffect } from 'react'
import { BarChart3, PieChart, Search, TrendingUp } from 'lucide-react';
import { QueryParser, GraphGenerator, type QueryIntent, type GraphConfig } from '@/lib/queryParser'
import { DynamicGraph } from './DynamicGraph'

interface QueryInterfaceProps {
  inventoryData?: any[]
  historyData?: any[]
}

export function QueryInterface({ inventoryData = [], historyData = [] }: QueryInterfaceProps) {
  const [query, setQuery] = useState('')
  const [parsedIntent, setParsedIntent] = useState<QueryIntent | null>(null)
  const [graphConfig, setGraphConfig] = useState<GraphConfig | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [queryHistory, setQueryHistory] = useState<string[]>([])
  const [realInventoryData, setRealInventoryData] = useState<any[]>([])

  // Fetch real inventory data on component mount
  useEffect(() => {
    const fetchInventoryData = async () => {
      try {
        const response = await fetch('/api/inventory/real')
        if (response.ok) {
          const data = await response.json()
          setRealInventoryData(data)
        }
      } catch (error) {
        console.error('Error fetching inventory data:', error)
      }
    }
    fetchInventoryData()
  }, [])

  const exampleQueries = [
    'Show me stock trends for SKU-001 over the last month',
    'Compare inventory levels across all products',
    'Forecast demand for the next week',
    'Analyze the relationship between sales and stock levels',
    'Give me a summary of high priority items',
    'Show me the trend of organic apples over time',
    'Compare dairy products vs fresh produce',
    'Predict when we will run out of milk'
  ]

  const handleQuery = async () => {
    if (!query.trim()) return

    setIsLoading(true)
    
    try {
      // Parse the query
      const intent = QueryParser.parseQuery(query)
      setParsedIntent(intent)
      
      // Generate appropriate data based on intent
      const data = await generateDataForIntent(intent)
      
      // Generate graph configuration
      const config = GraphGenerator.generateGraph(intent, data)
      setGraphConfig(config)
      
      // Add to query history
      setQueryHistory(prev => [query, ...prev.slice(0, 4)])
      
    } catch (error) {
      console.error('Error processing query:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const generateDataForIntent = async (intent: QueryIntent): Promise<any[]> => {
    // If specific SKUs are mentioned, get their history
    if (intent.entities.some(entity => entity.startsWith('SKU-'))) {
      const sku = intent.entities.find(entity => entity.startsWith('SKU-'))
      if (sku) {
        try {
          const response = await fetch(`/api/inventory/history/${sku}`)
          if (response.ok) {
            return await response.json()
          }
        } catch (error) {
          console.error('Error fetching history data:', error)
        }
      }
    }

    // If categories are mentioned, filter by category
    if (intent.entities.some(entity => 
      ['fresh produce', 'dairy', 'meat', 'bakery', 'beverages'].includes(entity)
    )) {
      const category = intent.entities.find(entity => 
        ['fresh produce', 'dairy', 'meat', 'bakery', 'beverages'].includes(entity)
      )
      return realInventoryData.filter(item => 
        item.category?.toLowerCase().includes(category || '')
      )
    }

    // Default to all inventory data
    return realInventoryData
  }

  const getIntentIcon = (intent: QueryIntent) => {
    switch (intent.type) {
      case 'trend':
        return <TrendingUp className="h-4 w-4" />
      case 'comparison':
        return <BarChart3 className="h-4 w-4" />
      case 'forecast':
        return <TrendingUp className="h-4 w-4" />
      case 'analysis':
        return <BarChart3 className="h-4 w-4" />
      case 'summary':
        return <PieChart className="h-4 w-4" />
      default:
        return <BarChart3 className="h-4 w-4" />
    }
  }

  const getIntentColor = (intent: QueryIntent) => {
    switch (intent.type) {
      case 'trend':
        return 'text-blue-600 bg-blue-100'
      case 'comparison':
        return 'text-green-600 bg-green-100'
      case 'forecast':
        return 'text-purple-600 bg-purple-100'
      case 'analysis':
        return 'text-orange-600 bg-orange-100'
      case 'summary':
        return 'text-pink-600 bg-pink-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  return (
    <div className="space-y-6">
      {/* Query Input */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Ask a Question About Your Data
        </h3>
        
        <div className="flex space-x-2">
          <div className="flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleQuery()}
              placeholder="e.g., Show me stock trends for SKU-001 over the last month"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={handleQuery}
            disabled={isLoading || !query.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <Search className="h-4 w-4" />
            <span>{isLoading ? 'Analyzing...' : 'Ask'}</span>
          </button>
        </div>

        {/* Example Queries */}
        <div className="mt-4">
          <p className="text-sm text-gray-600 mb-2">Try these examples:</p>
          <div className="flex flex-wrap gap-2">
            {exampleQueries.slice(0, 4).map((example, index) => (
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

      {/* Query Analysis */}
      {parsedIntent && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h4 className="text-md font-medium text-gray-900 mb-2">Query Analysis</h4>
          <div className="flex items-center space-x-4">
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium ${getIntentColor(parsedIntent)}`}>
              {getIntentIcon(parsedIntent)}
              <span>{parsedIntent.type.toUpperCase()}</span>
            </div>
            
            {parsedIntent.entities.length > 0 && (
              <div className="text-sm text-gray-600">
                <span className="font-medium">Entities:</span> {parsedIntent.entities.join(', ')}
              </div>
            )}
            
            {parsedIntent.timeframe && (
              <div className="text-sm text-gray-600">
                <span className="font-medium">Timeframe:</span> {parsedIntent.timeframe}
              </div>
            )}
            
            {parsedIntent.metric && (
              <div className="text-sm text-gray-600">
                <span className="font-medium">Metric:</span> {parsedIntent.metric}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Generated Graph */}
      {graphConfig && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-lg font-medium text-gray-900">Generated Visualization</h4>
            <div className="text-sm text-gray-500">
              {graphConfig.type.toUpperCase()} Chart
            </div>
          </div>
          <DynamicGraph config={graphConfig} />
        </div>
      )}

      {/* Query History */}
      {queryHistory.length > 0 && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h4 className="text-md font-medium text-gray-900 mb-2">Recent Queries</h4>
          <div className="space-y-2">
            {queryHistory.map((historyQuery, index) => (
              <button
                key={index}
                onClick={() => setQuery(historyQuery)}
                className="block w-full text-left text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 p-2 rounded transition-colors"
              >
                {historyQuery}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
