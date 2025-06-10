import { NextRequest, NextResponse } from 'next/server';

// Use the base backend URL without /api since we'll add it manually
// In Docker: use 'http://backend:8000' (internal network)
// In development: use 'http://localhost:8001' (host network)
const BACKEND_BASE_URL = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const searchParams = request.nextUrl.searchParams;
  const width = searchParams.get('width');
  const height = searchParams.get('height');

  try {
    // Forward the request to the FastAPI backend
    const backendUrl = new URL(`/api/documents/${id}/thumbnail`, BACKEND_BASE_URL);
    
    // Include query parameters if provided
    if (width) {
      backendUrl.searchParams.set('width', width);
    }
    if (height) {
      backendUrl.searchParams.set('height', height);
    }

    const response = await fetch(backendUrl.toString());

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: `Backend error: ${errorText}` },
        { status: response.status }
      );
    }

    // Get the image data
    const imageData = await response.arrayBuffer();

    // Return the image with proper headers
    return new NextResponse(imageData, {
      status: 200,
      headers: {
        'Content-Type': 'image/jpeg',
        'Cache-Control': 'public, max-age=3600', // Cache for 1 hour
      },
    });

  } catch (error) {
    console.error('Error serving thumbnail:', error);
    return NextResponse.json(
      { error: 'Failed to serve thumbnail' },
      { status: 500 }
    );
  }
} 