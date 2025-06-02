'use client';

import { useState } from 'react';
import { Sidebar } from './sidebar';

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  return (
    <div className="flex h-full">
      <Sidebar 
        isCollapsed={isSidebarCollapsed} 
        onToggle={() => setIsSidebarCollapsed(!isSidebarCollapsed)} 
      />
      <div className="flex-1 min-w-0">
        {children}
      </div>
    </div>
  );
} 