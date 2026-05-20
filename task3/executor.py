"""Query execution with error handling and retry logic."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from database import DatabaseConnection
from sql_generator import SQLGenerator
from validator import SQLValidator


class QueryExecutor:
    """Execute SQL queries with validation, error handling, and retry logic."""

    MAX_RETRIES = 1

    def __init__(self, db_connection: DatabaseConnection, log_dir: Path = Path("logs")):
        self.db = db_connection
        self.generator = SQLGenerator()
        self.validator = SQLValidator()
        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)

    def execute(
        self, question: str, sql_query: str, decomposition: dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute SQL query with validation and retry logic.

        Args:
            question: Original natural language question
            sql_query: SQL query to execute
            decomposition: Structured decomposition

        Returns:
            Structured result with status, SQL, and results
        """
        result = {
            "question": question,
            "decomposition": decomposition,
            "sql": sql_query,
            "result": [],
            "status": "failure",
            "error": "",
            "retried": False,
            "timestamp": datetime.now().isoformat(),
        }

        # Step 1: Validate query
        is_valid, validation_error = self.validator.validate(sql_query)
        if not is_valid:
            result["error"] = f"Validation failed: {validation_error}"
            self._log_execution(result)
            return result

        # Step 2: Sanitize query
        sanitized_query = self.validator.sanitize(sql_query)

        # Step 3: Execute query
        success, results, exec_error = self.db.execute_query(sanitized_query)

        if success:
            result["result"] = results
            result["status"] = "success"
            self._log_execution(result)
            return result

        # Step 4: Retry logic
        if result["status"] != "success" and not result["retried"]:
            result["retried"] = True
            result["error"] = f"Initial execution failed: {exec_error}"

            # Try to fix the query
            fix_success, fixed_sql, fix_error = self.generator.fix_query(
                sanitized_query, exec_error, decomposition
            )

            if fix_success:
                # Validate fixed query
                is_valid_fixed, validation_error_fixed = self.validator.validate(fixed_sql)

                if is_valid_fixed:
                    fixed_sanitized = self.validator.sanitize(fixed_sql)
                    retry_success, retry_results, retry_error = self.db.execute_query(
                        fixed_sanitized
                    )

                    if retry_success:
                        result["result"] = retry_results
                        result["status"] = "success"
                        result["sql"] = fixed_sql
                        result["error"] = f"Fixed after error: {exec_error}"
                        self._log_execution(result)
                        return result
                    else:
                        result["error"] = f"Retry failed: {retry_error}"
                else:
                    result["error"] = f"Fixed query validation failed: {validation_error_fixed}"
            else:
                result["error"] = f"Could not generate fix: {fix_error}"

        self._log_execution(result)
        return result

    def _log_execution(self, result: Dict[str, Any]) -> None:
        """Log query execution to file."""
        log_file = self.log_dir / f"execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            # Convert any non-serializable objects
            log_data = {
                "question": result["question"],
                "decomposition": result["decomposition"],
                "sql": result["sql"],
                "result": result["result"] if isinstance(result["result"], list) else str(result["result"]),
                "status": result["status"],
                "error": result["error"],
                "retried": result["retried"],
                "timestamp": result["timestamp"],
            }

            with log_file.open("w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"Failed to log execution: {e}")
