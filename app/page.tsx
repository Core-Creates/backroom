'use client'
// app/page.tsx
import { useState, useEffect, useRef, useCallback } from 'react'
import { ChevronDownIcon, RotateCw } from 'lucide-react'
import { InventoryDashboard } from '@/components/InventoryDashboard'
import { UploadSection } from '@/components/UploadSection'
import { ForecastSection } from '@/components/ForecastSection'
import { ChatInterface } from '@/components/ChatInterface'
import { ParquetUpload } from '@/components/ParquetUpload'
import { QueryInterface } from '@/components/QueryInterface'

// Lightweight apiGet helper: fetch wrapper used by this page to check backend health.
// This avoids a hard dependency on '@/lib/api' which may not exist in some environments.
async function apiGet<T = any>(path: string): Promise<T> {
  const base = process.env.NEXT_PUBLIC_API_URL ?? ''
  const res = await fetch(`${base}${path}`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Network response was not ok')
  return res.json()
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '(unset)'

export default function Home() {
  const [activeTab, setActiveTab] = useState<'overview' | 'upload' | 'forecast' | 'chat'>('overview')
  const [selectedCategory, setSelectedCategory] = useState('All Categories')
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [apiOk, setApiOk] = useState<'unknown' | 'ok' | 'down'>('unknown')
  const [checking, setChecking] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'upload', label: 'Upload & Clean', icon: '📤' },
    { id: 'parquet', label: 'Parquet Data', icon: '🗄️' },
    { id: 'query', label: 'Query Graphs', icon: '🔍' },
    { id: 'forecast', label: 'Forecast', icon: '🔮' },
    { id: 'chat', label: 'AI Chat', icon: '💬' },
  ] as const

  const groceryCategories = [
    'All Categories',
    'Fresh Produce',
    'Dairy & Eggs',
    'Meat & Seafood',
    'Bakery',
    'Pantry Staples',
    'Beverages',
    'Snacks',
    'Frozen Foods',
    'Health & Beauty',
    'Household Items',
    'Baby & Kids',
    'Pet Supplies',
    'Organic & Natural',
    'International Foods',
  ]

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Check backend health (FastAPI /health)
  const checkHealth = useCallback(async () => {
    setChecking(true)
    try {
      await apiGet<{ status: string }>('/health')
      setApiOk('ok')
    } catch {
      setApiOk('down')
    } finally {
      setChecking(false)
    }
  }, [])

  useEffect(() => {
    checkHealth()
  }, [checkHealth])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-6">
              {/* Grocery Categories Dropdown */}
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                  className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <span>🛒</span>
                  <span>{selectedCategory}</span>
                  <ChevronDownIcon className="h-4 w-4" />
                </button>

                {isDropdownOpen && (
                  <div className="absolute z-10 mt-1 w-56 bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none">
                    {groceryCategories.map((category) => (
                      <button
                        key={category}
                        onClick={() => {
                          setSelectedCategory(category)
                          setIsDropdownOpen(false)
                        }}
                        className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-100 ${
                          selectedCategory === category ? 'bg-blue-50 text-blue-600' : 'text-gray-900'
                        }`}
                      >
                        {category}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <h1 className="text-2xl font-bold text-gray-900">Backroom — Inventory Intelligence</h1>
            </div>

            {/* Right badges */}
            <div className="flex items-center space-x-3">
              {/* API status */}
              {apiOk === 'ok' && (
                <span
                  title={`Backend: ${API_BASE}`}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
                >
                  API Connected
                </span>
              )}
              {apiOk === 'down' && (
                <span
                  title={`Backend: ${API_BASE}`}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"
                >
                  API Down
                </span>
              )}
              {apiOk === 'unknown' && (
                <span
                  title={`Backend: ${API_BASE}`}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                >
                  Checking API…
                </span>
              )}

              {/* Retry health check */}
              <button
                onClick={checkHealth}
                disabled={checking}
                className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                title="Re-check API health"
              >
                <RotateCw className={`h-3.5 w-3.5 ${checking ? 'animate-spin' : ''}`} />
                Retry
              </button>

              {/* Existing DuckDB badge (kept) */}
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                DuckDB Connected
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {activeTab === 'overview' && <InventoryDashboard />}
          {activeTab === 'upload' && <UploadSection />}
          {activeTab === 'parquet' && <ParquetUpload />}
          {activeTab === 'query' && <QueryInterface />}
          {activeTab === 'forecast' && <ForecastSection />}
          {activeTab === 'chat' && <ChatInterface />}
        </div>
      </main>
    </div>
  )
}
