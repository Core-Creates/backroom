import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // This would typically fetch from your Streamlit backend or database
    // For now, returning mock data
    const mockInventory = [
      {
        sku: 'SKU-001',
        product_name: 'Premium Shampoo',
        on_hand: 150,
        backroom_units: 100,
        shelf_units: 50,
        avg_daily_sales: 12.5,
        lead_time_days: 7
      },
      {
        sku: 'SKU-002',
        product_name: 'Conditioner',
        on_hand: 75,
        backroom_units: 50,
        shelf_units: 25,
        avg_daily_sales: 8.2,
        lead_time_days: 5
      },
      {
        sku: 'SKU-003',
        product_name: 'Body Lotion',
        on_hand: 200,
        backroom_units: 150,
        shelf_units: 50,
        avg_daily_sales: 15.3,
        lead_time_days: 10
      }
    ]

    return NextResponse.json(mockInventory)
  } catch (error) {
    console.error('Error fetching inventory:', error)
    return NextResponse.json(
      { error: 'Failed to fetch inventory data' },
      { status: 500 }
    )
  }
}
