#!/usr/bin/env python3
"""
Quick verification script to check if BetArxiv test setup is working.
"""

import os
import sys
import asyncio


async def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")

    try:
        # Test basic dependencies
        import pytest
        import psycopg
        import pydantic

        print("✅ Basic dependencies imported successfully")

        # Test app modules
        from app.db import Database
        from app.models import DocumentCreate, Document

        print("✅ App modules imported successfully")

        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


async def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")

    try:
        from app.db import Database

        dsn = os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
        )
        db = Database(dsn)
        await db.connect()

        # Simple query test
        async with db.pool.cursor() as cur:
            await cur.execute("SELECT 1 as test")
            result = await cur.fetchone()
            assert result["test"] == 1

        await db.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def test_schema():
    """Test that documents table exists"""
    print("🔍 Testing database schema...")

    try:
        from app.db import Database

        dsn = os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
        )
        db = Database(dsn)
        await db.connect()

        # Check documents table
        async with db.pool.cursor() as cur:
            await cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'documents'
                )
            """)
            result = await cur.fetchone()
            assert result["exists"] is True

        await db.close()
        print("✅ Database schema verified")
        return True
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        return False


async def test_model_validation():
    """Test model validation"""
    print("🔍 Testing Pydantic models...")

    try:
        from app.models import DocumentCreate

        # Test basic document creation
        doc = DocumentCreate(title="Test Document", authors=["Test Author"])
        assert doc.title == "Test Document"
        assert doc.authors == ["Test Author"]
        assert doc.status == "pending"  # default

        print("✅ Model validation successful")
        return True
    except Exception as e:
        print(f"❌ Model validation failed: {e}")
        return False


async def main():
    """Run all verification tests"""
    print("🚀 BetArxiv Setup Verification")
    print("=" * 50)

    # Set environment
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = (
            "postgresql://postgres:postgres@localhost:5432/postgres"
        )

    tests = [test_imports, test_database_connection, test_schema, test_model_validation]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
        print()

    # Summary
    print("=" * 50)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ All {total} verification tests passed!")
        print("🎉 Ready to run the full test suite!")
        print("    Run: python test_runner.py")
    else:
        print(f"❌ {total - passed} out of {total} tests failed")
        print("🔧 Please fix the issues above before running tests")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
