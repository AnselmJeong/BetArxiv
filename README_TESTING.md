# BetArxiv Testing Documentation

This document describes the comprehensive test suite for the BetArxiv document management system.

## 📋 Overview

The test suite covers all major components of the BetArxiv system:

- **Database Operations**: CRUD operations, search, vector similarity
- **Document Processing**: PDF to markdown conversion, metadata extraction, LLM summarization
- **API Endpoints**: FastAPI routes and request/response handling
- **Data Models**: Pydantic model validation and serialization
- **Error Handling**: Edge cases and failure scenarios
- **Integration Testing**: End-to-end workflows

## 🚀 Quick Start

### Prerequisites

1. **PostgreSQL Database**: Running on `localhost:5432`
   ```bash
   # Using Homebrew (macOS)
   brew services start postgresql
   
   # Using Docker
   docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres
   ```

2. **Python Dependencies**:
   ```bash
   pip install -r requirements-test.txt
   ```

### Running Tests

**Simple Test Run:**
```bash
python test_runner.py
```

**With Coverage Report:**
```bash
python test_runner.py --coverage
```

**Verbose Output:**
```bash
python test_runner.py --verbose
```

**Specific Test Types:**
```bash
# Unit tests only
python test_runner.py --type unit

# Database tests only  
python test_runner.py --type db

# Integration tests only
python test_runner.py --type integration
```

**Direct pytest:**
```bash
pytest test_betarxiv.py -v
```

## 🧪 Test Structure

### Test Classes

#### `TestDatabaseSetup`
- Database connection verification
- Schema validation
- Table existence checks

#### `TestDocumentModels`
- Pydantic model validation
- Serialization/deserialization
- Field validation and defaults

#### `TestDatabaseOperations`
- Document CRUD operations
- Search functionality
- Pagination and filtering
- Status management
- Folder operations

#### `TestPaperProcessor`
- PDF to markdown conversion
- Metadata extraction via LLM
- Summary generation
- Embedding creation
- Full processing pipeline

#### `TestIngestScript`
- Bulk PDF ingestion
- File discovery
- Duplicate handling
- Error recovery

#### `TestErrorHandling`
- Database connection failures
- Invalid data handling
- API error responses
- Processing failures

#### `TestVectorOperations`
- Vector similarity search
- Keyword-based search
- Combined search strategies
- Embedding operations

## 🗄️ Database Schema Testing

The tests verify the complete database schema including:

```sql
documents table columns:
├── id (UUID, Primary Key)
├── title (TEXT, NOT NULL)
├── authors (TEXT[], NOT NULL)
├── journal_name (TEXT)
├── publication_year (INTEGER)
├── abstract (TEXT)
├── keywords (TEXT[])
├── markdown (TEXT)
├── url (TEXT) -- File path
├── folder_name (TEXT)
├── summary (TEXT)
├── distinction (TEXT)
├── methodology (TEXT)
├── results (TEXT)
├── implications (TEXT)
├── title_embedding (vector(768))
├── abstract_embedding (vector(768))
├── status (VARCHAR(20))
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)
```

## 🔧 Test Configuration

### Environment Variables

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/postgres"
export DIRECTORY="docs"  # Base directory for PDF files
```

### pytest Configuration

The test suite uses `pytest.ini` for configuration:
- Async test support via `pytest-asyncio`
- Coverage reporting
- Custom markers for test categorization
- Warning suppression

### Fixtures

Key fixtures provided:
- `db`: Database connection with automatic cleanup
- `sample_document`: Pre-configured test document
- `mock_ollama_client`: Mocked LLM client
- `temp_pdf_directory`: Temporary directory with test PDFs

## 📊 Coverage

The test suite aims for comprehensive coverage of:

- **Database Layer**: 95%+ coverage of all DB operations
- **Models**: 100% coverage of Pydantic models
- **Processing**: 90%+ coverage of PDF processing pipeline
- **API**: 85%+ coverage of FastAPI endpoints
- **Error Handling**: All major error paths tested

Generate coverage report:
```bash
python test_runner.py --coverage
open htmlcov/index.html  # View detailed coverage report
```

## 🐛 Debugging Tests

### Common Issues

1. **Database Connection Failed**
   ```
   ❌ Database connection failed: connection refused
   ```
   **Solution**: Ensure PostgreSQL is running on port 5432

2. **Missing Dependencies**
   ```
   ❌ Missing dependencies: pytest, psycopg
   ```
   **Solution**: `pip install -r requirements-test.txt`

3. **Schema Mismatch**
   ```
   AssertionError: expected columns not found
   ```
   **Solution**: Run schema migration: `psql -d postgres -f app/schema.sql`

### Running Specific Tests

```bash
# Single test class
pytest test_betarxiv.py::TestDatabaseOperations -v

# Single test method
pytest test_betarxiv.py::TestDatabaseOperations::test_insert_and_get_document -v

# Tests matching pattern
pytest test_betarxiv.py -k "test_search" -v
```

### Debug Mode

```bash
pytest test_betarxiv.py -v -s --pdb  # Drop into debugger on failure
```

## 🚀 Continuous Integration

For CI/CD pipelines, use:

```bash
# CI-friendly test run
python test_runner.py --skip-checks --coverage
```

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements-test.txt
      - run: python test_runner.py --coverage
```

## 📈 Performance Testing

The test suite includes performance considerations:

- **Bulk Operations**: Tests inserting multiple documents
- **Search Performance**: Tests with large datasets
- **Vector Operations**: Similarity search with many embeddings
- **Memory Usage**: Monitoring for memory leaks in long-running tests

## 🔐 Security Testing

Security aspects covered:

- **SQL Injection**: Parameterized queries only
- **Input Validation**: Malformed data handling
- **Access Control**: Database permission testing
- **Data Sanitization**: XSS prevention in text fields

## 📝 Contributing

When adding new features:

1. **Write tests first** (TDD approach)
2. **Maintain coverage** above 90%
3. **Add integration tests** for new endpoints
4. **Update fixtures** for new data models
5. **Document test cases** in docstrings

### Test Naming Convention

```python
async def test_[action]_[condition]_[expected_result](self, fixtures):
    """Test description explaining what is being tested"""
    # Arrange
    # Act  
    # Assert
    # Cleanup
```

## 🏃‍♂️ Running Tests in Development

During development, use these commands:

```bash
# Quick test during development
pytest test_betarxiv.py::TestDatabaseOperations -v --tb=short

# Watch mode (requires pytest-watch)
ptw test_betarxiv.py

# Test specific functionality
pytest test_betarxiv.py -k "search" -v
```

## 📋 Test Checklist

Before deploying:

- [ ] All tests pass
- [ ] Coverage > 90%
- [ ] No database connection leaks
- [ ] Memory usage stable
- [ ] Error handling tested
- [ ] Integration tests pass
- [ ] Performance acceptable

## 🆘 Getting Help

If you encounter issues:

1. Check the [Common Issues](#common-issues) section
2. Run tests with `--verbose` for detailed output
3. Check database connectivity with `psql -h localhost -U postgres`
4. Verify Python dependencies with `pip list`
5. Review logs in test output

For additional help, refer to the main project documentation or open an issue. 