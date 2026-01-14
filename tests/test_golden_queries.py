"""
End-to-end testing framework for natural language search golden queries.
"""

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path to import search modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.data import Document, NLSResult
from search import natural_language_search


@dataclass
class GoldenQuery:
    """Represents a golden query test case."""

    id: str
    query: str
    expected_result_type: str
    expected_files_contain: Optional[List[str]] = None
    expected_tools: Optional[List[str]] = None
    description: str = ""
    note: str = ""


@dataclass
class TestResult:
    """Represents the result of a single test."""

    query_id: str
    passed: bool
    errors: List[str]
    actual_result_type: Optional[str] = None
    actual_files: Optional[List[str]] = None
    actual_tools: Optional[List[str]] = None


class GoldenQueryTester:
    """Main testing class for golden queries."""

    def __init__(self, golden_queries_path: str = "tests/golden_queries.json"):
        """Initialize the tester with path to golden queries file."""
        self.golden_queries_path = Path(golden_queries_path)
        self.queries: List[GoldenQuery] = []
        self.results: List[TestResult] = []

    def load_queries(self) -> None:
        """Load golden queries from JSON file."""
        if not self.golden_queries_path.exists():
            raise FileNotFoundError(
                f"Golden queries file not found: {self.golden_queries_path}"
            )

        with open(self.golden_queries_path, "r") as f:
            queries_data = json.load(f)

        self.queries = [GoldenQuery(**query) for query in queries_data]
        print(f"Loaded {len(self.queries)} golden queries")

    def run_single_query(self, query: GoldenQuery) -> TestResult:
        """Run a single golden query and validate results."""
        print(f"\n🔍 Testing query: {query.id}")
        print(f"   Query: '{query.query}'")
        print(f"   Description: {query.description}")

        errors = []

        try:
            # Execute the search
            result, file_metas, tools_used = natural_language_search(query.query)

            # Extract actual results
            actual_result_type = result.result_type
            actual_files = result.files
            actual_tools = tools_used

            print(f"   Result type: {actual_result_type}")
            print(f"   Files found: {len(actual_files)}")
            print(f"   Tools used: {actual_tools}")

            # Validate result type
            if query.expected_result_type != actual_result_type:
                errors.append(
                    f"Expected result type '{query.expected_result_type}', "
                    f"got '{actual_result_type}'"
                )

            # Validate expected files are present
            if query.expected_files_contain:
                for expected_file in query.expected_files_contain:
                    if not any(expected_file in file for file in actual_files):
                        errors.append(
                            f"Expected file '{expected_file}' not found in results. "
                            f"Actual files: {actual_files}"
                        )

            # Validate expected tools were used
            if query.expected_tools:
                for expected_tool in query.expected_tools:
                    if expected_tool not in actual_tools:
                        errors.append(
                            f"Expected tool '{expected_tool}' was not used. "
                            f"Actual tools: {actual_tools}"
                        )

            return TestResult(
                query_id=query.id,
                passed=len(errors) == 0,
                errors=errors,
                actual_result_type=actual_result_type,
                actual_files=actual_files,
                actual_tools=actual_tools,
            )

        except Exception as e:
            errors.append(f"Exception occurred: {str(e)}")
            return TestResult(query_id=query.id, passed=False, errors=errors)

    def run_all_queries(self) -> None:
        """Run all golden queries and collect results."""
        print(f"🚀 Starting golden query tests...")
        print(f"=" * 60)

        self.results = []
        for query in self.queries:
            result = self.run_single_query(query)
            self.results.append(result)

            if result.passed:
                print(f"   ✅ PASSED")
            else:
                print(f"   ❌ FAILED")
                for error in result.errors:
                    print(f"      - {error}")

        self.print_summary()

    def print_summary(self) -> None:
        """Print test summary."""
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        print(f"\n{'=' * 60}")
        print(f"📊 TEST SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success rate: {passed/total*100:.1f}%")

        if total - passed > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.results:
                if not result.passed:
                    print(f"   - {result.query_id}")
                    for error in result.errors:
                        print(f"     └─ {error}")

    def run_specific_query(self, query_id: str) -> None:
        """Run a specific query by ID."""
        query = next((q for q in self.queries if q.id == query_id), None)
        if not query:
            print(f"❌ Query '{query_id}' not found")
            return

        result = self.run_single_query(query)
        self.results = [result]

        if result.passed:
            print(f"   ✅ PASSED")
        else:
            print(f"   ❌ FAILED")
            for error in result.errors:
                print(f"      - {error}")
        print("--------------------------------")


def main():
    """Main entry point for the test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Run golden query tests")
    parser.add_argument("--query-id", help="Run a specific query by ID", type=str)
    parser.add_argument(
        "--queries-file",
        help="Path to golden queries JSON file",
        default="tests/golden_queries.json",
    )

    args = parser.parse_args()

    # Check environment variables
    required_env_vars = ["OPENAI_API_KEY", "ELASTICSEARCH_HOST"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please set them in your .env file or environment")
        sys.exit(1)

    tester = GoldenQueryTester(args.queries_file)

    try:
        tester.load_queries()

        if args.query_id:
            tester.run_specific_query(args.query_id)
        else:
            tester.run_all_queries()

    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
