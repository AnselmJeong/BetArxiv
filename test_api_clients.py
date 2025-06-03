#!/usr/bin/env python3
"""
Test script for the new API clients (arXiv and CrossRef).
"""

import asyncio
import logging
from app.api_clients import IdentifierExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_arxiv_extraction():
    """Test arXiv ID extraction and metadata retrieval."""
    print("🧪 Testing arXiv API...")

    # Sample text with arXiv ID
    sample_text = """
    This paper is available on arXiv:2502.04780v1. The research demonstrates...
    """

    extractor = IdentifierExtractor()

    try:
        # Test identifier extraction
        arxiv_id, doi = extractor.extract_identifiers(sample_text)
        print(f"Extracted arXiv ID: {arxiv_id}")
        print(f"Extracted DOI: {doi}")

        if arxiv_id:
            # Test metadata retrieval
            metadata = await extractor.arxiv_client.fetch_metadata(arxiv_id)
            if metadata:
                print("✅ arXiv metadata retrieved successfully:")
                print(f"   Title: {metadata.get('title', 'N/A')}")
                print(f"   Authors: {metadata.get('authors', [])}")
                print(f"   Journal: {metadata.get('journal_name', 'N/A')}")
                print(f"   Year: {metadata.get('publication_year', 'N/A')}")
            else:
                print("❌ Failed to retrieve arXiv metadata")

    except Exception as e:
        print(f"❌ arXiv test failed: {e}")

    finally:
        await extractor.close()


async def test_doi_extraction():
    """Test DOI extraction and metadata retrieval."""
    print("\n🧪 Testing CrossRef API...")

    # Sample text with DOI
    sample_text = """
    This study was published at https://doi.org/10.1038/nature12373
    """

    extractor = IdentifierExtractor()

    try:
        # Test identifier extraction
        arxiv_id, doi = extractor.extract_identifiers(sample_text)
        print(f"Extracted arXiv ID: {arxiv_id}")
        print(f"Extracted DOI: {doi}")

        if doi:
            # Test metadata retrieval
            metadata = await extractor.crossref_client.fetch_metadata(doi)
            if metadata:
                print("✅ CrossRef metadata retrieved successfully:")
                print(f"   Title: {metadata.get('title', 'N/A')}")
                print(f"   Authors: {metadata.get('authors', [])}")
                print(f"   Journal: {metadata.get('journal_name', 'N/A')}")
                print(f"   Year: {metadata.get('publication_year', 'N/A')}")
                print(f"   Volume: {metadata.get('volume', 'N/A')}")
                print(f"   Issue: {metadata.get('issue', 'N/A')}")
            else:
                print("❌ Failed to retrieve CrossRef metadata")

    except Exception as e:
        print(f"❌ CrossRef test failed: {e}")

    finally:
        await extractor.close()


async def test_combined_extraction():
    """Test combined identifier extraction."""
    print("\n🧪 Testing combined identifier extraction...")

    # Sample text with both identifiers
    sample_text = """
    This is a preprint available on arXiv:2401.12345v2. 
    The published version can be found at DOI: 10.1038/s41586-024-07123-4
    """

    extractor = IdentifierExtractor()

    try:
        metadata = await extractor.fetch_metadata_by_identifier(sample_text)
        if metadata:
            print("✅ Combined metadata extraction successful:")
            print(f"   Title: {metadata.get('title', 'N/A')}")
            print(f"   Authors: {metadata.get('authors', [])}")
            print(f"   Journal: {metadata.get('journal_name', 'N/A')}")
            print(f"   DOI: {metadata.get('doi', 'N/A')}")
            print(f"   arXiv ID: {metadata.get('arxiv_id', 'N/A')}")
        else:
            print("❌ Combined extraction failed")

    except Exception as e:
        print(f"❌ Combined test failed: {e}")

    finally:
        await extractor.close()


async def main():
    """Run all tests."""
    print("🚀 Starting API client tests...\n")

    await test_arxiv_extraction()
    await test_doi_extraction()
    await test_combined_extraction()

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
