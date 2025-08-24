# Claude Code Configuration

## Python Configuration
- **Environment**: nlp (conda environment)
- **Setup**: Always run `conda activate nlp` before executing any Python commands
- **Python Binary**: `/opt/anaconda3/bin/python` (after activation)

## Project Commands
```bash
# Always activate environment first
conda activate nlp

# Run tests
python run_tests.py

# Setup test environment
python setup_test_environment.py

# Run indexing
python processor/processor.py --folder_path sample_folder

# Start application
python -m chainlit run app.py
```

## Test Commands
```bash
# Always activate environment first
conda activate nlp

# Setup test environment with separate index (recommended)
python setup_test_environment.py

# Setup and run tests immediately
python setup_test_environment.py --run-tests

# Force reindex when adding new files
python setup_test_environment.py --overwrite-index

# Run all golden query tests (uses nls_test index by default)
python run_tests.py

# Run specific test
python run_tests.py --query-id search_pdf_files

# Use custom test index
python run_tests.py --test-index-name my_custom_test_index
```