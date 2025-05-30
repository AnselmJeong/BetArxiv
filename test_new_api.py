#!/usr/bin/env python3
"""
Test script for the new document-based API endpoints.
Run this after starting the FastAPI server to verify all endpoints work.
"""

import asyncio
import aiohttp
import json
import time
import os
from uuid import UUID
from pathlib import Path

BASE_URL = "http://localhost:8000"
DOCS_DIRECTORY = "docs"  # Directory containing PDFs to test with


async def wait_for_processing(session, initial_count=0, timeout=300):
    """Wait for document processing to complete"""
    print(f"⏳ Waiting for document processing to complete...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        # Check status
        async with session.get(f"{BASE_URL}/papers/status") as resp:
            if resp.status == 200:
                status = await resp.json()
                processed = status.get("processed", 0)
                pending = status.get("pending", 0)
                errors = status.get("errors", 0)
                total = status.get("total_documents", 0)

                print(
                    f"   Status: {processed} processed, {pending} pending, {errors} errors (total: {total})"
                )

                # If we have new documents and no pending ones, we're done
                if total > initial_count and pending == 0:
                    print(
                        f"✅ Processing completed! {processed} documents ready for testing."
                    )
                    return True

        await asyncio.sleep(5)  # Check every 5 seconds

    print(f"⚠️ Timeout waiting for processing to complete")
    return False


async def test_api():
    async with aiohttp.ClientSession() as session:
        print("🧪 Testing BetArxiv API with real docs directory...")
        print(f"📁 Using directory: {DOCS_DIRECTORY}")

        # Check if docs directory exists and has PDFs
        docs_path = Path(DOCS_DIRECTORY)
        if not docs_path.exists():
            print(f"❌ Directory {DOCS_DIRECTORY} not found!")
            return

        pdf_files = list(docs_path.rglob("*.pdf"))
        print(f"📄 Found {len(pdf_files)} PDF files in {DOCS_DIRECTORY}")

        if len(pdf_files) == 0:
            print(
                f"⚠️ No PDF files found in {DOCS_DIRECTORY}. Please add some PDFs to test."
            )
            return

        # Show directory structure
        subdirs = [d.name for d in docs_path.iterdir() if d.is_dir()]
        if subdirs:
            print(f"📂 Subdirectories: {', '.join(subdirs)}")

        # Test 0: Check initial status
        print(f"\n📊 Testing GET /papers/status (initial check)")
        initial_count = 0
        async with session.get(f"{BASE_URL}/papers/status") as resp:
            if resp.status == 200:
                status = await resp.json()
                initial_count = status.get("total_documents", 0)
                print(f"✅ Initial status: {initial_count} documents in database")
                print(
                    f"   Processed: {status.get('processed', 0)}, Pending: {status.get('pending', 0)}, Errors: {status.get('errors', 0)}"
                )
            else:
                print(f"❌ Failed to get status: {resp.status}")

        # Test 1: Ingest documents from docs directory
        print(f"\n📥 Testing POST /ingest (docs directory)")
        ingest_data = {
            "folder_name": DOCS_DIRECTORY,
            "clean_ingest": False,  # Don't re-process if already exists
        }

        async with session.post(f"{BASE_URL}/ingest", json=ingest_data) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"✅ Ingestion started: {data.get('message')}")

                # Wait for processing to complete
                processing_completed = await wait_for_processing(session, initial_count)
                if not processing_completed:
                    print("⚠️ Continuing with tests despite processing timeout...")
            else:
                print(f"❌ Ingestion failed with status {resp.status}")
                error_text = await resp.text()
                print(f"   Error: {error_text}")

        # Test 2: List documents
        print(f"\n📋 Testing POST /documents (list documents)")
        async with session.post(f"{BASE_URL}/documents?skip=0&limit=10") as resp:
            if resp.status == 200:
                data = await resp.json()
                documents = data.get("documents", [])
                print(
                    f"✅ Listed {len(documents)} documents (total: {data.get('total', 0)})"
                )

                document_id = None
                if documents:
                    document_id = documents[0]["id"]
                    print(f"   Sample document: '{documents[0]['title'][:60]}...'")
                    print(f"   Using document ID for detailed tests: {document_id}")

                    # Show folder distribution
                    folders = {}
                    for doc in documents:
                        folder = doc.get("folder_name", "Unknown")
                        folders[folder] = folders.get(folder, 0) + 1
                    print(f"   Folder distribution: {folders}")
                else:
                    print(f"⚠️ No documents found after ingestion!")
                    return
            else:
                print(f"❌ Failed with status {resp.status}")
                return

        # Test 3: List folders
        print(f"\n📁 Testing GET /folders")
        async with session.get(f"{BASE_URL}/folders") as resp:
            if resp.status == 200:
                data = await resp.json()
                folders = data.get("folders", [])
                print(f"✅ Found {len(folders)} folders:")
                for folder in folders:
                    print(
                        f"   📂 {folder['name']}: {folder['document_count']} documents"
                    )

                # Use the first folder for folder-specific tests
                test_folder = folders[0]["name"] if folders else None
            else:
                print(f"❌ Failed with status {resp.status}")
                test_folder = None

        # Test 4: Get specific document details
        if document_id:
            print(f"\n📄 Testing GET /documents/{document_id}")
            async with session.get(f"{BASE_URL}/documents/{document_id}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(
                        f"✅ Retrieved document: '{data.get('title', 'Unknown title')[:80]}...'"
                    )
                    print(f"   Authors: {len(data.get('authors', []))} author(s)")
                    print(f"   Keywords: {len(data.get('keywords', []))} keyword(s)")
                    print(f"   Status: {data.get('status', 'Unknown')}")
                else:
                    print(f"❌ Failed with status {resp.status}")

            # Test 5: Get document metadata
            print(f"\n📊 Testing GET /documents/{document_id}/metadata")
            async with session.get(
                f"{BASE_URL}/documents/{document_id}/metadata"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Retrieved metadata:")
                    print(f"   Title: '{data.get('title', 'N/A')[:60]}...'")
                    print(f"   Authors: {data.get('authors', [])}")
                    print(f"   Journal: {data.get('journal_name', 'N/A')}")
                    print(f"   Year: {data.get('year_of_publication', 'N/A')}")
                    print(f"   Keywords: {data.get('keywords', [])}")
                else:
                    print(f"❌ Failed with status {resp.status}")

            # Test 6: Get document summary
            print(f"\n📝 Testing GET /documents/{document_id}/summary")
            async with session.get(
                f"{BASE_URL}/documents/{document_id}/summary"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    summary_len = len(data.get("summary", ""))
                    print(f"✅ Retrieved summary: {summary_len} characters")
                    if data.get("distinction"):
                        print(f"   Has distinction: {len(data['distinction'])} chars")
                    if data.get("methodology"):
                        print(f"   Has methodology: {len(data['methodology'])} chars")
                else:
                    print(f"❌ Failed with status {resp.status}")

        # Test 7: Get all keywords with real data
        print(f"\n🏷️  Testing GET /keywords")
        params = {"limit": 20}
        async with session.get(f"{BASE_URL}/keywords", params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"✅ Found {data['total_unique_keywords']} unique keywords")
                print(f"   Showing top {min(data['returned_count'], 5)} keywords:")

                keywords_for_search = []
                for i, kw in enumerate(data["keywords"][:5], 1):
                    print(f"   {i}. '{kw['keyword']}' (used {kw['usage_count']} times)")
                    keywords_for_search.append(kw["keyword"])

                # If no keywords found, use fallback
                if not keywords_for_search:
                    keywords_for_search = [
                        "machine learning",
                        "artificial intelligence",
                        "neural networks",
                    ]
                    print(f"   Using fallback keywords: {keywords_for_search}")
            else:
                print(f"❌ Failed: {resp.status}")
                keywords_for_search = [
                    "machine learning",
                    "artificial intelligence",
                    "neural networks",
                ]

        # Test 8: Keyword-based search with real keywords
        if keywords_for_search:
            print(f"\n🔍 Testing POST /search/keywords (exact keyword search)")
            keyword_search_data = {
                "keywords": keywords_for_search[:2],  # Use first 2 real keywords
                "search_mode": "any",  # OR logic
                "exact_match": True,
                "case_sensitive": False,
                "limit": 10,
                "include_snippet": True,
            }

            async with session.post(
                f"{BASE_URL}/search/keywords", json=keyword_search_data
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Keyword search returned {data['total_results']} results")
                    print(f"   Query keywords: {data['query_keywords']}")

                    if data["results"]:
                        for i, result in enumerate(data["results"][:3], 1):
                            print(
                                f"   {i}. '{result['title'][:50]}...' (score: {result['match_score']:.2f})"
                            )
                            print(f"      Matched: {result['matched_keywords']}")
                else:
                    print(f"❌ Failed: {resp.status}")

        # Test 9: Text search with content from your docs
        print(f"\n🔍 Testing POST /retrieve/docs (text search)")
        # Use a more generic search term that might be in academic papers
        search_data = {"query": "analysis", "k": 5, "folder_name": test_folder}
        async with session.post(f"{BASE_URL}/retrieve/docs", json=search_data) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"✅ Text search returned {len(data.get('results', []))} results")
                if data.get("results"):
                    for i, result in enumerate(data["results"][:3], 1):
                        print(f"   {i}. '{result['title'][:50]}...'")
            else:
                print(f"❌ Failed: {resp.status}")

        # Test 10: Combined search with real data
        if keywords_for_search:
            print(f"\n🔍 Testing POST /search/combined (text + keywords)")
            combined_search_data = {
                "text_query": "method",
                "keywords": keywords_for_search[:2],
                "keyword_mode": "any",
                "exact_keyword_match": False,
                "limit": 8,
                "include_snippet": True,
            }

            async with session.post(
                f"{BASE_URL}/search/combined", json=combined_search_data
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(
                        f"✅ Combined search returned {data['total_results']} results"
                    )
                    print(f"   Query: {data['query']}")

                    if data["results"]:
                        for i, result in enumerate(data["results"][:3], 1):
                            print(f"   {i}. '{result['title'][:45]}...'")
                else:
                    print(f"❌ Failed: {resp.status}")

        # Test 11: Similar documents with real data
        if document_id:
            print(
                f"\n🔍 Testing GET /documents/{document_id}/similar (3:1 weighted similarity)"
            )
            params = {
                "limit": 5,
                "threshold": 0.3,  # Lower threshold for real data
                "title_weight": 0.75,
                "abstract_weight": 0.25,
                "include_snippet": True,
            }

            async with session.get(
                f"{BASE_URL}/documents/{document_id}/similar", params=params
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(
                        f"✅ Found {len(data['similar_documents'])} similar documents"
                    )
                    print(
                        f"   Weights: Title={data['query_weights']['title_weight']:.2f}, Abstract={data['query_weights']['abstract_weight']:.2f}"
                    )

                    if data["similar_documents"]:
                        for i, doc in enumerate(data["similar_documents"][:3], 1):
                            print(
                                f"   {i}. '{doc['title'][:50]}...' (score: {doc['similarity_score']:.3f})"
                            )
                else:
                    print(f"❌ Failed: {resp.status}")

        # Test 12: Keyword suggestions with real data
        if keywords_for_search:
            # Use partial keyword from real data
            partial_keyword = (
                keywords_for_search[0][:4]
                if keywords_for_search[0] and len(keywords_for_search[0]) > 4
                else "data"
            )
            print(f"\n💡 Testing GET /search/keywords/suggestions")
            params = {"q": partial_keyword, "limit": 10}
            async with session.get(
                f"{BASE_URL}/search/keywords/suggestions", params=params
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(
                        f"✅ Found {data['total_matches']} suggestions for '{data['query']}'"
                    )

                    for i, suggestion in enumerate(data["suggestions"][:5], 1):
                        print(
                            f"   {i}. '{suggestion['keyword']}' (used {suggestion['usage_count']} times)"
                        )
                else:
                    print(f"❌ Failed: {resp.status}")

        # Test 13: Final status check
        print(f"\n📊 Testing GET /papers/status (final check)")
        async with session.get(f"{BASE_URL}/papers/status") as resp:
            if resp.status == 200:
                status = await resp.json()
                print(f"✅ Final status:")
                print(f"   Total documents: {status.get('total_documents', 0)}")
                print(f"   Processed: {status.get('processed', 0)}")
                print(f"   Pending: {status.get('pending', 0)}")
                print(f"   Errors: {status.get('errors', 0)}")
            else:
                print(f"❌ Failed: {resp.status}")

        print(f"\n🎉 API testing completed successfully!")
        print(
            f"📊 Summary: Tested with {len(pdf_files)} PDF files from {DOCS_DIRECTORY}"
        )


if __name__ == "__main__":
    print("🚀 Starting BetArxiv API tests with real docs...")
    print("Make sure your FastAPI server is running on http://localhost:8000")
    print("And ensure Ollama is running for document processing")
    asyncio.run(test_api())
