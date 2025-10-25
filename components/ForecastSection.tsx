'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, Download, RefreshCw, AlertTriangle } from 'lucide-react'

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

export function ForecastSection() {
  const [forecastData, setForecastData] = useState<ForecastData[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all')

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
                <tr key={item.sku} className="hover:bg-gray-50">
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
    </div>
  )
}
