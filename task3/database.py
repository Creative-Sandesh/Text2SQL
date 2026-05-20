"""Database connection and utilities for PostgreSQL."""
from __future__ import annotations

import os
from typing import Any, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor


class DatabaseConnection:
    """Manages PostgreSQL database connections."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "classicmodels",
        user: str = "postgres",
        password: str = "password",
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection: Optional[psycopg2.extensions.connection] = None

    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
            )
            return True
        except psycopg2.Error as e:
            print(f"Database connection error: {e}")
            return False

    def disconnect(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()

    def execute_query(self, query: str) -> tuple[bool, List[dict[str, Any]], str]:
        """
        Execute a SELECT query and return results.

        Returns:
            Tuple of (success, results, error_message)
        """
        if not self.connection:
            return False, [], "Database not connected"

        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return True, results, ""
        except psycopg2.Error as e:
            error_msg = str(e)
            return False, [], error_msg

    def get_schema_info(self, table_name: Optional[str] = None) -> dict[str, Any]:
        """Get database schema information."""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)

            if table_name:
                # Get columns for specific table
                query = f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
                """
            else:
                # Get all tables and their columns
                query = """
                SELECT table_name, column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
                """

            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return {"columns": results}
        except psycopg2.Error as e:
            return {"error": str(e)}


def load_database_config() -> dict[str, Any]:
    """Load database configuration from environment variables."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "classicmodels"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "password"),
    }
