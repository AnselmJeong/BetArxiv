#!/usr/bin/env python3
"""
Test runner for BetArxiv application.

This script sets up the test environment and runs the comprehensive test suite.
"""

import os
import sys
import subprocess
import asyncio
import warnings
from pathlib import Path

# Suppress all warnings at the Python level
warnings.filterwarnings("ignore")


def check_database_connection():
    """Check if PostgreSQL database is accessible"""
    try:
        import psycopg

        dsn = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
        conn = psycopg.connect(dsn)
        conn.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Please ensure PostgreSQL is running on localhost:5432")
        print("And that the database 'postgres' exists with user 'postgres'")
        return False


def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = ["pytest", "pytest-asyncio", "psycopg", "pydantic", "fastapi"]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing dependencies: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements-test.txt")
        return False

    print("✅ All dependencies available")
    return True


def setup_test_environment():
    """Setup test environment variables"""
    # Set default database URL if not provided
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/postgres"

    # Set test directory
    if not os.getenv("DIRECTORY"):
        os.environ["DIRECTORY"] = "docs"

    print(f"📊 Database URL: {os.environ['DATABASE_URL']}")
    print(f"📁 Test directory: {os.environ['DIRECTORY']}")


def run_tests(test_type="all", verbose=False, coverage=False):
    """Run the test suite"""
    cmd = ["uv", "run", "pytest"]

    if verbose:
        cmd.extend(["-v", "-s"])

    if coverage:
        # Check if pytest-cov is available
        try:
            import pytest_cov

            cmd.extend(["--cov=app", "--cov-report=term-missing", "--cov-report=html:htmlcov"])
        except ImportError:
            print("⚠️  pytest-cov not available, running without coverage")

    # Test selection
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "db":
        cmd.extend(["-m", "db"])

    # Add the test file
    cmd.append("test_betarxiv.py")

    print(f"🧪 Running tests: {' '.join(cmd)}")
    return subprocess.run(cmd)


def main():
    """Main test runner function"""
    print("🚀 BetArxiv Test Runner")
    print("=" * 50)

    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="Run BetArxiv tests")
    parser.add_argument(
        "--type", choices=["all", "unit", "integration", "db"], default="all", help="Type of tests to run"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    parser.add_argument("--skip-checks", action="store_true", help="Skip dependency and database checks")

    args = parser.parse_args()

    # Setup environment
    setup_test_environment()

    if not args.skip_checks:
        # Check dependencies
        if not check_dependencies():
            print("\n💡 Try running: pip install -r requirements-test.txt")
            sys.exit(1)

        # Check database connection
        if not check_database_connection():
            print("\n💡 Ensure PostgreSQL is running and accessible")
            print("   You can start PostgreSQL with: brew services start postgresql")
            print("   Or use Docker: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres")
            sys.exit(1)

    print("\n🔧 Environment setup complete")
    print("=" * 50)

    # Run tests
    result = run_tests(test_type=args.type, verbose=args.verbose, coverage=args.coverage)

    # Print results
    print("\n" + "=" * 50)
    if result.returncode == 0:
        print("✅ All tests passed!")
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
