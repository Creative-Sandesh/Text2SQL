"""SQL query validation and security checks."""
from __future__ import annotations

import re
from typing import Tuple


class SQLValidator:
    """Validate SQL queries for safety and correctness."""

    DANGEROUS_KEYWORDS = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
    ALLOWED_KEYWORDS = ["SELECT", "FROM", "WHERE", "JOIN", "ON", "GROUP", "BY", "ORDER", "LIMIT", "OFFSET"]

    @staticmethod
    def validate(query: str) -> Tuple[bool, str]:
        """
        Validate SQL query.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not query:
            return False, "Query is empty"

        query_upper = query.upper().strip()

        # Check if it's a SELECT query
        if not query_upper.startswith("SELECT"):
            return False, "Only SELECT queries are allowed"

        # Check for dangerous keywords
        for keyword in SQLValidator.DANGEROUS_KEYWORDS:
            if keyword in query_upper:
                return False, f"Dangerous keyword '{keyword}' is not allowed"

        # Check for SQL injection patterns
        if not SQLValidator._is_safe_from_injection(query):
            return False, "Potential SQL injection detected"

        # Check for unterminated strings
        if not SQLValidator._has_balanced_quotes(query):
            return False, "Unbalanced quotes in query"

        return True, ""

    @staticmethod
    def _is_safe_from_injection(query: str) -> bool:
        """Check for common SQL injection patterns."""
        injection_patterns = [
            r";\s*(DROP|DELETE|INSERT|UPDATE|ALTER)",
            r"'\s*OR\s*'1'\s*=\s*'1",
            r"--\s*(DROP|DELETE|INSERT)",
            r"/\*.*\*/",  # Comments
        ]

        for pattern in injection_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False

        return True

    @staticmethod
    def _has_balanced_quotes(query: str) -> bool:
        """Check if single and double quotes are balanced."""
        single_quotes = query.count("'") - query.count("\\'")
        double_quotes = query.count('"') - query.count('\\"')

        return single_quotes % 2 == 0 and double_quotes % 2 == 0

    @staticmethod
    def sanitize(query: str) -> str:
        """Sanitize query by removing unnecessary whitespace."""
        # Remove extra whitespace
        query = re.sub(r"\s+", " ", query)
        # Remove leading/trailing whitespace
        query = query.strip()
        return query
