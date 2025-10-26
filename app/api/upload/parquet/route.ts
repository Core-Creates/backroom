import { NextRequest, NextResponse } from 'next/server'
import { writeFileSync, mkdirSync } from 'fs'
import { join } from 'path'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File
    
    if (!file) {
      return NextResponse.json({ error: 'No file uploaded' }, { status: 400 })
    }

    // Check if it's a Parquet file
    if (!file.name.endsWith('.parquet')) {
      return NextResponse.json({ error: 'Only Parquet files are allowed' }, { status: 400 })
    }

    // Ensure data directory exists
    const dataDir = join(process.cwd(), 'data')
    mkdirSync(dataDir, { recursive: true })

    // Save the file
    const buffer = Buffer.from(await file.arrayBuffer())
    const filePath = join(dataDir, file.name)
    writeFileSync(filePath, buffer)

    return NextResponse.json({ 
      message: 'File uploaded successfully',
      filename: file.name,
      path: filePath
    })
  } catch (error) {
    console.error('Error uploading Parquet file:', error)
    return NextResponse.json(
      { error: 'Failed to upload file' },
      { status: 500 }
    )
  }
}

