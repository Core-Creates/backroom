import { NextResponse } from 'next/server'
import { dataService } from '@/lib/dataService'

export async function GET() {
  try {
    const inventoryData = await dataService.readInventoryData()
    return NextResponse.json(inventoryData)
  } catch (error) {
    console.error('Error fetching real inventory data:', error)
    return NextResponse.json(
      { error: 'Failed to fetch inventory data' },
      { status: 500 }
    )
  }
}

