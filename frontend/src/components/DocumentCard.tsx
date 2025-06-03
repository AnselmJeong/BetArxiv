import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { FileText, Calendar, Users } from "lucide-react"
import { Document } from "@/types/api"

interface DocumentCardProps {
  document: Document;
  index?: number;
  onClick?: () => void;
}

const backgroundColors = [
  "bg-orange-100",
  "bg-amber-50", 
  "bg-orange-50",
  "bg-yellow-50",
  "bg-red-50",
  "bg-pink-50"
];

export function DocumentCard({ document, index = 0, onClick }: DocumentCardProps) {
  const bgColor = backgroundColors[index % backgroundColors.length];

  return (
    <Card 
      className="overflow-hidden hover:shadow-lg transition-shadow cursor-pointer group"
      onClick={onClick}
    >
      <div className={`h-32 ${bgColor} flex items-center justify-center transition-all group-hover:scale-105`}>
        <div className="w-16 h-20 bg-white/80 rounded shadow-sm flex items-center justify-center">
          <FileText className="w-8 h-8 text-orange-600" />
        </div>
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