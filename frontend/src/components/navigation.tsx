'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

export function Navigation() {
  const pathname = usePathname();

  const navItems = [
    { href: '/papers', label: 'Browse' },
    { href: '/library', label: 'Library' },
    { href: '/search', label: 'Search' },
  ];

  return (
    <nav className="flex space-x-6">
      {navItems.map((item) => {
        const isActive = pathname === item.href || 
          (item.href === '/papers' && pathname.startsWith('/papers')) ||
          (item.href === '/library' && pathname.startsWith('/library')) ||
          (item.href === '/search' && pathname.startsWith('/search'));
        
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'hover:text-gray-900 transition-colors',
              isActive 
                ? 'text-gray-700 font-medium' 
                : 'text-gray-500 hover:text-gray-700'
            )}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
} 