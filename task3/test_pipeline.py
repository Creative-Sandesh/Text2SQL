"""Test script for Text-to-SQL Pipeline."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add task3 to path
sys.path.insert(0, str(Path(__file__).parent))

from main import TextToSQLPipeline


def test_pipeline():
    """Run pipeline tests."""
    print("=" * 60)
    print("Text-to-SQL Pipeline Test")
    print("=" * 60)

    pipeline = TextToSQLPipeline()

    # Test 1: Simple SELECT with default decomposition
    print("\n[Test 1] Simple question with default decomposition")
    print("-" * 60)
    question1 = "Show me all customers"
    result1 = pipeline.process(question1)
    print(f"Question: {question1}")
    print(f"Status: {result1['status']}")
    print(f"SQL: {result1['sql']}")
    if result1["status"] == "failure":
        print(f"Error: {result1['error']}")

    # Test 2: With custom decomposition
    print("\n[Test 2] Question with custom decomposition")
    print("-" * 60)
    question2 = "Show all customers from Germany"
    decomposition2 = {
        "Intent": "Retrieve customers from Germany",
        "Tables": ["customers"],
        "Columns": ["customerNumber", "customerName", "city", "country"],
        "Filters": "country = 'Germany'",
        "Joins": "None",
        "Aggregations": "None",
        "Ordering": "ORDER BY customerName",
    }
    result2 = pipeline.process(question2, decomposition2)
    print(f"Question: {question2}")
    print(f"Status: {result2['status']}")
    print(f"SQL: {result2['sql']}")
    if result2["status"] == "failure":
        print(f"Error: {result2['error']}")
    if result2["status"] == "success":
        print(f"Results: {len(result2['result'])} rows returned")
        if result2["result"]:
            print(f"First result: {result2['result'][0]}")

    # Test 3: Aggregation query
    print("\n[Test 3] Aggregation query")
    print("-" * 60)
    question3 = "Count the number of customers per country"
    decomposition3 = {
        "Intent": "Count customers grouped by country",
        "Tables": ["customers"],
        "Columns": ["country", "COUNT(*)"],
        "Filters": "None",
        "Joins": "None",
        "Aggregations": "GROUP BY country",
        "Ordering": "ORDER BY COUNT(*) DESC",
    }
    result3 = pipeline.process(question3, decomposition3)
    print(f"Question: {question3}")
    print(f"Status: {result3['status']}")
    print(f"SQL: {result3['sql']}")
    if result3["status"] == "failure":
        print(f"Error: {result3['error']}")
    if result3["status"] == "success":
        print(f"Results: {len(result3['result'])} rows returned")

    # Test 4: JOIN query
    print("\n[Test 4] JOIN query")
    print("-" * 60)
    question4 = "Get orders with customer names and details"
    decomposition4 = {
        "Intent": "Retrieve orders with associated customer information",
        "Tables": ["orders", "customers"],
        "Columns": ["orderNumber", "orderDate", "customerName", "status"],
        "Filters": "None",
        "Joins": "customers.customerNumber = orders.customerNumber",
        "Aggregations": "None",
        "Ordering": "ORDER BY orderDate DESC",
    }
    result4 = pipeline.process(question4, decomposition4)
    print(f"Question: {question4}")
    print(f"Status: {result4['status']}")
    print(f"SQL: {result4['sql']}")
    if result4["status"] == "failure":
        print(f"Error: {result4['error']}")
    if result4["status"] == "success":
        print(f"Results: {len(result4['result'])} rows returned")

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    test_pipeline()
