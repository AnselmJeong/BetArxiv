#!/usr/bin/env python3
"""
Test script with real arXiv and DOI identifiers.
"""

import asyncio
import logging
from app.api_clients import IdentifierExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_real_arxiv():
    """Test with a real arXiv paper."""
    print("🧪 Testing real arXiv paper...")

    # Real arXiv paper text
    sample_text = """
    This paper can be found at arXiv:1706.03762v5 [cs.CL] 6 Dec 2017
    
    # Attention Is All You Need
    
    **Abstract**: The dominant sequence transduction models are based on complex recurrent or 
    convolutional neural networks that include an encoder and a decoder.
    """

    extractor = IdentifierExtractor()

    try:
        metadata = await extractor.fetch_metadata_by_identifier(sample_text)
        if metadata:
            print("✅ Real arXiv metadata retrieved successfully:")
            print(f"   Title: {metadata.get('title', 'N/A')}")
            print(
                f"   Authors: {metadata.get('authors', [])[:3]}..."
            )  # Show first 3 authors
            print(f"   Journal: {metadata.get('journal_name', 'N/A')}")
            print(f"   Year: {metadata.get('publication_year', 'N/A')}")
            print(f"   arXiv ID: {metadata.get('arxiv_id', 'N/A')}")
        else:
            print("❌ Failed to retrieve arXiv metadata")

    except Exception as e:
        print(f"❌ Real arXiv test failed: {e}")

    finally:
        await extractor.close()


async def test_real_doi():
    """Test with a real DOI paper."""
    print("\n🧪 Testing real DOI paper...")

    # Real DOI paper text with correct format
    sample_text = """
    Citation: Nature. 2013;500(7463):453-457. 
    DOI: 10.1038/nature12373
    
    This work demonstrates quantum teleportation...
    """

    extractor = IdentifierExtractor()

    try:
        metadata = await extractor.fetch_metadata_by_identifier(sample_text)
        if metadata:
            print("✅ Real DOI metadata retrieved successfully:")
            print(f"   Title: {metadata.get('title', 'N/A')}")
            print(
                f"   Authors: {metadata.get('authors', [])[:3]}..."
            )  # Show first 3 authors
            print(f"   Journal: {metadata.get('journal_name', 'N/A')}")
            print(f"   Year: {metadata.get('publication_year', 'N/A')}")
            print(f"   Volume: {metadata.get('volume', 'N/A')}")
            print(f"   Issue: {metadata.get('issue', 'N/A')}")
            print(f"   DOI: {metadata.get('doi', 'N/A')}")
        else:
            print("❌ Failed to retrieve DOI metadata")

    except Exception as e:
        print(f"❌ Real DOI test failed: {e}")

    finally:
        await extractor.close()


async def test_real_doi_simple():
    """Test with a simpler DOI paper."""
    print("\n🧪 Testing simple DOI paper...")

    # Try a well-known DOI
    sample_text = """
    This paper is published at DOI: 10.1038/nature
    
    Simple test of DOI extraction...
    """

    extractor = IdentifierExtractor()

    try:
        # Just test identifier extraction first
        arxiv_id, doi = extractor.extract_identifiers(sample_text)
        print(f"Extracted DOI: {doi}")

        if doi:
            print(f"📡 Attempting to fetch metadata for DOI: {doi}")
            metadata = await extractor.crossref_client.fetch_metadata(doi)
            if metadata:
                print("✅ Simple DOI metadata retrieved successfully:")
                print(f"   Title: {metadata.get('title', 'N/A')}")
                print(f"   Journal: {metadata.get('journal_name', 'N/A')}")
                print(f"   Year: {metadata.get('publication_year', 'N/A')}")
            else:
                print("❌ Failed to retrieve simple DOI metadata")
        else:
            print("❌ No DOI extracted")

    except Exception as e:
        print(f"❌ Simple DOI test failed: {e}")

    finally:
        await extractor.close()


async def main():
    """Run all tests."""
    print("🚀 Starting real identifier tests...\n")

    await test_real_arxiv()
    await test_real_doi()
    await test_real_doi_simple()

    print("\n✅ All real identifier tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
