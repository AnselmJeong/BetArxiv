import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { FileText, Calendar, Users } from "lucide-react"
import { Document } from "@/types/api"
import { useState } from "react"
import { API_CONFIG } from "@/config/api"

interface DocumentCardProps {
  document: Document;
  index?: number;
  onClick?: () => void;
}

const backgroundColors = [
  "bg-gray-50",
  "bg-gray-100", 
  "bg-slate-50",
  "bg-slate-100",
  "bg-neutral-50",
  "bg-neutral-100"
];

export function DocumentCard({ document, index = 0, onClick }: DocumentCardProps) {
  const bgColor = backgroundColors[index % backgroundColors.length];
  const [imageError, setImageError] = useState(false);
  const [imageLoading, setImageLoading] = useState(true);

  const thumbnailUrl = `${API_CONFIG.baseUrl}/api/documents/${document.id}/thumbnail?width=480&height=320`;

  const handleImageLoad = () => {
    setImageLoading(false);
  };

  const handleImageError = () => {
    setImageError(true);
    setImageLoading(false);
  };

  // 썸네일이 있을 때는 흰색 배경, 없을 때는 색상 배경 사용
  const containerBgColor = (!imageError && document.url) ? "bg-white" : bgColor;

  return (
    <Card 
      className="overflow-hidden hover:shadow-lg transition-shadow cursor-pointer group"
      onClick={onClick}
    >
      <div className={`h-48 ${containerBgColor} flex items-center justify-center transition-all group-hover:scale-105 relative overflow-hidden`}>
        {!imageError && document.url ? (
          <>
            {imageLoading && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-16 h-20 bg-white/80 rounded shadow-sm flex items-center justify-center">
                  <FileText className="w-8 h-8 text-gray-400 animate-pulse" />
                </div>
              </div>
            )}
            <img
              src={thumbnailUrl}
              alt={`Thumbnail for ${document.title}`}
              className={`max-w-full max-h-full object-contain transition-opacity duration-300 border border-gray-200 ${
                imageLoading ? 'opacity-0' : 'opacity-100'
              }`}
              onLoad={handleImageLoad}
              onError={handleImageError}
            />
          </>
        ) : (
          <div className="w-16 h-20 bg-white/80 rounded shadow-sm flex items-center justify-center">
            <FileText className="w-8 h-8 text-gray-400" />
          </div>
        )}
      </div>
      <CardContent className="p-4">
        <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2 group-hover:text-blue-600 transition-colors">
          {document.title}
        </h3>
        
        <div className="flex items-center gap-1 text-sm text-blue-600 mb-2">
          <Users className="w-3 h-3" />
          <span className="line-clamp-1">
            {document.authors.slice(0, 2).join(", ")}
            {document.authors.length > 2 ? " et al." : ""}
          </span>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Calendar className="w-3 h-3" />
            <span>{document.publication_year}</span>
            {(document.volume || document.issue) && (
              <span className="text-gray-400">
                {document.volume && `Vol. ${document.volume}`}
                {document.volume && document.issue && ', '}
                {document.issue && `Issue ${document.issue}`}
              </span>
            )}
          </div>
          
          {document.journal_name && (
            <Badge variant="secondary" className="text-xs max-w-[120px] truncate">
              {document.journal_name}
            </Badge>
          )}
        </div>
        
        {document.folder_name && (
          <div className="mt-2">
            <Badge variant="outline" className="text-xs">
              {document.folder_name}
            </Badge>
          </div>
        )}
        
        {document.abstract && (
          <p className="text-xs text-gray-600 mt-2 line-clamp-2">
            {document.abstract}
          </p>
        )}
      </CardContent>
    </Card>
  );
} 