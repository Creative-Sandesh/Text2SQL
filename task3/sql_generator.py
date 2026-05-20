"""SQL generation from structured decomposition."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

import google.genai as genai

from config import GEMINI_API_KEY, MODEL_NAME, MAX_TOKENS


class SQLGenerator:
    """Generate SQL queries from structured decomposition."""

    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = MODEL_NAME
        self.max_tokens = MAX_TOKENS

    def generate_from_decomposition(self, decomposition: dict[str, Any]) -> tuple[bool, str, str]:
        """
        Generate SQL from structured decomposition.

        Args:
            decomposition: Dictionary with Intent, Tables, Columns, Filters, Joins

        Returns:
            Tuple of (success, sql_query, error_message)
        """
        prompt = self._build_generation_prompt(decomposition)

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=genai.types.GenerateContentConfig(maxOutputTokens=self.max_tokens),
            )

            sql_query = response.text.strip()

            # Try to extract SQL from markdown code blocks if needed
            if "```sql" in sql_query:
                start = sql_query.find("```sql") + 6
                end = sql_query.find("```", start)
                if end > start:
                    sql_query = sql_query[start:end].strip()

            if not sql_query:
                return False, "", "Empty SQL generated"

            return True, sql_query, ""
        except Exception as e:
            return False, "", str(e)

    def fix_query(self, sql_query: str, error_message: str, decomposition: dict[str, Any]) -> tuple[bool, str, str]:
        """
        Attempt to fix a failed SQL query.

        Args:
            sql_query: Original failing SQL
            error_message: Database error message
            decomposition: Original decomposition

        Returns:
            Tuple of (success, fixed_sql_query, error_message)
        """
        prompt = f"""
You are a SQL expert. Fix the following SQL query based on the database error.

Original SQL:
{sql_query}

Database Error:
{error_message}

Decomposition Context:
{json.dumps(decomposition, indent=2)}

Provide ONLY the corrected SQL query. No explanation needed. Return valid PostgreSQL syntax only.
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=genai.types.GenerateContentConfig(maxOutputTokens=self.max_tokens),
            )

            fixed_sql = response.text.strip()

            # Extract SQL from markdown if needed
            if "```sql" in fixed_sql:
                start = fixed_sql.find("```sql") + 6
                end = fixed_sql.find("```", start)
                if end > start:
                    fixed_sql = fixed_sql[start:end].strip()

            if not fixed_sql:
                return False, "", "Empty SQL generated"

            return True, fixed_sql, ""
        except Exception as e:
            return False, "", str(e)

    def _build_generation_prompt(self, decomposition: dict[str, Any]) -> str:
        """Build prompt for SQL generation from decomposition."""
        return f"""
You are a SQL expert. Generate a PostgreSQL SELECT query based on the following decomposition:

Intent: {decomposition.get('Intent', '')}
Tables: {', '.join(decomposition.get('Tables', []))}
Columns: {', '.join(decomposition.get('Columns', []))}
Filters: {decomposition.get('Filters', 'None')}
Joins: {decomposition.get('Joins', 'None')}
Aggregations: {decomposition.get('Aggregations', 'None')}
Ordering: {decomposition.get('Ordering', 'None')}

Generate a valid PostgreSQL SELECT query. Return ONLY the SQL, no explanation.
Ensure column names and table names match the database schema exactly.
Use proper aliases for tables if multiple tables are involved.
"""
