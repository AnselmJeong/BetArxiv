import { NextRequest, NextResponse } from 'next/server';

// Use the base backend URL without /api since we'll add it manually
const BACKEND_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const path = searchParams.get('path');
  const baseDir = searchParams.get('base_dir');

  if (!path) {
    return NextResponse.json(
      { error: 'Path parameter is required' },
      { status: 400 }
    );
  }

  try {
    // Forward the request to the FastAPI backend
    const backendUrl = new URL('/api/pdf', BACKEND_BASE_URL);
    backendUrl.searchParams.set('path', path);
    
    // Include base_dir parameter if provided
    if (baseDir) {
      backendUrl.searchParams.set('base_dir', baseDir);
    }

    const response = await fetch(backendUrl.toString());

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: `Backend error: ${errorText}` },
        { status: response.status }
      );
    }

    // Get the PDF data
    const pdfData = await response.arrayBuffer();

    // Return the PDF with proper headers
    return new NextResponse(pdfData, {
      status: 200,
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': `inline; filename="${path.split('/').pop()}"`,
        'Cache-Control': 'public, max-age=3600', // Cache for 1 hour
      },
    });

  } catch (error) {
    console.error('Error serving PDF:', error);
    return NextResponse.json(
      { error: 'Failed to serve PDF file' },
      { status: 500 }
    );
  }
} 