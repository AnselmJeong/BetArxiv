# Global Settings Feature

## Overview

The application now supports global settings that persist across the entire application and are saved to localStorage. The most important setting is the `baseDirectory`, which specifies where PDF files are stored and can be accessed by any component.

## Features

### Settings Context

The `SettingsProvider` component wraps the entire application and provides global access to:

- `baseDirectory` - The root directory where PDF files are stored
- `llmProvider` - The selected LLM provider (OpenAI, Anthropic, Google, Local)
- `apiKey` - The API key for the selected provider
- `displayMode` - Light or dark mode preference

### Usage in Components

```typescript
import { useSettings } from '@/contexts/settings-context';

function MyComponent() {
  const { baseDirectory, setBaseDirectory, saveSettings } = useSettings();
  
  // Use baseDirectory to construct file paths
  const pdfPath = `${baseDirectory}/my-document.pdf`;
  
  // Update settings
  setBaseDirectory('/new/path');
  saveSettings(); // Persist to localStorage
}
```

### PDF Path Helper Hook

The `usePdfPath` hook provides utilities for constructing PDF paths and URLs:

```typescript
import { usePdfPath } from '@/hooks/usePdfPath';

function PDFViewerComponent() {
  const { getPdfUrl, getPdfPath } = usePdfPath();
  
  // Get URL for serving PDF via API
  const pdfUrl = getPdfUrl(documentId);
  
  // Get local file system path
  const localPath = getPdfPath(documentId, 'custom-filename.pdf');
}
```

## Implementation Details

### Settings Persistence

Settings are automatically saved to and loaded from localStorage with the key `betarxiv-settings`. The settings are loaded when the provider mounts and can be manually saved using the `saveSettings()` function.

### PDF Serving

PDF files are served through a two-tier system:

1. **Next.js API Route** (`/api/pdf`): Handles the frontend request
2. **FastAPI Backend** (`/api/pdf`): Serves the actual file from the file system

The PDF serving endpoint:
- Validates file existence and type
- Provides security checks
- Returns the PDF with proper headers for browser viewing

### Security Considerations

The PDF serving endpoint includes several security measures:
- Path validation to ensure files exist
- File type checking (must be .pdf)
- Error handling for invalid paths

## Usage Example: Paper Inspector

The paper inspector page (`papers/[id]/inspect`) demonstrates how to use the global settings:

```typescript
'use client';

import { usePdfPath } from '@/hooks/usePdfPath';
import { useParams } from 'next/navigation';

export default function PaperInspectPage() {
  const { id: documentId } = useParams();
  const { getPdfUrl } = usePdfPath();
  
  // Automatically constructs PDF URL using global baseDirectory
  const pdfUrl = getPdfUrl(documentId as string);
  
  return <PDFViewer pdfUrl={pdfUrl} />;
}
```

## Configuration

Set the `NEXT_PUBLIC_API_URL` environment variable to point to your FastAPI backend:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The default baseDirectory is set to `/Volumes/Aquatope/_DEV_/BetArxiv/docs` but can be changed in the settings page. 