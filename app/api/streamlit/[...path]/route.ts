import { NextRequest, NextResponse } from 'next/server'

const STREAMLIT_BASE_URL = 'http://localhost:8502'

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const path = params.path.join('/')
  const url = new URL(request.url)
  const searchParams = url.searchParams.toString()
  
  try {
    const response = await fetch(
      `${STREAMLIT_BASE_URL}/${path}${searchParams ? `?${searchParams}` : ''}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )

    const data = await response.text()
    return new NextResponse(data, {
      status: response.status,
      headers: {
        'Content-Type': response.headers.get('content-type') || 'text/html',
      },
    })
  } catch (error) {
    console.error('Error proxying to Streamlit:', error)
    return NextResponse.json(
      { error: 'Failed to connect to Streamlit backend' },
      { status: 500 }
    )
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const path = params.path.join('/')
  const body = await request.text()
  
  try {
    const response = await fetch(`${STREAMLIT_BASE_URL}/${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': request.headers.get('content-type') || 'application/json',
      },
      body,
    })

    const data = await response.text()
    return new NextResponse(data, {
      status: response.status,
      headers: {
        'Content-Type': response.headers.get('content-type') || 'text/html',
      },
    })
  } catch (error) {
    console.error('Error proxying to Streamlit:', error)
    return NextResponse.json(
      { error: 'Failed to connect to Streamlit backend' },
      { status: 500 }
    )
  }
}
