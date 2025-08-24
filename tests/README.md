# End-to-End Testing for Natural Language Search

This directory contains the end-to-end testing framework for validating the natural language search system against a set of golden queries.

## Overview

The testing framework validates that:
- Queries are routed to the correct tools (semantic search, Q&A, time-ranged search)
- Expected files are returned in search results
- The system returns the correct result type (search vs answer)

## Files

- `test_golden_queries.py` - Main test runner
- `golden_queries.json` - Test cases with expected results
- `README.md` - This documentation

## Golden Query Format

Each golden query test case includes:

```json
{
  "id": "unique_test_id",
  "query": "natural language query to test",
  "expected_result_type": "search|answer",
  "expected_files_contain": ["list", "of", "expected", "files"],
  "expected_tools": ["list", "of", "expected", "tools"],
  "description": "Human readable description",
  "note": "Optional notes about the test"
}
```

## Running Tests

### Prerequisites

The easiest way to set up the test environment is to use the setup script:

```bash
# Automatic setup with separate test index (recommended)
python setup_test_environment.py

# Setup with custom folder and test index name
python setup_test_environment.py --index-folder /path/to/your/data --test-index-name my_test_index

# Setup and run tests immediately  
python setup_test_environment.py --run-tests

# Force reindex (useful when adding new files)
python setup_test_environment.py --overwrite-index
```

#### Manual Setup (if needed)

1. **Environment Setup**: Ensure these environment variables are set:
   ```bash
   OPENAI_API_KEY=your_openai_key
   ELASTICSEARCH_HOST=localhost  # optional, defaults to localhost
   ELASTICSEARCH_PORT=9200       # optional, defaults to 9200
   ELASTICSEARCH_INDEX_NAME=nls  # optional, defaults to nls
   ```

2. **Start Elasticsearch**: 
   ```bash
   # Using Docker
   docker run -d --name elasticsearch -p 9200:9200 -e "discovery.type=single-node" elasticsearch:8.11.0
   
   # Or install locally and start the service
   ```

3. **Index your data**:
   ```bash
   python processor/processor.py --folder_path sample_folder
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Test Execution

#### Run All Tests
```bash
# Using default test index (nls_test)
python run_tests.py

# Using specific test index
python run_tests.py --test-index-name my_test_index

# Or directly
python tests/test_golden_queries.py
```

#### Run Specific Test
```bash
# Run a single test by ID
python run_tests.py --query-id search_pdf_files

# With specific test index
python run_tests.py --query-id search_pdf_files --test-index-name my_test_index
```

#### Custom Golden Queries File
```bash
python run_tests.py --queries-file path/to/custom_queries.json --test-index-name my_test_index
```

### Example Output

```
🚀 Starting golden query tests...
============================================================

🔍 Testing query: search_pdf_files
   Query: 'pdf files about setup'
   Description: Test semantic search for PDF files
   Result type: search
   Files found: 1
   Tools used: ['get_semantic_search_results']
   ✅ PASSED

🔍 Testing query: question_about_steve_jobs
   Query: 'What did Steve Jobs say about connecting the dots?'
   Description: Test question answering from text files
   Result type: answer
   Files found: 1
   Tools used: ['get_answers_for_question']
   ✅ PASSED

============================================================
📊 TEST SUMMARY
============================================================
Total tests: 16
Passed: 14
Failed: 2
Success rate: 87.5%
```

## Test Categories

### Semantic Search Tests
- File type searches (PDF, images, audio, video)
- Content-based searches
- Subfolder file searches
- Empty result searches

### Question Answering Tests  
- Questions with question marks
- "How to" format questions
- "What is" format questions
- "Explain" format questions
- "Tell me about" format questions

### Time-Ranged Search Tests
- "Today" searches
- "Last week" searches
- Relative time queries

## Adding New Test Cases

1. **Add to golden_queries.json**:
   ```json
   {
     "id": "my_new_test",
     "query": "your test query",
     "expected_result_type": "search",
     "expected_files_contain": ["expected_file.pdf"],
     "expected_tools": ["get_semantic_search_results"],
     "description": "Description of what this tests"
   }
   ```

2. **Test the new query**:
   ```bash
   python run_tests.py --query-id my_new_test
   ```

3. **Run full suite** to ensure no regressions:
   ```bash
   python run_tests.py
   ```

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   ```
   ❌ Missing required environment variables: ['OPENAI_API_KEY']
   ```
   Solution: Set the required environment variables in your `.env` file

2. **Elasticsearch Connection Issues**
   ```
   Exception occurred: Connection error
   ```
   Solution: Ensure Elasticsearch is running and accessible

3. **File Not Found in Results**
   ```
   Expected file 'example.pdf' not found in results
   ```
   Solution: Check if the file exists in your indexed data or update the expected files

4. **Wrong Tool Used**
   ```
   Expected tool 'get_answers_for_question' was not used
   ```
   Solution: Review the query format - questions should use question words or punctuation

### Test Data Requirements

The tests assume the following sample files are indexed:
- `Setup Dev Environment.pdf`
- `Steve Jobs 2005 Stanford.txt` 
- `DSC_1843.JPG`
- `Introducing iPhone 15 Pro.mp3`
- `Deer video.mp4`
- `receipt.jpg`
- `photo.JPG`
- `big table.pdf`
- `yorkie-icon.png`

Make sure these files are present in your `sample_folder/` and indexed in Elasticsearch.

## Continuous Integration

For CI/CD integration, the test runner returns appropriate exit codes:
- `0`: All tests passed
- `1`: Some tests failed or error occurred

Example GitHub Actions integration:
```yaml
- name: Run Golden Query Tests
  run: python run_tests.py
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    ELASTICSEARCH_HOST: localhost
```