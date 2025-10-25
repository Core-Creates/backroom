'use client'

import { useState, useEffect, useRef } from 'react'
import { ChevronDownIcon } from 'lucide-react'
import { InventoryDashboard } from '@/components/InventoryDashboard'
import { UploadSection } from '@/components/UploadSection'
import { ForecastSection } from '@/components/ForecastSection'
import { ChatInterface } from '@/components/ChatInterface'
import { ParquetUpload } from '@/components/ParquetUpload'
import { QueryInterface } from '@/components/QueryInterface'

export default function Home() {
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedCategory, setSelectedCategory] = useState('All Categories')
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'upload', label: 'Upload & Clean', icon: '📤' },
    { id: 'parquet', label: 'Parquet Data', icon: '🗄️' },
    { id: 'query', label: 'Query Graphs', icon: '🔍' },
    { id: 'forecast', label: 'Forecast', icon: '🔮' },
    { id: 'chat', label: 'AI Chat', icon: '💬' },
  ]

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
    'International Foods'
  ]

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

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
              
              <h1 className="text-2xl font-bold text-gray-900">
                Backroom — Inventory Intelligence
              </h1>
            </div>
            <div className="flex items-center space-x-4">
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
