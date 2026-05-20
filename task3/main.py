"""Main Text-to-SQL pipeline orchestrator."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "task2"))

from database import DatabaseConnection, load_database_config
from executor import QueryExecutor
from sql_generator import SQLGenerator
from validator import SQLValidator


class TextToSQLPipeline:
    """Complete Text-to-SQL pipeline."""

    def __init__(self):
        self.db_config = load_database_config()
        self.db = DatabaseConnection(**self.db_config)
        self.executor = QueryExecutor(self.db, log_dir=Path(__file__).parent / "logs")
        self.generator = SQLGenerator()
        self.validator = SQLValidator()

    def process(
        self, question: str, decomposition: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a natural language question end-to-end.

        Args:
            question: Natural language question
            decomposition: Optional pre-computed decomposition

        Returns:
            Structured result with SQL, execution status, and results
        """
        # Step 1: Connect to database
        if not self.db.connect():
            return {
                "question": question,
                "status": "failure",
                "error": "Failed to connect to database",
                "sql": "",
                "result": [],
            }

        try:
            # Step 2: Use provided decomposition or create a simple one
            if not decomposition:
                decomposition = self._create_default_decomposition(question)

            # Step 3: Generate SQL from decomposition
            success, sql_query, gen_error = self.generator.generate_from_decomposition(
                decomposition
            )

            if not success:
                return {
                    "question": question,
                    "decomposition": decomposition,
                    "status": "failure",
                    "error": f"SQL generation failed: {gen_error}",
                    "sql": "",
                    "result": [],
                }

            # Step 4: Execute query with validation and retry
            result = self.executor.execute(question, sql_query, decomposition)

            return result

        finally:
            self.db.disconnect()

    def _create_default_decomposition(self, question: str) -> Dict[str, Any]:
        """Create a default decomposition for a question."""
        return {
            "Intent": f"Execute query for: {question}",
            "Tables": ["customers", "orders"],
            "Columns": ["*"],
            "Filters": "",
            "Joins": "",
            "Aggregations": "",
            "Ordering": "",
        }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Text-to-SQL Pipeline: Convert natural language to SQL and execute"
    )
    parser.add_argument("question", help="Natural language question")
    parser.add_argument(
        "--decomposition",
        type=str,
        help="Path to JSON file with decomposition or JSON string",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="result.json",
        help="Output file path for results",
    )

    args = parser.parse_args()

    # Load decomposition if provided
    decomposition = None
    if args.decomposition:
        try:
            # Try to load as file first
            decomp_path = Path(args.decomposition)
            if decomp_path.exists():
                with decomp_path.open("r") as f:
                    decomposition = json.load(f)
            else:
                # Try to parse as JSON string
                decomposition = json.loads(args.decomposition)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading decomposition: {e}")
            return 1

    # Run pipeline
    pipeline = TextToSQLPipeline()
    result = pipeline.process(args.question, decomposition)

    # Output results
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    # Save to file
    try:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\nResults saved to {output_path}")
    except Exception as e:
        print(f"Error saving results: {e}")
        return 1

    # Return success/failure code
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
