#!/usr/bin/env python3
"""
Setup script to prepare the environment for running golden query tests.
This script handles Elasticsearch indexing and environment validation.
"""

import os
import subprocess
import sys
from pathlib import Path

import rich
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

# Load environment variables
load_dotenv()


def check_environment() -> bool:
    """Check if required environment variables are set."""
    required_vars = ["OPENAI_API_KEY"]
    optional_vars = {
        "ELASTICSEARCH_HOST": "localhost",
        "ELASTICSEARCH_PORT": "9200",
        "ELASTICSEARCH_INDEX_NAME": "nls",
    }

    missing_vars = []

    # Check required variables
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    # Set defaults for optional variables
    for var, default in optional_vars.items():
        if not os.getenv(var):
            os.environ[var] = default
            rich.print(f"[yellow]Set {var} to default value: {default}[/yellow]")

    if missing_vars:
        rich.print(
            f"[red]❌ Missing required environment variables: {missing_vars}[/red]"
        )
        rich.print("[yellow]Please set them in your .env file or environment[/yellow]")
        return False

    rich.print("[green]✅ Environment variables are properly configured[/green]")
    return True


def check_elasticsearch() -> bool:
    """Check if Elasticsearch is running and accessible."""
    try:
        host = os.getenv("ELASTICSEARCH_HOST", "localhost")
        port = os.getenv("ELASTICSEARCH_PORT", "9200")
        es_url = f"http://{host}:{port}/"

        es = Elasticsearch(es_url)

        # Test connection
        if not es.ping():
            rich.print(f"[red]❌ Cannot connect to Elasticsearch at {es_url}[/red]")
            return False

        rich.print(f"[green]✅ Connected to Elasticsearch at {es_url}[/green]")
        return True

    except Exception as e:
        rich.print(f"[red]❌ Elasticsearch error: {e}[/red]")
        return False


def check_test_index(index_name: str, folder_path: str) -> bool:
    """Check if test index exists and is up to date with folder contents."""
    try:
        host = os.getenv("ELASTICSEARCH_HOST", "localhost")
        port = os.getenv("ELASTICSEARCH_PORT", "9200")
        es_url = f"http://{host}:{port}/"
        es = Elasticsearch(es_url)

        # Check if index exists
        if not es.indices.exists(index=index_name):
            rich.print(f"[yellow]⚠️  Test index '{index_name}' does not exist[/yellow]")
            return False

        # Get documents from index
        try:
            result = es.search(
                index=index_name,
                body={
                    "query": {"match_all": {}},
                    "size": 1000,
                    "_source": ["filename"],
                },
                timeout="30s",
            )
            indexed_files = {
                hit["_source"]["filename"] for hit in result["hits"]["hits"]
            }
            rich.print(
                f"[green]✅ Test index '{index_name}' exists with {len(indexed_files)} documents[/green]"
            )
        except Exception as e:
            rich.print(f"[yellow]⚠️  Could not retrieve indexed filenames: {e}[/yellow]")
            return False

        # Get supported files in folder
        sys.path.insert(0, os.getcwd())  # Add current directory to path
        try:
            from processor.handlers import (
                AudioFileHandler,
                ImageFileHandler,
                PDFFileHandler,
                TextFileHandler,
                VideoFileHandler,
            )

            # Build extension-to-handler mapping from handlers (same as processor.py)
            extension_to_handler = {}
            for handler in [
                TextFileHandler,
                ImageFileHandler,
                PDFFileHandler,
                AudioFileHandler,
                VideoFileHandler,
            ]:
                for ext in handler.get_supported_extensions():
                    extension_to_handler[ext] = handler
        except ImportError:
            rich.print(
                "[yellow]⚠️  Could not import handlers, assuming all common files are supported[/yellow]"
            )
            # Fallback: assume common extensions are supported
            supported_extensions = {
                ".pdf",
                ".txt",
                ".jpg",
                ".jpeg",
                ".png",
                ".mp3",
                ".mp4",
            }
            folder_files = set()
            for root, _, files in os.walk(folder_path):
                for file in files:
                    extension = os.path.splitext(file)[1].lower()
                    if extension in supported_extensions:
                        folder_files.add(file)
            rich.print(
                f"[blue]Found {len(folder_files)} files with common extensions in '{folder_path}'[/blue]"
            )
            return False  # Force reindex when we can't properly check

        folder_files = set()
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                extension = os.path.splitext(file)[1].lower()
                if extension in extension_to_handler:
                    folder_files.add(file)

        rich.print(
            f"[blue]Found {len(folder_files)} supported files in '{folder_path}'[/blue]"
        )

        # Compare file sets
        missing_from_index = folder_files - indexed_files
        extra_in_index = indexed_files - folder_files

        if missing_from_index:
            rich.print(
                f"[yellow]⚠️  Files in folder but not indexed: {sorted(missing_from_index)}[/yellow]"
            )
            return False

        if extra_in_index:
            rich.print(
                f"[yellow]⚠️  Files indexed but not in folder: {sorted(extra_in_index)}[/yellow]"
            )
            return False

        rich.print("[green]✅ Test index is up to date with folder contents[/green]")
        return True

    except Exception as e:
        rich.print(f"[red]❌ Error checking test index: {e}[/red]")
        return False


def run_indexing(
    folder_path: str = "sample_folder",
    index_name: str = "nls_test",
    overwrite: bool = False,
) -> bool:
    """Run the indexing process using the processor with specified index."""
    try:
        rich.print(
            f"[blue]🔄 Starting indexing process for {folder_path} into index '{index_name}'...[/blue]"
        )

        # Check if folder exists
        if not Path(folder_path).exists():
            rich.print(f"[red]❌ Folder '{folder_path}' does not exist[/red]")
            return False

        # Build environment with proper Python path and index name
        env = os.environ.copy()
        current_dir = os.getcwd()
        env["PYTHONPATH"] = current_dir + ":" + env.get("PYTHONPATH", "")
        env["ELASTICSEARCH_INDEX_NAME"] = index_name

        # Simple approach: run processor as module from project root
        cmd = [
            sys.executable,
            "-m",
            "processor.processor",
            "--folder-path",
            folder_path,
        ]

        if overwrite:
            cmd.append("--overwrite")

        # Run indexing from project root directory
        result = subprocess.run(cmd, env=env, cwd=current_dir, check=False)

        if result.returncode == 0:
            rich.print(
                f"[green]✅ Indexing completed successfully into '{index_name}'[/green]"
            )
            return True
        else:
            rich.print(
                f"[red]❌ Indexing failed with exit code {result.returncode}[/red]"
            )
            return False

    except Exception as e:
        rich.print(f"[red]❌ Error running indexing: {e}[/red]")
        return False


def main():
    """Main setup process."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Setup test environment for golden queries"
    )
    parser.add_argument(
        "--index-folder",
        default="sample_folder",
        help="Folder to index (default: sample_folder)",
    )
    parser.add_argument(
        "--test-index-name",
        default="nls_test",
        help="Name for the test index (default: nls_test)",
    )
    parser.add_argument(
        "--overwrite-index", action="store_true", help="Overwrite existing test index"
    )
    parser.add_argument(
        "--skip-indexing",
        action="store_true",
        help="Skip indexing step (assume data is already indexed)",
    )
    parser.add_argument(
        "--run-tests", action="store_true", help="Run tests after setup"
    )

    args = parser.parse_args()

    rich.print(
        "[bold blue]🔧 Setting up test environment for golden queries[/bold blue]"
    )
    rich.print("=" * 60)
    rich.print(f"[blue]Using test index: '{args.test_index_name}'[/blue]")
    rich.print(f"[blue]Data folder: '{args.index_folder}'[/blue]")

    # Step 1: Check environment
    rich.print("\n[bold]Step 1: Checking environment variables[/bold]")
    if not check_environment():
        sys.exit(1)

    # Step 2: Check Elasticsearch connection
    rich.print("\n[bold]Step 2: Checking Elasticsearch connection[/bold]")
    if not check_elasticsearch():
        rich.print("[red]❌ Setup failed - Cannot connect to Elasticsearch[/red]")
        sys.exit(1)

    # Step 3: Check and update test index
    if not args.skip_indexing:
        rich.print(
            f"\n[bold]Step 3: Checking test index '{args.test_index_name}'[/bold]"
        )
        index_ready = check_test_index(args.test_index_name, args.index_folder)

        if not index_ready or args.overwrite_index:
            rich.print(
                f"\n[bold]Step 3b: Indexing data from '{args.index_folder}' into '{args.test_index_name}'[/bold]"
            )
            if not run_indexing(
                args.index_folder, args.test_index_name, args.overwrite_index
            ):
                rich.print("[red]❌ Setup failed during indexing[/red]")
                sys.exit(1)
        else:
            rich.print("\n[bold]Step 3b: Test index is up to date[/bold]")
    else:
        rich.print("\n[bold]Step 3: Skipping indexing (--skip-indexing flag)[/bold]")

    # Final validation
    rich.print(
        f"\n[bold]Step 4: Final validation of test index '{args.test_index_name}'[/bold]"
    )
    if not check_test_index(args.test_index_name, args.index_folder):
        rich.print("[red]❌ Setup failed - Test index not ready[/red]")
        sys.exit(1)

    rich.print("\n[bold green]🎉 Test environment is ready![/bold green]")
    rich.print(
        f"\nTest index '{args.test_index_name}' is set up and ready for testing."
    )
    rich.print("\nYou can now run tests with:")
    rich.print("  [cyan]python run_tests.py[/cyan]")
    rich.print("  [cyan]python run_tests.py --query-id search_pdf_files[/cyan]")

    # Optionally run tests
    if args.run_tests:
        rich.print("\n[bold]Running golden query tests...[/bold]")
        # Set the test index for the test run
        env = os.environ.copy()
        env["ELASTICSEARCH_INDEX_NAME"] = args.test_index_name
        result = subprocess.run([sys.executable, "run_tests.py"], env=env, check=False)
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
