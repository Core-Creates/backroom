import { NextResponse } from 'next/server'
import { dataService } from '@/lib/dataService'

export async function GET(
  request: Request,
  { params }: { params: { sku: string } }
) {
  try {
    const { sku } = params
    const historyData = await dataService.readInventoryHistory(sku)
    return NextResponse.json(historyData)
  } catch (error) {
    console.error('Error fetching inventory history:', error)
    return NextResponse.json(
      { error: 'Failed to fetch inventory history' },
      { status: 500 }
    )
  }
}

