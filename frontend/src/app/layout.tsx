import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import Link from "next/link";
import { AppLayout } from "@/components/app-layout";
import { SettingsProvider } from "@/contexts/settings-context";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Betarxiv",
  description: "Academic paper archive and management system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased h-full`}>
        <SettingsProvider>
          <div className="h-screen flex flex-col">
            <header className="bg-white border-b border-gray-200 flex-shrink-0 sticky top-0 z-50">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center h-16">
                  <div className="flex items-center space-x-8">
                    <Link href="/" className="flex items-center">
                      <h1 className="text-xl font-bold text-gray-900">Betarxiv</h1>
                    </Link>
                    
                  </div>
                  <div className="flex items-center space-x-4">
                    {/* <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center">
                      <svg className="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                    </div> */}
                    <Avatar className="h-8 w-8">
                      <AvatarImage src="/api/placeholder/32/32" alt="User" />
                      <AvatarFallback>S</AvatarFallback>
                    </Avatar>
                  </div>
                </div>
              </div>
            </header>
            <main className="flex-1 overflow-hidden">
              <AppLayout>
                {children}
              </AppLayout>
            </main>
            <footer className="w-full py-4 text-center text-gray-400 text-sm border-t bg-white flex-shrink-0">
              © 2025 Betarxiv. All rights reserved.
            </footer>
          </div>
        </SettingsProvider>
      </body>
    </html>
  );
}
