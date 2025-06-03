#!/usr/bin/env python3
"""
Test script for title-based arXiv search functionality.
"""

import asyncio
import logging
from app.api_clients import IdentifierExtractor, ArxivSearchClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_title_search():
    """Test arXiv title search with a well-known paper."""
    print("🧪 Testing arXiv title search...")

    # Test with the famous "Attention Is All You Need" paper
    title = "Attention Is All You Need"

    search_client = ArxivSearchClient()

    try:
        metadata = search_client.search_by_title(title)
        if metadata:
            print("✅ Title search successful:")
            print(f"   Title: {metadata.get('title', 'N/A')}")
            print(f"   Authors: {metadata.get('authors', [])[:3]}...")
            print(f"   arXiv ID: {metadata.get('arxiv_id', 'N/A')}")
            print(f"   Year: {metadata.get('publication_year', 'N/A')}")
            print(f"   Similarity: {metadata.get('similarity_score', 'N/A'):.2f}")
        else:
            print("❌ Title search failed")

    except Exception as e:
        print(f"❌ Title search test failed: {e}")

    finally:
        await search_client.close()


async def test_comprehensive_extraction():
    """Test the comprehensive metadata extraction."""
    print("\n🧪 Testing comprehensive metadata extraction...")

    # Simulate markdown without identifiers but with a clear title
    markdown_text = """
# Attention Is All You Need

## Abstract

The dominant sequence transduction models are based on complex recurrent or 
convolutional neural networks that include an encoder and a decoder. The best 
performing models also connect the encoder and decoder through an attention mechanism.

## Introduction

Recurrent neural networks, long short-term memory and gated recurrent neural networks
in particular, have been firmly established as state of the art approaches in sequence
modeling and transduction problems such as language modeling and machine translation.
    """

    extractor = IdentifierExtractor()

    try:
        # Test the comprehensive approach
        metadata = await extractor.fetch_metadata_comprehensive(markdown_text)
        if metadata:
            print("✅ Comprehensive extraction successful:")
            print(f"   Title: {metadata.get('title', 'N/A')}")
            print(f"   Authors: {metadata.get('authors', [])[:3]}...")
            print(f"   arXiv ID: {metadata.get('arxiv_id', 'N/A')}")
            print(f"   Year: {metadata.get('publication_year', 'N/A')}")
            print(f"   Journal: {metadata.get('journal_name', 'N/A')}")
            if "similarity_score" in metadata:
                print(f"   Similarity: {metadata.get('similarity_score', 'N/A'):.2f}")
        else:
            print("❌ Comprehensive extraction failed")

    except Exception as e:
        print(f"❌ Comprehensive extraction test failed: {e}")

    finally:
        await extractor.close()


async def test_with_partial_title():
    """Test with a partial or modified title."""
    print("\n🧪 Testing with partial title...")

    # Test with a partial title
    partial_title = "Attention Is All You Need Transformer"

    search_client = ArxivSearchClient()

    try:
        metadata = search_client.search_by_title(partial_title)
        if metadata:
            print("✅ Partial title search successful:")
            print(f"   Original query: {partial_title}")
            print(f"   Found title: {metadata.get('title', 'N/A')}")
            print(f"   Similarity: {metadata.get('similarity_score', 'N/A'):.2f}")
        else:
            print("❌ Partial title search failed")

    except Exception as e:
        print(f"❌ Partial title search failed: {e}")

    finally:
        await search_client.close()


async def main():
    """Run all tests."""
    print("🚀 Starting title-based search tests...\n")

    await test_title_search()
    await test_comprehensive_extraction()
    await test_with_partial_title()

    print("\n✅ All title search tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
