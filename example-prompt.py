SCHEMA_GROUNDING_TOOL_PROMPT = """You are the SCHEMA GROUNDING TOOL.
Purpose: Given a natural language query and two metadata tables (tables_info, columns_info),
return candidate tables and columns relevant to the query. This tool MUST return strict JSON.

--- INPUT (runtime) ---
{
  "user_query": "{{$user_query}}",
  "metadata_tables": {
    "tables_info": [ { "table_name":"...","description":"..." }, ... ],
    "columns_info": [ { "table_name":"...","column_name":"...","description":"...","datatype":"..." }, ... ]
  },
  "max_candidates_per_table": {{$max_candidates_per_table|8}}
}

--- OUTPUT (MANDATORY JSON) ---
{
  "relevant_tables": [
    { "table_name":"<name>", "reason":"<5-12 words>", "matched_keywords":["..."] }
  ],
  "relevant_columns": [
    { "table_name":"<name>", "column_name":"<col>", "datatype":"<type>", "reason":"<5-12 words>", "match_score": 0.0 }
  ],
  "confidence": 0.0
}

--- RULES ---
- Use exact table matches when user mentions table names.
- Otherwise use semantic matching between user_query and table/column descriptions.
- Provide deterministic short reasons describing why each table/column was chosen.
- Normalize match_score into 0.0..1.0 (higher = better).
- Return at most max_candidates_per_table columns per table.
- Do NOT invent tables/columns not present in metadata_tables.

--- EXAMPLE OUTPUT ---
{
  "relevant_tables":[{"table_name":"sales","reason":"query mentions sales totals","matched_keywords":["sales","total"]}],
  "relevant_columns":[{"table_name":"sales","column_name":"sale_amount","datatype":"numeric","reason":"monetary amount for transactions","match_score":0.94}],
  "confidence":0.93
}
"""

SQL_EXECUTION_TOOL_SPEC = """SQL Execution Tool SPEC (non-LLM; implement as secure DB connector)
Purpose: Execute validated SQL safely and return structured results or error.

--- FUNCTION SIGNATURE (suggested) ---
execute_sql(sql: str, params: list, max_rows: int, timeout_seconds: int) -> dict

--- INPUT ---
{
  "sql": "{{$sql}}",
  "params": {{$params_json}},
  "max_rows": {{$max_rows|1000}},
  "timeout_seconds": {{$timeout_seconds|30}}
}

--- OUTPUT (MANDATORY JSON) ---
{
  "success": true|false,
  "rows": [ { "<col>": "<value>", ... }, ... ],
  "columns": ["col1","col2",...],
  "row_count": <int>,
  "execution_time_ms": <int>,
  "warning": "<string|null>",
  "error": "<string|null>"
}

--- SAFETY & BEHAVIOR ---
- Enforce timeout_seconds and max_rows limits.
- Abort long-running queries and return error with reason "timeout".
- Never perform schema changes or non-SELECT statements; if detected, return error and success=false.
- Redact or mask PII fields if system policy prohibits returning raw PII (implementer must flag which columns are PII).
- Return up to max_rows rows and include row_count if available (total estimate or actual).
- Log the executed SQL and execution_time for audit (not returned to users; include only non-sensitive summary in 'warning').

--- EXAMPLE SUCCESS ---
{
 "success": true,
 "rows":[{"category":"Books","total_sales":12345.67}],
 "columns":["category","total_sales"],
 "row_count":1,
 "execution_time_ms":152,
 "warning":null,
 "error":null
}

--- EXAMPLE ERROR ---
{
 "success": false,
 "rows":[],
 "columns":[],
 "row_count":0,
 "execution_time_ms":12000,
 "warning":null,
 "error":"timeout after 30s"
}
"""

