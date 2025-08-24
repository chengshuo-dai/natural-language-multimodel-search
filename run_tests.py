#!/usr/bin/env python3
"""
Convenience script to run golden query tests with different options.
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run golden query tests")
    parser.add_argument(
        "--query-id", 
        help="Run a specific query by ID",
        type=str
    )
    parser.add_argument(
        "--queries-file",
        help="Path to golden queries JSON file",
        default="tests/golden_queries.json"
    )
    parser.add_argument(
        "--test-index-name",
        help="Name of test index to use",
        default="nls_test"
    )
    
    args = parser.parse_args()
    
    test_script = Path(__file__).parent / "tests" / "test_golden_queries.py"
    
    # Build command
    cmd = [sys.executable, str(test_script)]
    if args.query_id:
        cmd.extend(["--query-id", args.query_id])
    if args.queries_file != "tests/golden_queries.json":
        cmd.extend(["--queries-file", args.queries_file])
    
    # Set environment for test index
    env = os.environ.copy()
    env["ELASTICSEARCH_INDEX_NAME"] = args.test_index_name
    
    try:
        result = subprocess.run(cmd, env=env, check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()