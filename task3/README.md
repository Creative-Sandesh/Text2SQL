# Task 3: Text-to-SQL Pipeline and Query Execution System

## Overview

This system converts natural language questions into SQL queries and executes them against a PostgreSQL database. It demonstrates a complete AI-powered database assistant pipeline.

## Architecture

```
Natural Language Question
    ↓
Structured Decomposition (from Task 2)
    ↓
SQL Generation (using Gemini API)
    ↓
SQL Validation (security & safety checks)
    ↓
Query Execution
    ↓
Error Handling & Retry (max 1 retry)
    ↓
Structured Output (JSON)
```

## Project Structure

```
task3/
├── database.py          # PostgreSQL connection and utilities
├── sql_generator.py     # Convert decomposition to SQL via LLM
├── validator.py         # SQL validation and security checks
├── executor.py          # Query execution with error handling
├── config.py            # Configuration (from Task 2)
├── main.py              # Main pipeline orchestrator
├── logs/                # Query execution logs
├── prompts/             # LLM prompts (for reference)
└── README.md            # This file
```

## Setup

### 1. Install Dependencies

```bash
pip install psycopg2-binary google-genai python-dotenv
```

### 2. Configure Database

Update `.env` file in the workspace root:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=classicmodels
DB_USER=postgres
DB_PASSWORD=your_password
```

### 3. Database Setup

Create the `classicmodels` database or use an existing PostgreSQL database with tables:
- customers
- orders
- orderdetails
- products
- etc.

## Usage

### Command Line

```bash
# Simple usage with default decomposition
python main.py "Show all orders from Germany"

# With custom decomposition (JSON file)
python main.py "Show all orders" --decomposition decomposition.json

# With inline decomposition
python main.py "Show all orders" --decomposition '{"Intent": "List orders", "Tables": ["orders"], ...}'

# Save results to file
python main.py "Show all orders" --output results.json
```

### Python API

```python
from main import TextToSQLPipeline

pipeline = TextToSQLPipeline()

# Without decomposition (uses default)
result = pipeline.process("Show all products")

# With decomposition
decomposition = {
    "Intent": "Retrieve products",
    "Tables": ["products"],
    "Columns": ["productCode", "productName", "price"],
    "Filters": "",
    "Joins": "",
}
result = pipeline.process("Show all products", decomposition)

print(result)
```

## Component Details

### database.py

**DatabaseConnection Class:**
- `connect()` - Establish PostgreSQL connection
- `disconnect()` - Close connection
- `execute_query(query)` - Execute SELECT query, returns (success, results, error)
- `get_schema_info(table_name)` - Retrieve schema information

### sql_generator.py

**SQLGenerator Class:**
- `generate_from_decomposition(decomposition)` - Convert decomposition to SQL
- `fix_query(sql, error_message, decomposition)` - Attempt to fix failed queries

Uses Gemini API for intelligent SQL generation and error recovery.

### validator.py

**SQLValidator Class:**
- `validate(query)` - Check query safety and correctness
- Blocks: DROP, DELETE, INSERT, UPDATE, ALTER, CREATE, TRUNCATE
- Checks: injection patterns, quote balancing, SELECT-only enforcement
- `sanitize(query)` - Clean up query formatting

### executor.py

**QueryExecutor Class:**
- `execute(question, sql_query, decomposition)` - Execute with validation and retry
- Validates query before execution
- Retries up to 1 time on failure (with LLM-suggested fixes)
- Logs all executions to `logs/` directory

### main.py

**TextToSQLPipeline Class:**
- `process(question, decomposition)` - Run complete pipeline
- Orchestrates all components
- Returns structured result with SQL, status, and results

## Output Format

### Success Response

```json
{
  "question": "Show all orders from Germany",
  "decomposition": {
    "Intent": "Retrieve orders",
    "Tables": ["orders", "customers"],
    "Columns": ["orderNumber", "customerName"],
    "Filters": "country = 'Germany'",
    "Joins": "..."
  },
  "sql": "SELECT o.orderNumber, c.customerName FROM orders o JOIN customers c ...",
  "result": [
    {"orderNumber": 10101, "customerName": "Customer 1"},
    ...
  ],
  "status": "success",
  "error": "",
  "retried": false,
  "timestamp": "2025-01-15T10:30:00.123456"
}
```

### Failure Response

```json
{
  "question": "...",
  "decomposition": {...},
  "sql": "...",
  "result": [],
  "status": "failure",
  "error": "Column 'xyz' does not exist",
  "retried": true,
  "timestamp": "..."
}
```

## Query Validation Rules

### ✅ Allowed

- SELECT queries
- JOINs (INNER, LEFT, RIGHT, FULL)
- WHERE clauses
- GROUP BY, ORDER BY
- LIMIT, OFFSET
- Aggregates: COUNT, SUM, AVG, MAX, MIN

### ❌ Blocked

- DELETE, DROP, INSERT, UPDATE, ALTER, CREATE
- Semicolons followed by dangerous keywords
- SQL injection patterns
- Comments (/* */ or --)
- Unbalanced quotes

## Error Handling

### Execution Flow

1. **Validation Failure** → Return error immediately (no retry)
2. **Execution Failure** → Log error
3. **Retry Attempt** → Use Gemini to fix query
4. **Retry Validation** → Validate fixed query
5. **Retry Execution** → Execute fixed query
6. **Final Failure** → Return error with attempted fixes

### Common Errors & Solutions

| Error | Solution |
|-------|----------|
| Column not found | LLM generates correct column names |
| Missing JOIN | LLM adds required joins |
| Syntax error | LLM corrects PostgreSQL syntax |
| Type mismatch | LLM adds proper type casting |

## Logging

All query executions are logged to `logs/execution_*.json`:

- Question
- Decomposition used
- Generated SQL
- Execution status
- Results (or error message)
- Retry information
- Timestamp

## Limitations

- Maximum 1 retry per query
- Only SELECT queries allowed
- Requires pre-computed decomposition or uses default
- Database must be PostgreSQL
- Results limited by query performance

## Future Enhancements

- [ ] Support for UPDATE/INSERT with safety guardrails
- [ ] Multi-step query execution (CTEs, subqueries)
- [ ] Query optimization suggestions
- [ ] Schema learning and auto-completion
- [ ] Result formatting and visualization
- [ ] Query caching and deduplication
- [ ] Natural language result explanation

## Troubleshooting

### Database Connection Failed

```
Check:
- PostgreSQL server is running
- Database credentials in .env are correct
- Database exists and is accessible
- Firewall allows connections to port 5432
```

### API Key Invalid

```
Check:
- GEMINI_API_KEY is set in .env
- API key is valid and not expired
- API key has permissions for generativelanguage.googleapis.com
```

### No Results

```
Check:
- Table names match database schema exactly
- Column names are correct
- Filters/WHERE clause are valid
- Check logs/ folder for error details
```

## Example Usage

```bash
# Test the pipeline
python main.py "List all customers from Germany"

# With custom decomposition
cat > decomposition.json << EOF
{
  "Intent": "Retrieve all customers from Germany",
  "Tables": ["customers"],
  "Columns": ["customerNumber", "customerName", "country"],
  "Filters": "country = 'Germany'",
  "Joins": "None"
}
EOF

python main.py "List all customers from Germany" --decomposition decomposition.json --output results.json
```

## References

- [Task 2: Query Decomposition](../task2/README.md)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Google Generative AI Python SDK](https://github.com/googleapis/python-genai)
