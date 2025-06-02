'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Document } from '@/types/api';

// Mock data for the papers library
const mockPapers: Document[] = [
  {
    id: '1',
    title: 'The Impact of AI on Education',
    authors: ['Dr. Emily Carter', 'Prof. David Lee'],
    journal_name: 'Journal of Educational Technology',
    publication_year: 2023,
    abstract: 'This paper explores the transformative impact of artificial intelligence on modern education systems.',
    folder_name: 'Education',
  },
  {
    id: '2',
    title: 'Advancements in Renewable Energy Technologies',
    authors: ['Dr. Robert Green', 'Dr. Sarah White'],
    journal_name: 'Energy Research Journal',
    publication_year: 2022,
    abstract: 'A comprehensive review of recent developments in renewable energy technologies.',
    folder_name: 'Energy',
  },
  {
    id: '3',
    title: 'Exploring the Human Microbiome',
    authors: ['Dr. Michael Brown', 'Dr. Olivia Taylor'],
    journal_name: 'Microbiology Today',
    publication_year: 2021,
    abstract: 'An in-depth analysis of the human microbiome and its implications for health.',
    folder_name: 'Biology',
  },
  {
    id: '4',
    title: 'The Future of Space Exploration',
    authors: ['Dr. Jessica Clark', 'Dr. Thomas Harris'],
    journal_name: 'Space Science Review',
    publication_year: 2020,
    abstract: 'Examining the future prospects and challenges of space exploration.',
    folder_name: 'Astronomy',
  },
  {
    id: '5',
    title: 'Understanding Climate Change',
    authors: ['Dr. Laura Adams', 'Dr. Kevin Scott'],
    journal_name: 'Environmental Science Journal',
    publication_year: 2019,
    abstract: 'A comprehensive study on climate change and its environmental impacts.',
    folder_name: 'Environment',
  },
  {
    id: '6',
    title: 'The Role of Genetics in Disease',
    authors: ['Dr. Christopher Evans', 'Dr. Amanda Wilson'],
    journal_name: 'Genetics and Health',
    publication_year: 2018,
    abstract: 'Investigating the role of genetic factors in disease development.',
    folder_name: 'Medicine',
  },
  {
    id: '7',
    title: 'Innovations in Medical Imaging',
    authors: ['Dr. Jennifer Hall', 'Dr. Richard Turner'],
    journal_name: 'Medical Imaging Advances',
    publication_year: 2017,
    abstract: 'Recent innovations and technological advances in medical imaging.',
    folder_name: 'Medicine',
  },
  {
    id: '8',
    title: 'The Evolution of Social Media',
    authors: ['Dr. Matthew Baker', 'Dr. Sophia Lewis'],
    journal_name: 'Social Media Studies',
    publication_year: 2016,
    abstract: 'Analyzing the evolution and impact of social media platforms.',
    folder_name: 'Technology',
  },
  {
    id: '9',
    title: 'Cybersecurity in the Digital Age',
    authors: ['Dr. Daniel Parker', 'Dr. Chloe Martin'],
    journal_name: 'Journal of Cybersecurity',
    publication_year: 2015,
    abstract: 'Addressing cybersecurity challenges in our increasingly digital world.',
    folder_name: 'Technology',
  },
  {
    id: '10',
    title: 'The Ethics of Artificial Intelligence',
    authors: ['Dr. Rebecca Hill', 'Dr. Andrew Cooper'],
    journal_name: 'AI Ethics Review',
    publication_year: 2014,
    abstract: 'Exploring the ethical implications of artificial intelligence development.',
    folder_name: 'Ethics',
  },
];

export default function PapersPage() {
  const router = useRouter();
  const [papers, setPapers] = useState<Document[]>(mockPapers);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFolder, setSelectedFolder] = useState<string>('all-folders');
  const [selectedYear, setSelectedYear] = useState<string>('all-years');
  const [selectedJournal, setSelectedJournal] = useState<string>('all-journals');
  const [selectedTags, setSelectedTags] = useState<string>('all-tags');

  // Extract unique values for filters
  const folders = Array.from(new Set(mockPapers.map(paper => paper.folder_name))).sort();
  const years = Array.from(new Set(mockPapers.map(paper => paper.publication_year))).sort((a, b) => b - a);
  const journals = Array.from(new Set(mockPapers.map(paper => paper.journal_name))).sort();

  // Filter papers based on search and filters
  const filteredPapers = papers.filter(paper => {
    const matchesSearch = searchQuery === '' || 
      paper.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      paper.authors.some(author => author.toLowerCase().includes(searchQuery.toLowerCase())) ||
      paper.journal_name.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesFolder = selectedFolder === 'all-folders' || paper.folder_name === selectedFolder;
    const matchesYear = selectedYear === 'all-years' || paper.publication_year.toString() === selectedYear;
    const matchesJournal = selectedJournal === 'all-journals' || paper.journal_name === selectedJournal;

    return matchesSearch && matchesFolder && matchesYear && matchesJournal;
  });

  const handlePaperClick = (paperId: string) => {
    router.push(`/papers/${paperId}`);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 h-full flex flex-col">
      {/* Header */}
      <div className="mb-8 flex-shrink-0">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Library</h1>
        <p className="text-gray-600">Explore and manage your collection of academic papers.</p>
      </div>

      {/* Search Bar */}
      <div className="mb-6 flex-shrink-0">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            placeholder="Search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6 flex-shrink-0">
        <Select value={selectedFolder} onValueChange={setSelectedFolder}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="Folder" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all-folders">All Folders</SelectItem>
            {folders.map(folder => (
              <SelectItem key={folder} value={folder}>{folder}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={selectedYear} onValueChange={setSelectedYear}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="Year" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all-years">All Years</SelectItem>
            {years.map(year => (
              <SelectItem key={year} value={year.toString()}>{year}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={selectedJournal} onValueChange={setSelectedJournal}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Journal" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all-journals">All Journals</SelectItem>
            {journals.map(journal => (
              <SelectItem key={journal} value={journal}>{journal}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={selectedTags} onValueChange={setSelectedTags}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="Tags" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all-tags">All Tags</SelectItem>
            <SelectItem value="ai">AI</SelectItem>
            <SelectItem value="energy">Energy</SelectItem>
            <SelectItem value="biology">Biology</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Papers Table - Now fills remaining space */}
      <div className="bg-white rounded-lg border shadow-sm flex-1 flex flex-col min-h-0">
        <div className="flex-1 overflow-auto">
          <Table>
            <TableHeader className="sticky top-0 bg-white z-10">
              <TableRow className="border-b">
                <TableHead className="w-[40%] font-semibold text-gray-900">Title</TableHead>
                <TableHead className="w-[25%] font-semibold text-gray-900">Authors</TableHead>
                <TableHead className="w-[25%] font-semibold text-gray-900">Journal</TableHead>
                <TableHead className="w-[10%] font-semibold text-gray-900">Year</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredPapers.map((paper) => (
                <TableRow 
                  key={paper.id} 
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => handlePaperClick(paper.id)}
                >
                  <TableCell className="font-medium text-gray-900">
                    {paper.title}
                  </TableCell>
                  <TableCell className="text-blue-600">
                    {paper.authors.join(', ')}
                  </TableCell>
                  <TableCell className="text-blue-600">
                    {paper.journal_name}
                  </TableCell>
                  <TableCell className="text-gray-600">
                    {paper.publication_year}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        
        {/* Results count - Fixed at bottom of table */}
        <div className="p-4 border-t bg-gray-50 text-sm text-gray-600 flex-shrink-0">
          Showing {filteredPapers.length} of {papers.length} papers
        </div>
      </div>
    </div>
  );
} 