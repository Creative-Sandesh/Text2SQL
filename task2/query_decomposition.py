import csv
import json
from pathlib import Path
from typing import Any, List, Optional

import google.genai as genai
from google.genai import types
from config import GEMINI_API_KEY, MODEL_NAME, MAX_TOKENS

client = genai.Client(api_key=GEMINI_API_KEY)

DECOMPOSITION_PROMPT = """
You are a SQL query decomposition expert. Analyze the given question and break it down into structured components.

For the question about a database table, provide:
1. Intent: What is being asked (e.g., "Count total customers", "Find average salary")
2. Tables: Which table(s) are involved
3. Columns: Which columns are needed
4. Filters: Any WHERE conditions (if any)
5. Joins: Any JOIN operations needed (if any)
6. Aggregations: Any GROUP BY, COUNT, SUM, AVG, etc.
7. Ordering: Any ORDER BY requirements (if any)

Respond in valid JSON format only, with no additional text.
"""

def decompose_query(question: str, table_schema: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """
    Decompose a natural language question into SQL components using Gemini API.
    
    Args:
        question: Natural language question about the database
        table_schema: Optional dictionary with table schema information
    
    Returns:
        Dictionary with decomposed query components
    """
    
    prompt = DECOMPOSITION_PROMPT + f"\n\nQuestion: {question}"
    
    if table_schema:
        prompt += f"\n\nTable Schema Information:\n{json.dumps(table_schema, indent=2)}"
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=genai.types.GenerateContentConfig(maxOutputTokens=MAX_TOKENS),
        )
        response_text = response.text.strip()

        try:
            decomposed = json.loads(response_text)
        except json.JSONDecodeError:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                decomposed = json.loads(response_text[json_start:json_end])
            else:
                return {"error": "Failed to parse API response", "raw_response": response_text}

        return decomposed
    
    except Exception as e:
        return {"error": str(e)}

def print_decomposition(decomposition: dict) -> None:
    """Pretty print the decomposed query."""
    if "error" in decomposition:
        print(f"❌ Error: {decomposition['error']}")
        if "raw_response" in decomposition:
            print(f"Raw response: {decomposition['raw_response']}")
        return
    
    print("\n" + "="*60)
    print("QUERY DECOMPOSITION")
    print("="*60)
    
    for key, value in decomposition.items():
        if isinstance(value, list):
            print(f"\n● {key.replace('_', ' ').title()}:")
            for item in value:
                print(f"  - {item}")
        elif isinstance(value, dict):
            print(f"\n● {key.replace('_', ' ').title()}:")
            for k, v in value.items():
                print(f"  - {k}: {v}")
        else:
            print(f"\n● {key.replace('_', ' ').title()}: {value}")
    
    print("\n" + "="*60 + "\n")


def load_questions_from_csv(csv_path: Path) -> List[str]:
    """Load question text from a CSV file with a header row."""
    questions: List[str] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            question = row.get("question")
            if question:
                question_text = question.strip()
                if question_text:
                    questions.append(question_text)
    return questions


def save_results_json(results: List[dict[str, Any]], json_path: Path) -> None:
    output = {"results": results}
    json_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")


def save_results_csv(results: List[dict[str, Any]], csv_path: Path) -> None:
    fieldnames = ["question", "decomposition", "error", "raw_response"]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in results:
            writer.writerow(
                {
                    "question": item["question"],
                    "decomposition": json.dumps(item.get("decomposition", {}), ensure_ascii=False),
                    "error": item.get("error", ""),
                    "raw_response": item.get("raw_response", ""),
                }
            )


def main() -> int:
    csv_path = Path(__file__).resolve().parent / "data" / "Sql_question.csv"
    output_json_path = Path(__file__).resolve().parent / "data" / "query_decomposition_output.json"
    output_csv_path = Path(__file__).resolve().parent / "data" / "query_decomposition_output.csv"

    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        return 1

    questions = load_questions_from_csv(csv_path)
    if not questions:
        print(f"No questions found in: {csv_path}")
        return 1

    results: List[dict[str, Any]] = []
    for index, question in enumerate(questions, start=1):
        response = decompose_query(question)
        if "error" in response:
            results.append(
                {
                    "question": question,
                    "decomposition": {},
                    "error": response["error"],
                    "raw_response": response.get("raw_response", ""),
                }
            )
        else:
            results.append(
                {
                    "question": question,
                    "decomposition": response,
                    "error": "",
                    "raw_response": "",
                }
            )

    save_results_json(results, output_json_path)
    save_results_csv(results, output_csv_path)

    print(json.dumps({"results": results}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
