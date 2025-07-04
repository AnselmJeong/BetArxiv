"use client"

import { Search, User, FileText, Calendar } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { DocumentCard } from "@/components/DocumentCard"
import { useRecentDocuments } from "@/hooks/useDocuments"
import { useStatistics } from "@/hooks/useFolders"
import { useState } from "react"
import { useRouter } from "next/navigation"

export default function Home() {
  const [searchQuery, setSearchQuery] = useState("")
  const router = useRouter()
  const { documents: recentDocuments, loading: documentsLoading } = useRecentDocuments(3)
  const { folderCount, totalDocuments, loading: statsLoading } = useStatistics()

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) return
    
    // Navigate to search page with semantic search
    const searchParams = new URLSearchParams({
      tab: 'semantic',
      query: searchQuery.trim()
    })
    router.push(`/search?${searchParams.toString()}`)
  }

  const handleDocumentClick = (documentId: string) => {
    router.push(`/papers/${documentId}`)
  }

  return (
    <div className="bg-gray-50 min-h-full">
      {/* Header */}
     

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <div className="mb-12">
          <Card className="bg-gradient-to-r from-blue-50 to-indigo-100 border-0 overflow-hidden">
            <CardContent className="p-8">
              <div className="max-w-3xl mx-auto text-center">
                <h1 className="text-4xl font-bold text-gray-900 mb-4">My Archive</h1>
                <p className="text-lg text-gray-600 mb-8">Welcome back! Wield the power of AI to understand your papers.</p>
                
                <form onSubmit={handleSearch} className="relative max-w-2xl mx-auto">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                  <Input
                    type="search"
                    placeholder="Search your archive with AI-powered semantic search..."
                    className="pl-12 pr-4 py-4 w-full bg-white border border-gray-200 rounded-xl text-lg shadow-sm focus:shadow-md transition-shadow"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </form>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Additions */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Recent Additions</h2>
          
          {documentsLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              {[1, 2, 3].map((i) => (
                <Card key={i} className="overflow-hidden animate-pulse">
                  <div className="h-32 bg-gray-200"></div>
                  <CardContent className="p-4">
                    <div className="h-4 bg-gray-200 rounded mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-2/3"></div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : recentDocuments.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              {recentDocuments.map((document, index) => (
                <DocumentCard
                  key={document.id}
                  document={document}
                  index={index}
                  onClick={() => handleDocumentClick(document.id)}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No papers yet</h3>
              <p className="text-gray-500">Start by adding some research papers to your archive.</p>
            </div>
          )}
        </div>

        {/* Explore Your Folders Section
        <div className="mb-12">
          <Card className="bg-gradient-to-r from-gray-100 to-orange-100 border-0 overflow-hidden">
            <div className="relative h-48">
              <div className="absolute inset-0 bg-gradient-to-r from-gray-500/20 to-orange-300/30"></div>
              <CardContent className="relative z-10 p-8 h-full flex flex-col justify-center">
                <h2 className="text-3xl font-bold text-white mb-4">Explore Your Folders</h2>
                <p className="text-white/90 mb-6 max-w-md">
                  Browse through your organized collection of academic papers. 
                  {!statsLoading && (
                    <span> Currently, you have {folderCount} folders containing {totalDocuments} articles.</span>
                  )}
                </p>
                <Button className="w-fit bg-blue-600 hover:bg-blue-700 text-white px-6">
                  View Folders
                </Button>
              </CardContent>
            </div>
          </Card>
        </div> */}

        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg text-gray-600">Folders</CardTitle>
            </CardHeader>
            <CardContent>
              {statsLoading ? (
                <div className="h-12 bg-gray-200 rounded animate-pulse"></div>
              ) : (
                <div className="text-4xl font-bold text-gray-900">{folderCount}</div>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg text-gray-600">Articles Archived</CardTitle>
            </CardHeader>
            <CardContent>
              {statsLoading ? (
                <div className="h-12 bg-gray-200 rounded animate-pulse"></div>
              ) : (
                <div className="text-4xl font-bold text-gray-900">{totalDocuments}</div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
